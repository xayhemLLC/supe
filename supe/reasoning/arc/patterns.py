"""Pattern detection for ARC grids.

This module detects patterns in ARC puzzles:
- Repetition patterns (tiling, duplication)
- Progression patterns (growth, movement)
- Alternation patterns (checkerboard, stripes)
- Grid structure patterns (alignment, spacing)
"""

from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject


class PatternType(Enum):
    """Types of patterns."""
    REPETITION = "repetition"  # Same element repeats
    TILING = "tiling"  # Pattern tiles the space
    PROGRESSION = "progression"  # Systematic change
    ALTERNATION = "alternation"  # Elements alternate
    SYMMETRY = "symmetry"  # Mirror or rotational symmetry
    ALIGNMENT = "alignment"  # Objects aligned
    GRID_STRUCTURE = "grid_structure"  # Regular grid arrangement
    NONE = "none"


@dataclass
class Pattern:
    """Detected pattern with properties."""
    pattern_type: PatternType
    confidence: float  # 0.0 to 1.0
    properties: Dict
    evidence: List  # Supporting evidence

    def __repr__(self):
        props_str = ", ".join(f"{k}={v}" for k, v in self.properties.items())
        return f"Pattern({self.pattern_type.value}, conf={self.confidence:.2f}, {props_str})"


class PatternDetector:
    """Detects patterns in ARC grids and object collections."""

    def detect_repetition(
        self,
        objects: List[ARCObject],
        tolerance: float = 0.1,
    ) -> Optional[Pattern]:
        """Detect if objects repeat (same shape/size).

        Args:
            objects: List of objects to analyze
            tolerance: Tolerance for considering objects "same"

        Returns:
            Pattern if repetition detected, else None
        """
        if len(objects) < 2:
            return None

        # Group by mass (size)
        size_groups = {}
        for obj in objects:
            size_groups.setdefault(obj.mass, []).append(obj)

        # Find largest group
        largest_group = max(size_groups.values(), key=len)

        if len(largest_group) >= 2:
            # Check if shapes are similar
            reference = largest_group[0]
            ref_arr = reference.to_array()

            similar_count = 1  # Reference itself

            for obj in largest_group[1:]:
                obj_arr = obj.to_array()

                # Check if same shape
                if obj_arr.shape == ref_arr.shape:
                    # Compare normalized arrays
                    similarity = np.sum(obj_arr > 0) == np.sum(ref_arr > 0)
                    if similarity:
                        similar_count += 1

            confidence = similar_count / len(objects)

            if confidence >= 0.5:
                return Pattern(
                    pattern_type=PatternType.REPETITION,
                    confidence=confidence,
                    properties={
                        "repeated_shape": "same",
                        "count": similar_count,
                        "total_objects": len(objects),
                        "repetition_rate": confidence,
                    },
                    evidence=largest_group[:similar_count],
                )

        return None

    def detect_tiling(
        self,
        grid: ARCGrid,
        tile_sizes: Optional[List[Tuple[int, int]]] = None,
    ) -> Optional[Pattern]:
        """Detect if grid is composed of repeating tiles.

        Args:
            grid: Grid to analyze
            tile_sizes: Candidate tile sizes to check, or None to auto-detect

        Returns:
            Pattern if tiling detected
        """
        if tile_sizes is None:
            # Common tile sizes
            tile_sizes = [
                (2, 2), (3, 3), (4, 4),  # Squares
                (2, 3), (3, 2),          # Small rectangles
                (2, 4), (4, 2),          # Larger rectangles
            ]

        best_pattern = None
        best_confidence = 0.0

        for tile_h, tile_w in tile_sizes:
            if grid.height % tile_h != 0 or grid.width % tile_w != 0:
                continue  # Grid not evenly divisible

            # Extract all tiles
            tiles = []
            for r in range(0, grid.height, tile_h):
                for c in range(0, grid.width, tile_w):
                    tile = grid.extract_subgrid(r, c, tile_h, tile_w)
                    tiles.append(tile)

            if not tiles:
                continue

            # Check if all tiles are identical
            reference = tiles[0]
            identical_count = sum(1 for tile in tiles if reference.equals(tile))

            confidence = identical_count / len(tiles)

            if confidence > best_confidence:
                best_confidence = confidence
                best_pattern = Pattern(
                    pattern_type=PatternType.TILING,
                    confidence=confidence,
                    properties={
                        "tile_size": (tile_h, tile_w),
                        "tiles_count": len(tiles),
                        "identical_tiles": identical_count,
                    },
                    evidence=tiles,
                )

        if best_confidence >= 0.7:
            return best_pattern

        return None

    def detect_alignment(self, objects: List[ARCObject]) -> Optional[Pattern]:
        """Detect if objects are aligned in rows/columns.

        Args:
            objects: Objects to analyze

        Returns:
            Pattern if alignment detected
        """
        if len(objects) < 2:
            return None

        # Get centers
        centers = [obj.center for obj in objects]

        # Check horizontal alignment (same row)
        rows = [r for r, c in centers]
        row_groups = {}
        for i, r in enumerate(rows):
            # Group by similar row position (within 0.5 cell)
            found_group = False
            for group_r in row_groups:
                if abs(r - group_r) < 0.5:
                    row_groups[group_r].append(i)
                    found_group = True
                    break
            if not found_group:
                row_groups[r] = [i]

        largest_row = max(row_groups.values(), key=len) if row_groups else []

        # Check vertical alignment (same column)
        cols = [c for r, c in centers]
        col_groups = {}
        for i, c in enumerate(cols):
            found_group = False
            for group_c in col_groups:
                if abs(c - group_c) < 0.5:
                    col_groups[group_c].append(i)
                    found_group = True
                    break
            if not found_group:
                col_groups[c] = [i]

        largest_col = max(col_groups.values(), key=len) if col_groups else []

        # Determine best alignment
        if len(largest_row) >= 2 and len(largest_row) >= len(largest_col):
            confidence = len(largest_row) / len(objects)
            return Pattern(
                pattern_type=PatternType.ALIGNMENT,
                confidence=confidence,
                properties={
                    "direction": "horizontal",
                    "aligned_count": len(largest_row),
                    "total_objects": len(objects),
                },
                evidence=[objects[i] for i in largest_row],
            )

        if len(largest_col) >= 2:
            confidence = len(largest_col) / len(objects)
            return Pattern(
                pattern_type=PatternType.ALIGNMENT,
                confidence=confidence,
                properties={
                    "direction": "vertical",
                    "aligned_count": len(largest_col),
                    "total_objects": len(objects),
                },
                evidence=[objects[i] for i in largest_col],
            )

        return None

    def detect_grid_structure(
        self,
        objects: List[ARCObject],
        tolerance: float = 1.0,
    ) -> Optional[Pattern]:
        """Detect if objects form a regular grid.

        Args:
            objects: Objects to analyze
            tolerance: Position tolerance for grid alignment

        Returns:
            Pattern if grid structure detected
        """
        if len(objects) < 4:
            return None

        # Get centers
        centers = [(obj.center[0], obj.center[1]) for obj in objects]

        # Sort by row, then column
        sorted_centers = sorted(centers, key=lambda p: (p[0], p[1]))

        # Try to infer grid dimensions
        # Group by row
        rows = {}
        for r, c in sorted_centers:
            found = False
            for row_r in rows:
                if abs(r - row_r) < tolerance:
                    rows[row_r].append(c)
                    found = True
                    break
            if not found:
                rows[r] = [c]

        # Check if rows have consistent counts
        row_counts = [len(cols) for cols in rows.values()]
        if not row_counts:
            return None

        most_common_count = max(set(row_counts), key=row_counts.count)

        # Check if enough rows match
        matching_rows = sum(1 for count in row_counts if count == most_common_count)
        confidence = matching_rows / len(rows)

        if confidence >= 0.7:
            return Pattern(
                pattern_type=PatternType.GRID_STRUCTURE,
                confidence=confidence,
                properties={
                    "rows": len(rows),
                    "cols": most_common_count,
                    "regular": confidence > 0.9,
                },
                evidence=objects,
            )

        return None

    def detect_alternation(
        self,
        grid: ARCGrid,
        direction: str = "both",
    ) -> Optional[Pattern]:
        """Detect alternating patterns (checkerboard, stripes).

        Args:
            grid: Grid to analyze
            direction: "horizontal", "vertical", or "both"

        Returns:
            Pattern if alternation detected
        """
        # Checkerboard pattern
        if direction in ("both", "checkerboard"):
            checker_result = self._check_checkerboard(grid)
            if checker_result:
                return checker_result

        # Horizontal stripes
        if direction in ("both", "horizontal"):
            h_stripes = self._check_horizontal_stripes(grid)
            if h_stripes:
                return h_stripes

        # Vertical stripes
        if direction in ("both", "vertical"):
            v_stripes = self._check_vertical_stripes(grid)
            if v_stripes:
                return v_stripes

        return None

    def _check_checkerboard(self, grid: ARCGrid) -> Optional[Pattern]:
        """Check for checkerboard pattern."""
        # Sample positions
        even_positions = []
        odd_positions = []

        for r in range(grid.height):
            for c in range(grid.width):
                if (r + c) % 2 == 0:
                    even_positions.append(grid.get(r, c))
                else:
                    odd_positions.append(grid.get(r, c))

        # Check if alternating
        even_unique = set(even_positions)
        odd_unique = set(odd_positions)

        # Perfect checkerboard: one color on even, another on odd
        if len(even_unique) == 1 and len(odd_unique) == 1 and even_unique != odd_unique:
            return Pattern(
                pattern_type=PatternType.ALTERNATION,
                confidence=1.0,
                properties={
                    "subtype": "checkerboard",
                    "even_color": list(even_unique)[0],
                    "odd_color": list(odd_unique)[0],
                },
                evidence=[],
            )

        return None

    def _check_horizontal_stripes(self, grid: ARCGrid) -> Optional[Pattern]:
        """Check for horizontal stripe pattern."""
        # Check if rows alternate
        row_colors = [grid.get_background_color() for _ in range(grid.height)]

        for r in range(grid.height):
            # Get most common color in row
            row_data = grid.data[r, :]
            unique, counts = np.unique(row_data, return_counts=True)
            row_colors[r] = int(unique[np.argmax(counts)])

        # Check for alternation
        if len(set(row_colors)) == 2:
            alternates = all(
                row_colors[i] != row_colors[i + 1]
                for i in range(len(row_colors) - 1)
            )

            if alternates:
                return Pattern(
                    pattern_type=PatternType.ALTERNATION,
                    confidence=1.0,
                    properties={
                        "subtype": "horizontal_stripes",
                        "colors": list(set(row_colors)),
                    },
                    evidence=[],
                )

        return None

    def _check_vertical_stripes(self, grid: ARCGrid) -> Optional[Pattern]:
        """Check for vertical stripe pattern."""
        # Check if columns alternate
        col_colors = [0] * grid.width

        for c in range(grid.width):
            # Get most common color in column
            col_data = grid.data[:, c]
            unique, counts = np.unique(col_data, return_counts=True)
            col_colors[c] = int(unique[np.argmax(counts)])

        # Check for alternation
        if len(set(col_colors)) == 2:
            alternates = all(
                col_colors[i] != col_colors[i + 1]
                for i in range(len(col_colors) - 1)
            )

            if alternates:
                return Pattern(
                    pattern_type=PatternType.ALTERNATION,
                    confidence=1.0,
                    properties={
                        "subtype": "vertical_stripes",
                        "colors": list(set(col_colors)),
                    },
                    evidence=[],
                )

        return None

    def analyze_all_patterns(
        self,
        grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
    ) -> List[Pattern]:
        """Detect all patterns in grid and objects.

        Args:
            grid: Grid to analyze
            objects: Objects (auto-detect if None)

        Returns:
            List of detected patterns
        """
        if objects is None:
            from supe.reasoning.arc.detector import ObjectDetector
            detector = ObjectDetector()
            objects = detector.detect_objects(grid)

        patterns = []

        # Object patterns
        if objects:
            rep = self.detect_repetition(objects)
            if rep:
                patterns.append(rep)

            align = self.detect_alignment(objects)
            if align:
                patterns.append(align)

            grid_struct = self.detect_grid_structure(objects)
            if grid_struct:
                patterns.append(grid_struct)

        # Grid patterns
        tiling = self.detect_tiling(grid)
        if tiling:
            patterns.append(tiling)

        alternation = self.detect_alternation(grid)
        if alternation:
            patterns.append(alternation)

        return patterns
