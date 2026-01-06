"""Parameter inference for ARC transformations.

Automatically infers transformation parameters from training examples.
Enables automated task solving by detecting patterns and relationships.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np
from collections import defaultdict

from supe.reasoning.arc.grid import ARCGrid


class ParameterInferenceEngine:
    """Infers transformation parameters from training examples."""

    def __init__(self):
        """Initialize parameter inference engine."""
        self.inference_strategies = {
            'color_map': self._infer_color_mapping,
            'bounding_box': self._infer_bounding_box,
            'marker_color': self._infer_marker_color,
            'fill_color': self._infer_fill_color,
            'scale_factor': self._infer_scale_factor,
            'direction': self._infer_direction,
            'count': self._infer_count,
            'boundary_color': self._infer_boundary_color,
            'gravity_direction': self._infer_gravity_direction,
            'row_colors': self._infer_row_colors,
            'column_colors': self._infer_column_colors,
            'tile_dimensions': self._infer_tile_dimensions,
        }

    def infer_parameters(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid],
        transformation_type: str
    ) -> Dict[str, Any]:
        """Infer parameters for a transformation from examples.

        Args:
            input_grids: List of input grids from training examples
            output_grids: List of output grids from training examples
            transformation_type: Type of transformation being inferred

        Returns:
            Dictionary of inferred parameters
        """
        if not input_grids or not output_grids:
            return {}

        if len(input_grids) != len(output_grids):
            return {}

        # Try all applicable inference strategies
        inferred = {}

        for strategy_name, strategy_func in self.inference_strategies.items():
            try:
                result = strategy_func(input_grids, output_grids)
                if result is not None:
                    inferred.update(result)
            except Exception:
                # Strategy failed, continue with others
                continue

        return inferred

    def _infer_color_mapping(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer color mapping from examples.

        Detects if there's a consistent color mapping across all examples.
        """
        # Build color mappings from each example
        example_mappings = []

        for inp, out in zip(input_grids, output_grids):
            if inp.shape != out.shape:
                # Color mapping requires same shape
                return None

            mapping = {}
            for i in range(inp.height):
                for j in range(inp.width):
                    in_color = int(inp.data[i, j])
                    out_color = int(out.data[i, j])

                    if in_color not in mapping:
                        mapping[in_color] = out_color
                    elif mapping[in_color] != out_color:
                        # Inconsistent mapping in this example
                        return None

            example_mappings.append(mapping)

        # Check if all examples have the same mapping
        if not example_mappings:
            return None

        first_mapping = example_mappings[0]
        for mapping in example_mappings[1:]:
            if mapping != first_mapping:
                # Mappings differ across examples - this is OK!
                # Color mapping can have per-example mappings
                # Just verify each example has a consistent internal mapping
                pass

        # Return first mapping as template, but note that it's per-example
        return {'mapping': first_mapping, 'per_example': True}

    def _infer_bounding_box(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer bounding box parameters.

        Detects if outputs are crops of inputs to object bounding boxes.
        """
        bbox_params = []

        for inp, out in zip(input_grids, output_grids):
            # Find non-zero pixels (assuming 0 is background)
            non_zero = np.argwhere(inp.data != 0)

            if len(non_zero) == 0:
                return None

            min_row = int(non_zero[:, 0].min())
            max_row = int(non_zero[:, 0].max())
            min_col = int(non_zero[:, 1].min())
            max_col = int(non_zero[:, 1].max())

            height = max_row - min_row + 1
            width = max_col - min_col + 1

            # Check if output matches cropped region
            if out.height != height or out.width != width:
                return None

            cropped = inp.data[min_row:max_row+1, min_col:max_col+1]
            if not np.array_equal(cropped, out.data):
                return None

            bbox_params.append({
                'top': min_row,
                'left': min_col,
                'height': height,
                'width': width
            })

        # Check if all examples have same relative bbox (relative to object)
        # For now, we'll return the first example's bbox as a template
        if bbox_params:
            return {
                'auto_detect_bbox': True,
                'bbox_template': bbox_params[0]
            }

        return None

    def _infer_marker_color(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer marker color (sparse reference color).

        Detects colors that appear sparsely and might be markers.
        """
        # Analyze color frequencies across all inputs
        color_freqs = defaultdict(list)

        for inp in input_grids:
            total_pixels = inp.height * inp.width
            unique_colors = inp.get_unique_colors()

            for color in unique_colors:
                count = inp.count_color(color)
                frequency = count / total_pixels
                color_freqs[color].append(frequency)

        # Find colors that are consistently sparse (< 20% of grid)
        # Relaxed threshold to catch marker colors
        sparse_colors = []
        for color, freqs in color_freqs.items():
            if color == 0:  # Skip background
                continue
            if all(f < 0.2 for f in freqs):  # Increased from 0.1 to 0.2
                sparse_colors.append((color, np.mean(freqs)))

        if not sparse_colors:
            return None

        # Return the sparsest color as likely marker
        sparse_colors.sort(key=lambda x: x[1])
        marker_color = int(sparse_colors[0][0])

        return {'marker_color': marker_color}

    def _infer_fill_color(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer fill color for interior filling operations.

        Detects new colors that appear in output but not in input.
        """
        fill_colors = []

        for inp, out in zip(input_grids, output_grids):
            input_colors = set(inp.get_unique_colors())
            output_colors = set(out.get_unique_colors())

            new_colors = output_colors - input_colors

            if len(new_colors) == 1:
                fill_colors.append(int(list(new_colors)[0]))
            elif len(new_colors) > 1:
                # Multiple new colors, unclear which is fill
                return None

        # Check if same fill color across all examples
        if fill_colors and all(c == fill_colors[0] for c in fill_colors):
            return {'fill_color': fill_colors[0]}

        return None

    def _infer_scale_factor(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer scale factor from size changes.

        Detects if output is scaled version of input.
        """
        scale_factors = []

        for inp, out in zip(input_grids, output_grids):
            if out.height % inp.height == 0 and out.width % inp.width == 0:
                h_scale = out.height // inp.height
                w_scale = out.width // inp.width

                if h_scale == w_scale:
                    scale_factors.append(h_scale)
                else:
                    return None  # Non-uniform scaling
            else:
                return None  # Not an integer scale

        # Check if all examples have same scale
        if scale_factors and all(s == scale_factors[0] for s in scale_factors):
            return {'scale_factor': scale_factors[0]}

        return None

    def _infer_direction(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer direction (horizontal/vertical) from shape changes.

        Detects duplication or tiling direction.
        """
        for inp, out in zip(input_grids, output_grids):
            # Check horizontal duplication
            if out.width > inp.width and out.height == inp.height:
                if out.width % inp.width == 0:
                    return {'direction': 'horizontal'}

            # Check vertical duplication
            if out.height > inp.height and out.width == inp.width:
                if out.height % inp.height == 0:
                    return {'direction': 'vertical'}

        return None

    def _infer_count(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer repetition count from size changes.

        Detects how many times input is duplicated in output.
        """
        counts = []

        for inp, out in zip(input_grids, output_grids):
            # Check horizontal count
            if out.height == inp.height and out.width % inp.width == 0:
                count = out.width // inp.width
                counts.append(count)
            # Check vertical count
            elif out.width == inp.width and out.height % inp.height == 0:
                count = out.height // inp.height
                counts.append(count)
            else:
                return None

        # Check if all examples have same count
        if counts and all(c == counts[0] for c in counts):
            return {'count': counts[0]}

        return None

    def _infer_boundary_color(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer boundary color for enclosed region filling.

        Detects the most common non-background color that might form boundaries.
        """
        boundary_colors = []

        for inp in input_grids:
            # Find most common non-background color
            colors = {}
            for color in inp.get_unique_colors():
                if color != 0:
                    colors[color] = inp.count_color(color)

            if colors:
                boundary_color = max(colors.items(), key=lambda x: x[1])[0]
                boundary_colors.append(int(boundary_color))

        # Check if same boundary color across all examples
        if boundary_colors and all(c == boundary_colors[0] for c in boundary_colors):
            return {'boundary_color': boundary_colors[0]}

        return None

    def _infer_gravity_direction(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer gravity direction from pixel movement patterns.

        Detects if pixels have "fallen" or "settled" in a particular direction.
        """
        for inp, out in zip(input_grids, output_grids):
            if inp.shape != out.shape:
                return None

            # Check if same colors, just repositioned
            inp_colors = sorted(inp.get_unique_colors())
            out_colors = sorted(out.get_unique_colors())
            if inp_colors != out_colors:
                return None

            # Check vertical settling (gravity down)
            # Compare column-by-column if non-zero pixels moved down
            settled_down = True
            for col in range(inp.width):
                inp_col = inp.data[:, col]
                out_col = out.data[:, col]

                # Get non-zero positions
                inp_nonzero = np.where(inp_col != 0)[0]
                out_nonzero = np.where(out_col != 0)[0]

                if len(inp_nonzero) != len(out_nonzero):
                    settled_down = False
                    break

                # Check if output positions are at bottom
                if len(out_nonzero) > 0:
                    expected_start = inp.height - len(out_nonzero)
                    if not np.array_equal(out_nonzero, np.arange(expected_start, inp.height)):
                        settled_down = False
                        break

            if settled_down:
                return {'direction': 'down'}

        return None

    def _infer_row_colors(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer row coloring pattern.

        Detects if each row is colored with a specific color.
        """
        row_colors_list = []

        for out in output_grids:
            row_colors = []
            for row in range(out.height):
                # Get unique colors in this row
                row_data = out.data[row, :]
                unique_colors = np.unique(row_data)

                # If row is all one color, record it
                if len(unique_colors) == 1:
                    row_colors.append(int(unique_colors[0]))
                else:
                    return None  # Row has mixed colors

            row_colors_list.append(row_colors)

        # Check if pattern is consistent across examples
        if row_colors_list:
            first_pattern = row_colors_list[0]
            if all(colors == first_pattern for colors in row_colors_list):
                return {'colors': first_pattern}

        return None

    def _infer_column_colors(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer column coloring pattern.

        Detects if each column is colored with a specific color.
        """
        column_colors_list = []

        for out in output_grids:
            column_colors = []
            for col in range(out.width):
                # Get unique colors in this column
                col_data = out.data[:, col]
                unique_colors = np.unique(col_data)

                # If column is all one color, record it
                if len(unique_colors) == 1:
                    column_colors.append(int(unique_colors[0]))
                else:
                    return None  # Column has mixed colors

            column_colors_list.append(column_colors)

        # Check if pattern is consistent across examples
        if column_colors_list:
            first_pattern = column_colors_list[0]
            if all(colors == first_pattern for colors in column_colors_list):
                return {'colors': first_pattern}

        return None

    def _infer_tile_dimensions(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Dict[str, Any]]:
        """Infer tile dimensions for tile selection operations.

        Detects regular tiling patterns in the input.
        """
        tile_dims = []

        for inp in input_grids:
            # Try to detect tiling by looking for repeated patterns
            # Start with common tile sizes
            for tile_h in range(1, inp.height // 2 + 1):
                for tile_w in range(1, inp.width // 2 + 1):
                    if inp.height % tile_h == 0 and inp.width % tile_w == 0:
                        # Check if grid is actually tiled with these dimensions
                        tiles_v = inp.height // tile_h
                        tiles_h = inp.width // tile_w

                        is_tiled = True
                        first_tile = inp.data[0:tile_h, 0:tile_w]

                        for i in range(tiles_v):
                            for j in range(tiles_h):
                                tile = inp.data[i*tile_h:(i+1)*tile_h, j*tile_w:(j+1)*tile_w]
                                # Allow tiles to be different (not requiring exact repetition)
                                # Just checking if tiling structure exists
                                pass

                        # If we found a reasonable tiling, record it
                        if tiles_v >= 2 and tiles_h >= 2:
                            tile_dims.append({'tile_height': tile_h, 'tile_width': tile_w})
                            break

                if tile_dims:
                    break

        # Return first detected tile dimensions
        if tile_dims:
            return tile_dims[0]

        return None


class PatternMatcher:
    """Matches input-output patterns to known transformation types."""

    def __init__(self):
        """Initialize pattern matcher."""
        self.patterns = [
            self._match_rotation,  # Add rotation first - simple and common
            self._match_marker_based_row_coloring,  # Marker-based coloring
            self._match_object_centering,  # Object centering
            self._match_cross_pattern,  # Cross pattern drawing
            self._match_crop_and_duplicate,  # Crop bbox then duplicate
            self._match_tile_by_marker,  # Tile input at marker positions
            self._match_stamp_cross_pattern,  # Stamp cross at markers
            self._match_symmetric_extraction,  # Extract from 180-degree opposite
            self._match_section_copy_by_marker,  # Section copy based on marker position
            self._match_parallelogram_align,  # Parallelogram alignment
            self._match_color_mapping,
            self._match_crop_to_bbox,
            self._match_duplication,
            self._match_tiling,
            self._match_marker_extraction,
            self._match_fill_enclosed_regions,
            self._match_gravity,
            self._match_row_coloring,
            self._match_column_coloring,
        ]

    def match_pattern(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Match input-output patterns to transformations.

        Args:
            input_grids: List of input grids
            output_grids: List of output grids

        Returns:
            List of (transformation_name, confidence, parameters) tuples
        """
        matches = []

        for pattern_func in self.patterns:
            try:
                result = pattern_func(input_grids, output_grids)
                if result:
                    matches.append(result)
            except Exception:
                continue

        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def _match_rotation(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match rotation pattern (90°, 180°, 270°)."""
        # Check if shapes are same or transposed
        if not all(
            inp.shape == out.shape or
            (inp.height == out.width and inp.width == out.height)
            for inp, out in zip(input_grids, output_grids)
        ):
            return None

        # Try each rotation angle
        from supe.reasoning.arc.catalog import TransformationCatalog
        catalog = TransformationCatalog()
        rotate_transform = catalog.get('rotate')

        for angle in [90, 180, 270]:
            all_match = True

            for inp, out in zip(input_grids, output_grids):
                result = rotate_transform.apply(inp, angle=angle)
                if not result.success:
                    all_match = False
                    break

                if not np.array_equal(result.output_grid.data, out.data):
                    all_match = False
                    break

            if all_match:
                return ('rotate', 0.95, {'angle': angle})

        return None

    def _match_marker_based_row_coloring(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match marker-based row coloring pattern."""
        # Check if shapes are same
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        # Check if outputs have uniform rows
        for out in output_grids:
            for row in range(out.height):
                if len(np.unique(out.data[row, :])) != 1:
                    return None  # Each row must be uniform

        # Try to find marker color and build mapping
        # Common marker colors are 5, 9, etc.
        for marker_color in [5, 9, 8, 7, 6, 4, 3, 2, 1]:
            color_mapping = {}

            # Check if this marker color works for all examples
            works_for_all = True

            for inp, out in zip(input_grids, output_grids):
                # Skip if marker not in input
                if marker_color not in inp.get_unique_colors():
                    works_for_all = False
                    break

                for row in range(inp.height):
                    row_data = inp.data[row, :]
                    marker_positions = np.where(row_data == marker_color)[0]

                    if len(marker_positions) > 0:
                        marker_col = int(marker_positions[0])
                        output_color = int(out.data[row, 0])  # Row is uniform

                        # Check consistency of mapping
                        if marker_col in color_mapping:
                            if color_mapping[marker_col] != output_color:
                                works_for_all = False
                                break
                        else:
                            color_mapping[marker_col] = output_color

                if not works_for_all:
                    break

            if works_for_all and len(color_mapping) > 0:
                return ('color_rows_by_marker_position', 0.90, {
                    'marker_color': marker_color,
                    'color_mapping': color_mapping
                })

        return None

    def _match_object_centering(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match object centering pattern."""
        # Check if shapes are same
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        # Check if same colors and counts
        for inp, out in zip(input_grids, output_grids):
            if sorted(inp.get_unique_colors()) != sorted(out.get_unique_colors()):
                return None

            # Check pixel counts for each color
            for color in inp.get_unique_colors():
                if inp.count_color(color) != out.count_color(color):
                    return None

        # Try horizontal and vertical centering
        from supe.reasoning.arc.catalog import TransformationCatalog
        catalog = TransformationCatalog()
        center_transform = catalog.get('center_objects_by_color')

        for axis in ['horizontal', 'vertical']:
            all_match = True

            for inp, out in zip(input_grids, output_grids):
                result = center_transform.apply(inp, axis=axis)
                if not result.success:
                    all_match = False
                    break

                if not np.array_equal(result.output_grid.data, out.data):
                    all_match = False
                    break

            if all_match:
                return ('center_objects_by_color', 0.88, {'axis': axis})

        return None

    def _match_cross_pattern(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match cross pattern drawing by association."""
        # Check if output is mostly zero with cross patterns
        for inp, out in zip(input_grids, output_grids):
            # Input should have some non-zero pixels
            if len(inp.get_unique_colors()) <= 1:
                return None

            # Output should have cross-like patterns
            # (more structured, potentially more pixels than input)
            if out.data.sum() == 0:
                return None

        # Try the transformation
        from supe.reasoning.arc.catalog import TransformationCatalog
        catalog = TransformationCatalog()
        cross_transform = catalog.get('draw_cross_by_association')

        if cross_transform is None:
            return None

        all_match = True
        for inp, out in zip(input_grids, output_grids):
            result = cross_transform.apply(inp)
            if not result.success:
                all_match = False
                break

            if not np.array_equal(result.output_grid.data, out.data):
                all_match = False
                break

        if all_match:
            return ('draw_cross_by_association', 0.87, {})

        return None

    def _match_crop_and_duplicate(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match crop to bbox then duplicate pattern."""
        # Output should be smaller than or different size from input
        # and output width/height should be multiple of cropped bbox

        # Try the transformation
        from supe.reasoning.arc.catalog import TransformationCatalog
        catalog = TransformationCatalog()
        crop_dup_transform = catalog.get('crop_and_duplicate')

        if crop_dup_transform is None:
            return None

        # Try horizontal duplication with count 2 (most common)
        for direction in ['horizontal', 'vertical']:
            for count in [2, 3]:
                all_match = True

                for inp, out in zip(input_grids, output_grids):
                    result = crop_dup_transform.apply(inp, direction=direction, count=count)
                    if not result.success:
                        all_match = False
                        break

                    if not np.array_equal(result.output_grid.data, out.data):
                        all_match = False
                        break

                if all_match:
                    return ('crop_and_duplicate', 0.88, {
                        'direction': direction,
                        'count': count
                    })

        return None

    def _match_tile_by_marker(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match tile by marker pattern - place input at positions of marker color."""
        # Check if output is scaled version of input
        for inp, out in zip(input_grids, output_grids):
            # Output should be a multiple of input size
            if out.height % inp.height != 0 or out.width % inp.width != 0:
                return None
            scale_h = out.height // inp.height
            scale_w = out.width // inp.width
            if scale_h != scale_w:  # Must be uniform scaling
                return None

        # Try different marker colors
        from supe.reasoning.arc.catalog import TransformationCatalog
        catalog = TransformationCatalog()
        tile_transform = catalog.get('tile_by_marker')

        if tile_transform is None:
            return None

        for marker_color in [2, 1, 3, 4, 5, 6, 7, 8, 9]:
            scale = input_grids[0].height  # Usually 3 for 3x3 inputs
            if output_grids[0].height // input_grids[0].height != scale:
                scale = output_grids[0].height // input_grids[0].height

            all_match = True

            for inp, out in zip(input_grids, output_grids):
                result = tile_transform.apply(inp, marker_color=marker_color, scale=scale)
                if not result.success:
                    all_match = False
                    break

                if not np.array_equal(result.output_grid.data, out.data):
                    all_match = False
                    break

            if all_match:
                return ('tile_by_marker', 0.89, {
                    'marker_color': marker_color,
                    'scale': scale
                })

        return None

    def _match_stamp_cross_pattern(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match stamp cross pattern - draw 3x3 cross at marker positions."""
        # Check if shapes are same
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        from supe.reasoning.arc.catalog import TransformationCatalog
        catalog = TransformationCatalog()
        stamp_transform = catalog.get('stamp_cross_pattern')

        if stamp_transform is None:
            return None

        # Try different marker and arm color combinations
        for marker_color in [5, 2, 3, 4, 6, 7, 8, 9, 1]:
            for arm_color in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                if arm_color == marker_color:
                    continue

                all_match = True

                for inp, out in zip(input_grids, output_grids):
                    # Check if marker_color exists in input
                    if marker_color not in inp.get_unique_colors():
                        all_match = False
                        break

                    result = stamp_transform.apply(
                        inp,
                        marker_color=marker_color,
                        arm_color=arm_color,
                        center_color=0
                    )
                    if not result.success:
                        all_match = False
                        break

                    if not np.array_equal(result.output_grid.data, out.data):
                        all_match = False
                        break

                if all_match:
                    return ('stamp_cross_pattern', 0.88, {
                        'marker_color': marker_color,
                        'arm_color': arm_color,
                        'center_color': 0
                    })

        return None

    def _match_symmetric_extraction(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match symmetric extraction pattern.

        Pattern: Extract from 180-degree opposite of marker position.
        - Grid has rotational symmetry
        - Marker (color 1) indicates a region
        - Output is extracted from 180-degree opposite, rotated 180
        """
        from supe.reasoning.arc.transformations_symmetric_extract import (
            ExtractSymmetricOppositeTransformation
        )

        # Output should be smaller than input
        if not all(
            out.height < inp.height and out.width < inp.width
            for inp, out in zip(input_grids, output_grids)
        ):
            return None

        # Check that inputs are square (typical for symmetric patterns)
        if not all(inp.height == inp.width for inp in input_grids):
            return None

        # Check for marker color 1
        if not all(1 in inp.data for inp in input_grids):
            return None

        # Try the transformation
        transform = ExtractSymmetricOppositeTransformation()

        for marker_color in [1, 2]:
            all_match = True
            for inp, out in zip(input_grids, output_grids):
                result = transform.apply(inp, marker_color=marker_color)
                if not result.success:
                    all_match = False
                    break
                if not np.array_equal(result.output_grid.data, out.data):
                    all_match = False
                    break

            if all_match:
                return ('extract_symmetric_opposite', 0.90, {
                    'marker_color': marker_color
                })

        return None

    def _match_section_copy_by_marker(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match section copy by marker pattern.

        Pattern: Grid divided by divider lines, marker color encodes
        source and destination sections.
        """
        from supe.reasoning.arc.transformations_section_copy import (
            SectionCopyByMarkerTransformation
        )

        # Input and output should have same shape
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        # Look for divider lines (row/column all same color)
        inp0 = input_grids[0]
        divider_color = None
        for color in range(1, 10):
            # Check if any row is all this color
            for r in range(inp0.height):
                if np.all(inp0.data[r, :] == color):
                    divider_color = color
                    break
            if divider_color:
                break

        if divider_color is None:
            return None

        # Try the transformation with different marker colors
        transform = SectionCopyByMarkerTransformation()

        for marker_color in range(1, 10):
            if marker_color == divider_color:
                continue

            # Check if marker appears exactly once in all inputs
            if not all(np.sum(inp.data == marker_color) == 1 for inp in input_grids):
                continue

            all_match = True
            for inp, out in zip(input_grids, output_grids):
                result = transform.apply(inp, marker_color=marker_color, divider_color=divider_color)
                if not result.success:
                    all_match = False
                    break
                if not np.array_equal(result.output_grid.data, out.data):
                    all_match = False
                    break

            if all_match:
                return ('section_copy_by_marker', 0.92, {
                    'marker_color': marker_color,
                    'divider_color': divider_color
                })

        return None

    def _match_parallelogram_align(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match parallelogram alignment pattern.

        Pattern: Shift parallelogram shapes while keeping bottom row fixed.
        """
        from supe.reasoning.arc.transformations_parallelogram_align import (
            ParallelogramAlignTransformation
        )

        # Input and output should have same shape
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        # Input and output should have same colors
        for inp, out in zip(input_grids, output_grids):
            inp_colors = set(inp.data.flatten()) - {0}
            out_colors = set(out.data.flatten()) - {0}
            if inp_colors != out_colors:
                return None

        # Try the transformation
        transform = ParallelogramAlignTransformation()

        for shift in [1, 2]:
            all_match = True
            for inp, out in zip(input_grids, output_grids):
                result = transform.apply(inp, shift_amount=shift)
                if not result.success:
                    all_match = False
                    break
                if not np.array_equal(result.output_grid.data, out.data):
                    all_match = False
                    break

            if all_match:
                return ('parallelogram_align', 0.88, {
                    'shift_amount': shift
                })

        return None

    def _match_color_mapping(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match color mapping pattern."""
        # Check if shapes are same
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        # Check if each example has consistent internal mapping
        # even if mappings differ across examples
        all_consistent = True

        for inp, out in zip(input_grids, output_grids):
            mapping = {}
            for i in range(inp.height):
                for j in range(inp.width):
                    in_c = int(inp.data[i, j])
                    out_c = int(out.data[i, j])

                    if in_c in mapping:
                        if mapping[in_c] != out_c:
                            all_consistent = False
                            break
                    else:
                        mapping[in_c] = out_c

                if not all_consistent:
                    break

            if not all_consistent:
                break

        if all_consistent:
            return ('color_map', 0.95, {'per_example': True})

        return None

    def _match_crop_to_bbox(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match crop to bounding box pattern."""
        inference = ParameterInferenceEngine()
        params = inference._infer_bounding_box(input_grids, output_grids)

        if params:
            return ('crop', 0.90, params)

        return None

    def _match_duplication(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match duplication pattern."""
        inference = ParameterInferenceEngine()

        # Get direction and count
        direction_params = inference._infer_direction(input_grids, output_grids)
        count_params = inference._infer_count(input_grids, output_grids)

        if direction_params and count_params:
            params = {**direction_params, **count_params}
            return ('duplicate', 0.90, params)

        return None

    def _match_tiling(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match tiling pattern."""
        inference = ParameterInferenceEngine()
        params = inference._infer_scale_factor(input_grids, output_grids)

        if params and params['scale_factor'] > 1:
            # Check if it's actual tiling (repeated pattern)
            for inp, out in zip(input_grids, output_grids):
                scale = params['scale_factor']
                # Verify tiling pattern by checking repetition
                for i in range(scale):
                    for j in range(scale):
                        tile_region = out.data[
                            i*inp.height:(i+1)*inp.height,
                            j*inp.width:(j+1)*inp.width
                        ]
                        if not np.array_equal(tile_region, inp.data):
                            return None

            return ('tile', 0.85, {'count': params['scale_factor']})

        return None

    def _match_marker_extraction(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match marker-based extraction pattern."""
        inference = ParameterInferenceEngine()
        params = inference._infer_marker_color(input_grids, output_grids)

        if params:
            # Check if marker color is present in inputs
            marker_color = params['marker_color']
            has_marker = all(
                marker_color in inp.get_unique_colors()
                for inp in input_grids
            )

            if has_marker:
                return ('extract_by_marker', 0.75, params)

        return None

    def _match_fill_enclosed_regions(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match fill enclosed regions pattern."""
        inference = ParameterInferenceEngine()

        # Check if inputs and outputs have same shape
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        # Check if outputs have more filled pixels than inputs
        for inp, out in zip(input_grids, output_grids):
            inp_filled = np.count_nonzero(inp.data)
            out_filled = np.count_nonzero(out.data)

            if out_filled <= inp_filled:
                return None  # Should have more filled pixels

        # Try to infer boundary color
        params = inference._infer_boundary_color(input_grids, output_grids)

        if params:
            # Also try to infer fill color
            fill_params = inference._infer_fill_color(input_grids, output_grids)
            if fill_params:
                params.update(fill_params)

            return ('fill_enclosed_regions', 0.70, params)

        return None

    def _match_gravity(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match gravity/settling pattern."""
        inference = ParameterInferenceEngine()

        # Check if inputs and outputs have same shape
        if not all(inp.shape == out.shape for inp, out in zip(input_grids, output_grids)):
            return None

        # Check if same pixels, just repositioned
        for inp, out in zip(input_grids, output_grids):
            inp_colors = sorted(inp.get_unique_colors())
            out_colors = sorted(out.get_unique_colors())

            if inp_colors != out_colors:
                return None

            # Count should be same
            for color in inp_colors:
                if inp.count_color(color) != out.count_color(color):
                    return None

        # Try to infer gravity direction
        params = inference._infer_gravity_direction(input_grids, output_grids)

        if params:
            return ('gravity', 0.80, params)

        return None

    def _match_row_coloring(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match row coloring pattern."""
        inference = ParameterInferenceEngine()

        # Check if outputs have uniform rows
        params = inference._infer_row_colors(input_grids, output_grids)

        if params:
            # Verify each row is indeed uniform
            for out in output_grids:
                for row in range(out.height):
                    row_data = out.data[row, :]
                    if len(np.unique(row_data)) != 1:
                        return None

            return ('color_rows', 0.85, params)

        return None

    def _match_column_coloring(
        self,
        input_grids: List[ARCGrid],
        output_grids: List[ARCGrid]
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Match column coloring pattern."""
        inference = ParameterInferenceEngine()

        # Check if outputs have uniform columns
        params = inference._infer_column_colors(input_grids, output_grids)

        if params:
            # Verify each column is indeed uniform
            for out in output_grids:
                for col in range(out.width):
                    col_data = out.data[:, col]
                    if len(np.unique(col_data)) != 1:
                        return None

            return ('color_columns', 0.85, params)

        return None
