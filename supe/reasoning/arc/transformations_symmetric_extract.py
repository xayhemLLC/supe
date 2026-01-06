"""Symmetric extraction transformations for ARC tasks.

Extract pattern from 180-degree opposite of marker position.
"""

from typing import Optional, List, Dict, Any, Tuple
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class ExtractSymmetricOppositeTransformation(Transformation):
    """Extract pattern from 180-degree opposite of marker position.

    Pattern:
    - Grid has rotational symmetry
    - Marker (color 1) indicates a 5x5 region
    - Extract from the 180-degree opposite position
    - Rotate extracted region 180 degrees to get output
    """

    def __init__(self):
        super().__init__("extract_symmetric_opposite", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        marker_color: int = 1,
        **kwargs
    ) -> TransformationResult:
        """Extract pattern from 180-degree opposite of marker.

        Args:
            input_grid: Input grid with marker and symmetric pattern
            marker_color: Color that marks the source position (default: 1)
        """
        try:
            data = input_grid.data
            h, w = data.shape

            # Find marker position
            marker_positions = np.argwhere(data == marker_color)
            if len(marker_positions) == 0:
                return TransformationResult(
                    success=False,
                    explanation="No marker positions found"
                )

            marker_min_r, marker_min_c = marker_positions.min(axis=0)
            marker_max_r, marker_max_c = marker_positions.max(axis=0)

            # Marker size
            marker_h = marker_max_r - marker_min_r + 1
            marker_w = marker_max_c - marker_min_c + 1

            # Compute 180-degree opposite position (reflect around grid center)
            opp_r = h - marker_max_r - 1
            opp_c = w - marker_max_c - 1

            # Bounds check
            if opp_r < 0 or opp_r + marker_h > h or opp_c < 0 or opp_c + marker_w > w:
                return TransformationResult(
                    success=False,
                    explanation="Opposite region out of bounds"
                )

            # Extract opposite region
            opp_region = data[opp_r:opp_r+marker_h, opp_c:opp_c+marker_w]

            # Rotate 180 degrees
            result = np.rot90(opp_region, 2)

            # Find output color (most common non-zero, non-marker color in the region)
            out_color = 0
            for color in range(1, 10):
                if color != marker_color and color in result:
                    out_color = color
                    break

            # Convert to binary (out_color vs 0)
            binary_result = np.where(result == out_color, out_color, 0)

            output_grid = ARCGrid(data=binary_result, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'marker_color': marker_color,
                    'output_color': int(out_color),
                    'marker_position': (int(marker_min_r), int(marker_min_c)),
                    'opposite_position': (int(opp_r), int(opp_c)),
                },
                explanation=f"Extracted {marker_h}x{marker_w} region from 180° opposite of marker",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Symmetric extraction failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "marker_color": {
                "type": "int",
                "min": 1,
                "max": 9,
                "default": 1,
                "description": "Color that marks the source position"
            }
        }

    def fit_parameters(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]]
    ) -> Optional[Dict[str, Any]]:
        """Try to fit parameters from examples."""
        if not examples:
            return None

        # Check first example
        inp, out = examples[0]

        # Output should be smaller than input (extraction)
        if out.height >= inp.height or out.width >= inp.width:
            return None

        # Grid should be square and have near rotational symmetry
        if inp.height != inp.width:
            return None

        # Check for marker color (typically 1)
        for marker_color in [1, 2, 3]:
            marker_positions = np.argwhere(inp.data == marker_color)
            if len(marker_positions) > 0:
                # Marker should form a rectangular region matching output size
                min_r, min_c = marker_positions.min(axis=0)
                max_r, max_c = marker_positions.max(axis=0)
                marker_h = max_r - min_r + 1
                marker_w = max_c - min_c + 1

                if marker_h == out.height and marker_w == out.width:
                    # Try this marker color
                    result = self.apply(inp, marker_color=marker_color)
                    if result.success and result.output_grid:
                        if np.array_equal(result.output_grid.data, out.data):
                            return {'marker_color': marker_color}

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
