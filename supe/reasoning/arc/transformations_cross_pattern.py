"""Cross pattern transformations for ARC tasks.

Operations that draw cross patterns around center pixels based on associated arm pixels.
"""

from typing import Optional, List, Dict, Any, Set, Tuple
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class DrawCrossByAssociationTransformation(Transformation):
    """Draw cross patterns around center pixels based on arm pixels.

    Pattern:
    - Center pixels: colors that appear exactly once in the entire grid
    - Arm color: the color that appears in BOTH the center's row AND column
    - Cross arms are drawn ONLY in directions where arm indicator pixels exist:
      - If arm pixel exists above center → draw up arm
      - If arm pixel exists below center → draw down arm
      - If arm pixel exists left of center → draw left arm
      - If arm pixel exists right of center → draw right arm
    """

    def __init__(self):
        super().__init__("draw_cross_by_association", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        **kwargs
    ) -> TransformationResult:
        """Draw cross patterns around center pixels.

        For each center pixel (color appearing exactly once in grid):
        - Find the arm color (appears in both center's row AND column)
        - Draw cross arms only in directions where arm indicators exist
        """
        try:
            output_data = np.zeros_like(input_grid.data)

            # Count occurrences of each color in the entire grid
            color_counts = {}
            color_positions = {}
            for r in range(input_grid.height):
                for c in range(input_grid.width):
                    color = int(input_grid.data[r, c])
                    if color != 0:
                        if color not in color_counts:
                            color_counts[color] = 0
                            color_positions[color] = []
                        color_counts[color] += 1
                        color_positions[color].append((r, c))

            # Find center pixels (colors appearing exactly once)
            center_pixels = []
            for color, count in color_counts.items():
                if count == 1:
                    pos = color_positions[color][0]
                    center_pixels.append((color, pos))

            # For each center, find the arm color and draw selective cross
            for center_color, (cr, cc) in center_pixels:
                # Find arm colors and their positions in row
                row_arm_positions = {}  # color -> list of columns
                for c in range(input_grid.width):
                    color = int(input_grid.data[cr, c])
                    if color != 0 and c != cc:
                        if color not in row_arm_positions:
                            row_arm_positions[color] = []
                        row_arm_positions[color].append(c)

                # Find arm colors and their positions in column
                col_arm_positions = {}  # color -> list of rows
                for r in range(input_grid.height):
                    color = int(input_grid.data[r, cc])
                    if color != 0 and r != cr:
                        if color not in col_arm_positions:
                            col_arm_positions[color] = []
                        col_arm_positions[color].append(r)

                # Arm color can appear in EITHER row OR column (union, not intersection)
                row_colors = set(row_arm_positions.keys())
                col_colors = set(col_arm_positions.keys())
                arm_colors = row_colors | col_colors

                if arm_colors:
                    # Find arm color that appears in both row and column preferentially
                    # If none, use one that appears in row or column
                    common_colors = row_colors & col_colors
                    if common_colors:
                        arm_color = min(common_colors)
                    else:
                        arm_color = min(arm_colors)  # Deterministic choice

                    # Place center pixel
                    output_data[cr, cc] = center_color

                    # Determine which directions to draw arms
                    # Check row for left/right indicators (only if arm_color in row)
                    has_left = any(c < cc for c in row_arm_positions.get(arm_color, []))
                    has_right = any(c > cc for c in row_arm_positions.get(arm_color, []))

                    # Check column for up/down indicators (only if arm_color in column)
                    has_up = any(r < cr for r in col_arm_positions.get(arm_color, []))
                    has_down = any(r > cr for r in col_arm_positions.get(arm_color, []))

                    # Draw arms only in indicated directions
                    if has_left and cc > 0:
                        output_data[cr, cc - 1] = arm_color
                    if has_right and cc < input_grid.width - 1:
                        output_data[cr, cc + 1] = arm_color
                    if has_up and cr > 0:
                        output_data[cr - 1, cc] = arm_color
                    if has_down and cr < input_grid.height - 1:
                        output_data[cr + 1, cc] = arm_color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={},
                explanation=f"Drew selective cross patterns around {len(center_pixels)} center pixels",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Cross pattern drawing failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {}
