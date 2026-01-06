"""Shape recognition for ARC objects and grids.

This module detects common shapes and patterns in ARC puzzles:
- Lines (horizontal, vertical, diagonal)
- Rectangles (filled, hollow, border)
- Common shapes (T, L, cross, plus)
- Geometric primitives
"""

from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from supe.reasoning.arc.grid import ARCGrid, ARCObject


class ShapeType(Enum):
    """Types of recognized shapes."""
    LINE = "line"
    RECTANGLE = "rectangle"
    SQUARE = "square"
    T_SHAPE = "t_shape"
    L_SHAPE = "l_shape"
    CROSS = "cross"
    PLUS = "plus"
    HOLLOW_RECTANGLE = "hollow_rectangle"
    BORDER = "border"
    DIAGONAL = "diagonal"
    UNKNOWN = "unknown"


class LineOrientation(Enum):
    """Orientation of line shapes."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL_MAIN = "diagonal_main"  # top-left to bottom-right
    DIAGONAL_ANTI = "diagonal_anti"  # top-right to bottom-left


@dataclass
class ShapeDescriptor:
    """Description of a detected shape."""
    shape_type: ShapeType
    confidence: float  # 0.0 to 1.0
    properties: Dict  # Shape-specific properties
    orientation: Optional[LineOrientation] = None

    def __repr__(self):
        props_str = ", ".join(f"{k}={v}" for k, v in self.properties.items())
        orient_str = f", orientation={self.orientation.value}" if self.orientation else ""
        return f"Shape({self.shape_type.value}, conf={self.confidence:.2f}{orient_str}, {props_str})"


class ShapeRecognizer:
    """Recognizes geometric shapes in ARC objects and grids."""

    def recognize_object(self, obj: ARCObject) -> ShapeDescriptor:
        """Recognize the shape of an object.

        Args:
            obj: Object to analyze

        Returns:
            Shape descriptor with type and properties
        """
        # Try recognition strategies in order of specificity

        # Check for lines first (most specific)
        line_result = self._recognize_line(obj)
        if line_result and line_result.confidence > 0.8:
            return line_result

        # Check for rectangles
        rect_result = self._recognize_rectangle(obj)
        if rect_result and rect_result.confidence > 0.8:
            return rect_result

        # Check for special shapes
        special_result = self._recognize_special_shape(obj)
        if special_result and special_result.confidence > 0.7:
            return special_result

        # Return best match or unknown
        results = [r for r in [line_result, rect_result, special_result] if r]
        if results:
            return max(results, key=lambda r: r.confidence)

        return ShapeDescriptor(
            shape_type=ShapeType.UNKNOWN,
            confidence=0.0,
            properties={"mass": obj.mass}
        )

    def _recognize_line(self, obj: ARCObject) -> Optional[ShapeDescriptor]:
        """Recognize line shapes."""
        min_r, min_c, max_r, max_c = obj.bounding_box
        width = max_c - min_c + 1
        height = max_r - min_r + 1

        # Horizontal line
        if height == 1:
            # Check density (should be contiguous)
            expected_pixels = width
            density = obj.mass / expected_pixels

            return ShapeDescriptor(
                shape_type=ShapeType.LINE,
                confidence=density,
                orientation=LineOrientation.HORIZONTAL,
                properties={
                    "length": width,
                    "thickness": 1,
                    "density": density,
                }
            )

        # Vertical line
        if width == 1:
            expected_pixels = height
            density = obj.mass / expected_pixels

            return ShapeDescriptor(
                shape_type=ShapeType.LINE,
                confidence=density,
                orientation=LineOrientation.VERTICAL,
                properties={
                    "length": height,
                    "thickness": 1,
                    "density": density,
                }
            )

        # Diagonal line (main diagonal: top-left to bottom-right)
        if width == height:
            # Check if pixels form diagonal
            diagonal_pixels = {(min_r + i, min_c + i) for i in range(width)}
            if obj.pixels == diagonal_pixels:
                return ShapeDescriptor(
                    shape_type=ShapeType.DIAGONAL,
                    confidence=1.0,
                    orientation=LineOrientation.DIAGONAL_MAIN,
                    properties={
                        "length": width,
                        "thickness": 1,
                    }
                )

            # Anti-diagonal: top-right to bottom-left
            anti_diagonal_pixels = {(min_r + i, max_c - i) for i in range(width)}
            if obj.pixels == anti_diagonal_pixels:
                return ShapeDescriptor(
                    shape_type=ShapeType.DIAGONAL,
                    confidence=1.0,
                    orientation=LineOrientation.DIAGONAL_ANTI,
                    properties={
                        "length": width,
                        "thickness": 1,
                    }
                )

        return None

    def _recognize_rectangle(self, obj: ARCObject) -> Optional[ShapeDescriptor]:
        """Recognize rectangle shapes (filled, hollow, border)."""
        min_r, min_c, max_r, max_c = obj.bounding_box
        width = max_c - min_c + 1
        height = max_r - min_r + 1

        # Perfect filled rectangle
        expected_pixels = width * height
        if obj.mass == expected_pixels:
            # Verify all pixels present
            expected = {
                (r, c)
                for r in range(min_r, max_r + 1)
                for c in range(min_c, max_c + 1)
            }
            if obj.pixels == expected:
                shape_type = ShapeType.SQUARE if width == height else ShapeType.RECTANGLE
                return ShapeDescriptor(
                    shape_type=shape_type,
                    confidence=1.0,
                    properties={
                        "width": width,
                        "height": height,
                        "filled": True,
                    }
                )

        # Hollow rectangle (only border)
        if width >= 3 and height >= 3:
            expected_border_pixels = 2 * (width + height) - 4

            # Check if it's a border
            border_pixels = set()
            for r in range(min_r, max_r + 1):
                border_pixels.add((r, min_c))  # Left edge
                border_pixels.add((r, max_c))  # Right edge
            for c in range(min_c, max_c + 1):
                border_pixels.add((min_r, c))  # Top edge
                border_pixels.add((max_r, c))  # Bottom edge

            if obj.pixels == border_pixels:
                return ShapeDescriptor(
                    shape_type=ShapeType.HOLLOW_RECTANGLE,
                    confidence=1.0,
                    properties={
                        "width": width,
                        "height": height,
                        "filled": False,
                        "border_thickness": 1,
                    }
                )

            # Partial match
            overlap = len(obj.pixels & border_pixels)
            confidence = overlap / len(border_pixels) if border_pixels else 0

            if confidence > 0.7:
                return ShapeDescriptor(
                    shape_type=ShapeType.BORDER,
                    confidence=confidence,
                    properties={
                        "width": width,
                        "height": height,
                        "completeness": confidence,
                    }
                )

        return None

    def _recognize_special_shape(self, obj: ARCObject) -> Optional[ShapeDescriptor]:
        """Recognize special shapes like T, L, cross, plus."""
        min_r, min_c, max_r, max_c = obj.bounding_box
        width = max_c - min_c + 1
        height = max_r - min_r + 1

        # Cross/Plus shape (requires odd dimensions and center)
        if width == height and width % 2 == 1:
            center_r = (min_r + max_r) // 2
            center_c = (min_c + max_c) // 2

            # Perfect cross: center row + center column
            cross_pixels = set()
            for r in range(min_r, max_r + 1):
                cross_pixels.add((r, center_c))  # Vertical line
            for c in range(min_c, max_c + 1):
                cross_pixels.add((center_r, c))  # Horizontal line

            if obj.pixels == cross_pixels:
                return ShapeDescriptor(
                    shape_type=ShapeType.CROSS,
                    confidence=1.0,
                    properties={
                        "size": width,
                        "center": (center_r, center_c),
                    }
                )

            # Plus shape (thicker cross)
            overlap = len(obj.pixels & cross_pixels)
            if overlap / len(cross_pixels) > 0.8:
                return ShapeDescriptor(
                    shape_type=ShapeType.PLUS,
                    confidence=0.8,
                    properties={
                        "size": width,
                        "thickness": 1,
                    }
                )

        # T-shape detection
        t_result = self._recognize_t_shape(obj, min_r, min_c, max_r, max_c)
        if t_result:
            return t_result

        # L-shape detection
        l_result = self._recognize_l_shape(obj, min_r, min_c, max_r, max_c)
        if l_result:
            return l_result

        return None

    def _recognize_t_shape(
        self,
        obj: ARCObject,
        min_r: int,
        min_c: int,
        max_r: int,
        max_c: int
    ) -> Optional[ShapeDescriptor]:
        """Recognize T-shapes in various orientations."""
        width = max_c - min_c + 1
        height = max_r - min_r + 1

        # T pointing down: top row + center column
        if height >= 2 and width >= 3:
            center_c = (min_c + max_c) // 2

            t_down = set()
            # Top horizontal bar
            for c in range(min_c, max_c + 1):
                t_down.add((min_r, c))
            # Vertical stem
            for r in range(min_r + 1, max_r + 1):
                t_down.add((r, center_c))

            overlap = len(obj.pixels & t_down)
            confidence = overlap / len(t_down) if t_down else 0

            if confidence > 0.85:
                return ShapeDescriptor(
                    shape_type=ShapeType.T_SHAPE,
                    confidence=confidence,
                    properties={
                        "orientation": "down",
                        "width": width,
                        "height": height,
                    }
                )

        return None

    def _recognize_l_shape(
        self,
        obj: ARCObject,
        min_r: int,
        min_c: int,
        max_r: int,
        max_c: int
    ) -> Optional[ShapeDescriptor]:
        """Recognize L-shapes in various orientations."""
        width = max_c - min_c + 1
        height = max_r - min_r + 1

        # L with corner at bottom-left
        if height >= 2 and width >= 2:
            l_shape = set()
            # Vertical part (left edge)
            for r in range(min_r, max_r + 1):
                l_shape.add((r, min_c))
            # Horizontal part (bottom edge)
            for c in range(min_c + 1, max_c + 1):
                l_shape.add((max_r, c))

            overlap = len(obj.pixels & l_shape)
            confidence = overlap / len(l_shape) if l_shape else 0

            if confidence > 0.85:
                return ShapeDescriptor(
                    shape_type=ShapeType.L_SHAPE,
                    confidence=confidence,
                    properties={
                        "orientation": "bottom_left",
                        "width": width,
                        "height": height,
                    }
                )

        return None

    def find_lines(
        self,
        grid: ARCGrid,
        orientation: Optional[LineOrientation] = None,
        min_length: int = 2,
    ) -> List[Tuple[ARCObject, ShapeDescriptor]]:
        """Find all lines in a grid.

        Args:
            grid: Grid to search
            orientation: Filter by orientation (None = all)
            min_length: Minimum line length

        Returns:
            List of (object, descriptor) pairs
        """
        from supe.reasoning.arc.detector import ObjectDetector

        detector = ObjectDetector()
        objects = detector.detect_objects(grid)

        lines = []
        for obj in objects:
            descriptor = self.recognize_object(obj)

            if descriptor.shape_type in (ShapeType.LINE, ShapeType.DIAGONAL):
                length = descriptor.properties.get("length", 0)

                if length >= min_length:
                    if orientation is None or descriptor.orientation == orientation:
                        lines.append((obj, descriptor))

        return lines

    def find_rectangles(
        self,
        grid: ARCGrid,
        include_hollow: bool = True,
    ) -> List[Tuple[ARCObject, ShapeDescriptor]]:
        """Find all rectangles in a grid.

        Args:
            grid: Grid to search
            include_hollow: Include hollow rectangles

        Returns:
            List of (object, descriptor) pairs
        """
        from supe.reasoning.arc.detector import ObjectDetector

        detector = ObjectDetector()
        objects = detector.detect_objects(grid)

        rectangles = []
        for obj in objects:
            descriptor = self.recognize_object(obj)

            types = {ShapeType.RECTANGLE, ShapeType.SQUARE}
            if include_hollow:
                types.add(ShapeType.HOLLOW_RECTANGLE)

            if descriptor.shape_type in types:
                rectangles.append((obj, descriptor))

        return rectangles

    def analyze_grid_shapes(self, grid: ARCGrid) -> Dict[str, any]:
        """Analyze all shapes in a grid.

        Returns:
            Dictionary with shape statistics and counts
        """
        from supe.reasoning.arc.detector import ObjectDetector

        detector = ObjectDetector()
        objects = detector.detect_objects(grid)

        shape_counts = {}
        all_shapes = []

        for obj in objects:
            descriptor = self.recognize_object(obj)
            shape_type = descriptor.shape_type.value

            shape_counts[shape_type] = shape_counts.get(shape_type, 0) + 1
            all_shapes.append((obj, descriptor))

        return {
            "total_objects": len(objects),
            "shape_counts": shape_counts,
            "shapes": all_shapes,
            "has_lines": "line" in shape_counts or "diagonal" in shape_counts,
            "has_rectangles": any(k in shape_counts for k in ["rectangle", "square", "hollow_rectangle"]),
            "has_special": any(k in shape_counts for k in ["cross", "plus", "t_shape", "l_shape"]),
        }
