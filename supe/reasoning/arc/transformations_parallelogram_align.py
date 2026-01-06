"""Parallelogram alignment transformations for ARC tasks.

Shift parallelogram shapes while keeping bottom row fixed.
"""

from typing import Optional, List, Dict, Any, Tuple
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class ParallelogramAlignTransformation(Transformation):
    """Align parallelogram by shifting while keeping bottom row fixed.

    Pattern:
    - For each colored object independently:
    - Bottom row stays completely fixed (anchor point)
    - All rows above shift right by 1 column
    - Pixels at the rightmost column stay in place
    - This "straightens" the right edge while keeping shape anchored at bottom-right
    """

    def __init__(self):
        super().__init__("parallelogram_align", TransformationType.GEOMETRIC)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        shift_amount: int = 1,
        **kwargs
    ) -> TransformationResult:
        """Align parallelogram shapes.

        Args:
            input_grid: Input grid with parallelogram shapes
            shift_amount: Amount to shift non-anchor rows (default: 1)
        """
        try:
            data = input_grid.data
            out = np.zeros_like(data)

            # Process each color separately
            colors = set(data.flatten()) - {0}

            for color in colors:
                # Find all positions for this color
                positions = np.argwhere(data == color)
                if len(positions) == 0:
                    continue

                # Find bottom row and max column for this object
                bottom_row = positions[:, 0].max()
                max_col = positions[:, 1].max()

                # Process each pixel
                for r, c in positions:
                    if r == bottom_row:
                        # Bottom row stays fixed
                        out[r, c] = color
                    elif c == max_col:
                        # Max column stays fixed
                        out[r, c] = color
                    else:
                        # Shift right by shift_amount
                        new_c = c + shift_amount
                        if new_c < data.shape[1]:
                            out[r, new_c] = color

            output_grid = ARCGrid(data=out, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={'shift_amount': shift_amount},
                explanation=f"Aligned parallelogram shapes with shift={shift_amount}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Parallelogram alignment failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "shift_amount": {
                "type": "int",
                "min": 1,
                "max": 5,
                "default": 1,
                "description": "Amount to shift non-anchor rows"
            }
        }

    def fit_parameters(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]]
    ) -> Optional[Dict[str, Any]]:
        """Try to fit parameters from examples."""
        if not examples:
            return None

        # Input and output should have same shape
        if not all(inp.shape == out.shape for inp, out in examples):
            return None

        # Try different shift amounts
        for shift in [1, 2]:
            all_match = True
            for inp, out in examples:
                result = self.apply(inp, shift_amount=shift)
                if not result.success:
                    all_match = False
                    break
                if not np.array_equal(result.output_grid.data, out.data):
                    all_match = False
                    break

            if all_match:
                return {'shift_amount': shift}

        return None

    def verify(
        self,
        input_grid: ARCGrid,
        output_grid: ARCGrid,
        **params
    ) -> bool:
        """Verify transformation produces expected output."""
        result = self.apply(input_grid, **params)
        if not result.success or result.output_grid is None:
            return False
        return np.array_equal(result.output_grid.data, output_grid.data)
