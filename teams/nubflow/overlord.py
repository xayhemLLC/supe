"""Overlord commit logic for Flow of Time (FoT) v0.0.0."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from .types import (
    AwarenessTrack,
    Buffer,
    BufferStatus,
    ExecutionTrack,
    LedgerCursor,
    NubContext,
    OverlordCommitResult,
    new_sid,
)


@dataclass
class OverlordRuleset:
    """Policy knobs used by FoT overlord commit."""

    promote_strength_threshold: float = 1.6
    allow_lossy_compression: bool = True
    automation_triggers_enabled: bool = False
    repeated_reference_threshold: int = 2
    important_tag_key: str = "important"


class Overlord:
    """Build track outputs and produce the next nub pack."""

    def __init__(self, memory: Any | None = None, ruleset: OverlordRuleset | None = None) -> None:
        self.memory = memory
        self.ruleset = ruleset or OverlordRuleset()

    def commit(
        self,
        context: NubContext,
        final_buffers: list[Buffer],
        hold_reasons: list[str] | None = None,
        error_messages: list[str] | None = None,
    ) -> OverlordCommitResult:
        hold_reasons = hold_reasons or []
        error_messages = error_messages or []

        awareness_track = self._build_awareness_track(context, final_buffers)
        execution_track = self._build_execution_track(
            context=context,
            final_buffers=final_buffers,
            hold_reasons=hold_reasons,
            error_messages=error_messages,
        )

        output_buffers = list(final_buffers)
        outbox_payload = {
            "awareness_track": asdict(awareness_track),
            "execution_track": asdict(execution_track),
            "errors": error_messages,
            "holds": hold_reasons,
        }
        output_buffers.append(
            Buffer(
                name="overlord_outbox",
                kind="outbox",
                payload=outbox_payload,
                status=BufferStatus.OK,
                destination="overlord_outbox",
                provenance=["overlord_commit"],
            )
        )

        working_context_pack = {
            "nub_sid": context.nub_sid,
            "objective": awareness_track.objective,
            "decisions": awareness_track.decisions[:5],
            "next_actions": execution_track.next_actions[:5],
        }

        updated_ledger_cursors = self._collect_ledger_cursors(final_buffers)
        next_query_plan_seeds = self._build_query_plan_seeds(final_buffers)
        next_moment_refs = [new_sid()]

        audit_records = [
            "overlord_commit:start",
            f"overlord_commit:buffers={len(final_buffers)}",
            f"overlord_commit:errors={len(error_messages)}",
            f"overlord_commit:holds={len(hold_reasons)}",
        ]

        self._persist_tracks(
            context=context,
            awareness_track=awareness_track,
            execution_track=execution_track,
            output_buffers=output_buffers,
        )

        return OverlordCommitResult(
            output_buffers=output_buffers,
            awareness_track=awareness_track,
            execution_track=execution_track,
            working_context_pack=working_context_pack,
            updated_ledger_cursors=updated_ledger_cursors,
            next_query_plan_seeds=next_query_plan_seeds,
            next_moment_refs=next_moment_refs,
            audit_records=audit_records,
        )

    def _build_awareness_track(self, context: NubContext, final_buffers: list[Buffer]) -> AwarenessTrack:
        objective = self._first_scalar(final_buffers, ("objective", "goal"))
        if not objective:
            objective = str(context.constraints.get("objective", ""))

        constraints = self._collect_list(final_buffers, ("constraints", "constraints_delta"))
        for key, value in context.constraints.items():
            if isinstance(value, (str, int, float)):
                constraints.append(f"{key}={value}")

        decisions = self._collect_list(final_buffers, ("decisions", "decision_log"))
        top_risks = self._collect_list(final_buffers, ("top_risks", "risks"))
        open_questions = self._collect_list(final_buffers, ("open_questions", "questions"))
        ledger_pointers = self._collect_ledger_pointers(final_buffers)

        return AwarenessTrack(
            objective=objective,
            decisions=self._dedupe(decisions),
            constraints=self._dedupe(constraints),
            top_risks=self._dedupe(top_risks),
            open_questions=self._dedupe(open_questions),
            ledger_pointers=self._dedupe(ledger_pointers),
        )

    def _build_execution_track(
        self,
        context: NubContext,
        final_buffers: list[Buffer],
        hold_reasons: list[str],
        error_messages: list[str],
    ) -> ExecutionTrack:
        next_actions = self._collect_list(final_buffers, ("next_actions", "actions"))
        artifacts = self._collect_list(final_buffers, ("artifacts_to_produce", "artifacts"))
        stop_conditions = self._collect_list(final_buffers, ("stop_conditions",))
        gates_and_signoffs = self._collect_list(final_buffers, ("gates_and_signoffs", "signoffs"))

        if hold_reasons:
            gates_and_signoffs.extend(f"hold:{reason}" for reason in hold_reasons)
        if error_messages and not next_actions:
            next_actions.append("retry_failed_buffers")

        if not stop_conditions and context.constraints.get("stop_when"):
            stop_conditions.append(str(context.constraints["stop_when"]))

        wip_budget = max(0, context.budget - context.budget_used)

        return ExecutionTrack(
            next_actions=self._dedupe(next_actions),
            gates_and_signoffs=self._dedupe(gates_and_signoffs),
            artifacts_to_produce=self._dedupe(artifacts),
            stop_conditions=self._dedupe(stop_conditions),
            wip_budget=wip_budget,
        )

    def _persist_tracks(
        self,
        context: NubContext,
        awareness_track: AwarenessTrack,
        execution_track: ExecutionTrack,
        output_buffers: list[Buffer],
    ) -> None:
        if self.memory is None:
            return

        try:
            from ab.models import Buffer as ABBuffer
        except Exception:
            return

        awareness_payload = json.dumps(asdict(awareness_track), sort_keys=True).encode("utf-8")
        execution_payload = json.dumps(asdict(execution_track), sort_keys=True).encode("utf-8")

        awareness_buf = ABBuffer(
            name="awareness_track",
            headers={"nub_sid": context.nub_sid, "type": "fot_awareness_track"},
            payload=awareness_payload,
        )
        execution_buf = ABBuffer(
            name="execution_track",
            headers={"nub_sid": context.nub_sid, "type": "fot_execution_track"},
            payload=execution_payload,
        )

        self.memory.store_card(
            label="fot_awareness_track",
            buffers=[awareness_buf],
            master_input=awareness_track.objective,
            master_output=json.dumps(awareness_track.decisions[:3]),
            track="awareness",
        )
        self.memory.store_card(
            label="fot_execution_track",
            buffers=[execution_buf],
            master_input="next_actions",
            master_output=json.dumps(execution_track.next_actions[:3]),
            track="execution",
        )

        for output in output_buffers:
            if not self._should_promote(output):
                continue
            compact = self._compact_payload(output.payload)
            card_buf = ABBuffer(
                name=output.name,
                headers={
                    "nub_sid": context.nub_sid,
                    "kind": output.kind,
                    "status": output.status.value,
                    "source": "fot_overlord",
                },
                payload=json.dumps(compact, sort_keys=True).encode("utf-8"),
            )
            self.memory.store_card(
                label="fot_memory_card",
                buffers=[card_buf],
                master_input=output.name,
                master_output=output.status.value,
                track="awareness",
            )

    def _should_promote(self, buffer: Buffer) -> bool:
        payload = buffer.payload if isinstance(buffer.payload, dict) else {}
        metadata = buffer.metadata or {}

        if payload.get(self.ruleset.important_tag_key) or metadata.get(self.ruleset.important_tag_key):
            return True

        references = payload.get("references", [])
        if isinstance(references, list) and len(references) >= self.ruleset.repeated_reference_threshold:
            return True

        score = float(payload.get("strength", 0.0) or 0.0)
        return score >= self.ruleset.promote_strength_threshold

    def _compact_payload(self, payload: Any) -> Any:
        if not self.ruleset.allow_lossy_compression:
            return payload
        if isinstance(payload, dict):
            return {k: payload[k] for k in list(payload)[:8]}
        return payload

    @staticmethod
    def _collect_ledger_cursors(final_buffers: list[Buffer]) -> dict[str, LedgerCursor]:
        cursors: dict[str, LedgerCursor] = {}
        for buffer in final_buffers:
            if buffer.kind == "ledger" and buffer.cursor is not None:
                cursors[buffer.name] = buffer.cursor
        return cursors

    @staticmethod
    def _build_query_plan_seeds(final_buffers: list[Buffer]) -> dict[str, dict[str, Any]]:
        seeds: dict[str, dict[str, Any]] = {}
        for buffer in final_buffers:
            if buffer.kind != "ledger":
                continue
            payload = buffer.payload if isinstance(buffer.payload, dict) else {}
            query_plan = payload.get("query_plan") or {}
            if query_plan:
                seeds[buffer.name] = dict(query_plan)
            elif buffer.cursor is not None and buffer.cursor.query_plan:
                seeds[buffer.name] = dict(buffer.cursor.query_plan)
        return seeds

    @staticmethod
    def _first_scalar(final_buffers: list[Buffer], keys: tuple[str, ...]) -> str:
        for buffer in final_buffers:
            if not isinstance(buffer.payload, dict):
                continue
            for key in keys:
                value = buffer.payload.get(key)
                if isinstance(value, (str, int, float)) and str(value).strip():
                    return str(value)
        return ""

    @staticmethod
    def _collect_list(final_buffers: list[Buffer], keys: tuple[str, ...]) -> list[str]:
        values: list[str] = []
        for buffer in final_buffers:
            payload = buffer.payload
            if not isinstance(payload, dict):
                continue
            for key in keys:
                if key not in payload:
                    continue
                raw = payload[key]
                if isinstance(raw, list):
                    values.extend(str(item) for item in raw if str(item).strip())
                elif isinstance(raw, (str, int, float)):
                    values.append(str(raw))
        return values

    @staticmethod
    def _collect_ledger_pointers(final_buffers: list[Buffer]) -> list[str]:
        pointers: list[str] = []
        for buffer in final_buffers:
            payload = buffer.payload if isinstance(buffer.payload, dict) else {}
            if buffer.kind == "ledger":
                pointers.append(buffer.name)
                if buffer.cursor is not None and buffer.cursor.paging_cursor:
                    pointers.append(f"{buffer.name}:{buffer.cursor.paging_cursor}")
            value = payload.get("pointers")
            if isinstance(value, list):
                pointers.extend(str(item) for item in value)
        return pointers

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in values:
            key = item.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
        return out
