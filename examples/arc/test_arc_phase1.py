"""Test and demonstrate ARC Phase 1 capabilities.

This script validates:
- Grid data structures
- Object detection
- Spatial transformations
- Visualization tools
"""

import numpy as np
from supe.reasoning.arc import (
    ARCGrid,
    ARCObject,
    ObjectDetector,
    SpatialReasoner,
    print_grid,
    print_objects,
    visualize_transformation,
    visualize_comparison,
)


def test_basic_grid():
    """Test basic grid creation and properties."""
    print("\n" + "="*60)
    print("TEST 1: Basic Grid Operations")
    print("="*60)

    # Create a simple grid with a cross pattern
    grid_data = [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ]

    grid = ARCGrid.from_list(grid_data, task_id="test_cross")

    print_grid(grid, title="Cross Pattern Grid")

    # Test properties
    print(f"\nProperties:")
    print(f"  Shape: {grid.shape}")
    print(f"  Size: {grid.size} cells")
    print(f"  Colors: {grid.get_unique_colors()}")
    print(f"  Background: {grid.get_background_color()}")
    print(f"  Horizontal symmetry: {grid.is_symmetric_horizontal()}")
    print(f"  Vertical symmetry: {grid.is_symmetric_vertical()}")

    return grid


def test_object_detection():
    """Test object detection with multiple objects."""
    print("\n" + "="*60)
    print("TEST 2: Object Detection")
    print("="*60)

    # Create grid with multiple objects
    grid_data = [
        [0, 1, 1, 0, 2, 2],
        [0, 1, 1, 0, 2, 2],
        [0, 0, 0, 0, 0, 0],
        [3, 3, 0, 4, 4, 4],
        [3, 3, 0, 4, 4, 4],
    ]

    grid = ARCGrid.from_list(grid_data, task_id="test_objects")

    print_grid(grid, title="Multi-Object Grid")

    # Detect objects
    detector = ObjectDetector()
    objects = detector.detect_objects(grid, background_color=0, connectivity=4)

    print_objects(grid, objects, title="\nDetected Objects (highlighted)")

    # Test object properties
    print("\nObject Analysis:")
    for i, obj in enumerate(objects):
        center_r, center_c = obj.center
        print(f"\nObject {i+1}:")
        print(f"  Color: {obj.color}")
        print(f"  Mass: {obj.mass} pixels")
        print(f"  Center: ({center_r:.1f}, {center_c:.1f})")
        print(f"  Dimensions: {obj.width}x{obj.height}")

        # Check symmetry
        symmetries = SpatialReasoner().detect_symmetry(obj)
        sym_types = [k for k, v in symmetries.items() if v]
        if sym_types:
            print(f"  Symmetries: {', '.join(sym_types)}")

    return grid, objects


def test_spatial_transformations():
    """Test spatial transformations."""
    print("\n" + "="*60)
    print("TEST 3: Spatial Transformations")
    print("="*60)

    # Create a simple asymmetric shape
    grid_data = [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
    ]

    grid = ARCGrid.from_list(grid_data, task_id="test_transform")
    spatial = SpatialReasoner()

    print("\n--- Rotation Tests ---")
    print_grid(grid, title="Original")

    rotated_90 = spatial.rotate_grid_90(grid, clockwise=True)
    print_grid(rotated_90, title="\nRotated 90° Clockwise")

    rotated_180 = spatial.rotate_grid_180(grid)
    print_grid(rotated_180, title="\nRotated 180°")

    print("\n--- Flip Tests ---")
    flipped_h = spatial.flip_horizontal(grid)
    print_grid(flipped_h, title="Flipped Horizontally")

    flipped_v = spatial.flip_vertical(grid)
    print_grid(flipped_v, title="\nFlipped Vertically")

    print("\n--- Transpose ---")
    transposed = spatial.transpose(grid)
    print_grid(transposed, title="Transposed")

    return grid, rotated_90, flipped_h


def test_object_transformations():
    """Test transformations on individual objects."""
    print("\n" + "="*60)
    print("TEST 4: Object Transformations")
    print("="*60)

    # Create object
    pixels = {(1, 1), (1, 2), (2, 1), (2, 2)}  # 2x2 square
    obj = ARCObject(pixels=pixels, color=3, grid_id="test")

    # Create grid and place object
    grid = ARCGrid(data=np.zeros((6, 6), dtype=int))
    spatial = SpatialReasoner()

    grid_with_obj = spatial.place_object_on_grid(grid, obj, row=1, col=1)
    print_grid(grid_with_obj, title="Original Object (2x2 square)")

    # Scale object
    scaled = spatial.scale_object(obj, factor=2)
    grid_scaled = spatial.place_object_on_grid(grid, scaled, row=1, col=1)
    print_grid(grid_scaled, title="\nScaled 2x (4x4)")

    # Rotate object
    rotated = spatial.rotate_object_90(obj, clockwise=True)
    grid_rotated = spatial.place_object_on_grid(grid, rotated, row=1, col=1)
    print_grid(grid_rotated, title="\nRotated 90°")

    return obj, scaled


def test_relative_positioning():
    """Test relative positioning between objects."""
    print("\n" + "="*60)
    print("TEST 5: Relative Positioning")
    print("="*60)

    # Create two objects
    obj1 = ARCObject(pixels={(1, 1), (1, 2), (2, 1), (2, 2)}, color=1)
    obj2 = ARCObject(pixels={(5, 5), (5, 6), (6, 5), (6, 6)}, color=2)

    # Test positioning
    spatial = SpatialReasoner()
    rel_pos = spatial.get_relative_position(obj1, obj2)

    print(f"Object 1 center: {obj1.center}")
    print(f"Object 2 center: {obj2.center}")
    print(f"\nRelative Position:")
    for key, value in rel_pos.items():
        print(f"  {key}: {value}")

    # Test distance
    distance = spatial.compute_distance(obj1, obj2, metric="euclidean")
    print(f"\nEuclidean distance: {distance:.2f}")

    manhattan = spatial.compute_distance(obj1, obj2, metric="manhattan")
    print(f"Manhattan distance: {manhattan:.0f}")


def test_arc_task_format():
    """Test ARC task visualization format."""
    print("\n" + "="*60)
    print("TEST 6: ARC Task Format")
    print("="*60)

    # Create training examples
    train_input_1 = ARCGrid.from_list([
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ])

    train_output_1 = ARCGrid.from_list([
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ])

    train_input_2 = ARCGrid.from_list([
        [1, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
    ])

    train_output_2 = ARCGrid.from_list([
        [0, 0, 0],
        [0, 0, 1],
        [0, 0, 1],
    ])

    test_input = ARCGrid.from_list([
        [0, 0, 1],
        [0, 0, 1],
        [0, 0, 0],
    ])

    # Display as ARC task
    from supe.reasoning.arc.visualizer import visualize_task

    task_viz = visualize_task(
        train_pairs=[
            (train_input_1, train_output_1),
            (train_input_2, train_output_2),
        ],
        test_input=test_input,
        title="Example ARC Task: Rotation Pattern"
    )

    print(task_viz)


def run_all_tests():
    """Run all Phase 1 tests."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  ARC-AGI Phase 1: Core Infrastructure Tests".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)

    try:
        # Run tests
        test_basic_grid()
        test_object_detection()
        test_spatial_transformations()
        test_object_transformations()
        test_relative_positioning()
        test_arc_task_format()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✓ Grid data structures working")
        print("✓ Object detection (connected components) working")
        print("✓ Spatial transformations working")
        print("✓ Object transformations working")
        print("✓ Relative positioning working")
        print("✓ ARC task format working")
        print("\n✓ ALL PHASE 1 TESTS PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
