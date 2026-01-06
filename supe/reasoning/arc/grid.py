"""Core data structures for ARC grids and objects."""

from dataclasses import dataclass, field
from typing import Set, Tuple, List, Optional, Dict
import numpy as np


@dataclass
class ARCObject:
    """Represents a discrete object in an ARC grid.

    An object is a connected component of same-colored pixels.
    """

    pixels: Set[Tuple[int, int]]  # Set of (row, col) coordinates
    color: int  # Color value (0-9)
    grid_id: Optional[str] = None  # Source grid identifier

    def __post_init__(self):
        if not self.pixels:
            raise ValueError("Object must have at least one pixel")

    @property
    def mass(self) -> int:
        """Number of pixels in object."""
        return len(self.pixels)

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Get bounding box (min_row, min_col, max_row, max_col)."""
        if not self.pixels:
            return (0, 0, 0, 0)

        rows = [r for r, c in self.pixels]
        cols = [c for r, c in self.pixels]

        return (min(rows), min(cols), max(rows), max(cols))

    @property
    def width(self) -> int:
        """Width of bounding box."""
        min_row, min_col, max_row, max_col = self.bounding_box
        return max_col - min_col + 1

    @property
    def height(self) -> int:
        """Height of bounding box."""
        min_row, min_col, max_row, max_col = self.bounding_box
        return max_row - min_row + 1

    @property
    def center(self) -> Tuple[float, float]:
        """Center of mass (row, col)."""
        if not self.pixels:
            return (0.0, 0.0)

        rows = [r for r, c in self.pixels]
        cols = [c for r, c in self.pixels]

        return (sum(rows) / len(rows), sum(cols) / len(cols))

    def to_array(self) -> np.ndarray:
        """Convert to dense array of minimal size."""
        min_row, min_col, max_row, max_col = self.bounding_box

        height = max_row - min_row + 1
        width = max_col - min_col + 1

        arr = np.zeros((height, width), dtype=int)

        for r, c in self.pixels:
            arr[r - min_row, c - min_col] = self.color

        return arr

    def translate(self, dr: int, dc: int) -> "ARCObject":
        """Create new object translated by (dr, dc)."""
        new_pixels = {(r + dr, c + dc) for r, c in self.pixels}
        return ARCObject(pixels=new_pixels, color=self.color, grid_id=self.grid_id)

    def contains_point(self, row: int, col: int) -> bool:
        """Check if point is in object."""
        return (row, col) in self.pixels

    def overlaps(self, other: "ARCObject") -> bool:
        """Check if this object overlaps with another."""
        return bool(self.pixels & other.pixels)

    def distance_to(self, other: "ARCObject") -> float:
        """Minimum distance to another object."""
        if self.overlaps(other):
            return 0.0

        min_dist = float('inf')

        for r1, c1 in self.pixels:
            for r2, c2 in other.pixels:
                dist = ((r1 - r2) ** 2 + (c1 - c2) ** 2) ** 0.5
                min_dist = min(min_dist, dist)

        return min_dist


@dataclass
class ARCGrid:
    """Represents an ARC grid.

    Grids are 2D arrays of colors (integers 0-9).
    Color 0 is typically the background.
    """

    data: np.ndarray  # 2D array of integers (0-9)
    task_id: Optional[str] = None
    grid_type: Optional[str] = None  # 'train_input', 'train_output', 'test_input', etc.

    def __post_init__(self):
        if not isinstance(self.data, np.ndarray):
            self.data = np.array(self.data, dtype=int)

        if self.data.ndim != 2:
            raise ValueError(f"Grid must be 2D, got {self.data.ndim}D")

        # Validate colors are in range 0-9
        if self.data.min() < 0 or self.data.max() > 9:
            raise ValueError(f"Grid colors must be 0-9, got {self.data.min()}-{self.data.max()}")

    @classmethod
    def from_list(cls, grid_list: List[List[int]], **kwargs) -> "ARCGrid":
        """Create grid from list of lists."""
        return cls(data=np.array(grid_list, dtype=int), **kwargs)

    @property
    def height(self) -> int:
        """Grid height (number of rows)."""
        return self.data.shape[0]

    @property
    def width(self) -> int:
        """Grid width (number of columns)."""
        return self.data.shape[1]

    @property
    def shape(self) -> Tuple[int, int]:
        """Grid shape (height, width)."""
        return (self.height, self.width)

    @property
    def size(self) -> int:
        """Total number of cells."""
        return self.height * self.width

    def get(self, row: int, col: int) -> int:
        """Get color at position."""
        if 0 <= row < self.height and 0 <= col < self.width:
            return int(self.data[row, col])
        return -1  # Out of bounds

    def set(self, row: int, col: int, color: int):
        """Set color at position."""
        if 0 <= row < self.height and 0 <= col < self.width:
            self.data[row, col] = color

    def copy(self) -> "ARCGrid":
        """Create a deep copy of this grid."""
        return ARCGrid(
            data=self.data.copy(),
            task_id=self.task_id,
            grid_type=self.grid_type,
        )

    def get_background_color(self) -> int:
        """Identify background color (most common)."""
        unique, counts = np.unique(self.data, return_counts=True)
        return int(unique[np.argmax(counts)])

    def get_color_histogram(self) -> Dict[int, int]:
        """Get histogram of colors."""
        unique, counts = np.unique(self.data, return_counts=True)
        return {int(color): int(count) for color, count in zip(unique, counts)}

    def get_unique_colors(self) -> Set[int]:
        """Get set of colors present in grid."""
        return set(int(c) for c in np.unique(self.data))

    def count_color(self, color: int) -> int:
        """Count pixels of specific color."""
        return int(np.sum(self.data == color))

    def apply_mask(self, mask: np.ndarray, fill_color: int = 0) -> "ARCGrid":
        """Apply boolean mask, setting False pixels to fill_color."""
        new_data = self.data.copy()
        new_data[~mask] = fill_color
        return ARCGrid(data=new_data, task_id=self.task_id)

    def extract_subgrid(self, row_start: int, col_start: int, height: int, width: int) -> "ARCGrid":
        """Extract a rectangular subgrid."""
        subdata = self.data[row_start:row_start+height, col_start:col_start+width].copy()
        return ARCGrid(data=subdata, task_id=self.task_id)

    def find_color_positions(self, color: int) -> Set[Tuple[int, int]]:
        """Find all positions with given color."""
        positions = np.argwhere(self.data == color)
        return {(int(r), int(c)) for r, c in positions}

    def is_symmetric_horizontal(self) -> bool:
        """Check if grid is symmetric about horizontal axis."""
        return np.array_equal(self.data, np.flipud(self.data))

    def is_symmetric_vertical(self) -> bool:
        """Check if grid is symmetric about vertical axis."""
        return np.array_equal(self.data, np.fliplr(self.data))

    def is_symmetric_diagonal(self) -> bool:
        """Check if grid is symmetric about main diagonal."""
        if self.height != self.width:
            return False
        return np.array_equal(self.data, self.data.T)

    def count_objects(self, background_color: Optional[int] = None) -> int:
        """Quick count of objects (connected components)."""
        if background_color is None:
            background_color = self.get_background_color()

        from supe.reasoning.arc.detector import ObjectDetector
        detector = ObjectDetector()
        objects = detector.detect_objects(self, background_color=background_color)
        return len(objects)

    def equals(self, other: "ARCGrid") -> bool:
        """Check if two grids are identical."""
        if not isinstance(other, ARCGrid):
            return False
        return np.array_equal(self.data, other.data)

    def __eq__(self, other) -> bool:
        """Equality operator."""
        return self.equals(other)

    def __repr__(self) -> str:
        """String representation."""
        return f"ARCGrid(shape={self.shape}, colors={len(self.get_unique_colors())})"

    def __str__(self) -> str:
        """Detailed string representation."""
        lines = [f"ARCGrid {self.shape}:"]
        for row in self.data:
            lines.append("  " + " ".join(str(c) for c in row))
        return "\n".join(lines)
