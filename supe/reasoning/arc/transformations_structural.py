"""Structural transformations for ARC tasks.

Includes duplication, extension, fill operations, and pattern completion.
"""

from typing import Optional, List, Dict, Any
import numpy as np
from collections import deque

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class DuplicateTransformation(Transformation):
    """Duplicate grid in specified direction."""

    def __init__(self):
        super().__init__("duplicate", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        direction: str = "horizontal",
        count: int = 2,
        **kwargs
    ) -> TransformationResult:
        """Duplicate grid."""
        try:
            if count < 1:
                return TransformationResult(
                    success=False,
                    explanation="Count must be >= 1"
                )

            if direction == "horizontal":
                # Stack horizontally
                new_data = np.tile(input_grid.data, (1, count))
            elif direction == "vertical":
                # Stack vertically
                new_data = np.tile(input_grid.data, (count, 1))
            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid direction: {direction}"
                )

            output = ARCGrid(data=new_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"direction": direction, "count": count},
                explanation=f"Duplicated {count}x {direction}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Duplicate failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "direction": {
                "type": "direction",
                "values": ["horizontal", "vertical"],
                "default": "horizontal"
            },
            "count": {
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 2,
                "description": "Number of copies"
            }
        }


class CropAndDuplicateTransformation(Transformation):
    """Crop to bounding box then duplicate horizontally."""

    def __init__(self):
        super().__init__("crop_and_duplicate", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        direction: str = "horizontal",
        count: int = 2,
        **kwargs
    ) -> TransformationResult:
        """Crop to bounding box of non-zero pixels, then duplicate."""
        try:
            data = input_grid.data

            # Find bounding box of non-zero pixels
            non_zero = np.argwhere(data != 0)
            if len(non_zero) == 0:
                return TransformationResult(
                    success=False,
                    explanation="No non-zero pixels to crop"
                )

            min_r, min_c = non_zero.min(axis=0)
            max_r, max_c = non_zero.max(axis=0)

            # Crop to bounding box
            cropped = data[min_r:max_r+1, min_c:max_c+1]

            # Duplicate
            if direction == "horizontal":
                new_data = np.tile(cropped, (1, count))
            elif direction == "vertical":
                new_data = np.tile(cropped, (count, 1))
            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid direction: {direction}"
                )

            output = ARCGrid(data=new_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={
                    "direction": direction,
                    "count": count,
                    "crop_bounds": (min_r, min_c, max_r, max_c)
                },
                explanation=f"Cropped to bbox and duplicated {count}x {direction}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Crop and duplicate failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "direction": {
                "type": "direction",
                "values": ["horizontal", "vertical"],
                "default": "horizontal"
            },
            "count": {
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 2,
                "description": "Number of copies"
            }
        }


class FloodFillTransformation(Transformation):
    """Flood fill from a position."""

    def __init__(self):
        super().__init__("flood_fill", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        start_row: int = 0,
        start_col: int = 0,
        fill_color: int = 1,
        **kwargs
    ) -> TransformationResult:
        """Flood fill from starting position."""
        try:
            output_data = input_grid.data.copy()

            start_color = input_grid.get(start_row, start_col)
            if start_color == fill_color:
                # Already filled
                return TransformationResult(
                    success=True,
                    output_grid=input_grid.copy(),
                    parameters_used={},
                    explanation="Already filled"
                )

            # BFS flood fill
            queue = deque([(start_row, start_col)])
            visited = set()

            while queue:
                r, c = queue.popleft()

                if (r, c) in visited:
                    continue

                if r < 0 or r >= input_grid.height or c < 0 or c >= input_grid.width:
                    continue

                if input_grid.get(r, c) != start_color:
                    continue

                visited.add((r, c))
                output_data[r, c] = fill_color

                # Add neighbors
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    queue.append((r + dr, c + dc))

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={
                    "start_row": start_row,
                    "start_col": start_col,
                    "fill_color": fill_color
                },
                explanation=f"Flood filled from ({start_row}, {start_col})",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Flood fill failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "start_row": {"type": "int", "min": 0},
            "start_col": {"type": "int", "min": 0},
            "fill_color": {"type": "color"}
        }


class ExtendPatternTransformation(Transformation):
    """Extend pattern to fill grid."""

    def __init__(self):
        super().__init__("extend_pattern", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        target_height: Optional[int] = None,
        target_width: Optional[int] = None,
        **kwargs
    ) -> TransformationResult:
        """Extend pattern by tiling."""
        try:
            if target_height is None:
                target_height = input_grid.height
            if target_width is None:
                target_width = input_grid.width

            # Calculate how many times to tile
            v_reps = (target_height + input_grid.height - 1) // input_grid.height
            h_reps = (target_width + input_grid.width - 1) // input_grid.width

            # Tile
            tiled = np.tile(input_grid.data, (v_reps, h_reps))

            # Crop to target size
            output_data = tiled[:target_height, :target_width]

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={
                    "target_height": target_height,
                    "target_width": target_width
                },
                explanation=f"Extended pattern to {target_height}x{target_width}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Extend pattern failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "target_height": {"type": "int", "min": 1, "default": None},
            "target_width": {"type": "int", "min": 1, "default": None}
        }


class HollowOutTransformation(Transformation):
    """Remove interior of objects, keeping only borders."""

    def __init__(self):
        super().__init__("hollow_out", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        background: int = 0,
        **kwargs
    ) -> TransformationResult:
        """Hollow out objects."""
        try:
            if objects is None:
                from supe.reasoning.arc.detector import ObjectDetector
                detector = ObjectDetector()
                objects = detector.detect_objects(input_grid, background_color=background)

            output_data = np.full_like(input_grid.data, background)

            for obj in objects:
                min_r, min_c, max_r, max_c = obj.bounding_box

                # Add border pixels only
                for r, c in obj.pixels:
                    # Check if on border
                    is_border = (
                        r == min_r or r == max_r or
                        c == min_c or c == max_c
                    )

                    # Or check if adjacent to background
                    if not is_border:
                        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if (nr, nc) not in obj.pixels:
                                is_border = True
                                break

                    if is_border:
                        output_data[r, c] = obj.color

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"background": background},
                explanation="Hollowed out objects (borders only)",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Hollow out failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "background": {
                "type": "color",
                "default": 0,
                "description": "Background color"
            }
        }


class FillInteriorTransformation(Transformation):
    """Fill interior of hollow objects."""

    def __init__(self):
        super().__init__("fill_interior", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        fill_color: Optional[int] = None,
        **kwargs
    ) -> TransformationResult:
        """Fill interior of objects."""
        try:
            if objects is None:
                from supe.reasoning.arc.detector import ObjectDetector
                detector = ObjectDetector()
                objects = detector.detect_objects(input_grid)

            output_data = input_grid.data.copy()

            for obj in objects:
                min_r, min_c, max_r, max_c = obj.bounding_box

                # Determine fill color
                color = fill_color if fill_color is not None else obj.color

                # Fill bounding box
                for r in range(min_r, max_r + 1):
                    for c in range(min_c, max_c + 1):
                        output_data[r, c] = color

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"fill_color": fill_color},
                explanation="Filled object interiors",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Fill interior failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "fill_color": {
                "type": "color",
                "default": None,
                "description": "Fill color (use object color if None)"
            }
        }


class AddBorderTransformation(Transformation):
    """Add border around grid or objects."""

    def __init__(self):
        super().__init__("add_border", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        thickness: int = 1,
        color: int = 1,
        **kwargs
    ) -> TransformationResult:
        """Add border around grid."""
        try:
            # Create larger grid
            new_height = input_grid.height + 2 * thickness
            new_width = input_grid.width + 2 * thickness

            output_data = np.full((new_height, new_width), color, dtype=int)

            # Copy original grid to center
            output_data[
                thickness:thickness + input_grid.height,
                thickness:thickness + input_grid.width
            ] = input_grid.data

            output = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output,
                parameters_used={"thickness": thickness, "color": color},
                explanation=f"Added {thickness}-pixel border (color {color})",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Add border failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "thickness": {
                "type": "int",
                "min": 1,
                "max": 5,
                "default": 1,
                "description": "Border thickness in pixels"
            },
            "color": {
                "type": "color",
                "default": 1,
                "description": "Border color"
            }
        }


class TileTransformation(Transformation):
    """Tile grid in NxM pattern (repeat grid in both dimensions)."""

    def __init__(self):
        super().__init__("tile", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        n_rows: int = 3,
        n_cols: int = 3,
        **kwargs
    ) -> TransformationResult:
        """Tile grid in n_rows × n_cols arrangement.

        Args:
            input_grid: Grid to tile
            objects: Not used (operates on entire grid)
            n_rows: Number of times to repeat vertically
            n_cols: Number of times to repeat horizontally

        Returns:
            TransformationResult with tiled grid

        Example:
            Input (3x3):        Output with n_rows=3, n_cols=3 (9x9):
            [A B C]            [A B C][A B C][A B C]
            [D E F]     →      [D E F][D E F][D E F]
            [G H I]            [G H I][G H I][G H I]

                               [A B C][A B C][A B C]
                               [D E F][D E F][D E F]
                               [G H I][G H I][G H I]

                               [A B C][A B C][A B C]
                               [D E F][D E F][D E F]
                               [G H I][G H I][G H I]
        """
        try:
            if n_rows < 1 or n_cols < 1:
                return TransformationResult(
                    success=False,
                    explanation="n_rows and n_cols must be >= 1"
                )

            # Use numpy.tile to repeat in both dimensions
            # tile((n_rows, n_cols)) repeats the array n_rows times vertically
            # and n_cols times horizontally
            new_data = np.tile(input_grid.data, (n_rows, n_cols))

            output_grid = ARCGrid(new_data)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                explanation=f"Tiled {n_rows}×{n_cols} ({input_grid.height}x{input_grid.width} → {output_grid.height}x{output_grid.width})",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Tile failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "n_rows": {
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 3,
                "description": "Number of vertical repetitions"
            },
            "n_cols": {
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 3,
                "description": "Number of horizontal repetitions"
            }
        }


class ExtractByMarker(Transformation):
    """Extract columns/rows based on marker position."""

    def __init__(self):
        super().__init__("extract_by_marker", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        marker_color: int = 5,
        mode: str = "before",
        axis: str = "vertical",
        **kwargs
    ) -> TransformationResult:
        """Extract grid sections based on marker position.

        Args:
            input_grid: Grid to extract from
            objects: Not used
            marker_color: Color that marks the extraction point
            mode: "before" (extract before marker),
                  "after" (extract after marker),
                  "around" (extract both sides, excluding marker)
            axis: "vertical" (marker is a column) or
                  "horizontal" (marker is a row)

        Returns:
            TransformationResult with extracted section

        Example (vertical, before):
            Input (3x7):          Marker at col 3:    Output (3x3):
            [1 0 0 | 5 | 0 1 0]   [1 0 0 | 5 | ...]   [1 0 0]
            [0 1 0 | 5 | 1 1 1]   [0 1 0 | 5 | ...]   [0 1 0]
            [1 0 0 | 5 | 0 0 0]   [1 0 0 | 5 | ...]   [1 0 0]
        """
        try:
            if axis == "vertical":
                # Find marker column (all cells in column = marker_color)
                marker_pos = None
                for col in range(input_grid.width):
                    if all(input_grid.data[row, col] == marker_color
                           for row in range(input_grid.height)):
                        marker_pos = col
                        break

                if marker_pos is None:
                    return TransformationResult(
                        success=False,
                        explanation=f"No marker column found (color {marker_color})"
                    )

                # Extract based on mode
                if mode == "before":
                    if marker_pos == 0:
                        return TransformationResult(
                            success=False,
                            explanation="Marker at leftmost position, nothing before"
                        )
                    new_data = input_grid.data[:, :marker_pos]
                    explanation = f"Extracted columns [0:{marker_pos}] (before marker at {marker_pos})"

                elif mode == "after":
                    if marker_pos == input_grid.width - 1:
                        return TransformationResult(
                            success=False,
                            explanation="Marker at rightmost position, nothing after"
                        )
                    new_data = input_grid.data[:, marker_pos+1:]
                    explanation = f"Extracted columns [{marker_pos+1}:] (after marker at {marker_pos})"

                elif mode == "around":
                    # Extract both before and after, concatenate
                    if marker_pos == 0 or marker_pos == input_grid.width - 1:
                        return TransformationResult(
                            success=False,
                            explanation="Marker at edge, cannot extract around"
                        )
                    before = input_grid.data[:, :marker_pos]
                    after = input_grid.data[:, marker_pos+1:]
                    new_data = np.hstack([before, after])
                    explanation = f"Extracted around marker at {marker_pos} (columns [0:{marker_pos}] + [{marker_pos+1}:])"

                else:
                    return TransformationResult(
                        success=False,
                        explanation=f"Invalid mode: {mode}"
                    )

            elif axis == "horizontal":
                # Find marker row (all cells in row = marker_color)
                marker_pos = None
                for row in range(input_grid.height):
                    if all(input_grid.data[row, col] == marker_color
                           for col in range(input_grid.width)):
                        marker_pos = row
                        break

                if marker_pos is None:
                    return TransformationResult(
                        success=False,
                        explanation=f"No marker row found (color {marker_color})"
                    )

                # Extract based on mode
                if mode == "before":
                    if marker_pos == 0:
                        return TransformationResult(
                            success=False,
                            explanation="Marker at topmost position, nothing before"
                        )
                    new_data = input_grid.data[:marker_pos, :]
                    explanation = f"Extracted rows [0:{marker_pos}] (before marker at {marker_pos})"

                elif mode == "after":
                    if marker_pos == input_grid.height - 1:
                        return TransformationResult(
                            success=False,
                            explanation="Marker at bottommost position, nothing after"
                        )
                    new_data = input_grid.data[marker_pos+1:, :]
                    explanation = f"Extracted rows [{marker_pos+1}:] (after marker at {marker_pos})"

                elif mode == "around":
                    # Extract both before and after, concatenate
                    if marker_pos == 0 or marker_pos == input_grid.height - 1:
                        return TransformationResult(
                            success=False,
                            explanation="Marker at edge, cannot extract around"
                        )
                    before = input_grid.data[:marker_pos, :]
                    after = input_grid.data[marker_pos+1:, :]
                    new_data = np.vstack([before, after])
                    explanation = f"Extracted around marker at {marker_pos} (rows [0:{marker_pos}] + [{marker_pos+1}:])"

                else:
                    return TransformationResult(
                        success=False,
                        explanation=f"Invalid mode: {mode}"
                    )

            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid axis: {axis}"
                )

            output_grid = ARCGrid(new_data)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                explanation=explanation,
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Extract by marker failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "marker_color": {
                "type": "color",
                "min": 0,
                "max": 9,
                "default": 5,
                "description": "Marker color to search for"
            },
            "mode": {
                "type": "enum",
                "values": ["before", "after", "around"],
                "default": "before",
                "description": "Which side(s) to extract"
            },
            "axis": {
                "type": "enum",
                "values": ["vertical", "horizontal"],
                "default": "vertical",
                "description": "Marker orientation (column or row)"
            }
        }


class CompareGrids(Transformation):
    """Compare two grids element-wise with various comparison operations.

    This is a binary transformation that takes two grids and produces
    a comparison result grid. Essential for compositional reasoning.
    """

    def __init__(self):
        super().__init__("compare_grids", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        second_grid: Optional[ARCGrid] = None,
        operation: str = "equal",
        true_value: int = 1,
        false_value: int = 0,
        ignore_color: Optional[int] = None,
        **kwargs
    ) -> TransformationResult:
        """Compare two grids element-wise.

        Args:
            input_grid: First grid to compare
            second_grid: Second grid to compare against (required)
            operation: Comparison operation
                - "equal" (==): True where values are equal
                - "not_equal" (!=): True where values differ
                - "greater" (>): True where first > second
                - "less" (<): True where first < second
                - "greater_equal" (>=): True where first >= second
                - "less_equal" (<=): True where first <= second
            true_value: Value to use where comparison is True (default: 1)
            false_value: Value to use where comparison is False (default: 0)
            ignore_color: Optional color to ignore in comparison (treated as always matching)

        Returns:
            Grid with true_value where comparison is True, false_value elsewhere

        Example:
            # Compare two 3x3 grids
            result = compare.apply(grid1, second_grid=grid2, operation="equal")
            # Result has 1 where grid1[i,j] == grid2[i,j], 0 elsewhere
        """
        try:
            # Validate second_grid is provided
            if second_grid is None:
                return TransformationResult(
                    success=False,
                    explanation="second_grid parameter is required for comparison"
                )

            # Validate grids have same shape
            if input_grid.shape != second_grid.shape:
                return TransformationResult(
                    success=False,
                    explanation=f"Grid shapes don't match: {input_grid.shape} vs {second_grid.shape}"
                )

            # Perform comparison based on operation
            if operation == "equal":
                comparison = (input_grid.data == second_grid.data)
                op_symbol = "=="
            elif operation == "not_equal":
                comparison = (input_grid.data != second_grid.data)
                op_symbol = "!="
            elif operation == "greater":
                comparison = (input_grid.data > second_grid.data)
                op_symbol = ">"
            elif operation == "less":
                comparison = (input_grid.data < second_grid.data)
                op_symbol = "<"
            elif operation == "greater_equal":
                comparison = (input_grid.data >= second_grid.data)
                op_symbol = ">="
            elif operation == "less_equal":
                comparison = (input_grid.data <= second_grid.data)
                op_symbol = "<="
            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid operation: {operation}. Valid: equal, not_equal, greater, less, greater_equal, less_equal"
                )

            # Handle ignore_color if specified
            if ignore_color is not None:
                # Where either grid has ignore_color, treat as matching
                ignore_mask = (input_grid.data == ignore_color) | (second_grid.data == ignore_color)
                if operation == "equal":
                    # Ignore positions always match
                    comparison = comparison | ignore_mask
                elif operation == "not_equal":
                    # Ignore positions never differ
                    comparison = comparison & ~ignore_mask

            # Create output grid with true/false values
            output_data = np.where(comparison, true_value, false_value)
            output_grid = ARCGrid(output_data)

            # Count matches for explanation
            match_count = np.sum(comparison)
            total = input_grid.height * input_grid.width
            match_pct = (match_count / total) * 100

            explanation = f"Compared grids ({op_symbol}): {match_count}/{total} cells True ({match_pct:.1f}%)"
            if ignore_color is not None:
                explanation += f", ignoring color {ignore_color}"

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                explanation=explanation,
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Grid comparison failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "second_grid": {
                "type": "grid",
                "required": True,
                "description": "Second grid to compare against"
            },
            "operation": {
                "type": "enum",
                "values": ["equal", "not_equal", "greater", "less", "greater_equal", "less_equal"],
                "default": "equal",
                "description": "Comparison operation"
            },
            "true_value": {
                "type": "color",
                "min": 0,
                "max": 9,
                "default": 1,
                "description": "Value where comparison is True"
            },
            "false_value": {
                "type": "color",
                "min": 0,
                "max": 9,
                "default": 0,
                "description": "Value where comparison is False"
            },
            "ignore_color": {
                "type": "color",
                "min": 0,
                "max": 9,
                "optional": True,
                "description": "Color to ignore in comparison"
            }
        }


class ConditionalColor(Transformation):
    """Apply colors conditionally based on a condition grid.

    This transformation enables if-then-else coloring logic, essential for
    compositional reasoning. Can use values from a source grid or apply
    constant colors based on conditions.
    """

    def __init__(self):
        super().__init__("conditional_color", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        condition_grid: Optional[ARCGrid] = None,
        source_grid: Optional[ARCGrid] = None,
        condition: str = "non_zero",
        true_value: Optional[int] = None,
        false_value: int = 0,
        use_source: bool = False,
        **kwargs
    ) -> TransformationResult:
        """Apply colors based on conditions.

        Args:
            input_grid: Input grid (used as source if source_grid not provided)
            condition_grid: Grid with condition values (required)
            source_grid: Optional grid to pull values from when condition is True
            condition: Type of condition to evaluate:
                - "non_zero": True where condition_grid != 0
                - "zero": True where condition_grid == 0
                - "equals": True where condition_grid == true_value
                - "and_non_zero": True where (condition_grid != 0) AND (source != 0)
            true_value: Value to use when condition is True (if not using source)
            false_value: Value to use when condition is False (default: 0)
            use_source: If True, use source_grid values when condition is True

        Returns:
            Grid with conditional coloring applied

        Examples:
            # Simple: Use value 2 where condition_grid is non-zero
            result = conditional.apply(
                grid,
                condition_grid=mask,
                condition="non_zero",
                true_value=2,
                false_value=0
            )

            # Task 0520fde7: Use value 2 where comparison==1 AND before!=0
            result = conditional.apply(
                before_grid,
                condition_grid=comparison,
                condition="and_non_zero",
                true_value=2,
                false_value=0
            )

            # Advanced: Copy from source where condition is True
            result = conditional.apply(
                grid,
                condition_grid=mask,
                source_grid=values,
                use_source=True,
                false_value=0
            )
        """
        try:
            # Validate condition_grid is provided
            if condition_grid is None:
                return TransformationResult(
                    success=False,
                    explanation="condition_grid parameter is required"
                )

            # Validate shapes match
            if condition_grid.shape != input_grid.shape:
                return TransformationResult(
                    success=False,
                    explanation=f"Shape mismatch: condition_grid {condition_grid.shape} vs input {input_grid.shape}"
                )

            if source_grid is not None and source_grid.shape != input_grid.shape:
                return TransformationResult(
                    success=False,
                    explanation=f"Shape mismatch: source_grid {source_grid.shape} vs input {input_grid.shape}"
                )

            # Use input_grid as source if source_grid not provided
            if source_grid is None:
                source_grid = input_grid

            # Evaluate condition
            if condition == "non_zero":
                # True where condition_grid is non-zero
                condition_mask = (condition_grid.data != 0)
                cond_desc = "non-zero"

            elif condition == "zero":
                # True where condition_grid is zero
                condition_mask = (condition_grid.data == 0)
                cond_desc = "zero"

            elif condition == "equals":
                # True where condition_grid equals true_value
                if true_value is None:
                    return TransformationResult(
                        success=False,
                        explanation="true_value required for 'equals' condition"
                    )
                condition_mask = (condition_grid.data == true_value)
                cond_desc = f"equals {true_value}"

            elif condition == "and_non_zero":
                # True where (condition_grid != 0) AND (source_grid != 0)
                # This is the pattern for task 0520fde7
                condition_mask = (condition_grid.data != 0) & (source_grid.data != 0)
                cond_desc = "condition non-zero AND source non-zero"

            elif condition == "or_non_zero":
                # True where (condition_grid != 0) OR (source_grid != 0)
                condition_mask = (condition_grid.data != 0) | (source_grid.data != 0)
                cond_desc = "condition non-zero OR source non-zero"

            else:
                return TransformationResult(
                    success=False,
                    explanation=f"Invalid condition: {condition}. Valid: non_zero, zero, equals, and_non_zero, or_non_zero"
                )

            # Apply conditional coloring
            if use_source:
                # Use values from source_grid where condition is True
                output_data = np.where(condition_mask, source_grid.data, false_value)
                value_desc = "source values"
            else:
                # Use constant true_value where condition is True
                if true_value is None:
                    return TransformationResult(
                        success=False,
                        explanation="true_value required when not using source"
                    )
                output_data = np.where(condition_mask, true_value, false_value)
                value_desc = f"value {true_value}"

            output_grid = ARCGrid(output_data)

            # Count conditional applications
            true_count = np.sum(condition_mask)
            total = input_grid.height * input_grid.width
            true_pct = (true_count / total) * 100

            explanation = f"Applied {value_desc} where {cond_desc}: {true_count}/{total} cells ({true_pct:.1f}%)"

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                explanation=explanation,
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Conditional color failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "condition_grid": {
                "type": "grid",
                "required": True,
                "description": "Grid with condition values"
            },
            "source_grid": {
                "type": "grid",
                "optional": True,
                "description": "Grid to pull values from (defaults to input_grid)"
            },
            "condition": {
                "type": "enum",
                "values": ["non_zero", "zero", "equals", "and_non_zero", "or_non_zero"],
                "default": "non_zero",
                "description": "Type of condition to evaluate"
            },
            "true_value": {
                "type": "color",
                "min": 0,
                "max": 9,
                "optional": True,
                "description": "Value when condition is True (required if not use_source)"
            },
            "false_value": {
                "type": "color",
                "min": 0,
                "max": 9,
                "default": 0,
                "description": "Value when condition is False"
            },
            "use_source": {
                "type": "boolean",
                "default": False,
                "description": "Use source_grid values when True"
            }
        }
