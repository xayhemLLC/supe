"""Visualization tools for ARC grids and objects."""

from typing import List, Optional, Dict
from supe.reasoning.arc.grid import ARCGrid, ARCObject


# ARC color palette (0-9)
ARC_COLORS = {
    0: "\033[40m  \033[0m",  # Black (background)
    1: "\033[44m  \033[0m",  # Blue
    2: "\033[41m  \033[0m",  # Red
    3: "\033[42m  \033[0m",  # Green
    4: "\033[43m  \033[0m",  # Yellow
    5: "\033[47m  \033[0m",  # Gray/White
    6: "\033[45m  \033[0m",  # Magenta
    7: "\033[46m  \033[0m",  # Cyan
    8: "\033[100m  \033[0m",  # Dark gray
    9: "\033[101m  \033[0m",  # Light red
}

# Numeric representation for plain display
ARC_SYMBOLS = {
    0: "·",  # Background
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
}


def visualize_grid(
    grid: ARCGrid,
    title: Optional[str] = None,
    use_color: bool = True,
    show_coords: bool = False,
) -> str:
    """Visualize an ARC grid with optional colors and coordinates.

    Args:
        grid: Grid to visualize
        title: Optional title to display above grid
        use_color: Use terminal colors (True) or symbols (False)
        show_coords: Show row/column coordinates

    Returns:
        String representation of the grid
    """
    lines = []

    if title:
        lines.append(f"\n{title}")
        lines.append("=" * len(title))

    # Column coordinates
    if show_coords:
        col_header = "   " + " ".join(str(i % 10) for i in range(grid.width))
        lines.append(col_header)
        lines.append("")

    # Grid rows
    for r in range(grid.height):
        row_parts = []

        if show_coords:
            row_parts.append(f"{r:2d} ")

        for c in range(grid.width):
            color = grid.get(r, c)
            if use_color:
                row_parts.append(ARC_COLORS.get(color, "  "))
            else:
                row_parts.append(ARC_SYMBOLS.get(color, "?"))

        lines.append("".join(row_parts))

    # Grid info
    colors = grid.get_unique_colors()
    bg_color = grid.get_background_color()
    lines.append("")
    lines.append(f"Shape: {grid.shape}, Colors: {len(colors)}, Background: {bg_color}")

    return "\n".join(lines)


def visualize_objects(
    grid: ARCGrid,
    objects: List[ARCObject],
    title: Optional[str] = None,
    highlight: bool = True,
) -> str:
    """Visualize detected objects on a grid.

    Args:
        grid: Original grid
        objects: Detected objects to highlight
        title: Optional title
        highlight: Add borders around objects

    Returns:
        String representation with object highlights
    """
    lines = []

    if title:
        lines.append(f"\n{title}")
        lines.append("=" * len(title))

    # Create object map for quick lookup
    object_map: Dict[tuple, int] = {}
    for i, obj in enumerate(objects):
        for r, c in obj.pixels:
            object_map[(r, c)] = i

    # Visualize grid with object borders
    for r in range(grid.height):
        row_parts = []

        for c in range(grid.width):
            color = grid.get(r, c)

            if (r, c) in object_map and highlight:
                # Add border for object pixels
                row_parts.append(f"\033[1m{ARC_COLORS.get(color, '  ')}\033[0m")
            else:
                row_parts.append(ARC_COLORS.get(color, "  "))

        lines.append("".join(row_parts))

    # Object statistics
    lines.append("")
    lines.append(f"Detected {len(objects)} objects:")
    for i, obj in enumerate(objects):
        min_r, min_c, max_r, max_c = obj.bounding_box
        lines.append(
            f"  Object {i+1}: Color={obj.color}, Mass={obj.mass}, "
            f"BBox=({min_r},{min_c})-({max_r},{max_c})"
        )

    return "\n".join(lines)


def visualize_task(
    train_pairs: List[tuple],
    test_input: Optional[ARCGrid] = None,
    test_output: Optional[ARCGrid] = None,
    title: Optional[str] = None,
) -> str:
    """Visualize an ARC task with training examples and test case.

    Args:
        train_pairs: List of (input_grid, output_grid) training pairs
        test_input: Test input grid
        test_output: Test output grid (if known)
        title: Task title

    Returns:
        String representation of the complete task
    """
    lines = []

    if title:
        lines.append(f"\n{'='*60}")
        lines.append(f"  {title}")
        lines.append(f"{'='*60}")

    # Training examples
    lines.append("\nTRAINING EXAMPLES:")
    lines.append("-" * 60)

    for i, (input_grid, output_grid) in enumerate(train_pairs):
        lines.append(f"\nExample {i+1}:")
        lines.append("")

        # Show input and output side by side
        lines.append("INPUT:")
        lines.append(visualize_grid(input_grid, use_color=True, show_coords=False))

        lines.append("\nOUTPUT:")
        lines.append(visualize_grid(output_grid, use_color=True, show_coords=False))

        lines.append("-" * 60)

    # Test case
    if test_input:
        lines.append("\nTEST CASE:")
        lines.append("-" * 60)
        lines.append("\nINPUT:")
        lines.append(visualize_grid(test_input, use_color=True, show_coords=False))

        if test_output:
            lines.append("\nEXPECTED OUTPUT:")
            lines.append(visualize_grid(test_output, use_color=True, show_coords=False))

    return "\n".join(lines)


def visualize_transformation(
    input_grid: ARCGrid,
    output_grid: ARCGrid,
    transformation_name: str,
    params: Optional[Dict] = None,
) -> str:
    """Visualize a transformation from input to output.

    Args:
        input_grid: Input grid
        output_grid: Output grid
        transformation_name: Name of the transformation
        params: Transformation parameters

    Returns:
        String showing the transformation
    """
    lines = []

    lines.append(f"\nTransformation: {transformation_name}")
    if params:
        lines.append(f"Parameters: {params}")
    lines.append("=" * 60)

    lines.append("\nINPUT:")
    lines.append(visualize_grid(input_grid, use_color=True))

    lines.append("\n     ↓")
    lines.append(f"  {transformation_name}")
    lines.append("     ↓")

    lines.append("\nOUTPUT:")
    lines.append(visualize_grid(output_grid, use_color=True))

    # Comparison
    lines.append("\nCHANGES:")
    if input_grid.shape != output_grid.shape:
        lines.append(f"  Shape: {input_grid.shape} → {output_grid.shape}")

    input_colors = input_grid.get_unique_colors()
    output_colors = output_grid.get_unique_colors()
    if input_colors != output_colors:
        added = output_colors - input_colors
        removed = input_colors - output_colors
        if added:
            lines.append(f"  Added colors: {added}")
        if removed:
            lines.append(f"  Removed colors: {removed}")

    return "\n".join(lines)


def visualize_comparison(
    grid1: ARCGrid,
    grid2: ARCGrid,
    label1: str = "Grid 1",
    label2: str = "Grid 2",
) -> str:
    """Compare two grids side by side.

    Args:
        grid1: First grid
        grid2: Second grid
        label1: Label for first grid
        label2: Label for second grid

    Returns:
        Side-by-side comparison
    """
    lines = []

    lines.append(f"\n{label1:30s}  {label2}")
    lines.append("=" * 60)

    # Display grids
    grid1_lines = visualize_grid(grid1, use_color=True).split("\n")
    grid2_lines = visualize_grid(grid2, use_color=True).split("\n")

    max_lines = max(len(grid1_lines), len(grid2_lines))

    for i in range(max_lines):
        line1 = grid1_lines[i] if i < len(grid1_lines) else ""
        line2 = grid2_lines[i] if i < len(grid2_lines) else ""
        lines.append(f"{line1:30s}  {line2}")

    # Comparison metrics
    lines.append("\nCOMPARISON:")
    lines.append(f"  Shape match: {grid1.shape == grid2.shape}")
    lines.append(f"  Exact match: {grid1.equals(grid2)}")

    if grid1.shape == grid2.shape:
        # Count differences
        diff_count = 0
        for r in range(grid1.height):
            for c in range(grid1.width):
                if grid1.get(r, c) != grid2.get(r, c):
                    diff_count += 1

        total_cells = grid1.size
        accuracy = (total_cells - diff_count) / total_cells * 100
        lines.append(f"  Pixel accuracy: {accuracy:.1f}% ({diff_count} differences)")

    return "\n".join(lines)


def print_grid(grid: ARCGrid, **kwargs):
    """Convenience function to print a grid."""
    print(visualize_grid(grid, **kwargs))


def print_objects(grid: ARCGrid, objects: List[ARCObject], **kwargs):
    """Convenience function to print objects on grid."""
    print(visualize_objects(grid, objects, **kwargs))


def print_task(train_pairs: List[tuple], test_input=None, test_output=None, **kwargs):
    """Convenience function to print a task."""
    print(visualize_task(train_pairs, test_input, test_output, **kwargs))
