"""Debug why solver misses known solutions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.parameter_inference import ParameterInferenceEngine, PatternMatcher
from supe.reasoning.arc.composition_search import CompositionSearchEngine


def debug_task_0d3d703e():
    """Debug color mapping task."""
    print("\n" + "="*70)
    print("DEBUGGING TASK 0d3d703e - Color Mapping")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/0d3d703e.json") as f:
        data = json.load(f)

    train_inputs = [ARCGrid.from_list(ex['input']) for ex in data['train']]
    train_outputs = [ARCGrid.from_list(ex['output']) for ex in data['train']]

    # Test parameter inference
    print("\n1. Testing parameter inference...")
    inference = ParameterInferenceEngine()
    params = inference._infer_color_mapping(train_inputs, train_outputs)
    print(f"   Inferred params: {params}")

    # Test pattern matcher
    print("\n2. Testing pattern matcher...")
    matcher = PatternMatcher()
    matches = matcher.match_pattern(train_inputs, train_outputs)
    print(f"   Found {len(matches)} matches:")
    for name, conf, params in matches:
        print(f"     • {name} (confidence: {conf:.2f})")

    # Test composition search
    print("\n3. Testing composition search...")
    search = CompositionSearchEngine()
    solutions = search.search(train_inputs, train_outputs, max_steps=1)
    print(f"   Found {len(solutions)} solutions")
    for sol in solutions:
        print(f"     • {sol}")


def debug_task_0520fde7():
    """Debug extract-compare-conditional task."""
    print("\n" + "="*70)
    print("DEBUGGING TASK 0520fde7 - Extract+Compare+Conditional")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/0520fde7.json") as f:
        data = json.load(f)

    train_inputs = [ARCGrid.from_list(ex['input']) for ex in data['train']]
    train_outputs = [ARCGrid.from_list(ex['output']) for ex in data['train']]

    # Test parameter inference
    print("\n1. Testing marker color inference...")
    inference = ParameterInferenceEngine()
    marker_params = inference._infer_marker_color(train_inputs, train_outputs)
    print(f"   Inferred marker: {marker_params}")

    # Test pattern matcher
    print("\n2. Testing pattern matcher...")
    matcher = PatternMatcher()
    matches = matcher.match_pattern(train_inputs, train_outputs)
    print(f"   Found {len(matches)} matches:")
    for name, conf, params in matches:
        print(f"     • {name} (confidence: {conf:.2f})")

    # Test extract-compare-conditional pattern
    print("\n3. Testing extract-compare-conditional pattern...")
    search = CompositionSearchEngine()
    result = search._try_extract_compare_conditional(train_inputs, train_outputs)
    print(f"   Result: {result}")


def debug_task_28bf18c6():
    """Debug crop-duplicate task (should work)."""
    print("\n" + "="*70)
    print("DEBUGGING TASK 28bf18c6 - Crop+Duplicate (SHOULD WORK)")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/28bf18c6.json") as f:
        data = json.load(f)

    train_inputs = [ARCGrid.from_list(ex['input']) for ex in data['train']]
    train_outputs = [ARCGrid.from_list(ex['output']) for ex in data['train']]

    # Test pattern matcher
    print("\n1. Testing pattern matcher...")
    matcher = PatternMatcher()
    matches = matcher.match_pattern(train_inputs, train_outputs)
    print(f"   Found {len(matches)} matches:")
    for name, conf, params in matches:
        print(f"     • {name} (confidence: {conf:.2f})")

    # Test crop-duplicate pattern
    print("\n2. Testing crop-duplicate pattern...")
    search = CompositionSearchEngine()
    result = search._try_crop_duplicate_pattern(train_inputs, train_outputs)
    print(f"   Result: {result}")


if __name__ == "__main__":
    debug_task_0d3d703e()
    debug_task_0520fde7()
    debug_task_28bf18c6()

    print("\n" + "="*70)
    print("DEBUGGING COMPLETE")
    print("="*70)
