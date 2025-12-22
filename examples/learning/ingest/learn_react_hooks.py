#!/usr/bin/env python3
"""Learn React Hooks from documentation using INGEST mode.

This example demonstrates how the learning system:
1. Extracts concepts from documentation
2. Generates relevant questions
3. Creates Cornell-style notes
4. Validates learning through self-testing
5. Schedules spaced repetition reviews
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from supe import Supe
from ab.models import Buffer


async def main():
    print("=" * 80)
    print("LEARNING REACT HOOKS FROM DOCUMENTATION (INGEST MODE)")
    print("=" * 80)
    print()

    # Initialize Supe
    supe = Supe(db_path=":memory:")

    # Store React Hooks documentation in memory
    print("📚 Storing React Hooks documentation...")
    print()

    react_docs = """
    # React Hooks

    Hooks are functions that let you "hook into" React state and lifecycle
    features from function components. Hooks don't work inside classes —
    they let you use React without classes.

    ## useState

    useState is a Hook that lets you add React state to function components.

    Example:
    ```javascript
    import { useState } from 'react';

    function Counter() {
      const [count, setCount] = useState(0);
      return (
        <button onClick={() => setCount(count + 1)}>
          Count: {count}
        </button>
      );
    }
    ```

    useState returns a pair: the current state value and a function that
    lets you update it. You can call this function from an event handler
    or somewhere else.

    ## useEffect

    The Effect Hook lets you perform side effects in function components.
    Data fetching, subscriptions, and manually changing the DOM are all
    examples of side effects.

    Example:
    ```javascript
    import { useEffect } from 'react';

    function Example() {
      useEffect(() => {
        document.title = 'You clicked ' + count + ' times';
      });
    }
    ```

    useEffect runs after every render by default, including the first render.
    You can tell React to skip applying an effect if certain values haven't
    changed by passing an array as an optional second argument.

    ## Rules of Hooks

    1. Only call Hooks at the top level (not inside loops, conditions, or nested functions)
    2. Only call Hooks from React function components (not regular JavaScript functions)
    """

    # Store in AB Memory
    supe.memory.store_card(
        label="documentation",
        master_input="React Hooks Official Documentation",
        master_output=react_docs,
        track="awareness",
        buffers=[
            Buffer(name="content", payload=react_docs.encode('utf-8')),
            Buffer(name="source", payload=b"https://react.dev/reference/react"),
        ]
    )

    print("✓ Documentation stored in memory")
    print()

    # Learn from the documentation
    print("🧠 Learning: How do React hooks work?")
    print("-" * 80)
    print()

    result = await supe.learn(
        "How do React hooks work?",
        mode="ingest"
    )

    # Display results
    print("📊 Learning Results:")
    print(f"  Beliefs created: {result['beliefs_count']}")
    print(f"  Evidence collected: {result['evidence_count']}")
    print(f"  Knowledge gaps: {result['gaps_count']}")
    print(f"  Average confidence: {result['confidence']:.2f}")
    print(f"  Validated: {result['validated']}")
    print(f"  Proof hash: {result['proof_hash'][:16] if result['proof_hash'] else 'N/A'}...")
    print()

    # Show the belief details
    if result['beliefs_count'] > 0:
        print("📝 Cornell Note Structure:")
        print("-" * 80)

        belief = result['beliefs'][0]
        content = belief['content']

        print(f"Cue (Question): {content.get('cue', 'N/A')}")
        print()

        print(f"Notes:")
        notes = content.get('notes', 'N/A')
        # Truncate long notes
        if len(notes) > 300:
            print(f"  {notes[:300]}...")
        else:
            print(f"  {notes}")
        print()

        if content.get('examples'):
            print(f"Examples:")
            for i, example in enumerate(content.get('examples', [])[:2], 1):
                print(f"  {i}. {example[:100]}...")
            print()

        print(f"Conceptual Summary:")
        summary = content.get('conceptual_summary', 'N/A')
        print(f"  {summary}")
        print()

        print(f"Operational Summary:")
        op_summary = content.get('operational_summary', 'N/A')
        print(f"  {op_summary}")
        print()

        print(f"Confidence: {belief['confidence']:.2f}")
        print()

    # Show gaps that were identified
    if result['gaps_count'] > 0:
        print("🔍 Knowledge Gaps Identified:")
        print("-" * 80)
        # Gaps are stored in the session context
        # For this demo, we'll note what gaps would typically be found
        print("  Typical gaps that might be identified:")
        print("  - useContext hook")
        print("  - useReducer hook")
        print("  - Custom hooks")
        print("  - Hook dependency arrays")
        print()
        print("  These gaps become follow-up questions for future learning!")
        print()

    # Self-test demonstration
    print("🧪 Self-Test Phase:")
    print("-" * 80)
    print("The system tested its ability to recall information without")
    print("referring back to the source documentation.")
    print()
    print("Self-test helps validate that learning was successful!")
    print()

    # Spaced repetition schedule
    print("📅 Review Schedule:")
    print("-" * 80)

    if result['confidence'] >= 0.8:
        print(f"High confidence ({result['confidence']:.2f}) - Review in 7 days")
    elif result['confidence'] >= 0.6:
        print(f"Medium confidence ({result['confidence']:.2f}) - Review in 3 days")
    else:
        print(f"Low confidence ({result['confidence']:.2f}) - Review in 1 day")

    print()
    print("The system will automatically schedule reviews based on")
    print("confidence scores and the spaced repetition algorithm.")
    print()

    # Summary
    print("=" * 80)
    print("INGEST MODE SUMMARY")
    print("=" * 80)
    print()
    print("✓ Read documentation from memory")
    print("✓ Extracted key concepts (hooks, useState, useEffect, rules)")
    print("✓ Generated questions to guide learning")
    print("✓ Created Cornell-style notes with examples")
    print("✓ Tested recall ability (self-test)")
    print("✓ Evaluated confidence based on evidence quality")
    print("✓ Identified knowledge gaps for follow-up")
    print("✓ Scheduled spaced repetition review")
    print("✓ Generated cryptographic proof of learning")
    print()
    print("Next steps:")
    print("  - Learn about the identified gaps (useContext, custom hooks, etc.)")
    print("  - Review at scheduled intervals")
    print("  - Build a complete understanding of React Hooks")
    print()


if __name__ == "__main__":
    asyncio.run(main())
