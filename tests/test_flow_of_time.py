"""Tests for Flow of Time (FoT) v0.0.0 engine."""

from __future__ import annotations

from ab.abdb import ABMemory
from teams.nubflow import FlowOfTimeEngine, FoTState
from teams.nubflow.overlord import Overlord


def test_fot_nub_next_routes_and_commits_tracks() -> None:
    engine = FlowOfTimeEngine()

    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[
            {
                "kind": "input",
                "source": "user",
                "payload": {
                    "goal": "Ship backend feature",
                    "objective": "Ship backend feature",
                    "decisions": ["use_canary_release"],
                    "next_actions": ["open_pr"],
                    "artifacts_to_produce": ["release_notes"],
                },
            }
        ],
        constraints_pack={"objective": "Ship backend feature"},
    )

    assert exit_pack.state == FoTState.EXIT
    assert exit_pack.awareness_track.objective == "Ship backend feature"
    assert "use_canary_release" in exit_pack.awareness_track.decisions
    assert "open_pr" in exit_pack.execution_track.next_actions
    assert "release_notes" in exit_pack.execution_track.artifacts_to_produce
    assert any(buf.name == "overlord_outbox" for buf in exit_pack.output_buffers)


def test_fot_hold_transition_requires_human_signoff() -> None:
    engine = FlowOfTimeEngine()

    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[
            {
                "kind": "input",
                "source": "user",
                "payload": {
                    "requires_human_signoff": True,
                    "hold_reason": "manual_scope_change",
                },
            }
        ],
    )

    assert exit_pack.state == FoTState.HOLD
    assert exit_pack.hold_pack is not None
    assert exit_pack.hold_pack.reason == "manual_scope_change"


def test_fot_transform_failure_passes_through_with_error() -> None:
    engine = FlowOfTimeEngine()

    node = engine.buffer_graph.node("master_input")
    assert node is not None

    def boom(*_args, **_kwargs):
        raise RuntimeError("forced_transform_failure")

    node.transform = boom

    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"goal": "x"}}],
    )

    assert exit_pack.state == FoTState.ERROR
    assert exit_pack.error_pack is not None
    assert "forced_transform_failure" in exit_pack.error_pack.message
    assert any("forced_transform_failure" in (buf.error or "") for buf in exit_pack.output_buffers)


def test_fot_ledger_routing_populates_pointers() -> None:
    engine = FlowOfTimeEngine()

    exit_pack = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[
            {
                "kind": "input",
                "source": "git",
                "payload": {
                    "goal": "inspect_commits",
                    "query_plan": {"limit": 2},
                },
            }
        ],
    )

    assert exit_pack.state == FoTState.EXIT
    assert any(pointer.startswith("git_ledger") for pointer in exit_pack.awareness_track.ledger_pointers)


def test_fot_overlord_persists_tracks_into_ab_memory() -> None:
    memory = ABMemory(":memory:")
    engine = FlowOfTimeEngine(overlord=Overlord(memory=memory))

    _ = engine.nub_next(
        prev_nub_exit_pack=None,
        sys_inputs=[{"kind": "input", "source": "user", "payload": {"goal": "persist"}}],
    )

    awareness_cards = memory.search_cards("fot_awareness_track", track="awareness")
    execution_cards = memory.search_cards("fot_execution_track", track="execution")

    assert any(card.label == "fot_awareness_track" for card in awareness_cards)
    assert any(card.label == "fot_execution_track" for card in execution_cards)

    memory.close()
