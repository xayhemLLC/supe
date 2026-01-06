"""Tile-based operations for ARC tasks.

Operations that work on tiled grids and modify specific tiles.
"""

from typing import Optional, List, Dict, Any
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
)


class ModifyTileRegionTransformation(Transformation):
    """Modify pixels in specific tile regions (rows/columns of tiles)."""

    def __init__(self):
        super().__init__("modify_tile_region", TransformationType.STRUCTURAL)

    def apply(
        self,
        input_grid: ARCGrid,
        objects: Optional[List[ARCObject]] = None,
        tile_height: int = 3,
        tile_width: int = 3,
        region_type: str = "tile_column",
        region_index: int = 0,
        modification: str = "zero_nonzero",
        original_grid: Optional[ARCGrid] = None,
        **kwargs
    ) -> TransformationResult:
        """Modify pixels in a tile region.

        Args:
            input_grid: Input grid (assumed to be tiled)
            tile_height: Height of each tile
            tile_width: Width of each tile
            region_type: Type of region ("tile_column", "tile_row")
            region_index: Which region (0 = first column/row of tiles)
            modification: Type of modification ("zero_nonzero", "set_all_zero", "conditional_zero")
            original_grid: Original grid before tiling (for conditional modifications)
        """
        try:
            output_data = input_grid.data.copy()

            if region_type == "all_tiles" and modification == "conditional_zero" and original_grid is not None:
                # Zero out ALL tiles conditionally based on original grid
                # For each tile position (i,j), check if original pixel was 0
                num_tile_rows = input_grid.height // tile_height
                num_tile_cols = input_grid.width // tile_width

                for tile_row in range(num_tile_rows):
                    for tile_col in range(num_tile_cols):
                        # Check original pixel at (tile_row, tile_col)
                        if tile_row < original_grid.height and tile_col < original_grid.width:
                            original_pixel = original_grid.data[tile_row, tile_col]

                            if original_pixel == 0:
                                # Zero out this tile
                                row_start = tile_row * tile_height
                                row_end = row_start + tile_height
                                col_start = tile_col * tile_width
                                col_end = col_start + tile_width

                                for i in range(row_start, row_end):
                                    for j in range(col_start, col_end):
                                        if i < input_grid.height and j < input_grid.width:
                                            output_data[i, j] = 0

            elif region_type == "tile_column":
                # Modify a column of tiles
                # For tile_width=3, region_index=0 means columns 0-2
                col_start = region_index * tile_width
                col_end = col_start + tile_width

                if modification == "zero_nonzero":
                    # Replace all non-zero pixels with 0
                    for i in range(input_grid.height):
                        for j in range(col_start, col_end):
                            if j < input_grid.width and output_data[i, j] != 0:
                                output_data[i, j] = 0
                elif modification == "set_all_zero":
                    # Set all pixels to 0
                    for i in range(input_grid.height):
                        for j in range(col_start, col_end):
                            if j < input_grid.width:
                                output_data[i, j] = 0
                elif modification == "conditional_zero" and original_grid is not None:
                    # Zero out tiles conditionally based on original grid
                    # For each tile in the column, check if the corresponding pixel in original was 0
                    num_tile_rows = input_grid.height // tile_height
                    for tile_row in range(num_tile_rows):
                        # Check original pixel at (tile_row, region_index)
                        if tile_row < original_grid.height and region_index < original_grid.width:
                            original_pixel = original_grid.data[tile_row, region_index]

                            if original_pixel == 0:
                                # Zero out this tile
                                row_start = tile_row * tile_height
                                row_end = row_start + tile_height
                                for i in range(row_start, row_end):
                                    for j in range(col_start, col_end):
                                        if i < input_grid.height and j < input_grid.width:
                                            output_data[i, j] = 0

            elif region_type == "tile_row":
                # Modify a row of tiles
                row_start = region_index * tile_height
                row_end = row_start + tile_height

                if modification == "zero_nonzero":
                    # Replace all non-zero pixels with 0
                    for i in range(row_start, row_end):
                        for j in range(input_grid.width):
                            if i < input_grid.height and output_data[i, j] != 0:
                                output_data[i, j] = 0
                elif modification == "set_all_zero":
                    # Set all pixels to 0
                    for i in range(row_start, row_end):
                        for j in range(input_grid.width):
                            if i < input_grid.height:
                                output_data[i, j] = 0

            output_grid = ARCGrid(data=output_data, task_id=input_grid.task_id)

            return TransformationResult(
                success=True,
                output_grid=output_grid,
                parameters_used={
                    'tile_height': tile_height,
                    'tile_width': tile_width,
                    'region_type': region_type,
                    'region_index': region_index,
                    'modification': modification
                },
                explanation=f"Modified {region_type} {region_index} with {modification}",
            )

        except Exception as e:
            return TransformationResult(
                success=False,
                explanation=f"Tile region modification failed: {str(e)}"
            )

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "tile_height": {
                "type": "integer",
                "default": 3,
                "description": "Height of each tile"
            },
            "tile_width": {
                "type": "integer",
                "default": 3,
                "description": "Width of each tile"
            },
            "region_type": {
                "type": "string",
                "enum": ["all_tiles", "tile_column", "tile_row"],
                "default": "tile_column",
                "description": "Type of region to modify"
            },
            "region_index": {
                "type": "integer",
                "default": 0,
                "description": "Which region (0-indexed)"
            },
            "modification": {
                "type": "string",
                "enum": ["zero_nonzero", "set_all_zero", "conditional_zero"],
                "default": "zero_nonzero",
                "description": "Type of modification"
            },
            "original_grid": {
                "type": "grid",
                "default": None,
                "description": "Original grid before tiling (for conditional modifications)"
            }
        }
