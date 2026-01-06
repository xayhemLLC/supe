"""Pattern stamp transformations for ARC tasks.

Draw patterns (stamps) around marker positions.
"""

from typing import Optional, List, Dict, Any
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class StampCrossPatternTransformation(Transformation):
    """Stamp a cross pattern around each marker position.

    Pattern:
    marker_color  arm_color  marker_color
    arm_color     center     arm_color
    marker_color  arm_color  marker_color
    """

    def __init__(self):
        super().__init__("stamp_cross_pattern", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        marker_color: int = 5,
        arm_color: int = 1,
        center_color: int = 0,
        **kwargs
    ) -> TransformationResult:
        """Stamp cross pattern at marker positions.

        Args:
            input_grid: Input grid with marker pixels
            marker_color: Color that marks stamp positions (default: 5)
            arm_color: Color for cardinal directions (default: 1)
            center_color: Color for center of pattern (default: 0)
        """
        try:
            output_data = np.zeros_like(input_grid.data)

            # Find marker positions
            marker_positions = np.argwhere(input_grid.data == marker_color)

            # Pattern offsets: (row_offset, col_offset, color)
            pattern = [
                # Corners get marker_color
                (-1, -1, marker_color),
                (-1, 1, marker_color),
                (1, -1, marker_color),
                (1, 1, marker_color),
                # Cardinals get arm_color
                (-1, 0, arm_color),
                (1, 0, arm_color),
                (0, -1, arm_color),
                (0, 1, arm_color),
                # Center gets center_color
                (0, 0, center_color),
            ]

            # Stamp pattern at each marker
            for pos in marker_positions:
                r, c = pos
                for dr, dc, color in pattern:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < input_grid.height and 0 <= nc < input_grid.width:
                        output_data[nr, nc] = color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'marker_color': marker_color,
                    'arm_color': arm_color,
                    'center_color': center_color
                },
                explanation=f"Stamped cross pattern at {len(marker_positions)} positions",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Stamp cross pattern failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "marker_color": {
                "type": "int",
                "min": 1,
                "max": 9,
                "default": 5,
                "description": "Color marking stamp positions"
            },
            "arm_color": {
                "type": "int",
                "min": 1,
                "max": 9,
                "default": 1,
                "description": "Color for cardinal directions"
            },
            "center_color": {
                "type": "int",
                "min": 0,
                "max": 9,
                "default": 0,
                "description": "Color for center of pattern"
            }
        }
