"""Tile by marker transformations for ARC tasks.

Place input pattern at positions indicated by marker color.
"""

from typing import Optional, List, Dict, Any
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class TileByMarkerTransformation(Transformation):
    """Tile input at positions indicated by marker color.

    Pattern:
    - Expand input to N times size (creating NxN blocks)
    - For each position of marker_color in input, place input in corresponding block
    """

    def __init__(self):
        super().__init__("tile_by_marker", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        marker_color: int = 2,
        scale: int = 3,
        **kwargs
    ) -> TransformationResult:
        """Tile input at marker positions.

        Args:
            input_grid: Input grid
            marker_color: Color that indicates tile positions (default: 2)
            scale: Scale factor (output = input_size * scale)
        """
        try:
            h, w = input_grid.height, input_grid.width
            new_h, new_w = h * scale, w * scale

            # Create output grid
            output_data = np.zeros((new_h, new_w), dtype=input_grid.data.dtype)

            # Find marker positions
            marker_positions = np.argwhere(input_grid.data == marker_color)

            # Place input at each marker position
            for pos in marker_positions:
                r, c = pos
                # Calculate block position in output
                block_r = r * h
                block_c = c * w
                # Place the input pattern
                output_data[block_r:block_r+h, block_c:block_c+w] = input_grid.data

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'marker_color': marker_color,
                    'scale': scale
                },
                explanation=f"Tiled input at {len(marker_positions)} marker positions",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Tile by marker failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "marker_color": {
                "type": "int",
                "min": 1,
                "max": 9,
                "default": 2,
                "description": "Color that marks tile positions"
            },
            "scale": {
                "type": "int",
                "min": 2,
                "max": 5,
                "default": 3,
                "description": "Scale factor for output"
            }
        }
