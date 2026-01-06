"""Learning loop that improves the system from every problem solved.

This module implements continuous learning:
1. Store every problem + solution as an example
2. Extract patterns from successful solutions
3. Abstract common patterns into new capabilities
4. Build reasoning by analogy from past problems
5. Improve confidence scores based on performance
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import json

from ab.abdb import ABMemory
from ab.models import Buffer
from tasc.relations import Relation, RelationType
from tasc.relation_storage import store_relation
from tasc.validation_integration import ValidationRelationIntegrator

from supe.reasoning.problem_types import ProblemSignature, ReasoningPattern, ProblemDomain
from supe.reasoning.capability_registry import ReasoningCapability


@dataclass
class ProblemSolution:
    """A solved problem with its solution trace."""
    problem_text: str
    signature: ProblemSignature
    solution: Any
    success: bool
    strategy_used: str
    steps_taken: List[Dict[str, Any]]
    time_to_solve: float
    capabilities_used: Set[str]
    timestamp: datetime = field(default_factory=datetime.now)
    card_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "problem_text": self.problem_text,
            "signature": self.signature.to_dict(),
            "solution": str(self.solution),
            "success": self.success,
            "strategy_used": self.strategy_used,
            "steps_taken": self.steps_taken,
            "time_to_solve": self.time_to_solve,
            "capabilities_used": list(self.capabilities_used),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReasoningPattern:
    """An extracted reasoning pattern from multiple problems."""
    name: str
    problem_structures: Set[str]
    typical_steps: List[str]
    success_count: int
    failure_count: int
    example_problems: List[int]  # Card IDs

    def confidence(self) -> float:
        """Calculate confidence in this pattern."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5


class ProblemLibrary:
    """Library of solved problems for reasoning by analogy."""

    def __init__(self, memory: ABMemory):
        """Initialize problem library.

        Args:
            memory: ABMemory instance for persistent storage
        """
        self.memory = memory
        self.integrator = ValidationRelationIntegrator(memory)
        self.solved_problems: List[ProblemSolution] = []
        self._load_from_memory()

    def _load_from_memory(self):
        """Load previously solved problems from memory."""
        # Query for problem solution cards
        # This is a placeholder - would need proper querying
        pass

    def add_solution(self, solution: ProblemSolution) -> int:
        """Add a solved problem to the library.

        Args:
            solution: The problem solution to store

        Returns:
            Card ID of stored solution
        """
        # Store in memory
        card = self.memory.store_card(
            label=f"Problem: {solution.signature.structure}",
            buffers=[
                Buffer(name="problem", payload=solution.problem_text.encode()),
                Buffer(name="solution_data", payload=json.dumps(solution.to_dict()).encode()),
                Buffer(name="domain", payload=solution.signature.domain.value.encode()),
                Buffer(name="success", payload=str(solution.success).encode()),
            ],
            track="awareness",
        )

        solution.card_id = card.id
        self.solved_problems.append(solution)

        return card.id

    def find_similar_problems(
        self,
        signature: ProblemSignature,
        min_similarity: float = 0.5,
    ) -> List[ProblemSolution]:
        """Find problems similar to the given signature.

        Args:
            signature: Problem signature to match
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of similar solved problems
        """
        similar = []

        for solution in self.solved_problems:
            similarity = self._calculate_similarity(signature, solution.signature)
            if similarity >= min_similarity:
                similar.append(solution)

        # Sort by similarity (most similar first)
        similar.sort(key=lambda s: self._calculate_similarity(signature, s.signature), reverse=True)

        return similar

    def _calculate_similarity(
        self,
        sig1: ProblemSignature,
        sig2: ProblemSignature,
    ) -> float:
        """Calculate similarity between two problem signatures.

        Returns:
            Similarity score (0-1)
        """
        score = 0.0

        # Domain match (0.3 weight)
        if sig1.domain == sig2.domain:
            score += 0.3

        # Structure match (0.3 weight)
        if sig1.structure == sig2.structure:
            score += 0.3

        # Pattern overlap (0.4 weight)
        if sig1.required_patterns and sig2.required_patterns:
            overlap = len(sig1.required_patterns & sig2.required_patterns)
            total = len(sig1.required_patterns | sig2.required_patterns)
            score += 0.4 * (overlap / total if total > 0 else 0)

        return score

    def get_success_rate_for_structure(self, structure: str) -> float:
        """Get success rate for a specific problem structure."""
        relevant = [s for s in self.solved_problems if s.signature.structure == structure]
        if not relevant:
            return 0.5  # Unknown

        successes = sum(1 for s in relevant if s.success)
        return successes / len(relevant)

    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics."""
        total = len(self.solved_problems)
        successful = sum(1 for s in self.solved_problems if s.success)

        # By domain
        by_domain = {}
        for solution in self.solved_problems:
            domain = solution.signature.domain.value
            if domain not in by_domain:
                by_domain[domain] = {"total": 0, "success": 0}
            by_domain[domain]["total"] += 1
            if solution.success:
                by_domain[domain]["success"] += 1

        # By structure
        by_structure = {}
        for solution in self.solved_problems:
            struct = solution.signature.structure
            if struct not in by_structure:
                by_structure[struct] = {"total": 0, "success": 0}
            by_structure[struct]["total"] += 1
            if solution.success:
                by_structure[struct]["success"] += 1

        return {
            "total_problems": total,
            "successful": successful,
            "success_rate": successful / total if total > 0 else 0,
            "by_domain": by_domain,
            "by_structure": by_structure,
            "unique_structures": len(by_structure),
        }


class PatternExtractor:
    """Extracts reusable patterns from solved problems."""

    def __init__(self, library: ProblemLibrary, memory: ABMemory):
        """Initialize pattern extractor.

        Args:
            library: Problem library to extract from
            memory: ABMemory instance
        """
        self.library = library
        self.memory = memory
        self.integrator = ValidationRelationIntegrator(memory)
        self.extracted_patterns: Dict[str, ReasoningPattern] = {}

    def extract_patterns(self, min_occurrences: int = 3) -> List[ReasoningPattern]:
        """Extract common patterns from solved problems.

        Args:
            min_occurrences: Minimum times pattern must appear

        Returns:
            List of extracted patterns
        """
        # Group problems by structure
        by_structure: Dict[str, List[ProblemSolution]] = {}

        for solution in self.library.solved_problems:
            struct = solution.signature.structure
            if struct not in by_structure:
                by_structure[struct] = []
            by_structure[struct].append(solution)

        # Extract patterns from groups
        patterns = []

        for structure, solutions in by_structure.items():
            if len(solutions) >= min_occurrences:
                pattern = self._extract_pattern_from_group(structure, solutions)
                if pattern:
                    patterns.append(pattern)
                    self.extracted_patterns[pattern.name] = pattern

        return patterns

    def _extract_pattern_from_group(
        self,
        structure: str,
        solutions: List[ProblemSolution],
    ) -> Optional[ReasoningPattern]:
        """Extract a pattern from a group of similar solutions."""
        # Find common steps
        all_steps = []
        for solution in solutions:
            steps = [step.get("action", "") for step in solution.steps_taken]
            all_steps.append(steps)

        # Find most common sequence
        if not all_steps:
            return None

        # Simple approach: use steps from most successful solution
        successful = [s for s in solutions if s.success]
        if not successful:
            return None

        best = max(successful, key=lambda s: len(s.steps_taken))
        typical_steps = [step.get("action", "") for step in best.steps_taken]

        # Count successes/failures
        success_count = sum(1 for s in solutions if s.success)
        failure_count = len(solutions) - success_count

        # Get example problem IDs
        example_ids = [s.card_id for s in solutions[:5] if s.card_id]

        return ReasoningPattern(
            name=f"pattern_{structure}",
            problem_structures={structure},
            typical_steps=typical_steps,
            success_count=success_count,
            failure_count=failure_count,
            example_problems=example_ids,
        )

    def suggest_capability_from_pattern(
        self,
        pattern: ReasoningPattern,
    ) -> Optional[Dict[str, Any]]:
        """Suggest a new capability based on extracted pattern.

        Args:
            pattern: The pattern to convert to capability

        Returns:
            Capability specification or None
        """
        if pattern.confidence() < 0.7:
            return None  # Not confident enough

        # This would analyze the pattern and suggest a new capability
        return {
            "name": f"learned_{pattern.name}",
            "description": f"Learned pattern for {list(pattern.problem_structures)}",
            "typical_steps": pattern.typical_steps,
            "confidence": pattern.confidence(),
            "evidence_count": pattern.success_count,
        }


class LearningLoop:
    """Continuous learning system that improves from each problem."""

    def __init__(self, memory: ABMemory):
        """Initialize learning loop.

        Args:
            memory: ABMemory instance
        """
        self.memory = memory
        self.integrator = ValidationRelationIntegrator(memory)
        self.library = ProblemLibrary(memory)
        self.pattern_extractor = PatternExtractor(self.library, memory)

    def record_solution(
        self,
        problem_text: str,
        signature: ProblemSignature,
        solution: Any,
        success: bool,
        strategy_used: str,
        steps_taken: List[Dict[str, Any]],
        capabilities_used: Set[str],
        time_to_solve: float = 0.0,
    ) -> ProblemSolution:
        """Record a problem solution for learning.

        Args:
            problem_text: The original problem
            signature: Problem signature
            solution: The solution found
            success: Whether solving succeeded
            strategy_used: Name of strategy used
            steps_taken: List of steps taken
            capabilities_used: Capabilities that were used
            time_to_solve: Time taken (seconds)

        Returns:
            ProblemSolution object
        """
        # Create solution record
        problem_solution = ProblemSolution(
            problem_text=problem_text,
            signature=signature,
            solution=solution,
            success=success,
            strategy_used=strategy_used,
            steps_taken=steps_taken,
            time_to_solve=time_to_solve,
            capabilities_used=capabilities_used,
        )

        # Add to library
        card_id = self.library.add_solution(problem_solution)

        # Create belief about this solution
        belief_text = f"Solved {signature.structure} problem "
        belief_text += "successfully" if success else "unsuccessfully"

        belief_card = self.integrator.store_belief_as_card(
            belief_text,
            metadata={
                "problem_structure": signature.structure,
                "domain": signature.domain.value,
                "success": success,
                "strategy": strategy_used,
            },
        )

        # Create DEPENDS_ON relation from belief to problem card
        rel = Relation.create(
            f"solution_{card_id}_belief",
            RelationType.DEPENDS_ON,
            belief_card,
            card_id,
            confidence=1.0 if success else 0.5,
        )
        store_relation(self.memory, rel)

        return problem_solution

    def learn_from_experience(
        self,
        min_pattern_occurrences: int = 3,
    ) -> Dict[str, Any]:
        """Extract learnings from accumulated experience.

        Args:
            min_pattern_occurrences: Min times pattern must appear to extract

        Returns:
            Dictionary of extracted learnings
        """
        # Extract patterns
        patterns = self.pattern_extractor.extract_patterns(min_pattern_occurrences)

        # Suggest new capabilities
        capability_suggestions = []
        for pattern in patterns:
            suggestion = self.pattern_extractor.suggest_capability_from_pattern(pattern)
            if suggestion:
                capability_suggestions.append(suggestion)

        # Get library statistics
        stats = self.library.get_statistics()

        return {
            "patterns_extracted": len(patterns),
            "patterns": [
                {
                    "name": p.name,
                    "structures": list(p.problem_structures),
                    "success_rate": p.confidence(),
                    "example_count": len(p.example_problems),
                }
                for p in patterns
            ],
            "capability_suggestions": capability_suggestions,
            "library_stats": stats,
        }

    def reason_by_analogy(
        self,
        problem_signature: ProblemSignature,
    ) -> Optional[Dict[str, Any]]:
        """Find similar past problems to reason by analogy.

        Args:
            problem_signature: Signature of current problem

        Returns:
            Analogy suggestion or None
        """
        similar = self.library.find_similar_problems(problem_signature, min_similarity=0.6)

        if not similar:
            return None

        # Use most similar successful solution
        successful = [s for s in similar if s.success]
        if not successful:
            return None

        best = successful[0]

        return {
            "similar_problem": best.problem_text,
            "similarity": self.library._calculate_similarity(
                problem_signature,
                best.signature,
            ),
            "strategy_used": best.strategy_used,
            "steps": [step.get("action") for step in best.steps_taken],
            "capabilities": list(best.capabilities_used),
            "confidence": best.signature.complexity / 10.0,  # Rough estimate
        }

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of what the system has learned."""
        stats = self.library.get_statistics()
        patterns = list(self.pattern_extractor.extracted_patterns.values())

        return {
            "total_problems_solved": stats["total_problems"],
            "success_rate": stats["success_rate"],
            "unique_problem_types": stats["unique_structures"],
            "patterns_learned": len(patterns),
            "domains_covered": list(stats["by_domain"].keys()),
            "best_domain": max(
                stats["by_domain"].items(),
                key=lambda x: x[1]["success"],
                default=("none", {"success": 0})
            )[0] if stats["by_domain"] else "none",
        }
