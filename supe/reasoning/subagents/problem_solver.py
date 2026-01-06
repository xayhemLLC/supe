"""ProblemSolver subagent - TASC format structured reasoning.

This subagent solves problems using the TASC (Task with Structured Checkpoints) format:
1. Identify problem type
2. Build step-by-step reasoning chain
3. Validate each step with checkpoints
4. Verify answer against options
5. Produce structured output with confidence

Example TASC output:
    ┌─────────────────────────────────────────────────┐
    │  TASC: MATH-001                                 │
    │  Function Composition: Find f(g(2))             │
    ├─────────────────────────────────────────────────┤
    │  Step 1: Evaluate g(2) = 2 - 2 = 0        ✓     │
    │  Step 2: Evaluate f(0) = 0² + 1 = 1       ✓     │
    │  Verification: f(g(x)) at x=2 = 1         ✓     │
    ├─────────────────────────────────────────────────┤
    │  Answer: A (1)   Confidence: 100%               │
    └─────────────────────────────────────────────────┘
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4
import json
from pathlib import Path

from ab.abdb import ABMemory
from ab.models import Buffer, Card


class StepStatus(Enum):
    """Status of a reasoning step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATED = "validated"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckpointType(Enum):
    """Types of validation checkpoints."""
    CALCULATION = "calculation"      # Verify arithmetic/algebra
    LOGIC = "logic"                  # Verify logical inference
    CONSISTENCY = "consistency"      # Check internal consistency
    BOUNDARY = "boundary"            # Check edge cases
    SANITY = "sanity"               # Quick sanity check
    VERIFICATION = "verification"    # Independent verification method


@dataclass
class ValidationCheckpoint:
    """A checkpoint that validates a reasoning step."""

    id: str
    checkpoint_type: CheckpointType
    description: str
    check_function: Optional[Callable] = None  # Optional programmatic check
    expected: Any = None
    actual: Any = None
    passed: bool = False
    error_message: str = ""

    def validate(self, result: Any) -> bool:
        """Run validation on a result."""
        self.actual = result

        if self.check_function:
            try:
                self.passed = self.check_function(result, self.expected)
            except Exception as e:
                self.passed = False
                self.error_message = str(e)
        elif self.expected is not None:
            self.passed = result == self.expected
        else:
            # No check function or expected value - assume passed
            self.passed = True

        return self.passed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.checkpoint_type.value,
            "description": self.description,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "error": self.error_message,
        }


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""

    step_number: int
    description: str
    observation: str = ""
    computation: str = ""
    result: Any = None
    status: StepStatus = StepStatus.PENDING
    checkpoints: List[ValidationCheckpoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        description: str,
        expected: Any = None,
        check_function: Optional[Callable] = None,
    ) -> ValidationCheckpoint:
        """Add a validation checkpoint to this step."""
        checkpoint = ValidationCheckpoint(
            id=f"cp_{self.step_number}_{len(self.checkpoints)}",
            checkpoint_type=checkpoint_type,
            description=description,
            expected=expected,
            check_function=check_function,
        )
        self.checkpoints.append(checkpoint)
        return checkpoint

    def validate_all(self, result: Any) -> bool:
        """Run all checkpoints and return overall pass/fail."""
        self.result = result
        all_passed = True

        for checkpoint in self.checkpoints:
            if not checkpoint.validate(result):
                all_passed = False

        self.status = StepStatus.VALIDATED if all_passed else StepStatus.FAILED
        return all_passed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "description": self.description,
            "observation": self.observation,
            "computation": self.computation,
            "result": self.result,
            "status": self.status.value,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "metadata": self.metadata,
        }


@dataclass
class TASC:
    """Task with Structured Checkpoints - the core reasoning format."""

    id: str
    title: str
    status: str = "pending"

    # Problem definition
    problem_text: str = ""
    given: List[str] = field(default_factory=list)
    find: str = ""
    options: Dict[str, Any] = field(default_factory=dict)

    # Reasoning chain
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)

    # Answer
    proposed_answer: Optional[str] = None
    proposed_value: Any = None
    confidence: float = 0.0
    confidence_reasoning: str = ""

    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    # Validation
    human_validation: Dict[str, Any] = field(default_factory=lambda: {
        "status": "awaiting",
        "validator": None,
        "timestamp": None,
        "verdict": None,
        "feedback": None,
    })

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

    def add_step(self, description: str) -> ReasoningStep:
        """Add a new reasoning step."""
        step = ReasoningStep(
            step_number=len(self.reasoning_steps) + 1,
            description=description,
        )
        self.reasoning_steps.append(step)
        return step

    def add_evidence(
        self,
        evidence_type: str,
        source: str,
        content: str,
        validated: bool = False,
    ):
        """Add evidence supporting the answer."""
        self.evidence.append({
            "type": evidence_type,
            "source": source,
            "content": content,
            "validated": validated,
        })

    def calculate_confidence(self) -> float:
        """Calculate confidence based on validation results."""
        if not self.reasoning_steps:
            return 0.0

        validated_steps = sum(
            1 for step in self.reasoning_steps
            if step.status == StepStatus.VALIDATED
        )
        step_confidence = validated_steps / len(self.reasoning_steps)

        # Boost for evidence
        evidence_boost = min(0.1, len(self.evidence) * 0.02)

        # Boost for multiple verification methods
        verification_methods = len(set(
            e["source"] for e in self.evidence if e.get("validated")
        ))
        method_boost = min(0.1, verification_methods * 0.05)

        self.confidence = min(1.0, step_confidence + evidence_boost + method_boost)
        return self.confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "problem": {
                "text": self.problem_text,
                "given": self.given,
                "find": self.find,
                "options": self.options,
            },
            "reasoning_chain": [step.to_dict() for step in self.reasoning_steps],
            "proposed_answer": self.proposed_answer,
            "proposed_value": self.proposed_value,
            "confidence": {
                "value": self.confidence,
                "reasoning": self.confidence_reasoning,
            },
            "evidence": self.evidence,
            "human_validation": self.human_validation,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    def to_ascii(self) -> str:
        """Render as ASCII box format."""
        width = 60
        lines = []

        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        lines.append(f"│  TASC: {self.id:<{width-12}}│")
        lines.append(f"│  {self.title:<{width-5}}│")
        lines.append("├" + "─" * (width - 2) + "┤")

        # Problem
        if self.given:
            for g in self.given:
                lines.append(f"│  Given: {g:<{width-12}}│")
        if self.find:
            lines.append(f"│  Find: {self.find:<{width-11}}│")

        lines.append("├" + "─" * (width - 2) + "┤")

        # Steps
        for step in self.reasoning_steps:
            status_icon = "✓" if step.status == StepStatus.VALIDATED else "✗" if step.status == StepStatus.FAILED else "○"
            step_text = f"Step {step.step_number}: {step.description}"
            if len(step_text) > width - 8:
                step_text = step_text[:width-11] + "..."
            lines.append(f"│  {step_text:<{width-7}}{status_icon}  │")

            if step.computation:
                comp = step.computation[:width-8]
                lines.append(f"│    {comp:<{width-7}}│")

        lines.append("├" + "─" * (width - 2) + "┤")

        # Answer
        answer_line = f"Answer: {self.proposed_answer} ({self.proposed_value})"
        conf_line = f"Confidence: {self.confidence*100:.0f}%"
        lines.append(f"│  {answer_line:<{width-5}}│")
        lines.append(f"│  {conf_line:<{width-5}}│")

        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)


class ProblemSolver:
    """Subagent that solves problems using TASC format with step validation.

    This implements structured reasoning with:
    - Problem decomposition into steps
    - Validation checkpoints at each step
    - Multiple verification methods
    - Confidence scoring

    Example:
        solver = ProblemSolver(memory)
        tasc = await solver.solve(problem_text, options)
        print(tasc.to_ascii())
    """

    name = "problem_solver"

    def __init__(self, memory: ABMemory, enable_capabilities: bool = True):
        self.memory = memory
        self.tasc_counter = 0
        self.enable_capabilities = enable_capabilities
        self.capability_manager = None

        # Initialize capability manager if enabled
        if enable_capabilities:
            try:
                scripts_dir = Path(__file__).parent.parent / "scripts"
                # Import here to avoid circular dependencies
                from supe.reasoning.scripts.capability_manager import CapabilityManager
                self.capability_manager = CapabilityManager(scripts_dir)
            except Exception:
                # Gracefully handle missing capability system
                self.enable_capabilities = False

    def create_tasc(self, title: str, problem_text: str = "") -> TASC:
        """Create a new TASC for a problem."""
        self.tasc_counter += 1
        return TASC(
            id=f"TASC-{self.tasc_counter:04d}",
            title=title,
            problem_text=problem_text,
        )

    async def solve(
        self,
        problem_text: str,
        options: Optional[Dict[str, Any]] = None,
        given: Optional[List[str]] = None,
        find: Optional[str] = None,
        title: Optional[str] = None,
    ) -> TASC:
        """Solve a problem using TASC format.

        This is the main entry point. Override _decompose_problem,
        _execute_step, and _verify_answer for custom problem types.

        Args:
            problem_text: The problem statement
            options: Optional answer options (e.g., {"A": 1, "B": 5})
            given: List of given information
            find: What we're looking for
            title: Optional title for the TASC

        Returns:
            Completed TASC with solution
        """
        # Create TASC
        tasc = self.create_tasc(
            title=title or self._generate_title(problem_text),
            problem_text=problem_text,
        )
        tasc.given = given or []
        tasc.find = find or ""
        tasc.options = options or {}

        # Step 1: Identify problem type
        step1 = tasc.add_step("Identify the problem type")
        problem_type = self._identify_problem_type(problem_text)
        step1.observation = problem_type["description"]
        step1.result = problem_type["type"]
        step1.add_checkpoint(
            CheckpointType.SANITY,
            "Problem type identified",
            expected=True,
        )
        step1.validate_all(True)

        # Step 2+: Execute problem-specific steps
        steps = self._decompose_problem(problem_text, problem_type)
        for step_def in steps:
            step = tasc.add_step(step_def["description"])
            result = await self._execute_step(step, step_def, tasc)

            # Add appropriate checkpoints
            if step_def.get("expected"):
                step.add_checkpoint(
                    CheckpointType.CALCULATION,
                    f"Expected result: {step_def['expected']}",
                    expected=step_def["expected"],
                )

            step.validate_all(result)

        # Final step: Verify answer
        if options:
            verify_step = tasc.add_step("Verify answer against options")
            answer, value = self._match_answer(tasc, options)
            tasc.proposed_answer = answer
            tasc.proposed_value = value
            verify_step.result = answer
            verify_step.add_checkpoint(
                CheckpointType.SANITY,
                "Answer matches an option",
                expected=True,
            )
            verify_step.validate_all(answer is not None)

        # Calculate confidence
        tasc.calculate_confidence()
        tasc.confidence_reasoning = self._explain_confidence(tasc)

        # Mark complete
        tasc.status = "completed"
        tasc.completed_at = datetime.utcnow().isoformat()

        # Store in memory
        await self._store_tasc(tasc)

        return tasc

    def _generate_title(self, problem_text: str) -> str:
        """Generate a title from problem text."""
        # Take first 50 chars, clean up
        title = problem_text[:50].strip()
        if len(problem_text) > 50:
            title += "..."
        return title

    def _identify_problem_type(self, problem_text: str) -> Dict[str, Any]:
        """Identify the type of problem. Override for custom classification."""
        text_lower = problem_text.lower()

        if any(w in text_lower for w in ["equation", "solve", "x =", "y ="]):
            return {"type": "algebra", "description": "Algebraic equation solving"}
        elif any(w in text_lower for w in ["f(x)", "g(x)", "composite", "composition"]):
            return {"type": "function", "description": "Function composition/evaluation"}
        elif any(w in text_lower for w in ["pattern", "sequence", "next"]):
            return {"type": "pattern", "description": "Pattern recognition"}
        elif any(w in text_lower for w in ["probability", "chance", "likely"]):
            return {"type": "probability", "description": "Probability calculation"}
        elif any(w in text_lower for w in ["logic", "truth", "lie", "always"]):
            return {"type": "logic", "description": "Logical reasoning puzzle"}
        else:
            return {"type": "general", "description": "General problem solving"}

    def _decompose_problem(
        self,
        problem_text: str,
        problem_type: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Decompose problem into steps. Override for custom decomposition."""
        # Default: single step
        return [
            {
                "description": "Analyze and solve the problem",
                "action": "solve",
            }
        ]

    async def _execute_step(
        self,
        step: ReasoningStep,
        step_def: Dict[str, Any],
        tasc: TASC,
    ) -> Any:
        """Execute a reasoning step. Override for custom execution."""
        # Check if we can use a capability for this problem
        if self.enable_capabilities and self.capability_manager:
            capabilities = self.capability_manager.find_capabilities(
                tasc.problem_text, threshold=0.3
            )

            if capabilities:
                # Use the best matching capability
                cap = capabilities[0]
                step.observation = f"Using capability: {cap.name}"

                # Prepare input data
                input_data = json.dumps({
                    "problem": tasc.problem_text,
                    "budget": tasc.options.get("budget", 100),
                    "risk_level": tasc.options.get("risk_level", "medium"),
                    "given": tasc.given,
                    "find": tasc.find,
                })

                # Execute capability
                result = self.capability_manager.execute_capability(
                    cap.id,
                    input_data,
                )

                if result["success"]:
                    try:
                        output_data = json.loads(result["output"])
                        step.computation = f"Executed {cap.name}"
                        step.metadata["capability_id"] = cap.id
                        step.metadata["capability_output"] = output_data
                        return output_data
                    except json.JSONDecodeError:
                        step.observation += " (capability returned non-JSON output)"
                        step.metadata["capability_raw_output"] = result["output"]
                else:
                    step.observation += f" (capability failed: {result['error']})"

        # Default execution
        step.observation = step_def.get("observation", "Executing step...")
        step.computation = step_def.get("computation", "")
        return step_def.get("result")

    def _match_answer(
        self,
        tasc: TASC,
        options: Dict[str, Any],
    ) -> tuple[Optional[str], Any]:
        """Match computed result to answer options."""
        # Get last computed result
        result = None
        for step in reversed(tasc.reasoning_steps):
            if step.result is not None:
                result = step.result
                break

        if result is None:
            return None, None

        # Find matching option
        for key, value in options.items():
            if value == result:
                return key, value

        return None, result

    def _explain_confidence(self, tasc: TASC) -> str:
        """Generate confidence explanation."""
        validated = sum(
            1 for s in tasc.reasoning_steps
            if s.status == StepStatus.VALIDATED
        )
        total = len(tasc.reasoning_steps)

        parts = [f"{validated}/{total} steps validated"]

        if tasc.evidence:
            parts.append(f"{len(tasc.evidence)} evidence pieces")

        verified_methods = len(set(e["source"] for e in tasc.evidence if e.get("validated")))
        if verified_methods > 1:
            parts.append(f"{verified_methods} verification methods agree")

        return ", ".join(parts)

    async def _store_tasc(self, tasc: TASC) -> int:
        """Store TASC in AB memory."""
        tasc_json = json.dumps(tasc.to_dict()).encode("utf-8")
        tasc_ascii = tasc.to_ascii().encode("utf-8")

        buffers = [
            Buffer(
                name="tasc_json",
                headers={"type": "tasc", "format": "json"},
                payload=tasc_json,
            ),
            Buffer(
                name="tasc_ascii",
                headers={"type": "tasc", "format": "ascii"},
                payload=tasc_ascii,
            ),
        ]

        card = self.memory.store_card(
            label=f"TASC: {tasc.title}",
            buffers=buffers,
            track="reasoning",
            master_input=tasc.problem_text[:200],
            master_output=f"Answer: {tasc.proposed_answer} ({tasc.proposed_value})",
        )

        return card.id
