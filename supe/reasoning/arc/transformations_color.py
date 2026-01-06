"""Color transformations for ARC tasks.

Includes color mapping, swapping, replacement, and palette operations.
"""

from typing import Optional, List, Dict, Any
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class ColorMapTransformation(Transformation):
    """Map colors according to a dictionary."""

    def __init__(self):
        super().__init__("color_map", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        mapping: Optional[Dict[int, int]] = None,
        **kwargs
    ) -> TransformationResult:
        """Apply color mapping to grid."""
        try:
            if mapping is None:
                return TransformationResult(
                    success=False,
                    explanation="No color mapping provided"
                )

            output_data = input_grid.data.copy()

            for r in range(input_grid.height):
                for c in range(input_grid.width):
                    color = input_grid.get(r, c)
                    if color in mapping:
                        output_data[r, c] = mapping[color]

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"mapping": mapping},
                explanation=f"Applied color mapping: {mapping}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Color map failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "mapping": {
                "type": "dict",
                "description": "Dictionary mapping old colors to new colors"
            }
        }


class ColorSwapTransformation(Transformation):
    """Swap two colors."""

    def __init__(self):
        super().__init__("color_swap", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        color1: int = 0,
        color2: int = 1,
        **kwargs
    ) -> TransformationResult:
        """Swap two colors in grid."""
        try:
            output_data = input_grid.data.copy()

            # Create mapping
            mask1 = output_data == color1
            mask2 = output_data == color2

            output_data[mask1] = color2
            output_data[mask2] = color1

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"color1": color1, "color2": color2},
                explanation=f"Swapped colors {color1} ↔ {color2}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Color swap failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "color1": {"type": "color", "description": "First color"},
            "color2": {"type": "color", "description": "Second color"},
        }


class ReplaceColorTransformation(Transformation):
    """Replace all occurrences of one color with another."""

    def __init__(self):
        super().__init__("replace_color", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        old_color: int = 0,
        new_color: int = 1,
        **kwargs
    ) -> TransformationResult:
        """Replace color in grid."""
        try:
            output_data = input_grid.data.copy()
            output_data[output_data == old_color] = new_color

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"old_color": old_color, "new_color": new_color},
                explanation=f"Replaced color {old_color} → {new_color}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Replace color failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "old_color": {"type": "color", "description": "Color to replace"},
            "new_color": {"type": "color", "description": "Replacement color"},
        }


class InvertColorsTransformation(Transformation):
    """Invert all colors (0→9, 1→8, 2→7, etc.)."""

    def __init__(self):
        super().__init__("invert_colors", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        **kwargs
    ) -> TransformationResult:
        """Invert colors in grid."""
        try:
            output_data = 9 - input_grid.data

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={},
                explanation="Inverted colors (0↔9, 1↔8, etc.)",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Invert colors failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {}  # No parameters


class RecolorObjectsTransformation(Transformation):
    """Recolor objects based on properties."""

    def __init__(self):
        super().__init__("recolor_objects", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        strategy: str = "by_size",
        colors: Optional[List[int]] = None,
        **kwargs
    ) -> TransformationResult:
        """Recolor objects based on strategy."""
        try:
            if objects is None:
                from supe.reasoning.arc.detector import ObjectDetector
                detector = ObjectDetector()
                objects = detector.detect_objects(input_grid)

            if not objects:
                return TransformationResult(
                    success=False,
                    explanation="No objects found"
                )

            if colors is None:
                colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]

            output_data = input_grid.data.copy()

            # Sort objects by strategy
            if strategy == "by_size":
                sorted_objects = sorted(objects, key=lambda o: o.mass)
            elif strategy == "by_row":
                sorted_objects = sorted(objects, key=lambda o: o.center[0])
            elif strategy == "by_column":
                sorted_objects = sorted(objects, key=lambda o: o.center[1])
            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid strategy: {strategy}"
                )

            # Assign colors
            for i, obj in enumerate(sorted_objects):
                new_color = colors[i % len(colors)]
                for r, c in obj.pixels:
                    output_data[r, c] = new_color

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"strategy": strategy, "colors": colors},
                explanation=f"Recolored objects {strategy}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Recolor objects failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "strategy": {
                "type": "string",
                "values": ["by_size", "by_row", "by_column"],
                "default": "by_size",
                "description": "How to order objects for recoloring"
            },
            "colors": {
                "type": "list",
                "default": None,
                "description": "List of colors to use (cycles if needed)"
            }
        }


class BackgroundSwapTransformation(Transformation):
    """Swap background and foreground colors."""

    def __init__(self):
        super().__init__("background_swap", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        new_background: int = 1,
        new_foreground: int = 0,
        **kwargs
    ) -> TransformationResult:
        """Swap background and foreground."""
        try:
            old_background = input_grid.get_background_color()

            output_data = input_grid.data.copy()

            # Map background to new foreground
            bg_mask = output_data == old_background
            fg_mask = ~bg_mask

            output_data[bg_mask] = new_background
            output_data[fg_mask] = new_foreground

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={
                    "new_background": new_background,
                    "new_foreground": new_foreground
                },
                explanation=f"Swapped background/foreground",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Background swap failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "new_background": {
                "type": "color",
                "default": 1,
                "description": "New background color"
            },
            "new_foreground": {
                "type": "color",
                "default": 0,
                "description": "New foreground color"
            }
        }
