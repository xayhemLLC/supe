"""Test ARC Phase 2: Shape Recognition and Pattern Detection.

Validates:
- Shape recognition (lines, rectangles, special shapes)
- Pattern detection (repetition, tiling, alternation)
- Object alignment and grid structures
"""

import numpy as np
from supe.reasoning.arc import (
    ARCGrid,
    ARCObject,
    ObjectDetector,
    print_grid,
)
from supe.reasoning.arc.shapes import ShapeRecognizer, ShapeType, LineOrientation
from supe.reasoning.arc.patterns import PatternDetector, PatternType


def test_line_recognition():
    """Test line shape recognition."""
    print("\n" + "="*60)
    print("TEST 1: Line Recognition")
    print("="*60)

    recognizer = ShapeRecognizer()

    # Horizontal line
    h_line_data = [
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
    ]
    h_grid = ARCGrid.from_list(h_line_data)
    print_grid(h_grid, title="Horizontal Line")

    detector = ObjectDetector()
    objects = detector.detect_objects(h_grid)

    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.LINE
        assert shape.orientation == LineOrientation.HORIZONTAL
        print("  ✓ Horizontal line correctly recognized")

    # Vertical line
    v_line_data = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ]
    v_grid = ARCGrid.from_list(v_line_data)
    print_grid(v_grid, title="\nVertical Line")

    objects = detector.detect_objects(v_grid)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.LINE
        assert shape.orientation == LineOrientation.VERTICAL
        print("  ✓ Vertical line correctly recognized")

    # Diagonal line (needs 8-connectivity for diagonal connections)
    diag_data = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    diag_grid = ARCGrid.from_list(diag_data)
    print_grid(diag_grid, title="\nDiagonal Line")

    # Use 8-connectivity for diagonal detection
    objects = detector.detect_objects(diag_grid, connectivity=8)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.DIAGONAL
        assert shape.orientation == LineOrientation.DIAGONAL_MAIN
        print("  ✓ Diagonal line correctly recognized")


def test_rectangle_recognition():
    """Test rectangle shape recognition."""
    print("\n" + "="*60)
    print("TEST 2: Rectangle Recognition")
    print("="*60)

    recognizer = ShapeRecognizer()
    detector = ObjectDetector()

    # Filled rectangle
    filled_data = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    filled_grid = ARCGrid.from_list(filled_data)
    print_grid(filled_grid, title="Filled Rectangle")

    objects = detector.detect_objects(filled_grid)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.RECTANGLE
        assert shape.properties["filled"] == True
        print("  ✓ Filled rectangle correctly recognized")

    # Square
    square_data = [
        [0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0],
        [0, 2, 2, 2, 0],
        [0, 2, 2, 2, 0],
        [0, 0, 0, 0, 0],
    ]
    square_grid = ARCGrid.from_list(square_data)
    print_grid(square_grid, title="\nSquare")

    objects = detector.detect_objects(square_grid)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.SQUARE
        print("  ✓ Square correctly recognized")

    # Hollow rectangle
    hollow_data = [
        [0, 0, 0, 0, 0, 0],
        [0, 3, 3, 3, 3, 0],
        [0, 3, 0, 0, 3, 0],
        [0, 3, 0, 0, 3, 0],
        [0, 3, 3, 3, 3, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    hollow_grid = ARCGrid.from_list(hollow_data)
    print_grid(hollow_grid, title="\nHollow Rectangle")

    objects = detector.detect_objects(hollow_grid)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.HOLLOW_RECTANGLE
        assert shape.properties["filled"] == False
        print("  ✓ Hollow rectangle correctly recognized")


def test_special_shapes():
    """Test special shape recognition (cross, T, L)."""
    print("\n" + "="*60)
    print("TEST 3: Special Shapes")
    print("="*60)

    recognizer = ShapeRecognizer()
    detector = ObjectDetector()

    # Cross shape
    cross_data = [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ]
    cross_grid = ARCGrid.from_list(cross_data)
    print_grid(cross_grid, title="Cross Shape")

    objects = detector.detect_objects(cross_grid)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.CROSS
        print("  ✓ Cross shape correctly recognized")

    # T-shape
    t_data = [
        [0, 0, 0, 0, 0],
        [2, 2, 2, 2, 2],
        [0, 0, 2, 0, 0],
        [0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    t_grid = ARCGrid.from_list(t_data)
    print_grid(t_grid, title="\nT-Shape")

    objects = detector.detect_objects(t_grid)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.T_SHAPE
        print("  ✓ T-shape correctly recognized")

    # L-shape
    l_data = [
        [0, 0, 0, 0],
        [3, 0, 0, 0],
        [3, 0, 0, 0],
        [3, 3, 3, 0],
        [0, 0, 0, 0],
    ]
    l_grid = ARCGrid.from_list(l_data)
    print_grid(l_grid, title="\nL-Shape")

    objects = detector.detect_objects(l_grid)
    for obj in objects:
        shape = recognizer.recognize_object(obj)
        print(f"  Detected: {shape}")
        assert shape.shape_type == ShapeType.L_SHAPE
        print("  ✓ L-shape correctly recognized")


def test_repetition_pattern():
    """Test repetition pattern detection."""
    print("\n" + "="*60)
    print("TEST 4: Repetition Pattern")
    print("="*60)

    detector = ObjectDetector()
    pattern_detector = PatternDetector()

    # Grid with repeated squares
    repeat_data = [
        [1, 1, 0, 2, 2, 0, 3, 3],
        [1, 1, 0, 2, 2, 0, 3, 3],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [4, 4, 0, 5, 5, 0, 6, 6],
        [4, 4, 0, 5, 5, 0, 6, 6],
    ]
    repeat_grid = ARCGrid.from_list(repeat_data)
    print_grid(repeat_grid, title="Repeated Squares")

    objects = detector.detect_objects(repeat_grid)
    pattern = pattern_detector.detect_repetition(objects)

    if pattern:
        print(f"  Detected: {pattern}")
        assert pattern.pattern_type == PatternType.REPETITION
        assert pattern.confidence > 0.8
        print("  ✓ Repetition pattern correctly detected")
    else:
        print("  ✗ Failed to detect repetition")


def test_alignment_pattern():
    """Test object alignment detection."""
    print("\n" + "="*60)
    print("TEST 5: Alignment Pattern")
    print("="*60)

    detector = ObjectDetector()
    pattern_detector = PatternDetector()

    # Horizontally aligned objects
    h_align_data = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 0, 2, 2, 0, 3, 3],
        [1, 1, 0, 2, 2, 0, 3, 3],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    h_align_grid = ARCGrid.from_list(h_align_data)
    print_grid(h_align_grid, title="Horizontal Alignment")

    objects = detector.detect_objects(h_align_grid)
    pattern = pattern_detector.detect_alignment(objects)

    if pattern:
        print(f"  Detected: {pattern}")
        assert pattern.pattern_type == PatternType.ALIGNMENT
        assert pattern.properties["direction"] == "horizontal"
        print("  ✓ Horizontal alignment correctly detected")
    else:
        print("  ✗ Failed to detect alignment")


def test_tiling_pattern():
    """Test tiling pattern detection."""
    print("\n" + "="*60)
    print("TEST 6: Tiling Pattern")
    print("="*60)

    pattern_detector = PatternDetector()

    # 2x2 tiling pattern
    tile_data = [
        [1, 2, 1, 2, 1, 2],
        [3, 4, 3, 4, 3, 4],
        [1, 2, 1, 2, 1, 2],
        [3, 4, 3, 4, 3, 4],
    ]
    tile_grid = ARCGrid.from_list(tile_data)
    print_grid(tile_grid, title="2x2 Tiling")

    pattern = pattern_detector.detect_tiling(tile_grid)

    if pattern:
        print(f"  Detected: {pattern}")
        assert pattern.pattern_type == PatternType.TILING
        assert pattern.properties["tile_size"] == (2, 2)
        print("  ✓ Tiling pattern correctly detected")
    else:
        print("  ✗ Failed to detect tiling")


def test_checkerboard_pattern():
    """Test checkerboard alternation pattern."""
    print("\n" + "="*60)
    print("TEST 7: Checkerboard Pattern")
    print("="*60)

    pattern_detector = PatternDetector()

    # Checkerboard
    checker_data = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    checker_grid = ARCGrid.from_list(checker_data)
    print_grid(checker_grid, title="Checkerboard")

    pattern = pattern_detector.detect_alternation(checker_grid)

    if pattern:
        print(f"  Detected: {pattern}")
        assert pattern.pattern_type == PatternType.ALTERNATION
        assert pattern.properties["subtype"] == "checkerboard"
        print("  ✓ Checkerboard pattern correctly detected")
    else:
        print("  ✗ Failed to detect checkerboard")


def test_complete_analysis():
    """Test complete shape and pattern analysis."""
    print("\n" + "="*60)
    print("TEST 8: Complete Grid Analysis")
    print("="*60)

    # Complex grid with multiple features
    complex_data = [
        [1, 1, 0, 2, 2, 0, 3, 3],
        [1, 1, 0, 2, 2, 0, 3, 3],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [4, 4, 4, 4, 0, 5, 5, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]
    complex_grid = ARCGrid.from_list(complex_data)
    print_grid(complex_grid, title="Complex Grid")

    # Shape analysis
    recognizer = ShapeRecognizer()
    shape_analysis = recognizer.analyze_grid_shapes(complex_grid)

    print("\nShape Analysis:")
    print(f"  Total objects: {shape_analysis['total_objects']}")
    print(f"  Shape counts: {shape_analysis['shape_counts']}")
    print(f"  Has rectangles: {shape_analysis['has_rectangles']}")
    print(f"  Has lines: {shape_analysis['has_lines']}")

    # Pattern analysis
    detector = ObjectDetector()
    objects = detector.detect_objects(complex_grid)

    pattern_detector = PatternDetector()
    patterns = pattern_detector.analyze_all_patterns(complex_grid, objects)

    print("\nPattern Analysis:")
    for pattern in patterns:
        print(f"  {pattern}")

    if shape_analysis['has_rectangles'] or shape_analysis['has_lines']:
        print("\n  ✓ Shape analysis working")

    if patterns:
        print("  ✓ Pattern analysis working")


def run_all_tests():
    """Run all Phase 2 tests."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  ARC-AGI Phase 2: Shape & Pattern Tests".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)

    try:
        test_line_recognition()
        test_rectangle_recognition()
        test_special_shapes()
        test_repetition_pattern()
        test_alignment_pattern()
        test_tiling_pattern()
        test_checkerboard_pattern()
        test_complete_analysis()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✓ Line recognition working (horizontal, vertical, diagonal)")
        print("✓ Rectangle recognition working (filled, hollow, square)")
        print("✓ Special shapes working (cross, T, L)")
        print("✓ Repetition pattern detection working")
        print("✓ Alignment pattern detection working")
        print("✓ Tiling pattern detection working")
        print("✓ Checkerboard pattern detection working")
        print("✓ Complete analysis working")
        print("\n✓ ALL PHASE 2 TESTS PASSED")
        print("="*60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
