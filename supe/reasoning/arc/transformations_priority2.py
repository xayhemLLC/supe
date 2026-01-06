"""Priority 2 transformations for ARC tasks.

Includes FloodFill, Gravity, Row/Column operations, and more.
"""

from typing import Optional, List, Dict, Any, Tuple, Set
import numpy as np
from collections import deque

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class FillEnclosedRegionsTransformation(Transformation):
    """Fill enclosed regions while preserving boundaries.

    This is different from FillInterior - it preserves boundary pixels
    and only fills truly enclosed interior regions using ray casting.
    """

    def __init__(self):
        super().__init__("fill_enclosed_regions", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        fill_color: int = 4,
        boundary_color: Optional[int] = None,
        preserve_boundaries: bool = True,
        **kwargs
    ) -> TransformationResult:
        """Fill interior regions while preserving boundaries.

        Args:
            input_grid: Input grid
            fill_color: Color to fill interior regions
            boundary_color: Color of boundaries (auto-detect if None)
            preserve_boundaries: Keep boundary pixels unchanged
        """
        try:
            output_data = input_grid.data.copy()

            # Detect boundary color if not specified
            if boundary_color is None:
                # Find most common non-background color
                colors = {}
                for color in input_grid.get_unique_colors():
                    if color != 0:
                        colors[color] = input_grid.count_color(color)
                if colors:
                    boundary_color = max(colors.items(), key=lambda x: x[1])[0]
                else:
                    return TransformationResult(
                        success=False,
                        explanation="No boundary color found"
                    )

            # Find all boundary pixels
            boundary_pixels = set()
            for i in range(input_grid.height):
                for j in range(input_grid.width):
                    if input_grid.data[i, j] == boundary_color:
                        boundary_pixels.add((i, j))

            # Flood fill from edges to find all pixels reachable without crossing boundaries
            reachable_from_edge = set()
            queue = deque()

            # Add all edge pixels that are not boundaries to queue
            for i in range(input_grid.height):
                if (i, 0) not in boundary_pixels:
                    queue.append((i, 0))
                if (i, input_grid.width - 1) not in boundary_pixels:
                    queue.append((i, input_grid.width - 1))

            for j in range(input_grid.width):
                if (0, j) not in boundary_pixels:
                    queue.append((0, j))
                if (input_grid.height - 1, j) not in boundary_pixels:
                    queue.append((input_grid.height - 1, j))

            # BFS to find all reachable pixels
            while queue:
                r, c = queue.popleft()

                if (r, c) in reachable_from_edge:
                    continue
                if r < 0 or r >= input_grid.height or c < 0 or c >= input_grid.width:
                    continue
                if (r, c) in boundary_pixels:
                    continue

                reachable_from_edge.add((r, c))

                # Add neighbors
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    queue.append((r + dr, c + dc))

            # For each non-boundary, non-filled pixel, check if it's enclosed
            for i in range(input_grid.height):
                for j in range(input_grid.width):
                    if (i, j) in boundary_pixels:
                        continue  # Skip boundary pixels
                    if input_grid.data[i, j] != 0:
                        continue  # Skip already colored pixels

                    # Check if this pixel is enclosed (not reachable from edge)
                    if self._is_enclosed(i, j, boundary_pixels, input_grid.height, input_grid.width, reachable_from_edge):
                        output_data[i, j] = fill_color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'fill_color': fill_color,
                    'boundary_color': boundary_color,
                    'preserve_boundaries': preserve_boundaries
                },
                explanation=f"Filled enclosed regions with color {fill_color}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Flood fill failed: {str(e)}"
            )

    def _is_enclosed(
        self,
        row: int,
        col: int,
        boundaries: Set[Tuple[int, int]],
        height: int,
        width: int,
        reachable_from_edge: Optional[Set[Tuple[int, int]]] = None
    ) -> bool:
        """Check if a pixel is enclosed by boundaries.

        Uses flood fill from edges: if a pixel is reachable from the edge
        without crossing boundaries, it's NOT enclosed.
        """
        if reachable_from_edge is not None:
            # Use pre-computed reachable set
            return (row, col) not in reachable_from_edge

        # Fallback to simple ray casting
        has_boundary = [False, False, False, False]  # up, down, left, right

        # Up
        for r in range(row - 1, -1, -1):
            if (r, col) in boundaries:
                has_boundary[0] = True
                break

        # Down
        for r in range(row + 1, height):
            if (r, col) in boundaries:
                has_boundary[1] = True
                break

        # Left
        for c in range(col - 1, -1, -1):
            if (row, c) in boundaries:
                has_boundary[2] = True
                break

        # Right
        for c in range(col + 1, width):
            if (row, c) in boundaries:
                has_boundary[3] = True
                break

        return all(has_boundary)

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "fill_color": {
                "type": "color",
                "default": 4,
                "description": "Color to fill enclosed regions"
            },
            "boundary_color": {
                "type": "color",
                "default": None,
                "description": "Boundary color (auto-detect if None)"
            },
            "preserve_boundaries": {
                "type": "boolean",
                "default": True,
                "description": "Keep boundary pixels unchanged"
            }
        }


class GravityTransformation(Transformation):
    """Apply gravity to make objects fall/settle in a direction."""

    def __init__(self):
        super().__init__("gravity", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        direction: str = "down",
        by_column: bool = True,
        **kwargs
    ) -> TransformationResult:
        """Apply gravity to make objects settle.

        Args:
            input_grid: Input grid
            direction: Direction for gravity ("down", "up", "left", "right")
            by_column: Apply gravity independently per column (for down/up)
        """
        try:
            output_data = np.zeros_like(input_grid.data)

            if direction == "down":
                if by_column:
                    # Process each column independently
                    for col in range(input_grid.width):
                        # Collect non-zero values in this column
                        values = []
                        for row in range(input_grid.height):
                            if input_grid.data[row, col] != 0:
                                values.append(input_grid.data[row, col])

                        # Place them at the bottom
                        if values:
                            start_row = input_grid.height - len(values)
                            for i, value in enumerate(values):
                                output_data[start_row + i, col] = value

            elif direction == "up":
                if by_column:
                    # Process each column independently
                    for col in range(input_grid.width):
                        # Collect non-zero values in this column
                        values = []
                        for row in range(input_grid.height):
                            if input_grid.data[row, col] != 0:
                                values.append(input_grid.data[row, col])

                        # Place them at the top
                        for i, value in enumerate(values):
                            output_data[i, col] = value

            elif direction == "left":
                # Process each row independently
                for row in range(input_grid.height):
                    # Collect non-zero values in this row
                    values = []
                    for col in range(input_grid.width):
                        if input_grid.data[row, col] != 0:
                            values.append(input_grid.data[row, col])

                    # Place them at the left
                    for i, value in enumerate(values):
                        output_data[row, i] = value

            elif direction == "right":
                # Process each row independently
                for row in range(input_grid.height):
                    # Collect non-zero values in this row
                    values = []
                    for col in range(input_grid.width):
                        if input_grid.data[row, col] != 0:
                            values.append(input_grid.data[row, col])

                    # Place them at the right
                    if values:
                        start_col = input_grid.width - len(values)
                        for i, value in enumerate(values):
                            output_data[row, start_col + i] = value

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={'direction': direction, 'by_column': by_column},
                explanation=f"Applied gravity in {direction} direction",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Gravity failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "direction": {
                "type": "string",
                "enum": ["down", "up", "left", "right"],
                "default": "down",
                "description": "Direction to apply gravity"
            },
            "by_column": {
                "type": "boolean",
                "default": True,
                "description": "Apply gravity per column (for vertical directions)"
            }
        }


class ColorRowsTransformation(Transformation):
    """Color entire rows with specified colors."""

    def __init__(self):
        super().__init__("color_rows", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        colors: Optional[List[int]] = None,
        **kwargs
    ) -> TransformationResult:
        """Color entire rows with specified colors.

        Args:
            input_grid: Input grid
            colors: List of colors (one per row)
        """
        try:
            if colors is None:
                return TransformationResult(
                    success=False,
                    explanation="colors parameter required"
                )

            if len(colors) != input_grid.height:
                return TransformationResult(
                    success=False,
                    explanation=f"Need {input_grid.height} colors, got {len(colors)}"
                )

            output_data = np.zeros_like(input_grid.data)

            for row_idx, color in enumerate(colors):
                output_data[row_idx, :] = color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={'colors': colors},
                explanation=f"Colored {len(colors)} rows",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Color rows failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "colors": {
                "type": "list",
                "description": "List of colors (one per row)"
            }
        }


class ColorColumnsTransformation(Transformation):
    """Color entire columns with specified colors."""

    def __init__(self):
        super().__init__("color_columns", TransformationType.COLOR)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        colors: Optional[List[int]] = None,
        **kwargs
    ) -> TransformationResult:
        """Color entire columns with specified colors.

        Args:
            input_grid: Input grid
            colors: List of colors (one per column)
        """
        try:
            if colors is None:
                return TransformationResult(
                    success=False,
                    explanation="colors parameter required"
                )

            if len(colors) != input_grid.width:
                return TransformationResult(
                    success=False,
                    explanation=f"Need {input_grid.width} colors, got {len(colors)}"
                )

            output_data = np.zeros_like(input_grid.data)

            for col_idx, color in enumerate(colors):
                output_data[:, col_idx] = color

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={'colors': colors},
                explanation=f"Colored {len(colors)} columns",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Color columns failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "colors": {
                "type": "list",
                "description": "List of colors (one per column)"
            }
        }


class SelectTilesTransformation(Transformation):
    """Select specific tiles from a tiled grid."""

    def __init__(self):
        super().__init__("select_tiles", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        tile_height: Optional[int] = None,
        tile_width: Optional[int] = None,
        positions: Optional[List[str]] = None,
        **kwargs
    ) -> TransformationResult:
        """Select specific tiles from tiled grid.

        Args:
            input_grid: Input grid (assumed to be tiled)
            tile_height: Height of each tile
            tile_width: Width of each tile
            positions: List of positions ('top_left', 'left_column', etc.)
        """
        try:
            if tile_height is None or tile_width is None:
                return TransformationResult(
                    success=False,
                    explanation="tile_height and tile_width required"
                )

            if positions is None or not positions:
                return TransformationResult(
                    success=False,
                    explanation="positions parameter required"
                )

            # Calculate grid dimensions in tiles
            tiles_v = input_grid.height // tile_height
            tiles_h = input_grid.width // tile_width

            # Create mask for selected tiles
            selected = np.zeros((tiles_v, tiles_h), dtype=bool)

            for pos in positions:
                if pos == "left_column":
                    selected[:, 0] = True
                elif pos == "right_column":
                    selected[:, -1] = True
                elif pos == "top_row":
                    selected[0, :] = True
                elif pos == "bottom_row":
                    selected[-1, :] = True
                elif pos == "top_left":
                    selected[0, 0] = True
                elif pos == "top_right":
                    selected[0, -1] = True
                elif pos == "bottom_left":
                    selected[-1, 0] = True
                elif pos == "bottom_right":
                    selected[-1, -1] = True

            # Create output with only selected tiles
            output_data = np.zeros_like(input_grid.data)

            for tile_row in range(tiles_v):
                for tile_col in range(tiles_h):
                    if selected[tile_row, tile_col]:
                        # Copy this tile
                        r_start = tile_row * tile_height
                        r_end = r_start + tile_height
                        c_start = tile_col * tile_width
                        c_end = c_start + tile_width

                        output_data[r_start:r_end, c_start:c_end] = \
                            input_grid.data[r_start:r_end, c_start:c_end]

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'tile_height': tile_height,
                    'tile_width': tile_width,
                    'positions': positions
                },
                explanation=f"Selected tiles at positions: {positions}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Select tiles failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "tile_height": {
                "type": "integer",
                "description": "Height of each tile"
            },
            "tile_width": {
                "type": "integer",
                "description": "Width of each tile"
            },
            "positions": {
                "type": "list",
                "description": "Tile positions to select"
            }
        }
