"""Transformation framework for ARC tasks.

This module defines the base transformation interface and parameter system
for ARC-AGI transformations. Transformations take grids or objects as input
and produce modified versions as output.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum

from supe.reasoning.arc.grid import ARCGrid, ARCObject


class TransformationType(Enum):
    """Categories of transformations."""
    GEOMETRIC = "geometric"  # Rotate, flip, scale, translate
    COLOR = "color"  # Color mapping, gradients
    STRUCTURAL = "structural"  # Duplicate, fill, extend
    LOGICAL = "logical"  # Conditional, masking, filtering
    COMPOSITIONAL = "compositional"  # Multi-step, chained


@dataclass
class TransformationResult:
    """Result of applying a transformation."""
    success: bool
    output_grid: Optional[ARCGrid] = None
    output_objects: Optional[List[ARCObject]] = None
    parameters_used: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # Confidence in the transformation
    explanation: str = ""  # Human-readable explanation


class Transformation(ABC):
    """Base class for all ARC transformations.

    Transformations are operations that convert input grids/objects
    to output grids/objects. They can be parameterized and composed.
    """

    def __init__(self, name: str, transformation_type: TransformationType):
        self.name = name
        self.transformation_type = transformation_type
        self.parameters: Dict[str, Any] = {}

    @abstractmethod
    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        **kwargs
    ) -> TransformationResult:
        """Apply transformation to input.

        Args:
            input_grid: Input grid to transform
            objects: Optional detected objects
            **kwargs: Transformation-specific parameters

        Returns:
            TransformationResult with output and metadata
        """
        pass

    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get schema describing required/optional parameters.

        Returns:
            Dictionary mapping parameter names to their types and constraints
        """
        pass

    def verify(
        self,
        input_grid: ARCGrid,
        expected_output: ARCGrid,
        **kwargs
    ) -> bool:
        """Verify transformation produces expected output.

        Args:
            input_grid: Input grid
            expected_output: Expected output grid
            **kwargs: Parameters to test

        Returns:
            True if transformation matches expected output
        """
        result = self.apply(input_grid, **kwargs)
        if not result.success or result.output_grid is None:
            return False
        return result.output_grid.equals(expected_output)

    def fit_parameters(
        self,
        examples: List[tuple],  # List of (input, output) pairs
        parameter_space: Optional[Dict[str, List]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fit transformation parameters from examples.

        Args:
            examples: List of (input_grid, output_grid) tuples
            parameter_space: Optional search space for each parameter

        Returns:
            Best parameters found, or None if no fit
        """
        if not examples:
            return None

        schema = self.get_parameter_schema()
        if not schema:
            # No parameters to fit
            return {}

        # Default parameter space if not provided
        if parameter_space is None:
            parameter_space = self._get_default_parameter_space(schema)

        # Try all parameter combinations
        best_params = None
        best_score = 0

        param_names = list(parameter_space.keys())
        param_values = [parameter_space[name] for name in param_names]

        # Generate all combinations
        from itertools import product
        for combination in product(*param_values):
            params = dict(zip(param_names, combination))

            # Test on all examples
            correct = 0
            for input_grid, output_grid in examples:
                if self.verify(input_grid, output_grid, **params):
                    correct += 1

            score = correct / len(examples)
            if score > best_score:
                best_score = score
                best_params = params

            # Early exit if perfect fit
            if score == 1.0:
                break

        return best_params if best_score > 0.5 else None

    def _get_default_parameter_space(self, schema: Dict[str, Any]) -> Dict[str, List]:
        """Generate default parameter space from schema.

        Args:
            schema: Parameter schema

        Returns:
            Dictionary mapping parameters to candidate values
        """
        space = {}

        for param_name, param_info in schema.items():
            param_type = param_info.get("type")

            if param_type == "angle":
                space[param_name] = [0, 90, 180, 270]
            elif param_type == "bool":
                space[param_name] = [True, False]
            elif param_type == "color":
                space[param_name] = list(range(10))  # ARC colors 0-9
            elif param_type == "int":
                min_val = param_info.get("min", 1)
                max_val = param_info.get("max", 5)
                space[param_name] = list(range(min_val, max_val + 1))
            elif param_type == "direction":
                space[param_name] = ["horizontal", "vertical", "both"]
            else:
                # Use provided values or skip
                space[param_name] = param_info.get("values", [None])

        return space

    def explain(self, parameters: Dict[str, Any]) -> str:
        """Generate human-readable explanation of transformation.

        Args:
            parameters: Parameters used

        Returns:
            Explanation string
        """
        param_str = ", ".join(f"{k}={v}" for k, v in parameters.items())
        return f"{self.name}({param_str})"

    def __repr__(self):
        return f"Transformation({self.name}, type={self.transformation_type.value})"


class CompositeTransformation(Transformation):
    """Composition of multiple transformations applied in sequence."""

    def __init__(
        self,
        name: str,
        transformations: List[Transformation],
    ):
        super().__init__(name, TransformationType.COMPOSITIONAL)
        self.transformations = transformations

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        **kwargs
    ) -> TransformationResult:
        """Apply transformations in sequence."""
        current_grid = input_grid
        current_objects = objects
        all_params = {}
        explanations = []

        for i, transform in enumerate(self.transformations):
            # Extract parameters for this transformation
            transform_params = {
                k.replace(f"step{i}_", ""): v
                for k, v in kwargs.items()
                if k.startswith(f"step{i}_")
            }

            result = transform.apply(current_grid, current_objects, **transform_params)

            if not result.success:
                return TransformationResult(
                    success=False,
                    explanation=f"Failed at step {i}: {transform.name}"
                )

            current_grid = result.output_grid
            current_objects = result.output_objects
            all_params.update({f"step{i}_{k}": v for k, v in result.parameters_used.items()})
            explanations.append(result.explanation)

        return TransformationResult(
            success=True,
            output_grid=current_grid,
            output_objects=current_objects,
            parameters_used=all_params,
            confidence=min(r.confidence for r in [
                t.apply(input_grid) for t in self.transformations
            ]),
            explanation=" → ".join(explanations),
        )

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Combine schemas from all sub-transformations."""
        schema = {}
        for i, transform in enumerate(self.transformations):
            sub_schema = transform.get_parameter_schema()
            for param_name, param_info in sub_schema.items():
                schema[f"step{i}_{param_name}"] = param_info
        return schema


class ParameterizedTransformation(Transformation):
    """Transformation with a parametric function."""

    def __init__(
        self,
        name: str,
        transformation_type: TransformationType,
        transform_fn: Callable,
        parameter_schema: Dict[str, Any],
    ):
        super().__init__(name, transformation_type)
        self.transform_fn = transform_fn
        self.parameter_schema = parameter_schema

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        **kwargs
    ) -> TransformationResult:
        """Apply parameterized function."""
        try:
            output_grid = self.transform_fn(input_grid, objects, **kwargs)
            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used=kwargs,
                explanation=self.explain(kwargs),
            )
        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Error: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return self.parameter_schema
