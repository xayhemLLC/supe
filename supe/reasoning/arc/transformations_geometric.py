"""Geometric transformations for ARC tasks.

Includes rotation, flipping, scaling, translation, and compositions.
"""

from typing import Optional, List, Dict, Any
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.spatial import SpatialReasoner
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class RotateTransformation(Transformation):
    """Rotate grid by specified angle."""

    def __init__(self):
        super().__init__("rotate", TransformationType.GEOMETRIC)
        self.spatial = SpatialReasoner()

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        angle: int = 90,
        **kwargs
    ) -> TransformationResult:
        """Rotate grid by angle (90, 180, 270 degrees)."""
        try:
            if angle == 90:
                output = self.spatial.rotate_grid_90(input_grid, clockwise=True)
            elif angle == 180:
                output = self.spatial.rotate_grid_180(input_grid)
            elif angle == 270:
                output = self.spatial.rotate_grid_90(input_grid, clockwise=False)
            elif angle == 0:
                output = input_grid.copy()
            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid angle: {angle}. Must be 0, 90, 180, or 270."
                )

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"angle": angle},
                explanation=f"Rotated by {angle}°",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Rotation failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "angle": {
                "type": "angle",
                "values": [0, 90, 180, 270],
                "default": 90,
                "description": "Rotation angle in degrees"
            }
        }


class FlipTransformation(Transformation):
    """Flip grid horizontally or vertically."""

    def __init__(self):
        super().__init__("flip", TransformationType.GEOMETRIC)
        self.spatial = SpatialReasoner()

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        direction: str = "horizontal",
        **kwargs
    ) -> TransformationResult:
        """Flip grid in specified direction."""
        try:
            if direction == "horizontal":
                output = self.spatial.flip_horizontal(input_grid)
            elif direction == "vertical":
                output = self.spatial.flip_vertical(input_grid)
            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid direction: {direction}"
                )

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"direction": direction},
                explanation=f"Flipped {direction}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Flip failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "direction": {
                "type": "direction",
                "values": ["horizontal", "vertical"],
                "default": "horizontal",
                "description": "Direction to flip"
            }
        }


class TransposeTransformation(Transformation):
    """Transpose grid (swap rows and columns)."""

    def __init__(self):
        super().__init__("transpose", TransformationType.GEOMETRIC)
        self.spatial = SpatialReasoner()

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        **kwargs
    ) -> TransformationResult:
        """Transpose the grid."""
        try:
            output = self.spatial.transpose(input_grid)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={},
                explanation="Transposed (swapped rows/columns)",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Transpose failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {}  # No parameters


class ScaleTransformation(Transformation):
    """Scale grid by integer factor."""

    def __init__(self):
        super().__init__("scale", TransformationType.GEOMETRIC)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        factor: int = 2,
        **kwargs
    ) -> TransformationResult:
        """Scale grid by integer factor."""
        try:
            if factor <= 0:
                return TransformationResult(
                    success=False,
                    explanation="Scale factor must be positive"
                )

            if factor == 1:
                output = input_grid.copy()
            else:
                # Scale each pixel
                new_height = input_grid.height * factor
                new_width = input_grid.width * factor
                new_data = np.zeros((new_height, new_width), dtype=int)

                for r in range(input_grid.height):
                    for c in range(input_grid.width):
                        color = input_grid.get(r, c)
                        # Fill factor×factor block
                        for dr in range(factor):
                            for dc in range(factor):
                                new_r = r * factor + dr
                                new_c = c * factor + dc
                                new_data[new_r, new_c] = color

                output = ARCGrid(data=new_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"factor": factor},
                explanation=f"Scaled by {factor}x",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Scale failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "factor": {
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 2,
                "description": "Scaling factor"
            }
        }


class CropTransformation(Transformation):
    """Crop grid to bounding box of non-background pixels."""

    def __init__(self):
        super().__init__("crop", TransformationType.GEOMETRIC)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        background: Optional[int] = None,
        **kwargs
    ) -> TransformationResult:
        """Crop to minimal bounding box."""
        try:
            if background is None:
                background = input_grid.get_background_color()

            # Find bounding box of non-background pixels
            non_bg_positions = []
            for r in range(input_grid.height):
                for c in range(input_grid.width):
                    if input_grid.get(r, c) != background:
                        non_bg_positions.append((r, c))

            if not non_bg_positions:
                # All background - return 1x1 grid
                output = ARCGrid(data=np.array([[background]]))
            else:
                rows = [r for r, c in non_bg_positions]
                cols = [c for r, c in non_bg_positions]

                min_r, max_r = min(rows), max(rows)
                min_c, max_c = min(cols), max(cols)

                height = max_r - min_r + 1
                width = max_c - min_c + 1

                output = input_grid.extract_subgrid(min_r, min_c, height, width)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"background": background},
                explanation=f"Cropped to content (background={background})",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Crop failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "background": {
                "type": "color",
                "default": None,
                "description": "Background color (auto-detect if None)"
            }
        }


class SymmetryCompletionTransformation(Transformation):
    """Complete partial symmetry in grid."""

    def __init__(self):
        super().__init__("complete_symmetry", TransformationType.GEOMETRIC)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        axis: str = "vertical",
        **kwargs
    ) -> TransformationResult:
        """Complete symmetry along specified axis."""
        try:
            output_data = input_grid.data.copy()

            if axis == "vertical":
                # Complete vertical symmetry (left-right)
                width = input_grid.width
                for r in range(input_grid.height):
                    for c in range(width // 2):
                        mirror_c = width - 1 - c
                        left_color = input_grid.get(r, c)
                        right_color = input_grid.get(r, mirror_c)

                        # If one side has content, copy to other
                        if left_color != 0 and right_color == 0:
                            output_data[r, mirror_c] = left_color
                        elif right_color != 0 and left_color == 0:
                            output_data[r, c] = right_color

            elif axis == "horizontal":
                # Complete horizontal symmetry (top-bottom)
                height = input_grid.height
                for r in range(height // 2):
                    mirror_r = height - 1 - r
                    for c in range(input_grid.width):
                        top_color = input_grid.get(r, c)
                        bottom_color = input_grid.get(mirror_r, c)

                        if top_color != 0 and bottom_color == 0:
                            output_data[mirror_r, c] = top_color
                        elif bottom_color != 0 and top_color == 0:
                            output_data[r, c] = bottom_color

            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid axis: {axis}"
                )

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"axis": axis},
                explanation=f"Completed {axis} symmetry",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Symmetry completion failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "axis": {
                "type": "direction",
                "values": ["horizontal", "vertical"],
                "default": "vertical",
                "description": "Axis of symmetry"
            }
        }
