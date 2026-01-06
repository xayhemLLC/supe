#!/usr/bin/env python3
"""
Human-Validated Tasc for Function Composition Problem

This creates a tasc with evidence that requires human validation.
The human will confirm whether the answer is correct.
"""

import json
from datetime import datetime
from pathlib import Path

# Tasc data structure
TASC = {
    "id": "MATH-001",
    "title": "Function Composition: Find f(g(2))",
    "status": "pending_human_validation",
    "problem": {
        "given": [
            "f(x) = x² + 1",
            "g(x) = x - 2"
        ],
        "find": "f(g(2))",
        "options": {
            "A": 1,
            "B": 5,
            "C": -1,
            "D": 0
        }
    },
    "reasoning_chain": [
        {
            "step": 1,
            "description": "Identify the problem type",
            "observation": "This is function composition - evaluate inner function first",
            "validated": True
        },
        {
            "step": 2,
            "description": "Evaluate g(2)",
            "computation": "g(2) = 2 - 2 = 0",
            "result": 0,
            "validated": True
        },
        {
            "step": 3,
            "description": "Evaluate f(g(2)) = f(0)",
            "computation": "f(0) = 0² + 1 = 0 + 1 = 1",
            "result": 1,
            "validated": True
        },
        {
            "step": 4,
            "description": "Verify with composite function",
            "computation": "f(g(x)) = (x-2)² + 1 = x² - 4x + 5",
            "verification": "f(g(2)) = 4 - 8 + 5 = 1",
            "result": 1,
            "validated": True
        }
    ],
    "proposed_answer": "A",
    "proposed_value": 1,
    "confidence": {
        "self_assessed": 1.0,
        "reasoning": "Two independent methods (direct evaluation and composite function) both yield 1"
    },
    "evidence": [
        {
            "type": "calculation",
            "source": "direct_evaluation",
            "content": "g(2) = 0, f(0) = 1",
            "validated": True
        },
        {
            "type": "verification",
            "source": "algebraic_composition",
            "content": "f(g(x)) = x² - 4x + 5, f(g(2)) = 1",
            "validated": True
        },
        {
            "type": "error_check",
            "source": "common_mistakes_analysis",
            "content": "Checked for order confusion, arithmetic errors",
            "validated": True
        }
    ],
    "human_validation": {
        "status": "awaiting",
        "validator": None,
        "timestamp": None,
        "verdict": None,
        "feedback": None
    },
    "created_at": datetime.utcnow().isoformat()
}


def display_tasc():
    """Display the tasc for human review."""
    print("=" * 70)
    print("                    TASC: HUMAN VALIDATION REQUIRED")
    print("=" * 70)
    print()
    print(f"  ID: {TASC['id']}")
    print(f"  Title: {TASC['title']}")
    print()
    print("  PROBLEM:")
    print("  ────────")
    for given in TASC['problem']['given']:
        print(f"    {given}")
    print(f"    Find: {TASC['problem']['find']}")
    print()
    print("  OPTIONS:")
    for opt, val in TASC['problem']['options'].items():
        marker = " ◄── PROPOSED" if opt == TASC['proposed_answer'] else ""
        print(f"    {opt}. {val}{marker}")
    print()
    print("  REASONING CHAIN:")
    print("  ─────────────────")
    for step in TASC['reasoning_chain']:
        print(f"    Step {step['step']}: {step['description']}")
        if 'computation' in step:
            print(f"      {step['computation']}")
        if 'verification' in step:
            print(f"      Verification: {step['verification']}")
        print(f"      → Result: {step.get('result', 'N/A')}")
        print()
    print("  EVIDENCE:")
    print("  ─────────")
    for i, ev in enumerate(TASC['evidence'], 1):
        print(f"    {i}. [{ev['type']}] {ev['content']}")
    print()
    print("  CONFIDENCE: {:.0%}".format(TASC['confidence']['self_assessed']))
    print(f"  Reasoning: {TASC['confidence']['reasoning']}")
    print()
    print("=" * 70)
    print("              PROPOSED ANSWER: {} ({})".format(
        TASC['proposed_answer'],
        TASC['proposed_value']
    ))
    print("=" * 70)
    print()


def request_validation():
    """Request human validation."""
    print("  HUMAN VALIDATION REQUIRED")
    print("  ─────────────────────────")
    print()
    print("  Please validate the proposed answer.")
    print()

    while True:
        response = input("  Is the answer correct? (y/n/skip): ").strip().lower()

        if response in ['y', 'yes']:
            TASC['human_validation']['status'] = 'validated'
            TASC['human_validation']['verdict'] = 'correct'
            TASC['human_validation']['timestamp'] = datetime.utcnow().isoformat()

            feedback = input("  Any feedback? (press Enter to skip): ").strip()
            if feedback:
                TASC['human_validation']['feedback'] = feedback

            print()
            print("  ✓ VALIDATION COMPLETE: Answer marked as CORRECT")
            TASC['status'] = 'validated_correct'
            break

        elif response in ['n', 'no']:
            TASC['human_validation']['status'] = 'validated'
            TASC['human_validation']['verdict'] = 'incorrect'
            TASC['human_validation']['timestamp'] = datetime.utcnow().isoformat()

            correct_answer = input("  What is the correct answer? (A/B/C/D): ").strip().upper()
            feedback = input("  Feedback on the error: ").strip()

            TASC['human_validation']['correct_answer'] = correct_answer
            TASC['human_validation']['feedback'] = feedback

            print()
            print(f"  ✗ VALIDATION COMPLETE: Answer marked as INCORRECT")
            print(f"    Correct answer: {correct_answer}")
            TASC['status'] = 'validated_incorrect'
            break

        elif response == 'skip':
            print("  Skipping validation...")
            break

        else:
            print("  Please enter 'y', 'n', or 'skip'")


def save_tasc():
    """Save tasc to file."""
    output_path = Path(__file__).parent / "math_tasc_result.json"
    with open(output_path, 'w') as f:
        json.dump(TASC, f, indent=2)
    print(f"\n  Tasc saved to: {output_path}")


def main():
    """Main entry point."""
    print()
    display_tasc()
    request_validation()
    save_tasc()

    # Print final status
    print()
    print("  FINAL STATUS")
    print("  ────────────")
    print(f"  Status: {TASC['status']}")
    print(f"  Verdict: {TASC['human_validation'].get('verdict', 'N/A')}")
    if TASC['human_validation'].get('feedback'):
        print(f"  Feedback: {TASC['human_validation']['feedback']}")
    print()


if __name__ == "__main__":
    main()
