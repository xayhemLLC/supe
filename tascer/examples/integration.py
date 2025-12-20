#!/usr/bin/env python3
"""Tasc Integration Example - Comprehensive demonstration.

This example demonstrates the full Tasc architecture:
1. Action Registry - Loading and querying actions
2. Checkpoint - Safe exploration with rollback
3. Ledgers - Recording intent (Exe) and reality (Moments)
4. Overlord - Decision-making with stop conditions
5. Audit - Exporting to Markdown

Run with: python -m tascer.examples.integration
"""

import os
import sys
import tempfile

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tascer.action_registry import get_registry, get_action
from tascer.checkpoint import CheckpointManager
from tascer.ledgers import LedgerStorage, MomentsLedger, ExeLedger
from tascer.overlord.decision import (
    StopConditionState,
    should_stop,
    create_continue_decision,
)
from tascer.overlord.legality import check_action_legality
from tascer.audit import export_to_markdown
from tascer.primitives import run_and_observe, snapshot_directory


def main():
    """Run the integration example."""
    print("=" * 60)
    print("Tasc Integration Example")
    print("=" * 60)
    print()
    
    # Create temp directory for example
    with tempfile.TemporaryDirectory() as tmpdir:
        run_id = "demo_run_001"
        
        # =========================================================
        # Step 1: Initialize Action Registry
        # =========================================================
        print("1. Loading Action Registry...")
        registry = get_registry()
        registry.load()
        
        all_actions = registry.list_all()
        observations = registry.list_observations()
        mutations = registry.list_mutations()
        
        print(f"   ✓ Loaded {len(all_actions)} actions")
        print(f"   - Observations: {len(observations)}")
        print(f"   - Mutations: {len(mutations)}")
        print()
        
        # =========================================================
        # Step 2: Initialize Ledgers
        # =========================================================
        print("2. Initializing Ledgers...")
        storage = LedgerStorage(run_id=run_id, output_dir=tmpdir)
        
        # Record initial context
        storage.moments.record_context({
            "cwd": tmpdir,
            "purpose": "Integration demo",
        })
        storage.exe.record_narrative("Starting integration demonstration")
        
        print(f"   ✓ MomentsLedger: {len(storage.moments)} entries")
        print(f"   ✓ ExeLedger: {len(storage.exe)} entries")
        print()
        
        # =========================================================
        # Step 3: Create Checkpoint for Safe Exploration
        # =========================================================
        print("3. Creating Checkpoint...")
        checkpoint_mgr = CheckpointManager(
            run_id=run_id,
            root_dir=tmpdir,
            output_dir=tmpdir,
        )
        
        # Create a test file
        test_file = os.path.join(tmpdir, "example.txt")
        with open(test_file, "w") as f:
            f.write("Original content\n")
        
        checkpoint = checkpoint_mgr.create("Before exploration")
        print(f"   ✓ Checkpoint ID: {checkpoint.checkpoint_id}")
        print(f"   ✓ Files tracked: {len(checkpoint.file_snapshot)}")
        print()
        
        # =========================================================
        # Step 4: Check Action Legality
        # =========================================================
        print("4. Checking Action Legality...")
        
        # Check a safe action
        result = check_action_legality(
            action_id="terminal.run",
            inputs={"command": "echo hello"},
            permissions={"terminal"},
            has_checkpoint=True,
        )
        print(f"   terminal.run 'echo hello': {'✓ Legal' if result.is_legal else '✗ Illegal'}")
        
        # Check a dangerous action
        result = check_action_legality(
            action_id="terminal.run",
            inputs={"command": "rm -rf /"},
            permissions={"terminal"},
            has_checkpoint=True,
        )
        print(f"   terminal.run 'rm -rf /': {'✓ Legal' if result.is_legal else '✗ Blocked'}")
        if result.violations:
            print(f"     Reason: {result.violations[0]}")
        print()
        
        # =========================================================
        # Step 5: Execute Actions with Ledger Recording
        # =========================================================
        print("5. Executing Actions...")
        
        # Action 1: Run terminal command
        action_id = "terminal.run"
        inputs = {"command": "echo 'Hello from Tasc!'"}
        
        # Record intent
        storage.exe.record_execution(action_id)
        storage.moments.record_action_start(action_id, inputs)
        
        # Execute
        result = run_and_observe(inputs["command"], shell=True)
        
        # Record result
        storage.moments.record_action_result(action_id, {
            "exit_code": result.exit_code,
            "stdout": result.stdout.strip(),
        })
        
        print(f"   ✓ {action_id}: exit_code={result.exit_code}")
        print(f"     Output: {result.stdout.strip()}")
        
        # Action 2: Modify file (mutation)
        with open(test_file, "w") as f:
            f.write("Modified content\n")
        
        storage.moments.record_action_result("file.write", {
            "path": "example.txt",
            "status": "modified",
        })
        print(f"   ✓ file.write: Modified example.txt")
        print()
        
        # =========================================================
        # Step 6: Evaluate Stop Conditions
        # =========================================================
        print("6. Evaluating Stop Conditions...")
        
        # Simulate state after actions
        state = StopConditionState(
            legal_actions={"terminal.run", "file.read"},
            actions_taken=2,
            max_actions=10,
            goal_achieved=False,
            recent_info_gains=[0.5, 0.4, 0.3],
        )
        
        decision = should_stop(state)
        if decision:
            print(f"   Decision: STOP ({decision.stop_reason.value})")
        else:
            print(f"   Decision: CONTINUE (no stop conditions triggered)")
        print()
        
        # =========================================================
        # Step 7: Demonstrate Rollback
        # =========================================================
        print("7. Demonstrating Rollback...")
        
        # Read current content
        with open(test_file, "r") as f:
            current = f.read().strip()
        print(f"   Current content: '{current}'")
        
        # Rollback
        rollback_result = checkpoint_mgr.rollback()
        
        # Read restored content
        with open(test_file, "r") as f:
            restored = f.read().strip()
        print(f"   Restored content: '{restored}'")
        print(f"   ✓ Files restored: {len(rollback_result['files_restored'])}")
        print()
        
        # =========================================================
        # Step 8: Save Ledgers
        # =========================================================
        print("8. Saving Ledgers...")
        
        # Mark stop in exe ledger
        from tascer.ledgers.exe import StopReason
        storage.exe.record_stop(StopReason.GOAL_ACHIEVED, "Demo complete")
        
        paths = storage.save()
        print(f"   ✓ Moments: {paths['moments']}")
        print(f"   ✓ Exe: {paths['exe']}")
        print(f"   Total moments: {len(storage.moments)}")
        print(f"   Total decisions: {len(storage.exe)}")
        print()
        
        # =========================================================
        # Step 9: Export to Markdown
        # =========================================================
        print("9. Exporting Audit Report...")
        
        audit_path = export_to_markdown(
            storage=storage,
            output_dir=tmpdir,
            hypothesis="Demonstrate Tasc architecture",
        )
        
        print(f"   ✓ Audit report: {audit_path}")
        
        # Show preview
        with open(audit_path, "r") as f:
            lines = f.readlines()[:15]
        print("   Preview:")
        for line in lines:
            print(f"   | {line.rstrip()}")
        print()
        
        # =========================================================
        # Summary
        # =========================================================
        print("=" * 60)
        print("Integration Example Complete!")
        print("=" * 60)
        print()
        print("Components Demonstrated:")
        print("  ✓ Action Registry - 32 actions loaded")
        print("  ✓ Checkpoint - Create and rollback")
        print("  ✓ Ledgers - Intent (Exe) and Reality (Moments)")
        print("  ✓ Overlord - Legality checks and stop conditions")
        print("  ✓ Audit - Markdown export")
        print()


if __name__ == "__main__":
    main()
