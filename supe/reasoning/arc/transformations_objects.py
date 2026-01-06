"""Object-based transformations for ARC tasks.

Includes object detection, manipulation, and pattern application.
"""

from typing import Optional, List, Dict, Any, Tuple, Set
import numpy as np
from collections import deque
from dataclasses import dataclass

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


@dataclass
class DetectedObject:
    """A detected connected component."""
    pixels: Set[Tuple[int, int]]
    color: int
    bounding_box: Tuple[int, int, int, int]  # min_row, min_col, max_row, max_col

    @property
    def center(self) -> Tuple[float, float]:
        """Get center of object."""
        if not self.pixels:
            return (0.0, 0.0)
        rows = [p[0] for p in self.pixels]
        cols = [p[1] for p in self.pixels]
        return (np.mean(rows), np.mean(cols))

    @property
    def size(self) -> int:
        """Get number of pixels in object."""
        return len(self.pixels)


class ExtractObjectsTransformation(Transformation):
    """Detect and extract connected components as objects."""

    def __init__(self):
        super().__init__("extract_objects", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        min_size: int = 1,
        connectivity: str = "4-connected",
        ignore_background: bool = True,
        **kwargs
    ) -> TransformationResult:
        """Detect connected components.

        Args:
            input_grid: Input grid
            min_size: Minimum object size (in pixels)
            connectivity: "4-connected" or "8-connected"
            ignore_background: Skip background color (0)
        """
        try:
            detected_objects = self._detect_objects(
                input_grid,
                min_size=min_size,
                connectivity=connectivity,
                ignore_background=ignore_background
            )

            # Store objects in metadata for use by other transformations
            # Return the input grid unchanged (this is a detection operation)
            return TransformationResult(
                success=True,
                output_grid=input_grid.copy(),
                parameters_used={
                    'min_size': min_size,
                    'connectivity': connectivity,
                    'object_count': len(detected_objects)
                },
                explanation=f"Detected {len(detected_objects)} objects",
                metadata={'detected_objects': detected_objects}
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Object detection failed: {str(e)}"
            )

    def _detect_objects(
        self,
        grid: ARCGrid,
        min_size: int,
        connectivity: str,
        ignore_background: bool
    ) -> List[DetectedObject]:
        """Detect connected components using flood fill."""
        visited = set()
        objects = []

        for i in range(grid.height):
            for j in range(grid.width):
                if (i, j) in visited:
                    continue

                color = int(grid.data[i, j])

                if ignore_background and color == 0:
                    visited.add((i, j))
                    continue

                # Start flood fill from this pixel
                obj_pixels = self._flood_fill(
                    grid, i, j, color, connectivity
                )

                if len(obj_pixels) >= min_size:
                    # Compute bounding box
                    rows = [p[0] for p in obj_pixels]
                    cols = [p[1] for p in obj_pixels]
                    bbox = (min(rows), min(cols), max(rows), max(cols))

                    objects.append(DetectedObject(
                        pixels=obj_pixels,
                        color=color,
                        bounding_box=bbox
                    ))

                visited.update(obj_pixels)

        return objects

    def _flood_fill(
        self,
        grid: ARCGrid,
        start_row: int,
        start_col: int,
        target_color: int,
        connectivity: str
    ) -> Set[Tuple[int, int]]:
        """Flood fill to find connected pixels of same color."""
        pixels = set()
        queue = deque([(start_row, start_col)])

        # Neighbor offsets
        if connectivity == "4-connected":
            neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        else:  # 8-connected
            neighbors = [
                (0, 1), (1, 0), (0, -1), (-1, 0),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ]

        while queue:
            r, c = queue.popleft()

            if (r, c) in pixels:
                continue
            if r < 0 or r >= grid.height or c < 0 or c >= grid.width:
                continue
            if grid.data[r, c] != target_color:
                continue

            pixels.add((r, c))

            for dr, dc in neighbors:
                queue.append((r + dr, c + dc))

        return pixels

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "min_size": {
                "type": "integer",
                "default": 1,
                "description": "Minimum object size in pixels"
            },
            "connectivity": {
                "type": "string",
                "enum": ["4-connected", "8-connected"],
                "default": "4-connected",
                "description": "Connectivity type"
            },
            "ignore_background": {
                "type": "boolean",
                "default": True,
                "description": "Skip background color (0)"
            }
        }


class TranslateObjectTransformation(Transformation):
    """Translate (move) objects by specified offset."""

    def __init__(self):
        super().__init__("translate_object", TransformationType.GEOMETRIC)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        dx: int = 0,
        dy: int = 0,
        object_indices: Optional[List[int]] = None,
        **kwargs
    ) -> TransformationResult:
        """Translate objects.

        Args:
            input_grid: Input grid
            dx: Horizontal offset (positive = right)
            dy: Vertical offset (positive = down)
            object_indices: Which objects to translate (None = all)
        """
        try:
            # First detect objects if not provided
            if not objects:
                detector = ExtractObjectsTransformation()
                result = detector.apply(input_grid)
                if not result.success or not result.metadata:
                    return TransformationResult(
                        success=False,
                        explanation="No objects detected"
                    )
                detected_objects = result.metadata['detected_objects']
            else:
                # Convert ARCObject to DetectedObject
                detected_objects = self._convert_objects(input_grid, objects)

            # Create output grid
            output_data = np.zeros_like(input_grid.data)

            # Translate specified objects
            for i, obj in enumerate(detected_objects):
                if object_indices is not None and i not in object_indices:
                    # Don't translate this object, copy as-is
                    for r, c in obj.pixels:
                        if 0 <= r < input_grid.height and 0 <= c < input_grid.width:
                            output_data[r, c] = obj.color
                else:
                    # Translate this object
                    for r, c in obj.pixels:
                        new_r = r + dy
                        new_c = c + dx
                        if 0 <= new_r < input_grid.height and 0 <= new_c < input_grid.width:
                            output_data[new_r, new_c] = obj.color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={'dx': dx, 'dy': dy, 'object_indices': object_indices},
                explanation=f"Translated objects by ({dx}, {dy})",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Translation failed: {str(e)}"
            )

    def _convert_objects(
        self,
        grid: ARCGrid,
        arc_objects: List[ARCObject]
    ) -> List[DetectedObject]:
        """Convert ARCObject to DetectedObject format."""
        detected = []
        for obj in arc_objects:
            pixels = set()
            min_r, min_c, max_r, max_c = obj.bounding_box

            # Find all pixels of this object's color in its bounding box
            for r in range(min_r, max_r + 1):
                for c in range(min_c, max_c + 1):
                    if grid.data[r, c] == obj.color:
                        pixels.add((r, c))

            detected.append(DetectedObject(
                pixels=pixels,
                color=obj.color,
                bounding_box=obj.bounding_box
            ))

        return detected

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "dx": {
                "type": "integer",
                "default": 0,
                "description": "Horizontal offset (positive = right)"
            },
            "dy": {
                "type": "integer",
                "default": 0,
                "description": "Vertical offset (positive = down)"
            },
            "object_indices": {
                "type": "list",
                "default": None,
                "description": "Which objects to translate (None = all)"
            }
        }


class ApplyPatternToObjectTransformation(Transformation):
    """Apply a pattern (like cross, plus, square) to each object."""

    def __init__(self):
        super().__init__("apply_pattern_to_object", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        pattern: str = "cross",
        size: int = 3,
        preserve_original: bool = False,
        **kwargs
    ) -> TransformationResult:
        """Apply pattern to objects.

        Args:
            input_grid: Input grid
            pattern: Pattern type ("cross", "plus", "square", "diamond")
            size: Pattern size (odd number, e.g., 3 for 3x3)
            preserve_original: Keep original pixels
        """
        try:
            # First detect objects if not provided
            detector = ExtractObjectsTransformation()
            result = detector.apply(input_grid)
            if not result.success or not result.metadata:
                return TransformationResult(
                    success=False,
                    explanation="No objects detected"
                )
            detected_objects = result.metadata['detected_objects']

            # Create output grid
            output_data = input_grid.data.copy() if preserve_original else np.zeros_like(input_grid.data)

            # Apply pattern to each object
            for obj in detected_objects:
                center_r, center_c = obj.center
                center_r = int(round(center_r))
                center_c = int(round(center_c))

                pattern_pixels = self._generate_pattern(
                    center_r, center_c, pattern, size
                )

                for r, c in pattern_pixels:
                    if 0 <= r < input_grid.height and 0 <= c < input_grid.width:
                        output_data[r, c] = obj.color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'pattern': pattern,
                    'size': size,
                    'preserve_original': preserve_original
                },
                explanation=f"Applied {pattern} pattern (size {size}) to {len(detected_objects)} objects",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Pattern application failed: {str(e)}"
            )

    def _generate_pattern(
        self,
        center_r: int,
        center_c: int,
        pattern: str,
        size: int
    ) -> Set[Tuple[int, int]]:
        """Generate pattern pixels centered at position."""
        pixels = set()
        half = size // 2

        if pattern == "cross":
            # Vertical line
            for i in range(-half, half + 1):
                pixels.add((center_r + i, center_c))
            # Horizontal line
            for j in range(-half, half + 1):
                pixels.add((center_r, center_c + j))

        elif pattern == "plus":
            # Same as cross
            for i in range(-half, half + 1):
                pixels.add((center_r + i, center_c))
            for j in range(-half, half + 1):
                pixels.add((center_r, center_c + j))

        elif pattern == "square":
            # Filled square
            for i in range(-half, half + 1):
                for j in range(-half, half + 1):
                    pixels.add((center_r + i, center_c + j))

        elif pattern == "diamond":
            # Diamond shape
            for i in range(-half, half + 1):
                for j in range(-half, half + 1):
                    if abs(i) + abs(j) <= half:
                        pixels.add((center_r + i, center_c + j))

        return pixels

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "pattern": {
                "type": "string",
                "enum": ["cross", "plus", "square", "diamond"],
                "default": "cross",
                "description": "Pattern type to apply"
            },
            "size": {
                "type": "integer",
                "default": 3,
                "description": "Pattern size (odd number)"
            },
            "preserve_original": {
                "type": "boolean",
                "default": False,
                "description": "Keep original pixels"
            }
        }
