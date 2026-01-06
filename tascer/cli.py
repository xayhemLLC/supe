#!/usr/bin/env python3
"""Tasc CLI - Command-line interface for Tasc.

Usage:
    tascer run <command>           Run a command with safety checks
    tascer check <command>         Check if a command is safe (dry run)
    tascer checkpoint <name>       Create a checkpoint
    tascer rollback                Rollback to last checkpoint
    tascer sandbox enter           Enter sandbox mode
    tascer sandbox exit [--commit] Exit sandbox (discard or commit)
    tascer capture <url>           Capture browser screenshot
    tascer plugins                 List available plugins
    tascer metrics                 Show current metrics
    tascer benchmark               Run capability benchmarks
    tascer audit <run_id>          Export audit report
    tascer plan <goal>             Generate a TascPlan using Claude
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime


def cmd_run(args):
    """Run a command with Tasc safety checks."""
    from tascer.overlord.legality import check_action_legality
    from tascer.primitives import run_and_observe
    
    command = " ".join(args.cmd)
    
    # Check legality first
    result = check_action_legality(
        action_id="terminal.run",
        inputs={"command": command},
        permissions={"terminal"},
        has_checkpoint=args.force,
    )
    
    if not result.is_legal:
        print(f"🚫 BLOCKED: {result.violations[0]}")
        if not args.force:
            print("   Use --force to override (not recommended)")
            return 1
        print("   Proceeding anyway due to --force flag...")
    
    # Execute
    print(f"▶️  Running: {command}")
    output = run_and_observe(command, shell=True, timeout_seconds=args.timeout)
    
    print(f"\n📤 Exit code: {output.exit_code}")
    if output.stdout:
        print(f"📝 Output:\n{output.stdout}")
    if output.stderr:
        print(f"⚠️  Stderr:\n{output.stderr}")
    
    return output.exit_code


def cmd_check(args):
    """Check if a command is safe (dry run)."""
    from tascer.overlord.legality import check_action_legality
    
    command = " ".join(args.cmd)
    
    result = check_action_legality(
        action_id="terminal.run",
        inputs={"command": command},
        permissions={"terminal"},
        has_checkpoint=True,
    )
    
    if result.is_legal:
        print(f"✅ SAFE: {command}")
        if result.warnings:
            print(f"   ⚠️  Warnings: {', '.join(result.warnings)}")
        return 0
    else:
        print(f"🚫 BLOCKED: {command}")
        for v in result.violations:
            print(f"   • {v}")
        return 1


def cmd_checkpoint(args):
    """Create a checkpoint."""
    from tascer.checkpoint import CheckpointManager
    
    cwd = os.getcwd()
    run_id = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    mgr = CheckpointManager(
        run_id=run_id,
        root_dir=cwd,
        output_dir=os.path.join(cwd, ".tascer"),
    )
    
    os.makedirs(os.path.join(cwd, ".tascer"), exist_ok=True)
    
    cp = mgr.create(args.name or "CLI checkpoint")
    
    print(f"✅ Checkpoint created: {cp.checkpoint_id}")
    print(f"   Files tracked: {len(cp.file_snapshot)}")
    print(f"   Description: {args.name or 'CLI checkpoint'}")
    
    # Save checkpoint ID for rollback
    with open(os.path.join(cwd, ".tascer", "last_checkpoint"), "w") as f:
        json.dump({"checkpoint_id": cp.checkpoint_id, "run_id": run_id}, f)
    
    return 0


def cmd_rollback(args):
    """Rollback to last checkpoint."""
    from tascer.checkpoint import CheckpointManager
    
    cwd = os.getcwd()
    checkpoint_file = os.path.join(cwd, ".tascer", "last_checkpoint")
    
    if not os.path.exists(checkpoint_file):
        print("❌ No checkpoint found. Create one first with: tascer checkpoint")
        return 1
    
    with open(checkpoint_file) as f:
        data = json.load(f)
    
    mgr = CheckpointManager(
        run_id=data["run_id"],
        root_dir=cwd,
        output_dir=os.path.join(cwd, ".tascer"),
    )
    
    # Load checkpoints
    # Note: In a full implementation, we'd persist and reload checkpoints
    print(f"⏪ Rolling back to checkpoint: {data['checkpoint_id']}")
    print("   (Note: Full rollback requires checkpoint persistence)")
    
    return 0


def cmd_sandbox_enter(args):
    """Enter sandbox mode."""
    from tascer.primitives.sandbox import sandbox_enter
    
    cwd = os.getcwd()
    result = sandbox_enter(cwd, "CLI sandbox session")
    
    if result.success:
        print(f"🏖️  Entered sandbox mode")
        print(f"   Sandbox ID: {result.sandbox_id}")
        print(f"   Method: {result.isolation_method}")
        print(f"   Working dir: {result.sandbox_dir}")
        print()
        print("   Changes are isolated. Exit with:")
        print("   - tascer sandbox exit         (discard changes)")
        print("   - tascer sandbox exit --commit (apply changes)")
        
        # Save sandbox info
        os.makedirs(os.path.join(cwd, ".tascer"), exist_ok=True)
        with open(os.path.join(cwd, ".tascer", "sandbox"), "w") as f:
            json.dump({"sandbox_id": result.sandbox_id, "sandbox_dir": result.sandbox_dir}, f)
    else:
        print(f"❌ Failed to enter sandbox: {result.error}")
        return 1
    
    return 0


def cmd_sandbox_exit(args):
    """Exit sandbox mode."""
    from tascer.primitives.sandbox import sandbox_exit
    
    action = "commit" if args.commit else "discard"
    result = sandbox_exit(action)
    
    if result.success:
        if action == "commit":
            print(f"✅ Sandbox changes committed")
            print(f"   Files affected: {len(result.files_affected)}")
        else:
            print(f"🗑️  Sandbox changes discarded")
    else:
        print(f"❌ Failed to exit sandbox: {result.error}")
        return 1
    
    return 0


def cmd_capture(args):
    """Capture browser screenshot."""
    try:
        from tascer.primitives.browser import browser_capture, browser_close
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return 1
    
    print(f"📸 Capturing: {args.url}")
    
    state = browser_capture(
        url=args.url,
        capture_screenshot=True,
        capture_dom=args.dom,
        screenshot_dir=args.output or ".",
    )
    
    browser_close()
    
    print(f"✅ Captured!")
    print(f"   Title: {state.title}")
    print(f"   Screenshot: {state.screenshot_path}")
    if state.dom_snapshot:
        print(f"   DOM: {len(state.dom_snapshot)} chars")
    
    return 0


def cmd_plugins(args):
    """List available plugins."""
    from tascer.plugins.discord_plugin import DiscordPlugin
    from tascer.plugins.mcp_plugin import MCPPlugin
    from tascer.plugins.slack_plugin import SlackPlugin
    from tascer.plugins.github_plugin import GitHubPlugin
    from tascer.plugins.webhook_plugin import WebhookPlugin
    from tascer.plugins.metrics_plugin import MetricsPlugin
    
    plugins = [
        DiscordPlugin(),
        MCPPlugin(),
        SlackPlugin(),
        GitHubPlugin(),
        WebhookPlugin(),
        MetricsPlugin(),
    ]
    
    print("📦 Tasc Plugins")
    print("=" * 50)
    
    for p in plugins:
        info = p.info
        ctx = p.get_context()
        configured = ctx.get("configured", ctx.get("available", "?"))
        
        status = "✅" if configured else "⚪"
        print(f"\n{status} {info.name} v{info.version}")
        print(f"   {info.description}")
        print(f"   Capabilities: {', '.join(info.capabilities)}")
    
    print()
    return 0


def cmd_metrics(args):
    """Show current metrics."""
    from tascer.plugins.metrics_plugin import MetricsPlugin
    
    m = MetricsPlugin()
    print("📊 Tasc Metrics")
    print("=" * 50)
    print(m.get_metrics_text())
    
    return 0


def cmd_benchmark(args):
    """Run capability benchmarks."""
    from tascer.benchmarks.core import CORE_BENCHMARKS, run_benchmark
    
    print("🧪 Tasc Benchmarks")
    print("=" * 50)
    
    for bench in CORE_BENCHMARKS.benchmarks:
        results, stats = run_benchmark(bench, reps=args.repetitions)
        status = "✅" if stats.success_rate == 1.0 else "❌"
        print(f"{status} {bench.name}: {stats.success_rate:.0%} ({stats.mean_duration_ms:.1f}ms)")
    
    print()
    return 0


def cmd_audit(args):
    """Export audit report."""
    from tascer.ledgers import LedgerStorage
    from tascer.audit import export_to_markdown
    
    output_dir = args.output or "."
    
    # Create a sample storage for demo
    storage = LedgerStorage(run_id=args.run_id, output_dir=output_dir)
    storage.exe.record_narrative(f"Audit report for {args.run_id}")
    
    path = export_to_markdown(
        storage=storage,
        output_dir=output_dir,
        hypothesis=args.hypothesis or "Tasc run",
    )
    
    print(f"📝 Audit report exported: {path}")
    return 0


def cmd_plan(args):
    """Generate a TascPlan using Claude."""
    try:
        from tascer import generate_plan
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Install anthropic: pip install anthropic")
        return 1

    goal = " ".join(args.goal)

    print(f"🤖 Generating plan with Claude...")
    print(f"📋 Goal: {goal}\n")

    try:
        # Generate plan
        result = generate_plan(
            goal=goal,
            context=args.context or "",
            constraints=args.constraint or [],
            max_tascs=args.max_tascs,
            require_approval=not args.no_approval,
            temperature=args.temperature,
        )

        # Display results
        print(f"✅ Plan generated: {result.plan.title}")
        print(f"📊 Confidence: {result.confidence:.0%}")
        if result.reasoning:
            print(f"💭 Reasoning: {result.reasoning}\n")

        print(f"📋 Tascs ({len(result.plan.tascs)}):")
        for i, tasc in enumerate(result.plan.tascs, 1):
            deps = f" [after: {', '.join(tasc.dependencies)}]" if tasc.dependencies else ""
            print(f"  {i}. {tasc.title}{deps}")
            if args.verbose and tasc.testing_instructions:
                print(f"     Test: {tasc.testing_instructions}")

        # Save plan if requested
        if args.save:
            from tascer import save_plan
            plan_file = save_plan(result.plan, output_dir=args.output or ".tascer/plans")
            print(f"\n💾 Plan saved: {plan_file}")
            print(f"   Plan ID: {result.plan.id}")
            print(f"\n📝 To execute: tascer execute {result.plan.id}")

        # Show JSON output if requested
        if args.json:
            plan_dict = {
                "title": result.plan.title,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "tascs": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "testing_instructions": t.testing_instructions,
                        "dependencies": t.dependencies,
                    }
                    for t in result.plan.tascs
                ],
            }
            print(f"\n{json.dumps(plan_dict, indent=2)}")

        return 0

    except Exception as e:
        print(f"❌ Error generating plan: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Tasc - Task Automation and Safety Certification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # run
    run_parser = subparsers.add_parser("run", help="Run a command with safety checks")
    run_parser.add_argument("cmd", nargs="+", help="Command to run")
    run_parser.add_argument("--force", action="store_true", help="Override safety checks")
    run_parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    
    # check
    check_parser = subparsers.add_parser("check", help="Check if a command is safe")
    check_parser.add_argument("cmd", nargs="+", help="Command to check")
    
    # checkpoint
    cp_parser = subparsers.add_parser("checkpoint", help="Create a checkpoint")
    cp_parser.add_argument("name", nargs="?", help="Checkpoint description")
    
    # rollback
    subparsers.add_parser("rollback", help="Rollback to last checkpoint")
    
    # sandbox
    sandbox_parser = subparsers.add_parser("sandbox", help="Sandbox mode")
    sandbox_sub = sandbox_parser.add_subparsers(dest="sandbox_command")
    sandbox_sub.add_parser("enter", help="Enter sandbox mode")
    exit_parser = sandbox_sub.add_parser("exit", help="Exit sandbox mode")
    exit_parser.add_argument("--commit", action="store_true", help="Commit changes")
    
    # capture
    capture_parser = subparsers.add_parser("capture", help="Capture browser screenshot")
    capture_parser.add_argument("url", help="URL to capture")
    capture_parser.add_argument("--output", "-o", help="Output directory")
    capture_parser.add_argument("--dom", action="store_true", help="Also capture DOM")
    
    # plugins
    subparsers.add_parser("plugins", help="List available plugins")
    
    # metrics
    subparsers.add_parser("metrics", help="Show current metrics")
    
    # benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    bench_parser.add_argument("--repetitions", "-r", type=int, default=3, help="Repetitions")
    
    # audit
    audit_parser = subparsers.add_parser("audit", help="Export audit report")
    audit_parser.add_argument("run_id", help="Run ID for the report")
    audit_parser.add_argument("--output", "-o", help="Output directory")
    audit_parser.add_argument("--hypothesis", help="Hypothesis description")

    # plan
    plan_parser = subparsers.add_parser("plan", help="Generate a TascPlan using Claude")
    plan_parser.add_argument("goal", nargs="+", help="Goal description")
    plan_parser.add_argument("--context", "-c", help="Additional context")
    plan_parser.add_argument("--constraint", action="append", help="Constraints (can specify multiple times)")
    plan_parser.add_argument("--max-tascs", type=int, default=10, help="Maximum number of tascs")
    plan_parser.add_argument("--no-approval", action="store_true", help="Skip approval gate")
    plan_parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for Claude (0.0-1.0)")
    plan_parser.add_argument("--save", action="store_true", help="Save plan to file")
    plan_parser.add_argument("--output", "-o", help="Output directory for saved plan")
    plan_parser.add_argument("--json", action="store_true", help="Output as JSON")
    plan_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        "run": cmd_run,
        "check": cmd_check,
        "checkpoint": cmd_checkpoint,
        "rollback": cmd_rollback,
        "capture": cmd_capture,
        "plugins": cmd_plugins,
        "metrics": cmd_metrics,
        "benchmark": cmd_benchmark,
        "audit": cmd_audit,
        "plan": cmd_plan,
    }
    
    if args.command == "sandbox":
        if args.sandbox_command == "enter":
            return cmd_sandbox_enter(args)
        elif args.sandbox_command == "exit":
            return cmd_sandbox_exit(args)
        else:
            sandbox_parser.print_help()
            return 0
    
    if args.command in commands:
        return commands[args.command](args)
    
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
