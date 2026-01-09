#!/usr/bin/env python3
"""Test Tascer Agent SDK integration with AB Memory.

This script demonstrates:
1. TascerAgent with AB Memory storage
2. Execution records stored as Cards with Buffers
3. Proof verification
4. Querying stored execution history

Run: python scripts/test_tascer_agent.py
"""

import asyncio
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ab import ABMemory, Card, Buffer
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    ToolExecutionRecord,
)
from tascer.contracts import GateResult


async def simulate_tool_execution(agent: TascerAgent, tool_name: str, tool_input: dict, tool_output: any):
    """Simulate a tool execution through the hooks (without real SDK)."""
    import uuid

    tool_use_id = f"tu_{uuid.uuid4().hex[:8]}"

    # Simulate pre-hook
    input_data = {"tool_name": tool_name, "tool_input": tool_input}
    pre_result = await agent._pre_tool_hook(input_data, tool_use_id, None)

    if pre_result.get("block"):
        print(f"  BLOCKED: {pre_result.get('message')}")
        return

    # Simulate post-hook
    result_data = {"tool_result": tool_output}
    await agent._post_tool_hook(result_data, tool_use_id, None)


async def main():
    print("=" * 60)
    print("Tascer Agent SDK Integration Test")
    print("=" * 60)

    # Create AB Memory instance
    db_path = ".tascer/test_agent_memory.sqlite"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Remove old test DB
    if os.path.exists(db_path):
        os.remove(db_path)

    ab = ABMemory(db_path)
    print(f"\n1. Created AB Memory: {db_path}")

    # Create TascerAgent with AB Memory
    agent = TascerAgent(
        tascer_options=TascerAgentOptions(
            tool_configs={
                "Read": ToolValidationConfig(tool_name="Read"),
                "Edit": ToolValidationConfig(
                    tool_name="Edit",
                    pre_gates=["always_pass"],
                    post_gates=["always_pass"],
                ),
                "Bash": ToolValidationConfig(
                    tool_name="Bash",
                    post_gates=["exit_code_zero"],
                ),
                "Dangerous": ToolValidationConfig(
                    tool_name="Dangerous",
                    pre_gates=["always_block"],
                ),
            },
            capture_git_state=True,
            store_to_ab=True,
        ),
        ab_memory=ab,
    )
    agent._session_id = "test_session_001"
    print("2. Created TascerAgent with AB Memory integration")

    # Simulate tool executions
    print("\n3. Simulating tool executions...")

    # Read file
    print("\n   [Read] Reading config.py...")
    await simulate_tool_execution(
        agent,
        "Read",
        {"file_path": "/app/config.py"},
        "DEBUG = True\nPORT = 8080",
    )

    # Edit file
    print("   [Edit] Editing auth.py...")
    await simulate_tool_execution(
        agent,
        "Edit",
        {"file_path": "/app/auth.py", "old_string": "pass", "new_string": "return True"},
        "File edited successfully",
    )

    # Run bash command (success)
    print("   [Bash] Running tests...")
    await simulate_tool_execution(
        agent,
        "Bash",
        {"command": "pytest tests/"},
        {"exit_code": 0, "stdout": "5 passed in 0.3s"},
    )

    # Run bash command (failure)
    print("   [Bash] Running lint (will fail)...")
    await simulate_tool_execution(
        agent,
        "Bash",
        {"command": "ruff check ."},
        {"exit_code": 1, "stderr": "Found 3 errors"},
    )

    # Try dangerous tool (will be blocked)
    print("   [Dangerous] Attempting dangerous operation...")
    await simulate_tool_execution(
        agent,
        "Dangerous",
        {"action": "delete_all"},
        None,
    )

    # Get validation report
    print("\n4. Validation Report:")
    print("-" * 40)
    for record in agent.get_validation_report():
        status_icon = "✓" if record.status == "validated" else "✗" if record.status == "blocked" else "!"
        print(f"   {status_icon} {record.tool_name:12} | {record.status:10} | proof: {record.proof_hash[:12]}...")

    # Verify proofs
    print("\n5. Proof Verification:")
    proofs_valid = agent.verify_proofs()
    print(f"   All proofs valid: {proofs_valid}")

    # Check AB Memory storage
    print("\n6. AB Memory Storage:")
    print("-" * 40)

    # Query cards by label pattern
    cursor = ab.conn.cursor()
    cursor.execute("SELECT id, label, track, master_input FROM cards WHERE label LIKE 'tascer:%'")
    cards = cursor.fetchall()

    print(f"   Stored {len(cards)} execution cards:")
    for card in cards:
        print(f"   - [{card['id']}] {card['label']} (track: {card['track']})")

    # Show buffers for first card
    if cards:
        first_card_id = cards[0]["id"]
        cursor.execute("SELECT name, headers FROM buffers WHERE card_id = ?", (first_card_id,))
        buffers = cursor.fetchall()
        print(f"\n   Buffers in card {first_card_id}:")
        for buf in buffers:
            headers = json.loads(buf["headers"]) if buf["headers"] else {}
            print(f"     - {buf['name']}: {headers}")

    # Export report
    report_path = ".tascer/validation_report.json"
    agent.export_report(report_path)
    print(f"\n7. Exported validation report to: {report_path}")

    # Tamper detection demo
    print("\n8. Tamper Detection Demo:")
    print("-" * 40)

    # Get a record and tamper with it
    records = agent.get_validation_report()
    if records:
        original_input = records[0].tool_input.copy()
        records[0].tool_input = {"tampered": True}

        tampered_valid = agent.verify_proofs()
        print(f"   After tampering: proofs_valid = {tampered_valid}")

        # Restore
        records[0].tool_input = original_input
        restored_valid = agent.verify_proofs()
        print(f"   After restoring: proofs_valid = {restored_valid}")

    # Recall demonstration
    print("\n9. Recall Demo:")
    print("-" * 40)

    # Recall by keyword
    print("\n   Searching for 'config'...")
    results = agent.recall("config", top_k=3)
    if results:
        for r in results:
            print(f"   - [{r.score:.2f}] {r.tool_name}: {r.tool_input}")
    else:
        print("   (No results - recall requires ab.recall module)")

    # Recall by tool
    print("\n   Getting all Read executions...")
    read_results = agent.recall_tool("Read", top_k=5)
    if read_results:
        for r in read_results:
            print(f"   - {r.tool_name}: {r.tool_input.get('file_path', 'N/A')}")
    else:
        print("   (No results)")

    # Recall similar
    print("\n   Finding similar to '/app/auth.py'...")
    similar = agent.recall_similar({"file_path": "/app/auth.py"}, top_k=3)
    if similar:
        for r in similar:
            print(f"   - [{r.score:.2f}] {r.tool_name}: {r.tool_input}")
    else:
        print("   (No results)")

    # Get context for upcoming tool
    print("\n   Getting context for Read('/app/settings.py')...")
    context = agent.get_context_for("Read", {"file_path": "/app/settings.py"})
    if context:
        for c in context:
            print(f"   - Previous: {c['tool_name']} @ {c['timestamp'][:19] if c['timestamp'] else 'N/A'}")
    else:
        print("   (No relevant context)")

    # Session recall
    print("\n   Recalling current session history...")
    session_history = agent.recall_session()
    if session_history:
        print(f"   Found {len(session_history)} executions in session")
    else:
        print("   (No session history)")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
