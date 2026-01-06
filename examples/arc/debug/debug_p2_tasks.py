"""Debug Priority 2 task solving."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.catalog import TransformationCatalog
from supe.reasoning.arc.parameter_inference import ParameterInferenceEngine, PatternMatcher

def test_task_00d62c1b():
    """Test fill enclosed regions on task 00d62c1b."""
    print("\n" + "="*70)
    print("TESTING TASK 00d62c1b - Fill Enclosed Regions")
    print("="*70)

    # Load task
    with open("data/arc_tasks/training/00d62c1b.json") as f:
        data = json.load(f)

    # Parse training examples
    train_inputs = []
    train_outputs = []
    for example in data['train']:
        train_inputs.append(ARCGrid.from_list(example['input']))
        train_outputs.append(ARCGrid.from_list(example['output']))

    print(f"\nLoaded {len(train_inputs)} training examples")

    # Test pattern matcher
    print("\n--- Testing Pattern Matcher ---")
    matcher = PatternMatcher()
    matches = matcher.match_pattern(train_inputs, train_outputs)

    if matches:
        print(f"✅ Found {len(matches)} pattern matches:")
        for transform_name, confidence, params in matches:
            print(f"  • {transform_name} (confidence: {confidence:.2f})")
            print(f"    Parameters: {params}")
    else:
        print("❌ No patterns matched!")

    # Test parameter inference
    print("\n--- Testing Parameter Inference ---")
    inference = ParameterInferenceEngine()

    # Try boundary color inference
    boundary_params = inference._infer_boundary_color(train_inputs, train_outputs)
    print(f"Boundary color: {boundary_params}")

    # Try fill color inference
    fill_params = inference._infer_fill_color(train_inputs, train_outputs)
    print(f"Fill color: {fill_params}")

    # Test transformation directly
    print("\n--- Testing FillEnclosedRegionsTransformation Directly ---")
    catalog = TransformationCatalog()
    transform = catalog.get('fill_enclosed_regions')

    if transform:
        print(f"✅ Found transformation: {transform.name}")

        # Try on ALL training examples
        if boundary_params and fill_params:
            params = {**boundary_params, **fill_params}
            print(f"  Parameters: {params}")

            results = []
            for i, (inp, expected_out) in enumerate(zip(train_inputs, train_outputs)):
                print(f"\n  Example {i+1}:")
                print(f"    Input shape: {inp.shape}")
                print(f"    Expected output shape: {expected_out.shape}")

                result = transform.apply(inp, **params)

                if result.success:
                    matches = (result.output_grid.data == expected_out.data).all()
                    print(f"    ✅ Transformation succeeded, match: {matches}")
                    results.append(matches)

                    if not matches:
                        diff_count = (result.output_grid.data != expected_out.data).sum()
                        print(f"    Differences: {diff_count} pixels")
                else:
                    print(f"    ❌ Transformation failed: {result.explanation}")
                    results.append(False)

            print(f"\n  Overall: {sum(results)}/{len(results)} examples match")
        else:
            print(f"  ❌ Missing parameters")
    else:
        print("❌ Transformation not found in catalog!")


def main():
    test_task_00d62c1b()


if __name__ == "__main__":
    main()
