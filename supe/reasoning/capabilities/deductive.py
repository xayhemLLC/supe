"""Deductive reasoning and logic capabilities."""

from typing import Dict, Any, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LogicOperator(Enum):
    """Logical operators."""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"


@dataclass
class LogicStatement:
    """Represents a logical statement."""
    proposition: str
    truth_value: Optional[bool] = None
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DeductiveReasoner:
    """Performs deductive logical reasoning."""

    def __init__(self):
        self.knowledge_base: Dict[str, LogicStatement] = {}

    def execute(self, problem_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deductive reasoning.

        Args:
            problem_text: The problem statement
            context: Context including logical statements

        Returns:
            Result dictionary
        """
        # Get statements from context
        statements = context.get("statements", [])
        if not statements:
            return {"success": False, "error": "No logical statements provided"}

        # Get goal/query
        goal = context.get("goal")

        # Build knowledge base
        for stmt in statements:
            if isinstance(stmt, dict):
                self.knowledge_base[stmt["name"]] = LogicStatement(
                    proposition=stmt.get("proposition", stmt["name"]),
                    truth_value=stmt.get("truth_value"),
                    dependencies=stmt.get("dependencies", []),
                )

        # If goal specified, try to derive it
        if goal:
            result = self.can_derive(goal)
            return {
                "success": True,
                "goal": goal,
                "derivable": result["derivable"],
                "proof": result.get("proof", []),
                "confidence": result.get("confidence", 0.0),
            }

        # Otherwise, list all derivable facts
        return {
            "success": True,
            "knowledge_base": {k: v.proposition for k, v in self.knowledge_base.items()},
        }

    def can_derive(self, goal: str) -> Dict[str, Any]:
        """Check if goal can be derived from knowledge base.

        Args:
            goal: Goal statement to derive

        Returns:
            Result with derivability and proof
        """
        # Check if goal is directly in knowledge base
        if goal in self.knowledge_base:
            stmt = self.knowledge_base[goal]
            if stmt.truth_value is True:
                return {
                    "derivable": True,
                    "proof": [f"Given: {stmt.proposition}"],
                    "confidence": 1.0,
                }

        # Try to derive through dependencies
        proof_steps = []
        confidence = self._attempt_derivation(goal, proof_steps, visited=set())

        return {
            "derivable": confidence > 0,
            "proof": proof_steps,
            "confidence": confidence,
        }

    def _attempt_derivation(
        self,
        goal: str,
        proof_steps: List[str],
        visited: Set[str],
    ) -> float:
        """Attempt to derive goal recursively.

        Args:
            goal: Goal to derive
            proof_steps: Accumulating proof steps
            visited: Visited statements (avoid cycles)

        Returns:
            Confidence in derivation (0.0-1.0)
        """
        if goal in visited:
            return 0.0

        visited.add(goal)

        # Check direct facts
        if goal in self.knowledge_base:
            stmt = self.knowledge_base[goal]

            if stmt.truth_value is True:
                proof_steps.append(f"Known: {stmt.proposition}")
                return 1.0

            # Try to derive from dependencies
            if stmt.dependencies:
                all_derived = True
                min_confidence = 1.0

                for dep in stmt.dependencies:
                    dep_confidence = self._attempt_derivation(dep, proof_steps, visited)
                    if dep_confidence == 0:
                        all_derived = False
                        break
                    min_confidence = min(min_confidence, dep_confidence)

                if all_derived:
                    proof_steps.append(
                        f"Derive: {stmt.proposition} from {', '.join(stmt.dependencies)}"
                    )
                    return min_confidence * 0.95  # Slight degradation

        return 0.0

    def modus_ponens(self, p: str, p_implies_q: str) -> Optional[str]:
        """Apply modus ponens: if P and (P → Q), then Q.

        Args:
            p: Statement P
            p_implies_q: Statement "P implies Q"

        Returns:
            Derived statement Q or None
        """
        # Check if both premises are true
        if p not in self.knowledge_base or p_implies_q not in self.knowledge_base:
            return None

        p_stmt = self.knowledge_base[p]
        impl_stmt = self.knowledge_base[p_implies_q]

        if p_stmt.truth_value and impl_stmt.truth_value:
            # Extract Q from "P implies Q"
            # Simple parsing for demonstration
            return f"derived_from_{p}_and_{p_implies_q}"

        return None

    def syllogism(
        self,
        all_p_are_q: str,
        all_q_are_r: str
    ) -> Optional[str]:
        """Apply syllogism: if all P are Q and all Q are R, then all P are R.

        Args:
            all_p_are_q: Statement "all P are Q"
            all_q_are_r: Statement "all Q are R"

        Returns:
            Derived statement or None
        """
        # Check both premises
        if all_p_are_q not in self.knowledge_base or all_q_are_r not in self.knowledge_base:
            return None

        p1 = self.knowledge_base[all_p_are_q]
        p2 = self.knowledge_base[all_q_are_r]

        if p1.truth_value and p2.truth_value:
            return f"all_P_are_R_derived_from_{all_p_are_q}_and_{all_q_are_r}"

        return None

    def check_consistency(self) -> Dict[str, Any]:
        """Check knowledge base for logical consistency.

        Returns:
            Consistency check result
        """
        contradictions = []

        # Look for direct contradictions (P and NOT P)
        statements = list(self.knowledge_base.keys())

        for i, stmt1 in enumerate(statements):
            for stmt2 in statements[i+1:]:
                # Simple check: same proposition with opposite truth values
                if self.knowledge_base[stmt1].proposition == self.knowledge_base[stmt2].proposition:
                    if self.knowledge_base[stmt1].truth_value != self.knowledge_base[stmt2].truth_value:
                        contradictions.append({
                            "stmt1": stmt1,
                            "stmt2": stmt2,
                            "type": "direct_contradiction",
                        })

        return {
            "consistent": len(contradictions) == 0,
            "contradictions": contradictions,
        }

    def two_guards_puzzle(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Solve the classic two guards puzzle.

        Args:
            context: Puzzle context

        Returns:
            Solution
        """
        solution = {
            "question": "What would the other guard say is the door to freedom?",
            "strategy": "Ask either guard and take the opposite door",
            "reasoning": [
                "If you ask the truth-teller: they'll truthfully say the liar would point to death",
                "If you ask the liar: they'll lie and say the truth-teller would point to death",
                "Either way, both point to the death door",
                "So take the opposite door to get freedom",
            ],
            "proof": [
                "Let T = truth-teller, L = liar, F = freedom door, D = death door",
                "Case 1: Ask T 'What would L say?' → T truthfully reports L would say D → Take opposite (F)",
                "Case 2: Ask L 'What would T say?' → L lies, T would say F, but L says D → Take opposite (F)",
                "Both cases lead to freedom door",
            ],
        }

        return {
            "success": True,
            "solution": solution,
        }
