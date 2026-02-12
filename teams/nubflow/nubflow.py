"""Flow of Time (FoT) v0.0.0 deterministic nub lifecycle engine."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .buffers import MasterBufferRegistry
from .graph import BufferGraph
from .ledgers import LedgerRegistry
from .overlord import Overlord, OverlordRuleset
from .types import (
    Buffer,
    BufferEdge,
    BufferNode,
    BufferStatus,
    ErrorPack,
    FoTState,
    HoldPack,
    InputEvent,
    NubContext,
    NubExitPack,
    RouteBounds,
    TransformResult,
    ensure_input_event,
    new_sid,
    utcnow_iso,
)


class FlowOfTimeEngine:
    """Deterministic FSM implementing ``nub::next`` for FoT v0.0.0."""

    def __init__(
        self,
        *,
        ledger_registry: LedgerRegistry | None = None,
        buffer_registry: MasterBufferRegistry | None = None,
        buffer_graph: BufferGraph | None = None,
        overlord: Overlord | None = None,
        overlord_ruleset: OverlordRuleset | None = None,
        route_bounds: RouteBounds | None = None,
    ) -> None:
        self.ledger_registry = ledger_registry or LedgerRegistry.with_defaults()
        self.buffer_registry = buffer_registry or MasterBufferRegistry.initialize(self.ledger_registry)
        self.buffer_graph = buffer_graph or self._default_graph()
        self.overlord = overlord or Overlord(ruleset=overlord_ruleset)
        self.route_bounds = route_bounds or RouteBounds()

    def nub_next(
        self,
        prev_nub_exit_pack: NubExitPack | dict[str, Any] | None,
        sys_inputs: list[InputEvent | dict[str, Any] | Any] | InputEvent | dict[str, Any] | Any | None,
        context_ref: dict[str, Any] | None = None,
        constraints_pack: dict[str, Any] | None = None,
        budget: int = 200,
    ) -> NubExitPack:
        """Advance to the next moment using FoT lifecycle semantics."""
        context = NubContext(
            nub_sid=new_sid(),
            start_time=utcnow_iso(),
            budget=max(1, budget),
            constraints=constraints_pack or {},
            active_workflow_cursor=(context_ref or {}).get("workflow_cursor"),
            team_scope=(context_ref or {}).get("team_scope"),
            state=FoTState.ENTER,
        )
        context.audit.append(f"{FoTState.ENTER.value}:{context.nub_sid}")

        context.state = FoTState.ABSORB
        context.audit.append(FoTState.ABSORB.value)
        events = self._normalize_inputs(prev_nub_exit_pack, sys_inputs)

        context.state = FoTState.STORE
        context.audit.append(FoTState.STORE.value)
        route_inputs = self.buffer_registry.absorb_events(events)

        context.state = FoTState.ROUTE
        context.audit.append(FoTState.ROUTE.value)
        route_outcome = self.buffer_graph.route(route_inputs, context=context, bounds=self.route_bounds)
        context.budget_used += route_outcome.emitted_tokens

        context.state = FoTState.FINALIZE
        context.audit.append(FoTState.FINALIZE.value)
        final_buffers = self._finalize(route_outcome.final_buffers)

        hold_reasons = [buf.error or "human_signoff_required" for buf in route_outcome.holds]
        error_messages = [buf.error for buf in route_outcome.errors if buf.error]

        context.state = FoTState.OVERLORD_COMMIT
        context.audit.append(FoTState.OVERLORD_COMMIT.value)
        commit = self.overlord.commit(
            context=context,
            final_buffers=final_buffers,
            hold_reasons=hold_reasons,
            error_messages=error_messages,
        )

        for name, cursor in commit.updated_ledger_cursors.items():
            self.buffer_registry.update_ledger_cursor(name, cursor)

        hold_pack = None
        error_pack = None
        state = FoTState.EXIT
        if hold_reasons:
            state = FoTState.HOLD
            hold_pack = HoldPack(
                reason=hold_reasons[0],
                required_signoff="role:Approver",
                artifact_key="human_signoff_artifact",
            )
        elif error_messages:
            state = FoTState.ERROR
            error_pack = ErrorPack(
                message=error_messages[0],
                recoverable=True,
                details={"count": len(error_messages)},
            )

        if state == FoTState.EXIT:
            context.audit.append(FoTState.EXIT.value)
        elif state == FoTState.HOLD:
            context.audit.append(FoTState.HOLD.value)
        else:
            context.audit.append(FoTState.ERROR.value)

        return NubExitPack(
            nub_sid=context.nub_sid,
            state=state,
            output_buffers=commit.output_buffers,
            awareness_track=commit.awareness_track,
            execution_track=commit.execution_track,
            updated_ledger_cursors=commit.updated_ledger_cursors,
            next_query_plan_seeds=commit.next_query_plan_seeds,
            next_moment_refs=commit.next_moment_refs,
            audit_records=context.audit + commit.audit_records,
            hold_pack=hold_pack,
            error_pack=error_pack,
        )

    def _default_graph(self) -> BufferGraph:
        graph = BufferGraph()

        graph.add_node(BufferNode(name="master_input", kind="input"))
        graph.add_node(BufferNode(name="sensory_input", kind="input"))
        graph.add_node(BufferNode(name="exec_track_in", kind="track_in"))
        graph.add_node(BufferNode(name="awareness_track_in", kind="track_in"))
        graph.add_node(BufferNode(name="git_ledger", kind="ledger", transform=self._ledger_transform("git_ledger")))
        graph.add_node(BufferNode(name="jira_ledger", kind="ledger", transform=self._ledger_transform("jira_ledger")))
        graph.add_node(BufferNode(name="notion_ledger", kind="ledger", transform=self._ledger_transform("notion_ledger")))
        graph.add_node(BufferNode(name="discord_ledger", kind="ledger", transform=self._ledger_transform("discord_ledger")))
        graph.add_node(BufferNode(name="web_ledger", kind="ledger", transform=self._ledger_transform("web_ledger")))
        graph.add_node(BufferNode(name="human_gate", kind="gate", transform=self._human_gate_transform))
        graph.add_node(BufferNode(name="overlord_inbox", kind="inbox", is_terminal=True))
        graph.add_node(BufferNode(name="overlord_outbox", kind="outbox", is_terminal=True))
        graph.add_node(BufferNode(name="output_overlord", kind="outbox", is_terminal=True))

        graph.add_edge(
            BufferEdge(
                from_node="master_input",
                to_node="human_gate",
                condition=lambda b, _t, _c: bool(isinstance(b.payload, dict) and b.payload.get("requires_human_signoff")),
                weight=2.0,
            )
        )
        graph.add_edge(
            BufferEdge(
                from_node="master_input",
                to_node="overlord_inbox",
                condition=lambda b, _t, _c: not bool(
                    isinstance(b.payload, dict) and b.payload.get("requires_human_signoff")
                ),
                weight=1.0,
            )
        )

        for source in (
            "sensory_input",
            "exec_track_in",
            "awareness_track_in",
            "git_ledger",
            "jira_ledger",
            "notion_ledger",
            "discord_ledger",
            "web_ledger",
            "human_gate",
        ):
            graph.add_edge(BufferEdge(from_node=source, to_node="overlord_inbox", weight=1.0))

        graph.add_edge(BufferEdge(from_node="overlord_inbox", to_node="output_overlord", weight=1.0))

        return graph

    def _ledger_transform(self, buffer_name: str):
        def _transform(buffer: Buffer, _token, context: NubContext) -> TransformResult:
            adapter = self.ledger_registry.by_buffer_name(buffer_name)
            if adapter is None:
                return TransformResult(applicable=False, buffers=[buffer])

            payload = buffer.payload if isinstance(buffer.payload, dict) else {"value": buffer.payload}
            query_plan = payload.get("query_plan") or {}
            goal = str(payload.get("goal") or context.constraints.get("objective") or "")
            cursor = buffer.cursor
            if cursor is None:
                cursor = self.buffer_registry.get(buffer_name).cursor
            if cursor is None:
                cursor = replace(
                    self.buffer_registry.get(buffer_name).cursor
                ) if self.buffer_registry.get(buffer_name).cursor else None
            if cursor is None:
                from .types import LedgerCursor

                cursor = LedgerCursor(ledger_sid=adapter.sid)

            result = adapter.query(query_plan=query_plan, cursor=cursor, budget=max(1, context.budget))
            summary = adapter.summarize(items=result.items, goal=goal, budget=max(1, context.budget))

            next_cursor = replace(cursor)
            next_cursor.paging_cursor = result.next_cursor
            next_cursor.last_seen = utcnow_iso()
            next_cursor.query_plan = query_plan

            transformed_payload = {
                **payload,
                "ledger_kind": adapter.kind,
                "items": result.items,
                "evidence_pack": result.evidence_pack,
                "summary_artifact": summary.summary_artifact,
                "pointers": summary.pointers,
                "query_plan": query_plan,
            }

            transformed = replace(buffer, payload=transformed_payload, cursor=next_cursor)
            transformed.transforms = list(buffer.transforms) + [f"ledger_query:{buffer_name}"]
            transformed.ledger_ref_sid = adapter.sid
            return TransformResult(applicable=True, buffers=[transformed])

        return _transform

    @staticmethod
    def _human_gate_transform(buffer: Buffer, _token, _context: NubContext) -> TransformResult:
        payload = buffer.payload if isinstance(buffer.payload, dict) else {}
        if payload.get("requires_human_signoff"):
            reason = str(payload.get("hold_reason") or "human_signoff_required")
            held = replace(buffer)
            held.status = BufferStatus.HELD
            held.error = reason
            held.transforms = list(buffer.transforms) + ["human_gate:hold"]
            return TransformResult(applicable=True, buffers=[held], hold=True, hold_reason=reason, stop_token=True)
        return TransformResult(applicable=False, buffers=[buffer])

    @staticmethod
    def _normalize_inputs(
        prev_nub_exit_pack: NubExitPack | dict[str, Any] | None,
        sys_inputs: list[InputEvent | dict[str, Any] | Any] | InputEvent | dict[str, Any] | Any | None,
    ) -> list[InputEvent]:
        events: list[InputEvent] = []

        if prev_nub_exit_pack:
            output_buffers: list[Any] = []
            if isinstance(prev_nub_exit_pack, NubExitPack):
                output_buffers = list(prev_nub_exit_pack.output_buffers)
            elif isinstance(prev_nub_exit_pack, dict):
                output_buffers = list(prev_nub_exit_pack.get("output_buffers") or [])

            for item in output_buffers:
                if isinstance(item, Buffer):
                    payload = {
                        "name": item.name,
                        "kind": item.kind,
                        "payload": item.payload,
                        "status": item.status.value,
                        "provenance": list(item.provenance),
                    }
                elif isinstance(item, dict):
                    payload = item
                else:
                    payload = {"value": item}
                events.append(InputEvent(kind="prev_output", payload=payload, source="prev_nub_exit_pack"))

        if sys_inputs is None:
            return events

        values = sys_inputs if isinstance(sys_inputs, list) else [sys_inputs]
        for value in values:
            events.append(ensure_input_event(value))

        return events

    @staticmethod
    def _finalize(final_buffers: list[Buffer]) -> list[Buffer]:
        finalized: list[Buffer] = []
        for buffer in final_buffers:
            item = replace(buffer)
            if item.status == BufferStatus.PENDING:
                item.status = BufferStatus.FAILED if item.error else BufferStatus.OK
            if item.destination is None:
                item.destination = "overlord_inbox"
            finalized.append(item)
        return finalized


class FlowOfTime(FlowOfTimeEngine):
    """Alias class with product naming."""


NubFlow = FlowOfTimeEngine
