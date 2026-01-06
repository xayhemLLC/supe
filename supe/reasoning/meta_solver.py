"""Meta-solver that adapts its problem-solving approach dynamically.

This is the core of supe's adaptive reasoning system. It:
1. Analyzes problems to understand what's needed
2. Checks if it has the required capabilities
3. Synthesizes new strategies when needed
4. Solves the problem using appropriate methods
5. Learns from the experience to improve future solving
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path

from ab.abdb import ABMemory
from tasc.validation_integration import ValidationRelationIntegrator
from tasc.reasoning_engine import ReasoningEngine
from tasc.relations import Relation, RelationType
from tasc.relation_storage import store_relation

from supe.reasoning.problem_types import (
    ProblemClassifier,
    ProblemSignature,
    ProblemDomain,
    ReasoningPattern,
)
from supe.reasoning.capability_registry import CapabilityRegistry, ReasoningCapability
from supe.reasoning.learning_loop import LearningLoop, ProblemSolution


@dataclass
class SolvingStrategy:
    """A strategy for solving a particular problem type."""
    name: str
    problem_signature: ProblemSignature
    steps: List[Dict[str, Any]]  # Ordered solving steps
    required_capabilities: Set[str]
    confidence: float = 0.5  # How confident we are this will work
    success_count: int = 0
    failure_count: int = 0

    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class ProblemAnalysis:
    """Analysis of a problem and how to solve it."""
    problem_text: str
    signature: ProblemSignature
    available_capabilities: List[ReasoningCapability]
    missing_capabilities: Set[ReasoningPattern]
    suggested_strategy: Optional[SolvingStrategy]
    can_solve: bool
    reasoning: str  # Explanation of the analysis


class MetaSolver:
    """Adaptive problem solver that extends its own capabilities."""

    def __init__(self, memory: ABMemory):
        """Initialize the meta-solver.

        Args:
            memory: ABMemory instance for persistent storage
        """
        self.memory = memory
        self.integrator = ValidationRelationIntegrator(memory)
        self.reasoning_engine = ReasoningEngine(memory)

        # Core components
        self.classifier = ProblemClassifier()
        self.registry = CapabilityRegistry()
        self.learning_loop = LearningLoop(memory)

        # Strategy library
        self.strategies: Dict[str, SolvingStrategy] = {}
        self._initialize_base_strategies()

    def _initialize_base_strategies(self):
        """Initialize with base solving strategies."""

        # Strategy for grid patterns
        self.strategies["grid_pattern"] = SolvingStrategy(
            name="grid_pattern_solver",
            problem_signature=self.classifier.get_signature("grid_number_pattern"),
            steps=[
                {"action": "identify_pattern", "pattern": ReasoningPattern.PATTERN_MATCHING, "capability": "pattern_matcher"},
                {"action": "test_hypotheses", "pattern": ReasoningPattern.HYPOTHESIS_TESTING, "capability": "hypothesis_testing"},
            ],
            required_capabilities={"hypothesis_testing", "pattern_matcher"},
            confidence=0.9,
        )

        # Strategy for factorization
        self.strategies["factorization"] = SolvingStrategy(
            name="polynomial_factorization_solver",
            problem_signature=self.classifier.get_signature("polynomial_factorization"),
            steps=[
                {"action": "factor_polynomial", "pattern": ReasoningPattern.ALGEBRAIC, "capability": "algebraic_manipulation"},
            ],
            required_capabilities={"algebraic_manipulation"},
            confidence=0.95,
        )

        # Strategy for logic puzzles
        self.strategies["logic_puzzle"] = SolvingStrategy(
            name="logic_puzzle_solver",
            problem_signature=self.classifier.get_signature("logic_puzzle"),
            steps=[
                {"action": "apply_deductive_reasoning", "pattern": ReasoningPattern.DEDUCTIVE, "capability": "deductive_reasoner"},
            ],
            required_capabilities={"deductive_reasoner"},
            confidence=0.85,
        )

    def analyze_problem(self, problem_text: str, context: Optional[Dict] = None) -> ProblemAnalysis:
        """Analyze a problem to determine how to solve it.

        Args:
            problem_text: The problem statement
            context: Optional additional context

        Returns:
            ProblemAnalysis describing what's needed to solve it
        """
        # Step 1: Classify the problem
        signature = self.classifier.classify(problem_text, context)

        # Step 2: Check for similar past problems (reasoning by analogy)
        analogy = self.learning_loop.reason_by_analogy(signature)
        if analogy:
            # Found similar problem - add to context
            if context is None:
                context = {}
            context["analogy"] = analogy

        # Step 3: Check what capabilities we have
        available = []
        missing = set()

        for pattern in signature.required_patterns:
            caps = self.registry.find_capabilities(signature.domain, pattern)
            if caps:
                available.extend(caps)
            else:
                missing.add(pattern)

        # Step 4: Find or synthesize a strategy
        strategy = self._find_strategy(signature)
        if not strategy and not missing:
            # We have capabilities but no strategy - synthesize one
            strategy = self._synthesize_strategy(signature, available)

        # Step 5: Determine if we can solve it
        can_solve = len(missing) == 0 and strategy is not None

        # Step 6: Generate reasoning explanation
        reasoning = self._explain_analysis(signature, available, missing, strategy, can_solve, analogy)

        return ProblemAnalysis(
            problem_text=problem_text,
            signature=signature,
            available_capabilities=available,
            missing_capabilities=missing,
            suggested_strategy=strategy,
            can_solve=can_solve,
            reasoning=reasoning,
        )

    def solve(self, problem_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Solve a problem using adaptive reasoning.

        Args:
            problem_text: The problem to solve
            context: Optional additional context

        Returns:
            Dictionary with solution and metadata
        """
        # Analyze the problem
        analysis = self.analyze_problem(problem_text, context)

        # Store analysis in memory
        analysis_card = self._store_analysis(analysis)

        if not analysis.can_solve:
            # Try to extend capabilities
            if analysis.missing_capabilities:
                return {
                    "success": False,
                    "error": "Missing required capabilities",
                    "missing": [p.value for p in analysis.missing_capabilities],
                    "suggestion": "System needs to learn these reasoning patterns",
                    "analysis": analysis,
                }

        # Execute the strategy
        result = self._execute_strategy(analysis.suggested_strategy, problem_text, context)

        # Learn from the experience
        self._learn_from_solving(analysis, result)

        return result

    def _find_strategy(self, signature: ProblemSignature) -> Optional[SolvingStrategy]:
        """Find an existing strategy for this problem type."""
        # Try exact structure match
        for strategy in self.strategies.values():
            if strategy.problem_signature.structure == signature.structure:
                return strategy

        # Try domain match with similar patterns
        for strategy in self.strategies.values():
            if strategy.problem_signature.domain == signature.domain:
                pattern_overlap = len(
                    strategy.problem_signature.required_patterns & signature.required_patterns
                )
                if pattern_overlap >= len(signature.required_patterns) * 0.5:
                    return strategy

        return None

    def _synthesize_strategy(
        self,
        signature: ProblemSignature,
        available_capabilities: List[ReasoningCapability],
    ) -> Optional[SolvingStrategy]:
        """Synthesize a new strategy for this problem type.

        This is where the system "programs itself" with a new solving method.
        """
        # Build steps from required patterns
        steps = []
        required_cap_names = set()

        for pattern in signature.required_patterns:
            # Find best capability for this pattern
            best_cap = None
            for cap in available_capabilities:
                if cap.pattern == pattern:
                    if best_cap is None or cap.confidence > best_cap.confidence:
                        best_cap = cap

            if best_cap:
                steps.append({
                    "action": f"apply_{pattern.value}",
                    "pattern": pattern,
                    "capability": best_cap.name,
                })
                required_cap_names.add(best_cap.name)

        if not steps:
            return None

        # Create new strategy
        strategy = SolvingStrategy(
            name=f"synthesized_{signature.structure}_{len(self.strategies)}",
            problem_signature=signature,
            steps=steps,
            required_capabilities=required_cap_names,
            confidence=0.6,  # Lower confidence for synthesized strategies
        )

        # Register it
        self.strategies[strategy.name] = strategy

        return strategy

    def _execute_strategy(
        self,
        strategy: SolvingStrategy,
        problem_text: str,
        context: Optional[Dict],
    ) -> Dict[str, Any]:
        """Execute a solving strategy.

        Args:
            strategy: The strategy to execute
            problem_text: Problem statement
            context: Optional context

        Returns:
            Solution result
        """
        results = {
            "success": False,
            "strategy_name": strategy.name,
            "steps_completed": [],
            "answer": None,
            "confidence": strategy.confidence,
            "reasoning_trace": [],
        }

        try:
            # Execute each step
            for i, step in enumerate(strategy.steps):
                step_result = self._execute_step(step, problem_text, context, results)
                results["steps_completed"].append(step_result)
                results["reasoning_trace"].append(f"Step {i+1}: {step['action']}")

                # Check if step failed
                if not step_result.get("success", True):
                    results["error"] = f"Step {i+1} failed: {step_result.get('error', 'Unknown')}"
                    return results

            # If we got here, all steps succeeded
            results["success"] = True

        except Exception as e:
            results["error"] = str(e)
            results["exception"] = type(e).__name__

        return results

    def _execute_step(
        self,
        step: Dict[str, Any],
        problem_text: str,
        context: Optional[Dict],
        previous_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single strategy step.

        Dispatches to actual reasoning capability implementations.
        """
        pattern = step["pattern"]
        action = step["action"]
        capability_name = step.get("capability")

        # Get capability implementation
        if capability_name:
            capability = self.registry.get_capability(capability_name)
            if capability and capability.implementation:
                try:
                    # Prepare context for capability
                    exec_context = {
                        **(context or {}),
                        "problem_text": problem_text,
                        "previous_results": previous_results,
                        "action": action,
                    }

                    # Execute capability
                    result = capability.implementation.execute(problem_text, exec_context)

                    return {
                        "success": result.get("success", True),
                        "action": action,
                        "pattern": pattern.value,
                        "capability": capability_name,
                        "result": result,
                    }

                except Exception as e:
                    return {
                        "success": False,
                        "action": action,
                        "pattern": pattern.value,
                        "capability": capability_name,
                        "error": str(e),
                        "exception": type(e).__name__,
                    }

        # Fallback: capability not found or no implementation
        return {
            "success": False,
            "action": action,
            "pattern": pattern.value,
            "error": f"No implementation for capability: {capability_name}",
        }

    def _explain_analysis(
        self,
        signature: ProblemSignature,
        available: List[ReasoningCapability],
        missing: Set[ReasoningPattern],
        strategy: Optional[SolvingStrategy],
        can_solve: bool,
        analogy: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate explanation of problem analysis."""
        lines = []
        lines.append(f"Problem Domain: {signature.domain.value}")
        lines.append(f"Required Patterns: {[p.value for p in signature.required_patterns]}")

        if analogy:
            lines.append(f"\nReasoning by Analogy:")
            lines.append(f"  Similar Problem Found (similarity={analogy['similarity']:.2f})")
            lines.append(f"  Previous Strategy: {analogy['strategy_used']}")
            lines.append(f"  Confidence: {analogy['confidence']:.2f}")

        if available:
            lines.append(f"\nAvailable Capabilities: {len(available)}")
            for cap in available[:3]:  # Show top 3
                lines.append(f"  - {cap.name} ({cap.pattern.value}, conf={cap.confidence:.2f})")

        if missing:
            lines.append(f"\nMissing Patterns: {[p.value for p in missing]}")

        if strategy:
            lines.append(f"\nStrategy: {strategy.name} (conf={strategy.confidence:.2f})")
            lines.append(f"Steps: {len(strategy.steps)}")

        lines.append(f"\nCan Solve: {can_solve}")

        return "\n".join(lines)

    def _store_analysis(self, analysis: ProblemAnalysis) -> int:
        """Store problem analysis in memory."""
        card = self.memory.store_card(
            label=f"Problem Analysis: {analysis.signature.structure}",
            buffers=[],
            track="awareness",
        )

        # Store as belief
        belief_card = self.integrator.store_belief_as_card(
            analysis.reasoning,
            metadata={
                "domain": analysis.signature.domain.value,
                "can_solve": analysis.can_solve,
                "missing_count": len(analysis.missing_capabilities),
            },
        )

        return belief_card

    def _learn_from_solving(self, analysis: ProblemAnalysis, result: Dict[str, Any]):
        """Learn from solving experience to improve future performance."""
        if analysis.suggested_strategy:
            strategy = analysis.suggested_strategy

            # Update strategy statistics
            if result["success"]:
                strategy.success_count += 1
                # Increase confidence slightly
                strategy.confidence = min(1.0, strategy.confidence + 0.05)
            else:
                strategy.failure_count += 1
                # Decrease confidence
                strategy.confidence = max(0.1, strategy.confidence - 0.1)

            # Update capability statistics
            for cap_name in strategy.required_capabilities:
                self.registry.update_statistics(cap_name, result["success"])

            # Record solution in learning loop
            capabilities_used = strategy.required_capabilities
            steps_taken = result.get("steps_completed", [])

            problem_solution = self.learning_loop.record_solution(
                problem_text=analysis.problem_text,
                signature=analysis.signature,
                solution=result.get("answer"),
                success=result["success"],
                strategy_used=strategy.name,
                steps_taken=steps_taken,
                capabilities_used=capabilities_used,
                time_to_solve=result.get("time_elapsed", 0.0),
            )

            # Store link between analysis and solution
            if hasattr(problem_solution, "card_id") and problem_solution.card_id:
                # Create DEPENDS_ON relation
                rel = Relation.create(
                    f"solution_learning_{problem_solution.card_id}",
                    RelationType.DEPENDS_ON,
                    problem_solution.card_id,
                    result.get("analysis_card_id", 0),
                    confidence=1.0 if result["success"] else 0.5,
                )
                store_relation(self.memory, rel)

    def extend_capability(
        self,
        name: str,
        pattern: ReasoningPattern,
        domains: Set[ProblemDomain],
        description: str,
        implementation: Optional[Any] = None,
    ):
        """Extend the system with a new capability.

        This allows the system to learn new reasoning methods.
        """
        capability = ReasoningCapability(
            name=name,
            pattern=pattern,
            domains=domains,
            description=description,
            implementation=implementation,
            confidence=0.5,  # Start with moderate confidence
        )

        self.registry.register(capability)

        # Store in memory
        cap_card = self.integrator.store_belief_as_card(
            f"New capability learned: {name}",
            metadata={
                "pattern": pattern.value,
                "domains": [d.value for d in domains],
                "description": description,
            },
        )

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get summary of system capabilities."""
        return {
            "total_capabilities": len(self.registry.capabilities),
            "capabilities": self.registry.list_capabilities(),
            "statistics": self.registry.get_statistics(),
            "strategies": {
                name: {
                    "steps": len(s.steps),
                    "confidence": s.confidence,
                    "success_rate": s.success_rate(),
                }
                for name, s in self.strategies.items()
            },
        }

    def learn_from_experience(self, min_pattern_occurrences: int = 3) -> Dict[str, Any]:
        """Extract learnings from all problems solved so far.

        This analyzes the accumulated problem-solving experience to:
        - Extract common patterns
        - Suggest new capabilities
        - Identify what's working best

        Args:
            min_pattern_occurrences: Minimum times pattern must appear to extract

        Returns:
            Dictionary of learnings including patterns and capability suggestions
        """
        learnings = self.learning_loop.learn_from_experience(min_pattern_occurrences)

        # Auto-register suggested capabilities
        for suggestion in learnings.get("capability_suggestions", []):
            # Check if we should auto-add this capability
            if suggestion["confidence"] > 0.8 and suggestion["evidence_count"] >= 5:
                # High confidence and sufficient evidence - auto-register
                # Try to map to existing pattern, default to PATTERN_MATCHING
                try:
                    pattern_name = suggestion["name"].replace("learned_", "")
                    pattern = ReasoningPattern(pattern_name)
                except (ValueError, KeyError):
                    # If pattern name doesn't match enum, use PATTERN_MATCHING
                    pattern = ReasoningPattern.PATTERN_MATCHING

                self.extend_capability(
                    name=suggestion["name"],
                    pattern=pattern,
                    domains={ProblemDomain.UNKNOWN},  # Would need better domain inference
                    description=suggestion["description"],
                )

        return learnings

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of what the system has learned from experience.

        Returns:
            Dictionary with learning statistics and progress
        """
        learning_summary = self.learning_loop.get_learning_summary()
        capability_summary = self.get_capabilities_summary()

        return {
            "learning": learning_summary,
            "capabilities": capability_summary,
            "integration": {
                "problems_solved": learning_summary["total_problems_solved"],
                "success_rate": learning_summary["success_rate"],
                "patterns_learned": learning_summary["patterns_learned"],
                "total_capabilities": capability_summary["total_capabilities"],
                "total_strategies": len(capability_summary["strategies"]),
            },
        }
