"""Marker-based color transformations for ARC tasks.

Operations that color rows/columns based on marker positions.
"""

from typing import Optional, List, Dict, Any
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class ColorRowsByMarkerPositionTransformation(Transformation):
    """Color rows based on marker position in each row."""

    def __init__(self):
        super().__init__("color_rows_by_marker_position", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        marker_color: int = 5,
        color_mapping: Optional[Dict[int, int]] = None,
        **kwargs
    ) -> TransformationResult:
        """Color rows based on where marker appears.

        Args:
            input_grid: Input grid with marker pixels
            marker_color: Color of the marker (default: 5)
            color_mapping: Map from column index to output color
                          e.g., {0: 2, 1: 4, 2: 3}
        """
        try:
            output_data = np.zeros_like(input_grid.data)

            # Default mapping if not provided (based on task a85d4709)
            if color_mapping is None:
                color_mapping = {0: 2, 1: 4, 2: 3}

            for row in range(input_grid.height):
                row_data = input_grid.data[row, :]

                # Find marker position
                marker_positions = np.where(row_data == marker_color)[0]

                if len(marker_positions) > 0:
                    marker_col = int(marker_positions[0])  # Use first marker

                    # Get color for this position
                    if marker_col in color_mapping:
                        fill_color = color_mapping[marker_col]

                        # Fill entire row with this color
                        output_data[row, :] = fill_color
                    else:
                        # No mapping for this column, leave as 0
                        pass

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'marker_color': marker_color,
                    'color_mapping': color_mapping
                },
                explanation=f"Colored rows by marker position",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Marker-based row coloring failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "marker_color": {
                "type": "integer",
                "default": 5,
                "description": "Color of the marker pixel"
            },
            "color_mapping": {
                "type": "dict",
                "default": None,
                "description": "Map from column index to row color"
            }
        }
