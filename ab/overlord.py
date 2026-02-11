"""Overlord arbitration and self-selection helpers.

This module provides a lightweight coordinator that can:
1. Accept proposals from subselves and decide on a winner.
2. Track simple per-self performance metrics and select a self for a task class.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class SelfProfile:
    """Profile of an available self."""

    name: str
    specialty: str
    past_accuracy: float = 0.5
    past_speed: float = 0.5


class Overlord:
    """Coordinator for proposal arbitration and self selection."""

    def __init__(self, _memory: Any | None = None):
        self.memory = _memory
        self.selves: list[SelfProfile] = []
        self.history: list[dict[str, Any]] = []
        self._proposals: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Proposal arbitration API (used by ab.mind)
    # ------------------------------------------------------------------
    def add_proposal(self, proposal: dict[str, Any]) -> None:
        """Register a proposal candidate.

        Expected fields:
        - ``action``: proposed output/action
        - ``priority``: numeric score, higher means better
        """
        self._proposals.append(proposal)

    def clear_proposals(self) -> None:
        """Clear pending proposals."""
        self._proposals.clear()

    def decide(self) -> dict[str, Any] | None:
        """Choose the highest-priority proposal."""
        if not self._proposals:
            return None
        winner = max(self._proposals, key=lambda p: float(p.get("priority", 0.0)))
        self.history.append({"type": "proposal_decision", "winner": winner})
        return winner

    # ------------------------------------------------------------------
    # Self selection API
    # ------------------------------------------------------------------
    def register_self(self, name: str, specialty: str) -> None:
        self.selves.append(SelfProfile(name=name, specialty=specialty))

    def select_self(self, problem_type: int = 0) -> str:
        """Select a self using weighted sampling from tracked performance."""
        if not self.selves:
            return "default"

        weights = []
        for s in self.selves:
            # Blend accuracy and speed into one simple score.
            score = max(0.01, (0.8 * s.past_accuracy) + (0.2 * s.past_speed))
            weights.append(score)

        chosen = random.choices(self.selves, weights=weights, k=1)[0]
        self.history.append(
            {
                "type": "self_selection",
                "problem_type": problem_type,
                "selected": chosen.name,
                "weights": {s.name: w for s, w in zip(self.selves, weights)},
            }
        )
        return chosen.name

    def update_performance(self, self_name: str, accuracy: float, speed: float) -> None:
        for s in self.selves:
            if s.name == self_name:
                s.past_accuracy = 0.9 * s.past_accuracy + 0.1 * accuracy
                s.past_speed = 0.9 * s.past_speed + 0.1 * speed
                return

    @staticmethod
    def get_reward(accuracy: float, speed: float) -> float:
        return accuracy * 100 + speed * 10


def create_random_overlord() -> Overlord:
    return Overlord()
