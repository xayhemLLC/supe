#!/usr/bin/env python3
"""Compare INGEST and EXPLORE modes side-by-side.

This example demonstrates the key differences between the two learning modes
by applying both to similar topics and showing how they produce different
types of knowledge.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supe import Supe
from ab.models import Buffer


async def main():
    print("=" * 80)
    print("COMPARING INGEST vs EXPLORE MODES")
    print("=" * 80)
    print()

    supe = Supe(db_path=":memory:")

    # ========================================================================
    # Example 1: Learning about addition
    # ========================================================================

    print("📚 Example 1: Learning about Addition")
    print("=" * 80)
    print()

    # Store documentation about addition
    addition_docs = """
    Addition is a basic arithmetic operation that combines two numbers to
    produce a sum. It is one of the four fundamental operations of arithmetic.

    Properties:
    - Commutative: a + b = b + a
    - Associative: (a + b) + c = a + (b + c)
    - Identity element: 0 (a + 0 = a)
    - Closed: Sum of two numbers is always a number

    Examples:
    - 2 + 3 = 5
    - 10 + 20 = 30
    - 0 + 5 = 5 (demonstrates identity)
    """

    supe.memory.store_card(
        label="documentation",
        master_input="Addition documentation",
        master_output=addition_docs,
        track="awareness",
    )

    # INGEST: Learn ABOUT addition from docs
    print("🔵 INGEST MODE: What is addition?")
    print("-" * 80)

    ingest_result = await supe.learn(
        "What is addition?",
        mode="ingest"
    )

    if ingest_result['beliefs_count'] > 0:
        belief = ingest_result['beliefs'][0]
        content = belief['content']

        print(f"Output Type: Cornell Note")
        print(f"Cue: {content.get('cue', 'N/A')}")
        print(f"Summary: {content.get('conceptual_summary', 'N/A')[:150]}...")
        print(f"Confidence: {belief['confidence']:.2f}")
        print(f"Evidence: Documentation-based")
    print()

    # EXPLORE: PROVE properties of addition
    print("🟢 EXPLORE MODE: Is addition commutative?")
    print("-" * 80)

    explore_result = await supe.learn(
        "Is addition commutative?",
        mode="explore"
    )

    if explore_result['beliefs_count'] > 0:
        belief = explore_result['beliefs'][0]
        content = belief['content']

        print(f"Output Type: Theorem")
        print(f"Statement: {content['statement']}")
        print(f"Status: {content['status']}")
        print(f"Proof: {content['proof'][:100]}...")
        print(f"Confidence: {belief['confidence']:.2f}")
        print(f"Evidence: Experimental validation")
    print()

    # Comparison
    print("📊 COMPARISON")
    print("-" * 80)
    print(f"INGEST - Purpose: Understand WHAT addition is")
    print(f"       - Output: Descriptive notes")
    print(f"       - Evidence: Documentation")
    print(f"       - Confidence: {ingest_result.get('confidence', 0):.2f}")
    print()
    print(f"EXPLORE - Purpose: Prove addition IS commutative")
    print(f"        - Output: Formal theorem")
    print(f"        - Evidence: Experiments")
    print(f"        - Confidence: {explore_result.get('confidence', 0):.2f}")
    print()

    # ========================================================================
    # Example 2: Learning about Python dictionaries
    # ========================================================================

    print()
    print("📚 Example 2: Learning about Python Dictionaries")
    print("=" * 80)
    print()

    dict_docs = """
    Python dictionaries are hash tables that store key-value pairs.
    They provide O(1) average-case lookup time.

    Usage:
    my_dict = {'name': 'Alice', 'age': 30}
    value = my_dict['name']  # O(1) lookup

    Dictionaries use hashing internally to achieve fast lookups.
    """

    supe.memory.store_card(
        label="documentation",
        master_input="Python dict documentation",
        master_output=dict_docs,
        track="awareness",
    )

    # INGEST: Learn HOW to use dicts
    print("🔵 INGEST MODE: How do Python dicts work?")
    print("-" * 80)

    ingest_result2 = await supe.learn(
        "How do Python dictionaries work?",
        mode="ingest"
    )

    if ingest_result2['beliefs_count'] > 0:
        belief = ingest_result2['beliefs'][0]
        print(f"Output: Cornell note with usage examples")
        print(f"Focus: Understanding and usage patterns")
        print(f"Confidence: {belief['confidence']:.2f}")
    print()

    # EXPLORE: PROVE performance characteristics
    print("🟢 EXPLORE MODE: Is dict lookup O(1)?")
    print("-" * 80)

    explore_result2 = await supe.learn(
        "Is Python dictionary lookup constant time?",
        mode="explore"
    )

    if explore_result2['beliefs_count'] > 0:
        belief = explore_result2['beliefs'][0]
        content = belief['content']
        print(f"Output: Theorem about time complexity")
        print(f"Status: {content['status']}")
        print(f"Focus: Formal property validation")
        print(f"Confidence: {belief['confidence']:.2f}")
    print()

    # ========================================================================
    # Summary
    # ========================================================================

    print()
    print("=" * 80)
    print("MODE COMPARISON SUMMARY")
    print("=" * 80)
    print()

    print("🔵 INGEST MODE - Best for:")
    print("   • Understanding concepts")
    print("   • Learning from documentation")
    print("   • API usage patterns")
    print("   • Historical knowledge")
    print("   • Descriptive learning")
    print()
    print("   Output: Cornell notes (cue/notes/examples/summaries)")
    print("   Evidence: Documentation, code examples, existing knowledge")
    print("   Confidence: Based on evidence quality + self-test")
    print()

    print("🟢 EXPLORE MODE - Best for:")
    print("   • Discovering properties")
    print("   • Mathematical proofs")
    print("   • Testing hypotheses")
    print("   • Validating claims")
    print("   • Experimental learning")
    print()
    print("   Output: Theorems (statement/proof/status)")
    print("   Evidence: Experimental validation, test cases")
    print("   Confidence: Based on experiment pass rate")
    print()

    print("💡 When to use which:")
    print()
    print("   Use INGEST when asking:")
    print("   - 'What is X?'")
    print("   - 'How do I use X?'")
    print("   - 'What does X do?'")
    print()
    print("   Use EXPLORE when asking:")
    print("   - 'Is X commutative?'")
    print("   - 'Does X have property Y?'")
    print("   - 'Is this claim true?'")
    print()

    print("🔗 Combine both modes:")
    print("   1. INGEST: Learn what addition is (from docs)")
    print("   2. EXPLORE: Prove addition is commutative (through experiments)")
    print("   3. Result: Complete understanding (description + formal proof)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
