"""Object centering transformations for ARC tasks.

Operations that center objects horizontally or vertically.
"""

from typing import Optional, List, Dict, Any
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class CenterObjectsByColorTransformation(Transformation):
    """Center each colored object horizontally in the grid."""

    def __init__(self):
        super().__init__("center_objects_by_color", TransformationType.GEOMETRIC)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        axis: str = "horizontal",
        **kwargs
    ) -> TransformationResult:
        """Center objects by translating them.

        Args:
            input_grid: Input grid with objects
            axis: "horizontal" or "vertical" centering
        """
        try:
            output_data = np.zeros_like(input_grid.data)

            # Get all non-background colors
            colors = [c for c in input_grid.get_unique_colors() if c != 0]

            if axis == "horizontal":
                target_center_col = input_grid.width / 2.0

                for color in colors:
                    # Find all pixels of this color
                    positions = np.argwhere(input_grid.data == color)

                    if len(positions) > 0:
                        # Calculate current center
                        center_col = positions[:, 1].mean()

                        # Calculate offset to center
                        offset = int(round(target_center_col - center_col))

                        # Translate object
                        for pos in positions:
                            row, col = pos
                            new_col = col + offset

                            # Place in output if within bounds
                            if 0 <= new_col < input_grid.width:
                                output_data[row, new_col] = color

            elif axis == "vertical":
                target_center_row = input_grid.height / 2.0

                for color in colors:
                    # Find all pixels of this color
                    positions = np.argwhere(input_grid.data == color)

                    if len(positions) > 0:
                        # Calculate current center
                        center_row = positions[:, 0].mean()

                        # Calculate offset to center
                        offset = int(round(target_center_row - center_row))

                        # Translate object
                        for pos in positions:
                            row, col = pos
                            new_row = row + offset

                            # Place in output if within bounds
                            if 0 <= new_row < input_grid.height:
                                output_data[new_row, col] = color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={'axis': axis},
                explanation=f"Centered objects {axis}ly",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Object centering failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "axis": {
                "type": "string",
                "enum": ["horizontal", "vertical"],
                "default": "horizontal",
                "description": "Axis along which to center"
            }
        }
