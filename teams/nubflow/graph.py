"""Buffer graph and bounded routing engine for FoT."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import replace
from time import monotonic

from .types import (
    Buffer,
    BufferEdge,
    BufferNode,
    BufferStatus,
    FoTState,
    RouteBounds,
    RouteOutcome,
    RouteToken,
    TransformResult,
    new_sid,
)


class BufferGraph:
    """Directed graph with bounded token traversal."""

    def __init__(self) -> None:
        self._nodes: dict[str, BufferNode] = {}
        self._edges: dict[str, list[BufferEdge]] = defaultdict(list)

    def add_node(self, node: BufferNode) -> None:
        self._nodes[node.name] = node

    def add_edge(self, edge: BufferEdge) -> None:
        if edge.from_node not in self._nodes:
            raise KeyError(f"Unknown node: {edge.from_node}")
        if edge.to_node not in self._nodes:
            raise KeyError(f"Unknown node: {edge.to_node}")
        self._edges[edge.from_node].append(edge)

    def node(self, name: str) -> BufferNode | None:
        return self._nodes.get(name)

    def route(
        self,
        seed_buffers: list[Buffer],
        context,
        bounds: RouteBounds | None = None,
    ) -> RouteOutcome:
        """Route buffers through the graph with bounded traversal."""
        limits = bounds or RouteBounds()
        queue: deque[tuple[RouteToken, Buffer]] = deque()
        outcome = RouteOutcome()
        emitted_tokens = 0
        started_at = monotonic()

        for seed in seed_buffers:
            start = self.node(seed.name)
            if start is None:
                finalized = self._finalize_buffer(seed, destination="overlord_inbox")
                outcome.final_buffers.append(finalized)
                if finalized.status == BufferStatus.FAILED:
                    outcome.errors.append(finalized)
                continue
            token = RouteToken(
                buffer_sid=seed.sid,
                current_node=start.name,
                provenance=[start.name],
            )
            queue.append((token, seed))

        while queue:
            elapsed_ms = int((monotonic() - started_at) * 1000)
            if elapsed_ms >= limits.max_ms or emitted_tokens >= limits.max_tokens:
                context.audit.append(
                    f"route bounds reached: elapsed_ms={elapsed_ms}, emitted_tokens={emitted_tokens}"
                )
                outcome.exhausted_budget = True
                break

            token, buffer = queue.popleft()
            node = self.node(token.current_node)
            if node is None:
                finalized = self._finalize_buffer(buffer, destination="overlord_inbox")
                outcome.final_buffers.append(finalized)
                continue

            if token.hop_count > limits.max_hops:
                capped = replace(
                    buffer,
                    status=BufferStatus.SKIPPED,
                    error="max_hops_exceeded",
                    destination=node.name,
                )
                capped.provenance = list(buffer.provenance) + ["max_hops_exceeded"]
                outcome.final_buffers.append(capped)
                outcome.errors.append(capped)
                continue

            context.state = FoTState.TRANSFORM
            transformed = self._apply_transform(node, buffer, token, context)
            if transformed.hold:
                held_items = transformed.buffers or [buffer]
                for held in held_items:
                    held.status = BufferStatus.HELD
                    held.error = transformed.hold_reason or "human_signoff_required"
                    held.destination = node.name
                    if node.name not in held.provenance:
                        held.provenance.append(node.name)
                    outcome.holds.append(held)
                continue

            current_buffers = transformed.buffers or [buffer]
            if transformed.error:
                for current in current_buffers:
                    current.status = BufferStatus.FAILED
                    current.error = transformed.error
                    current.transforms.append(f"error:{node.name}")

            if transformed.stop_token:
                for current in current_buffers:
                    finalized = self._finalize_buffer(current, destination=node.name)
                    outcome.final_buffers.append(finalized)
                    if finalized.status == BufferStatus.FAILED:
                        outcome.errors.append(finalized)
                continue

            context.state = FoTState.ROUTE
            outgoing = self._sorted_edges(node.name)

            for current in current_buffers:
                if node.name not in current.provenance:
                    current.provenance.append(node.name)

                matched = [
                    edge
                    for edge in outgoing
                    if self._edge_matches(edge, current, token, context)
                ]

                if node.is_terminal or not matched:
                    finalized = self._finalize_buffer(current, destination=node.name)
                    outcome.final_buffers.append(finalized)
                    if finalized.status == BufferStatus.FAILED:
                        outcome.errors.append(finalized)
                    continue

                for edge in matched:
                    if token.hop_count + 1 > min(limits.max_hops, edge.max_hops):
                        skipped = replace(
                            current,
                            status=BufferStatus.SKIPPED,
                            error="edge_max_hops_exceeded",
                            destination=edge.to_node,
                        )
                        skipped.provenance = list(current.provenance) + ["edge_max_hops_exceeded"]
                        outcome.final_buffers.append(skipped)
                        outcome.errors.append(skipped)
                        continue

                    next_buffer = replace(current, sid=new_sid())
                    next_buffer.provenance = list(current.provenance)

                    next_token = RouteToken(
                        buffer_sid=next_buffer.sid,
                        current_node=edge.to_node,
                        hop_count=token.hop_count + 1,
                        provenance=list(token.provenance) + [edge.to_node],
                        budget_used=token.budget_used + 1,
                    )
                    emitted_tokens += 1
                    queue.append((next_token, next_buffer))

        outcome.active_tokens = len(queue)
        outcome.emitted_tokens = emitted_tokens
        for _token, buffer in queue:
            if buffer.status == BufferStatus.PENDING:
                buffer.status = BufferStatus.SKIPPED
                buffer.error = "routing_budget_exhausted"
                buffer.destination = buffer.destination or _token.current_node
                if buffer.destination not in buffer.provenance:
                    buffer.provenance.append(buffer.destination)
            outcome.final_buffers.append(buffer)
            outcome.errors.append(buffer)

        return outcome

    def _sorted_edges(self, node_name: str) -> list[BufferEdge]:
        edges = self._edges.get(node_name, [])
        return sorted(edges, key=lambda edge: (-edge.weight, edge.to_node))

    @staticmethod
    def _edge_matches(edge: BufferEdge, buffer: Buffer, token: RouteToken, context) -> bool:
        if edge.condition is None:
            return True
        try:
            return bool(edge.condition(buffer, token, context))
        except Exception:
            return False

    @staticmethod
    def _apply_transform(node: BufferNode, buffer: Buffer, token: RouteToken, context) -> TransformResult:
        if node.transform is None:
            return TransformResult(applicable=False, buffers=[buffer])

        try:
            result = node.transform(buffer, token, context)
        except Exception as exc:
            # v0 transform policy: pass-through with error.
            pass_buffer = replace(buffer)
            pass_buffer.error = str(exc)
            pass_buffer.status = BufferStatus.FAILED
            return TransformResult(applicable=True, buffers=[pass_buffer], error=str(exc))

        if not result.applicable:
            return TransformResult(applicable=False, buffers=[buffer])

        if not result.buffers:
            result.buffers = [buffer]
        return result

    @staticmethod
    def _finalize_buffer(buffer: Buffer, destination: str) -> Buffer:
        if buffer.destination is None:
            buffer.destination = destination
        if buffer.status == BufferStatus.PENDING:
            buffer.status = BufferStatus.FAILED if buffer.error else BufferStatus.OK
        if buffer.status == BufferStatus.OK and buffer.error:
            buffer.status = BufferStatus.FAILED
        return buffer
