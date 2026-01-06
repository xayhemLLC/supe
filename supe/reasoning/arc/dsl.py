"""Domain-Specific Language for ARC programs.

This module defines a DSL for expressing ARC transformation programs.
Programs are compositions of transformations with support for:
- Sequential composition
- Conditional execution
- Iteration
- Object-level operations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable
from enum import Enum

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import Transformation, TransformationResult


class NodeType(Enum):
    """Types of program nodes."""
    TRANSFORM = "transform"
    SEQUENCE = "sequence"
    CONDITION = "condition"
    FOREACH = "foreach"
    IDENTITY = "identity"


@dataclass
class ExecutionContext:
    """Context for program execution."""
    input_grid: ARCGrid
    current_grid: ARCGrid
    objects: Optional[List[ARCObject]] = None
    variables: Dict[str, Any] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


class ProgramNode(ABC):
    """Base class for DSL program nodes."""

    def __init__(self, node_type: NodeType):
        self.node_type = node_type

    @abstractmethod
    def execute(self, context: ExecutionContext) -> TransformationResult:
        """Execute this program node.

        Args:
            context: Execution context with input and state

        Returns:
            TransformationResult with output
        """
        pass

    @abstractmethod
    def to_string(self, indent: int = 0) -> str:
        """Convert to human-readable string.

        Args:
            indent: Indentation level

        Returns:
            Formatted string representation
        """
        pass

    def __repr__(self):
        return self.to_string()


class TransformNode(ProgramNode):
    """Node representing a single transformation."""

    def __init__(
        self,
        transformation: Transformation,
        parameters: Dict[str, Any],
    ):
        super().__init__(NodeType.TRANSFORM)
        self.transformation = transformation
        self.parameters = parameters

    def execute(self, context: ExecutionContext) -> TransformationResult:
        """Execute transformation."""
        return self.transformation.apply(
            context.current_grid,
            objects=context.objects,
            **self.parameters
        )

    def to_string(self, indent: int = 0) -> str:
        indent_str = "  " * indent
        params_str = ", ".join(f"{k}={v}" for k, v in self.parameters.items())
        return f"{indent_str}{self.transformation.name}({params_str})"


class SequenceNode(ProgramNode):
    """Node representing sequential composition of programs."""

    def __init__(self, steps: List[ProgramNode]):
        super().__init__(NodeType.SEQUENCE)
        self.steps = steps

    def execute(self, context: ExecutionContext) -> TransformationResult:
        """Execute steps in sequence."""
        current_result = TransformationResult(
            success=True,
            output_grid=context.current_grid,
            output_objects=context.objects,
        )

        for i, step in enumerate(self.steps):
            # Update context with previous result
            context.current_grid = current_result.output_grid
            context.objects = current_result.output_objects

            # Execute step
            result = step.execute(context)

            if not result.success:
                return TransformationResult(
                    success=False,
                    explanation=f"Step {i} failed: {result.explanation}"
                )

            current_result = result

        return current_result

    def to_string(self, indent: int = 0) -> str:
        indent_str = "  " * indent
        steps_str = "\n".join(step.to_string(indent + 1) for step in self.steps)
        return f"{indent_str}sequence:\n{steps_str}"


class ConditionNode(ProgramNode):
    """Node representing conditional execution."""

    def __init__(
        self,
        condition: Callable[[ExecutionContext], bool],
        then_branch: ProgramNode,
        else_branch: Optional[ProgramNode] = None,
        condition_name: str = "condition",
    ):
        super().__init__(NodeType.CONDITION)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.condition_name = condition_name

    def execute(self, context: ExecutionContext) -> TransformationResult:
        """Execute conditional."""
        if self.condition(context):
            return self.then_branch.execute(context)
        elif self.else_branch:
            return self.else_branch.execute(context)
        else:
            # No-op if condition false and no else branch
            return TransformationResult(
                success=True,
                output_grid=context.current_grid,
                output_objects=context.objects,
            )

    def to_string(self, indent: int = 0) -> str:
        indent_str = "  " * indent
        result = f"{indent_str}if {self.condition_name}:\n"
        result += self.then_branch.to_string(indent + 1)
        if self.else_branch:
            result += f"\n{indent_str}else:\n"
            result += self.else_branch.to_string(indent + 1)
        return result


class ForEachNode(ProgramNode):
    """Node representing iteration over objects."""

    def __init__(
        self,
        body: ProgramNode,
        object_filter: Optional[Callable[[ARCObject], bool]] = None,
        filter_name: str = "all_objects",
    ):
        super().__init__(NodeType.FOREACH)
        self.body = body
        self.object_filter = object_filter
        self.filter_name = filter_name

    def execute(self, context: ExecutionContext) -> TransformationResult:
        """Execute body for each object."""
        if not context.objects:
            # Detect objects if not provided
            from supe.reasoning.arc.detector import ObjectDetector
            detector = ObjectDetector()
            context.objects = detector.detect_objects(context.current_grid)

        # Filter objects if needed
        objects = context.objects
        if self.object_filter:
            objects = [obj for obj in objects if self.object_filter(obj)]

        # Execute body for each object
        current_grid = context.current_grid

        for obj in objects:
            # Create context for this iteration
            iter_context = ExecutionContext(
                input_grid=context.input_grid,
                current_grid=current_grid,
                objects=[obj],
                variables=context.variables.copy(),
            )

            result = self.body.execute(iter_context)

            if not result.success:
                return result

            current_grid = result.output_grid

        return TransformationResult(
            success=True,
            output_grid=current_grid,
            explanation=f"Applied to {len(objects)} objects",
        )

    def to_string(self, indent: int = 0) -> str:
        indent_str = "  " * indent
        result = f"{indent_str}foreach {self.filter_name}:\n"
        result += self.body.to_string(indent + 1)
        return result


class IdentityNode(ProgramNode):
    """Node representing identity transformation (no-op)."""

    def __init__(self):
        super().__init__(NodeType.IDENTITY)

    def execute(self, context: ExecutionContext) -> TransformationResult:
        """Return input unchanged."""
        return TransformationResult(
            success=True,
            output_grid=context.current_grid,
            output_objects=context.objects,
            explanation="identity",
        )

    def to_string(self, indent: int = 0) -> str:
        indent_str = "  " * indent
        return f"{indent_str}identity"


class Program:
    """Complete ARC program with execution."""

    def __init__(self, root: ProgramNode, name: str = "program"):
        self.root = root
        self.name = name

    def execute(self, input_grid: ARCGrid) -> TransformationResult:
        """Execute program on input grid.

        Args:
            input_grid: Input grid

        Returns:
            TransformationResult with output
        """
        context = ExecutionContext(
            input_grid=input_grid,
            current_grid=input_grid.copy(),
        )

        return self.root.execute(context)

    def verify(self, examples: List[tuple]) -> float:
        """Verify program on examples.

        Args:
            examples: List of (input, output) tuples

        Returns:
            Accuracy (0.0 to 1.0)
        """
        if not examples:
            return 0.0

        correct = 0
        for input_grid, output_grid in examples:
            result = self.execute(input_grid)
            if result.success and result.output_grid.equals(output_grid):
                correct += 1

        return correct / len(examples)

    def to_string(self) -> str:
        """Get string representation."""
        return f"Program '{self.name}':\n{self.root.to_string(indent=1)}"

    def __repr__(self):
        return self.to_string()


# Common condition predicates

def has_symmetry(axis: str = "horizontal") -> Callable[[ExecutionContext], bool]:
    """Check if grid has symmetry."""
    def check(context: ExecutionContext) -> bool:
        if axis == "horizontal":
            return context.current_grid.is_symmetric_horizontal()
        elif axis == "vertical":
            return context.current_grid.is_symmetric_vertical()
        elif axis == "diagonal":
            return context.current_grid.is_symmetric_diagonal()
        return False
    return check


def has_color(color: int) -> Callable[[ExecutionContext], bool]:
    """Check if grid contains color."""
    def check(context: ExecutionContext) -> bool:
        return color in context.current_grid.get_unique_colors()
    return check


def object_count_equals(count: int) -> Callable[[ExecutionContext], bool]:
    """Check if object count equals value."""
    def check(context: ExecutionContext) -> bool:
        if not context.objects:
            from supe.reasoning.arc.detector import ObjectDetector
            detector = ObjectDetector()
            context.objects = detector.detect_objects(context.current_grid)
        return len(context.objects) == count
    return check


def grid_size_equals(height: int, width: int) -> Callable[[ExecutionContext], bool]:
    """Check if grid size equals dimensions."""
    def check(context: ExecutionContext) -> bool:
        return context.current_grid.shape == (height, width)
    return check


# Common object filters

def color_filter(color: int) -> Callable[[ARCObject], bool]:
    """Filter objects by color."""
    return lambda obj: obj.color == color


def size_filter(min_size: int, max_size: Optional[int] = None) -> Callable[[ARCObject], bool]:
    """Filter objects by size."""
    def check(obj: ARCObject) -> bool:
        if max_size is None:
            return obj.mass >= min_size
        return min_size <= obj.mass <= max_size
    return check


def largest_object_filter() -> Callable[[ARCObject], bool]:
    """Filter to keep only largest object."""
    max_size = [0]  # Mutable to allow updating

    def check(obj: ARCObject) -> bool:
        if obj.mass > max_size[0]:
            max_size[0] = obj.mass
            return True
        return obj.mass == max_size[0]
    return check
