"""Section copy transformations for ARC tasks.

Copy section based on marker position encoding.
"""

from typing import Optional, List, Dict, Any, Tuple
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class SectionCopyByMarkerTransformation(Transformation):
    """Copy section based on marker position encoding.

    Pattern:
    - Grid divided into 3x3 sections by divider color
    - Marker color appears exactly once and marks source section
    - Local position of marker within section encodes destination section
    - Copy source section to destination, clear everything else
    """

    def __init__(self):
        super().__init__("section_copy_by_marker", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        marker_color: int = 4,
        divider_color: int = 5,
        **kwargs
    ) -> TransformationResult:
        """Copy section based on marker position.

        Args:
            input_grid: Input grid with dividers and marker
            marker_color: Color that marks source section (default: 4)
            divider_color: Color of divider lines (default: 5)
        """
        try:
            data = input_grid.data
            h, w = data.shape

            # Create output with just dividers
            out = np.zeros_like(data)

            # Find divider rows and columns
            divider_rows = [r for r in range(h) if np.all(data[r, :] == divider_color)]
            divider_cols = [c for c in range(w) if np.all(data[:, c] == divider_color)]

            # Copy divider lines
            for r in divider_rows:
                out[r, :] = divider_color
            for c in divider_cols:
                out[:, c] = divider_color

            # Find where marker color is
            marker_pos = np.argwhere(data == marker_color)
            if len(marker_pos) == 0:
                return TransformationResult(
                    success=False,
                    explanation=f"Marker color {marker_color} not found"
                )

            r_marker, c_marker = marker_pos[0]

            # Determine section structure
            # Section rows: 0 to first_divider, first_divider+1 to second_divider, etc.
            section_row_starts = [0] + [r + 1 for r in divider_rows]
            section_col_starts = [0] + [c + 1 for c in divider_cols]

            # Find which section contains marker
            source_row_idx = 0
            for i, start in enumerate(section_row_starts):
                if i < len(section_row_starts) - 1:
                    if start <= r_marker < section_row_starts[i + 1] - 1:
                        source_row_idx = i
                        break
                else:
                    source_row_idx = i

            source_col_idx = 0
            for i, start in enumerate(section_col_starts):
                if i < len(section_col_starts) - 1:
                    if start <= c_marker < section_col_starts[i + 1] - 1:
                        source_col_idx = i
                        break
                else:
                    source_col_idx = i

            # Calculate section size (assuming uniform)
            if len(divider_rows) >= 1:
                section_height = divider_rows[0]
            else:
                section_height = h

            if len(divider_cols) >= 1:
                section_width = divider_cols[0]
            else:
                section_width = w

            # Source section boundaries
            source_start_r = section_row_starts[source_row_idx]
            source_start_c = section_col_starts[source_col_idx]

            # Local position of marker within section
            local_r = r_marker - source_start_r
            local_c = c_marker - source_start_c

            # Destination section is determined by local position
            dest_row_idx = local_r
            dest_col_idx = local_c

            # Ensure valid destination
            if dest_row_idx >= len(section_row_starts) or dest_col_idx >= len(section_col_starts):
                return TransformationResult(
                    success=False,
                    explanation="Destination section out of range"
                )

            # Destination section boundaries
            dest_start_r = section_row_starts[dest_row_idx]
            dest_start_c = section_col_starts[dest_col_idx]

            # Copy source section to destination
            source_section = data[
                source_start_r:source_start_r+section_height,
                source_start_c:source_start_c+section_width
            ]
            out[
                dest_start_r:dest_start_r+section_height,
                dest_start_c:dest_start_c+section_width
            ] = source_section

            output_grid = ARCGrid(data=out, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'marker_color': marker_color,
                    'divider_color': divider_color,
                    'source_section': (source_row_idx, source_col_idx),
                    'dest_section': (dest_row_idx, dest_col_idx),
                },
                explanation=f"Copied section ({source_row_idx},{source_col_idx}) to ({dest_row_idx},{dest_col_idx}) based on marker position",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Section copy failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "marker_color": {
                "type": "int",
                "min": 1,
                "max": 9,
                "default": 4,
                "description": "Color that marks source section"
            },
            "divider_color": {
                "type": "int",
                "min": 1,
                "max": 9,
                "default": 5,
                "description": "Color of divider lines"
            }
        }

    def fit_parameters(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]]
    ) -> Optional[Dict[str, Any]]:
        """Try to fit parameters from examples."""
        if not examples:
            return None

        inp, out = examples[0]

        # Check for divider lines
        divider_color = None
        for color in range(1, 10):
            # Check if any row is all this color
            for r in range(inp.height):
                if np.all(inp.data[r, :] == color):
                    divider_color = color
                    break
            if divider_color:
                break

        if divider_color is None:
            return None

        # Check for marker color (appears exactly once)
        for marker_color in range(1, 10):
            if marker_color == divider_color:
                continue
            if np.sum(inp.data == marker_color) == 1:
                # Try this combination
                result = self.apply(inp, marker_color=marker_color, divider_color=divider_color)
                if result.success and result.output_grid:
                    if np.array_equal(result.output_grid.data, out.data):
                        # Verify on all examples
                        all_match = True
                        for inp2, out2 in examples:
                            result2 = self.apply(inp2, marker_color=marker_color, divider_color=divider_color)
                            if not result2.success or not np.array_equal(result2.output_grid.data, out2.data):
                                all_match = False
                                break
                        if all_match:
                            return {'marker_color': marker_color, 'divider_color': divider_color}

        return None

    def verify(
        self,
        input_grid: ARCGrid,
        output_grid: ARCGrid,
        **params
    ) -> bool:
        """Verify transformation produces expected output."""
        result = self.apply(input_grid, **params)
        if not result.success or result.output_grid is None:
            return False
        return np.array_equal(result.output_grid.data, output_grid.data)
