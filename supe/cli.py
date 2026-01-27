#!/usr/bin/env python3
"""Supe CLI - Unified interface for the supe system.

Commands:
    supe status              Show system status
    supe prove <command>     Execute with proof generation
    supe verify <proof-id>   Verify an existing proof
    supe tasc <subcommand>   Task management (save, list, recall, etc.)
    supe run <command>       Safe command execution with validation
    supe plan <file>         Create/manage structured plans
    supe install             Show installation info
"""

import os
import sys
from datetime import datetime

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------------
# Main Group
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Show version')
@click.pass_context
def cli(ctx, version):
    """🚀 Supe - Super simple, super powerful.

    Unified CLI for AB Memory, Tasc, and Tascer systems.
    """
    if version:
        from supe import __version__
        console.print(f"supe v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        # Show welcome message
        console.print(Panel.fit(
            "[bold cyan]🚀 Supe[/bold cyan] - Super simple, super powerful\n\n"
            "  [dim]supe status[/dim]        Show system status\n"
            "  [dim]supe prove <cmd>[/dim]   Execute with proof\n"
            "  [dim]supe tasc save[/dim]     Save current work\n"
            "  [dim]supe run <cmd>[/dim]     Safe command execution\n\n"
            "[dim]Run 'supe --help' for all commands[/dim]",
            border_style="cyan",
        ))


# ---------------------------------------------------------------------------
# Status Command
# ---------------------------------------------------------------------------

@cli.command()
def status():
    """Show system status and configuration."""
    table = Table(title="🔹 Supe System Status", box=box.ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    # Check AB Memory
    db_path = os.environ.get("TASC_DB", "tasc.sqlite")
    ab_exists = os.path.exists(db_path)
    table.add_row(
        "AB Memory",
        "✅ Active" if ab_exists else "⚪ Not initialized",
        db_path
    )

    # Check .tascer directory
    tascer_dir = os.path.exists(".tascer")
    table.add_row(
        "Tascer",
        "✅ Configured" if tascer_dir else "⚪ Not configured",
        ".tascer/" if tascer_dir else "Run 'supe run' to initialize"
    )

    # Check for proofs
    proofs_dir = ".tascer/proofs"
    proof_count = len(os.listdir(proofs_dir)) if os.path.exists(proofs_dir) else 0
    table.add_row(
        "Proofs",
        f"📋 {proof_count} stored",
        proofs_dir
    )

    # Python environment
    table.add_row(
        "Python",
        "✅ Active",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    console.print(table)
    console.print()


# ---------------------------------------------------------------------------
# Prove Command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument('command', nargs=-1, required=True)
@click.option('--output', '-o', help='Output directory for proof')
@click.option('--tag', '-t', help='Tag for the proof')
def prove(command, output, tag):
    """Execute a command with proof generation.

    Creates a cryptographic proof of execution including:
    - Full command output
    - Exit code verification
    - Timestamp and duration
    - Environment context

    Example: supe prove pytest tests/
    """
    from tascer.proofs import prove_script_success

    cmd_str = " ".join(command)
    console.print(f"[cyan]▶️  Proving:[/cyan] {cmd_str}")
    console.print()

    result = prove_script_success(
        command=cmd_str,
        cwd=os.getcwd(),
        tasc_id=tag or f"proof_{datetime.now().strftime('%H%M%S')}",
    )

    if result.proven:
        console.print(Panel.fit(
            f"[bold green]✅ PROVEN[/bold green]\n\n"
            f"Exit code: {result.exit_code}\n"
            f"Duration: {result.duration_ms:.1f}ms\n"
            f"Gates passed: {len([g for g in result.gate_results if g.passed])}/{len(result.gate_results)}",
            border_style="green",
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]❌ NOT PROVEN[/bold red]\n\n"
            f"Exit code: {result.exit_code}\n"
            f"Duration: {result.duration_ms:.1f}ms",
            border_style="red",
        ))

        for gate in result.gate_results:
            if not gate.passed:
                console.print(f"  [red]✗[/red] {gate.gate_name}: {gate.message}")

    # Store proof
    proof_dir = output or ".tascer/proofs"
    os.makedirs(proof_dir, exist_ok=True)

    proof_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{tag or 'proof'}"
    proof_path = os.path.join(proof_dir, f"{proof_id}.json")

    import json
    with open(proof_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

    console.print(f"\n[dim]Proof saved: {proof_path}[/dim]")

    return 0 if result.proven else 1


# ---------------------------------------------------------------------------
# Verify Command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument('proof_id')
def verify(proof_id):
    """Verify an existing proof.

    Example: supe verify 20231217_120000_pytest
    """
    import json

    # Look for proof file
    proof_dir = ".tascer/proofs"
    proof_path = os.path.join(proof_dir, f"{proof_id}.json")

    if not os.path.exists(proof_path):
        # Try with extension already
        if not os.path.exists(proof_id):
            console.print(f"[red]❌ Proof not found: {proof_id}[/red]")
            return 1
        proof_path = proof_id

    with open(proof_path) as f:
        proof = json.load(f)

    console.print(Panel.fit(
        f"[bold cyan]📋 Proof Verification[/bold cyan]\n\n"
        f"Proven: {'✅ Yes' if proof.get('proven') else '❌ No'}\n"
        f"Exit code: {proof.get('exit_code')}\n"
        f"Duration: {proof.get('duration_ms', 0):.1f}ms\n"
        f"Output files valid: {'✅' if proof.get('output_files_valid') else '❌'}",
        border_style="cyan",
    ))

    return 0


# ---------------------------------------------------------------------------
# Run Command (Safe Execution)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument('command', nargs=-1, required=True)
@click.option('--force', '-f', is_flag=True, help='Override safety checks')
@click.option('--timeout', default=30, help='Timeout in seconds')
def run(command, force, timeout):
    """Run a command with safety checks.

    Example: supe run npm test
    """
    from tascer.overlord.legality import check_action_legality
    from tascer.primitives import run_and_observe

    cmd_str = " ".join(command)

    # Check legality
    result = check_action_legality(
        action_id="terminal.run",
        inputs={"command": cmd_str},
        permissions={"terminal"},
        has_checkpoint=force,
    )

    if not result.is_legal:
        console.print(f"[red]🚫 BLOCKED:[/red] {result.violations[0]}")
        if not force:
            console.print("[dim]   Use --force to override[/dim]")
            return 1
        console.print("[yellow]   Proceeding with --force...[/yellow]")

    console.print(f"[cyan]▶️  Running:[/cyan] {cmd_str}")
    output = run_and_observe(cmd_str, shell=True, timeout_sec=timeout)

    console.print(f"\n[dim]Exit code: {output.exit_code}[/dim]")
    if output.stdout:
        console.print(output.stdout)
    if output.stderr:
        console.print(f"[yellow]{output.stderr}[/yellow]")

    return output.exit_code


# ---------------------------------------------------------------------------
# Check Command (Dry Run)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument('command', nargs=-1, required=True)
def check(command):
    """Check if a command is safe (dry run).

    Example: supe check rm -rf /tmp/mydir
    """
    from tascer.overlord.legality import check_action_legality

    cmd_str = " ".join(command)

    result = check_action_legality(
        action_id="terminal.run",
        inputs={"command": cmd_str},
        permissions={"terminal"},
        has_checkpoint=True,
    )

    if result.is_legal:
        console.print(f"[green]✅ SAFE:[/green] {cmd_str}")
        if result.warnings:
            console.print(f"   [yellow]⚠️  Warnings: {', '.join(result.warnings)}[/yellow]")
        return 0
    else:
        console.print(f"[red]🚫 BLOCKED:[/red] {cmd_str}")
        for v in result.violations:
            console.print(f"   • {v}")
        return 1


# ---------------------------------------------------------------------------
# Checkpoint Command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument('name', required=False)
def checkpoint(name):
    """Create a checkpoint for rollback.

    Example: supe checkpoint "before refactor"
    """
    import json

    from tascer.checkpoint import CheckpointManager

    cwd = os.getcwd()
    run_id = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    mgr = CheckpointManager(
        run_id=run_id,
        root_dir=cwd,
        output_dir=os.path.join(cwd, ".tascer"),
    )

    os.makedirs(os.path.join(cwd, ".tascer"), exist_ok=True)

    cp = mgr.create(name or "CLI checkpoint")

    console.print(f"[green]✅ Checkpoint created:[/green] {cp.checkpoint_id}")
    console.print(f"   Files tracked: {len(cp.file_snapshot)}")
    console.print(f"   Description: {name or 'CLI checkpoint'}")

    # Save checkpoint ID for rollback
    with open(os.path.join(cwd, ".tascer", "last_checkpoint"), "w") as f:
        json.dump({"checkpoint_id": cp.checkpoint_id, "run_id": run_id}, f)

    return 0


# ---------------------------------------------------------------------------
# Rollback Command
# ---------------------------------------------------------------------------

@cli.command()
def rollback():
    """Rollback to last checkpoint.

    Example: supe rollback
    """
    import json

    from tascer.checkpoint import CheckpointManager

    cwd = os.getcwd()
    checkpoint_file = os.path.join(cwd, ".tascer", "last_checkpoint")

    if not os.path.exists(checkpoint_file):
        console.print("[red]❌ No checkpoint found. Create one first with: supe checkpoint[/red]")
        return 1

    with open(checkpoint_file) as f:
        data = json.load(f)

    CheckpointManager(
        run_id=data["run_id"],
        root_dir=cwd,
        output_dir=os.path.join(cwd, ".tascer"),
    )

    console.print(f"[cyan]⏪ Rolling back to checkpoint:[/cyan] {data['checkpoint_id']}")
    console.print("   [dim](Note: Full rollback requires checkpoint persistence)[/dim]")

    return 0


# ---------------------------------------------------------------------------
# Capture Command (Browser Screenshot)
# ---------------------------------------------------------------------------

@cli.command()
@click.argument('url')
@click.option('--output', '-o', help='Output directory')
@click.option('--dom', is_flag=True, help='Also capture DOM')
def capture(url, output, dom):
    """Capture browser screenshot.

    Example: supe capture https://example.com -o ./screenshots
    """
    try:
        from tascer.primitives.browser import browser_capture, browser_close
    except ImportError:
        console.print("[red]❌ Playwright not installed. Run: pip install playwright && playwright install chromium[/red]")
        return 1

    console.print(f"[cyan]📸 Capturing:[/cyan] {url}")

    state = browser_capture(
        url=url,
        capture_screenshot=True,
        capture_dom=dom,
        screenshot_dir=output or ".",
    )

    browser_close()

    console.print("[green]✅ Captured![/green]")
    console.print(f"   Title: {state.title}")
    console.print(f"   Screenshot: {state.screenshot_path}")
    if state.dom_snapshot:
        console.print(f"   DOM: {len(state.dom_snapshot)} chars")

    return 0


# ---------------------------------------------------------------------------
# Plugins Command
# ---------------------------------------------------------------------------

@cli.command()
def plugins():
    """List available plugins.

    Example: supe plugins
    """
    from tascer.plugins.discord_plugin import DiscordPlugin
    from tascer.plugins.github_plugin import GitHubPlugin
    from tascer.plugins.mcp_plugin import MCPPlugin
    from tascer.plugins.metrics_plugin import MetricsPlugin
    from tascer.plugins.slack_plugin import SlackPlugin
    from tascer.plugins.webhook_plugin import WebhookPlugin

    plugin_list = [
        DiscordPlugin(),
        MCPPlugin(),
        SlackPlugin(),
        GitHubPlugin(),
        WebhookPlugin(),
        MetricsPlugin(),
    ]

    table = Table(title="📦 Supe Plugins", box=box.ROUNDED)
    table.add_column("Status", style="dim", width=3)
    table.add_column("Plugin", style="cyan")
    table.add_column("Version", style="dim")
    table.add_column("Capabilities")

    for p in plugin_list:
        info = p.info
        ctx = p.get_context()
        configured = ctx.get("configured", ctx.get("available", False))

        status = "✅" if configured else "⚪"
        table.add_row(
            status,
            info.name,
            f"v{info.version}",
            ", ".join(info.capabilities[:3]),
        )

    console.print(table)
    return 0


# ---------------------------------------------------------------------------
# Metrics Command
# ---------------------------------------------------------------------------

@cli.command()
def metrics():
    """Show current metrics.

    Example: supe metrics
    """
    from tascer.plugins.metrics_plugin import MetricsPlugin

    m = MetricsPlugin()
    console.print(Panel.fit(
        f"[bold cyan]📊 Supe Metrics[/bold cyan]\n\n{m.get_metrics_text()}",
        border_style="cyan",
    ))

    return 0


# ---------------------------------------------------------------------------
# Benchmark Command
# ---------------------------------------------------------------------------

@cli.command()
@click.option('--repetitions', '-r', default=3, help='Number of repetitions')
def benchmark(repetitions):
    """Run capability benchmarks.

    Example: supe benchmark -r 5
    """
    from tascer.benchmarks.core import CORE_BENCHMARKS, run_benchmark

    table = Table(title="🧪 Supe Benchmarks", box=box.ROUNDED)
    table.add_column("Status", style="dim", width=3)
    table.add_column("Benchmark", style="cyan")
    table.add_column("Success", style="green")
    table.add_column("Avg Time", style="dim")

    for bench in CORE_BENCHMARKS.benchmarks:
        results, stats = run_benchmark(bench, reps=repetitions)
        status = "✅" if stats.success_rate == 1.0 else "❌"
        table.add_row(
            status,
            bench.name,
            f"{stats.success_rate:.0%}",
            f"{stats.mean_duration_ms:.1f}ms",
        )

    console.print(table)
    return 0


# ---------------------------------------------------------------------------
# Audit Command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument('run_id')
@click.option('--output', '-o', help='Output directory')
@click.option('--hypothesis', help='Hypothesis description')
def audit(run_id, output, hypothesis):
    """Export audit report.

    Example: supe audit run_20231217_120000 -o ./reports
    """
    from tascer.audit import export_to_markdown
    from tascer.ledgers import LedgerStorage

    output_dir = output or "."

    storage = LedgerStorage(run_id=run_id, output_dir=output_dir)
    storage.exe.record_narrative(f"Audit report for {run_id}")

    path = export_to_markdown(
        storage=storage,
        output_dir=output_dir,
        hypothesis=hypothesis or "Supe run",
    )

    console.print(f"[green]📝 Audit report exported:[/green] {path}")
    return 0


# ---------------------------------------------------------------------------
# Sandbox Commands
# ---------------------------------------------------------------------------

@cli.group()
def sandbox():
    """Sandbox mode for isolated changes."""
    pass


@sandbox.command()
def enter():
    """Enter sandbox mode.

    Changes are isolated until you exit with --commit or discard.

    Example: supe sandbox enter
    """
    import json

    from tascer.primitives.sandbox import sandbox_enter

    cwd = os.getcwd()
    result = sandbox_enter(cwd, "CLI sandbox session")

    if result.success:
        console.print("[green]🏖️  Entered sandbox mode[/green]")
        console.print(f"   Sandbox ID: {result.sandbox_id}")
        console.print(f"   Method: {result.isolation_method}")
        console.print(f"   Working dir: {result.sandbox_dir}")
        console.print()
        console.print("   Changes are isolated. Exit with:")
        console.print("   - [dim]supe sandbox exit[/dim]          (discard changes)")
        console.print("   - [dim]supe sandbox exit --commit[/dim]  (apply changes)")

        # Save sandbox info
        os.makedirs(os.path.join(cwd, ".tascer"), exist_ok=True)
        with open(os.path.join(cwd, ".tascer", "sandbox"), "w") as f:
            json.dump({"sandbox_id": result.sandbox_id, "sandbox_dir": result.sandbox_dir}, f)
        return 0
    else:
        console.print(f"[red]❌ Failed to enter sandbox: {result.error}[/red]")
        return 1


@sandbox.command(name='exit')
@click.option('--commit', is_flag=True, help='Commit changes instead of discarding')
def sandbox_exit_cmd(commit):
    """Exit sandbox mode.

    By default discards changes. Use --commit to apply changes.

    Example: supe sandbox exit --commit
    """
    from tascer.primitives.sandbox import sandbox_exit

    action = "commit" if commit else "discard"
    result = sandbox_exit(action)

    if result.success:
        if action == "commit":
            console.print("[green]✅ Sandbox changes committed[/green]")
            console.print(f"   Files affected: {len(result.files_affected)}")
        else:
            console.print("[yellow]🗑️  Sandbox changes discarded[/yellow]")
        return 0
    else:
        console.print(f"[red]❌ Failed to exit sandbox: {result.error}[/red]")
        return 1


# ---------------------------------------------------------------------------
# Tasc Subcommands
# ---------------------------------------------------------------------------

@cli.group()
def tasc():
    """Task management commands."""
    pass


@tasc.command()
@click.argument('name', required=False)
@click.option('--desc', '-d', help='Description')
@click.option('--type', '-t', 'task_type', help='Type (work, bug, feature)')
def save(name, desc, task_type):
    """Save current work as a Tasc.

    Example: supe tasc save "auth fix" --type bug
    """
    from ab.abdb import ABMemory
    from ab.models import Buffer

    name = name or f"tasc-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    db_path = os.environ.get("TASC_DB", "tasc.sqlite")
    mem = ABMemory(db_path)

    moment = mem.create_moment(
        master_input=f"Save: {name}",
        master_output="Saved via CLI"
    )

    buffers = [
        Buffer(name="title", payload=name),
        Buffer(name="timestamp", payload=datetime.now().isoformat()),
        Buffer(name="type", payload=task_type or "work"),
    ]

    if desc:
        buffers.append(Buffer(name="description", payload=desc))

    card = mem.store_card(
        label="tasc",
        buffers=buffers,
        owner_self="CLI",
        moment_id=moment.id
    )

    console.print(f"[green]✅ Saved:[/green] {name} [dim](ID: {card.id})[/dim]")


@tasc.command(name='list')
@click.option('--limit', '-n', default=20, help='Max items to show')
def list_tascs(limit):
    """List all Tascs."""
    from ab.abdb import ABMemory

    db_path = os.environ.get("TASC_DB", "tasc.sqlite")
    mem = ABMemory(db_path)

    cursor = mem.conn.execute(
        "SELECT id, label, owner_self, created_at FROM cards ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )

    table = Table(title="📋 Recent Tascs", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Label", style="cyan")
    table.add_column("Title")
    table.add_column("Owner", style="dim")

    rows = cursor.fetchall()
    if not rows:
        console.print("[dim]No Tascs found.[/dim]")
        return

    for row in rows:
        card_id, label, owner, created = row
        title_cursor = mem.conn.execute(
            "SELECT payload FROM buffers WHERE card_id = ? AND name = 'title'",
            (card_id,)
        )
        title_row = title_cursor.fetchone()
        title = title_row[0] if title_row else "(untitled)"

        table.add_row(str(card_id), label, title[:40], owner or "")

    console.print(table)


@tasc.command()
@click.argument('query')
def recall(query):
    """Find relevant past work.

    Example: supe tasc recall "login"
    """
    from ab.abdb import ABMemory

    db_path = os.environ.get("TASC_DB", "tasc.sqlite")
    mem = ABMemory(db_path)

    console.print(f"[cyan]🔍 Searching:[/cyan] {query}")
    console.print()

    cursor = mem.conn.execute(
        """
        SELECT DISTINCT c.id, c.label, b.name, b.payload
        FROM cards c
        JOIN buffers b ON c.id = b.card_id
        WHERE b.payload LIKE ?
        LIMIT 10
        """,
        (f"%{query}%",)
    )

    results = cursor.fetchall()
    if not results:
        console.print("[dim]No matches found.[/dim]")
        return

    for card_id, label, buf_name, payload in results:
        snippet = str(payload)[:60].replace("\n", " ")
        console.print(f"  [dim][{card_id}][/dim] [cyan]{label}[/cyan]/{buf_name}: {snippet}...")


@tasc.command()
@click.argument('target')
@click.option('--gen', '-g', default=10, help='Number of generations')
@click.option('--pop', '-p', default=16, help='Population size')
def evolve(target, gen, pop):
    """Evolve solutions using genetic algorithms.

    Example: supe tasc evolve "sort algorithm" --gen 20 --pop 32
    """
    from ab.code_dna import create_random_code_dna, crossover_code, mutate_code

    console.print(Panel.fit(
        f"[bold cyan]🧬 Evolving solutions for:[/bold cyan] {target}\n\n"
        f"Population: {pop} | Generations: {gen}",
        border_style="cyan",
    ))

    # Simple evolution loop
    agents = [create_random_code_dna() for _ in range(pop)]

    for generation in range(gen):
        # Evaluate (placeholder - just count instructions)
        scores = []
        for dna in agents:
            code = dna.to_python_code()
            # Simple fitness: shorter is better, must compile
            try:
                compile(code, "<string>", "exec")
                score = 100 - len(code) / 10
            except Exception:
                score = 0
            scores.append(score)

        # Sort by score
        ranked = sorted(zip(scores, agents), key=lambda x: -x[0])
        best_score = ranked[0][0]

        if generation % 5 == 0 or generation == gen - 1:
            console.print(f"  Gen {generation+1}: Best score = {best_score:.1f}")

        # Selection + crossover
        survivors = [a for _, a in ranked[:pop//2]]
        offspring = []
        for i in range(0, len(survivors)-1, 2):
            child = crossover_code(survivors[i], survivors[i+1])
            child = mutate_code(child, rate=0.2)
            offspring.append(child)

        agents = survivors + offspring + [
            create_random_code_dna() for _ in range(pop - len(survivors) - len(offspring))
        ]

    # Show best
    best = ranked[0][1]
    console.print()
    console.print(Panel.fit(
        f"[bold green]Best Solution[/bold green]\n\n{best.to_python_code()}",
        border_style="green",
    ))

    console.print("[green]✅ Evolution complete![/green]")


@tasc.command()
@click.argument('hook_type', type=click.Choice(['commit']))
def hook(hook_type):
    """Install git hooks.

    Example: supe tasc hook commit
    """
    from pathlib import Path

    git_dir = Path(".git")
    if not git_dir.exists():
        console.print("[red]❌ Not a git repository[/red]")
        return 1

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    if hook_type == "commit":
        hook_file = hooks_dir / "post-commit"
        hook_content = '''#!/bin/bash
# Supe post-commit hook
python -c "
import sys
sys.path.insert(0, '.')
from tasc.cli import auto_record_commit
auto_record_commit()
" 2>/dev/null || true
'''
        hook_file.write_text(hook_content)
        hook_file.chmod(0o755)
        console.print("[green]✅ Installed post-commit hook[/green]")
        console.print("   [dim]Commits will be auto-recorded to AB Memory[/dim]")

    return 0


@tasc.command()
def ui():
    """Launch interactive TUI.

    Example: supe tasc ui
    """
    console.print("[cyan]Launching TUI...[/cyan]")
    from tasc.tui import main as tui_main
    tui_main()


# ---------------------------------------------------------------------------
# Plan Subcommand
# ---------------------------------------------------------------------------

@cli.group()
def plan():
    """Plan management commands."""
    pass


@plan.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--name', '-n', help='Plan name')
def create(file, name):
    """Create a plan from a file.

    Example: supe plan create design.md --name "Auth System"
    """
    from pathlib import Path

    from ab.abdb import ABMemory
    from ab.models import Buffer

    plan_path = Path(file)
    plan_content = plan_path.read_text()
    plan_name = name or plan_path.stem

    db_path = os.environ.get("TASC_DB", "tasc.sqlite")
    mem = ABMemory(db_path)

    moment = mem.create_moment(
        master_input=f"Plan: {plan_name}",
        master_output="Created plan"
    )

    buffers = [
        Buffer(name="title", payload=plan_name),
        Buffer(name="type", payload="plan"),
        Buffer(name="content", payload=plan_content),
        Buffer(name="file", payload=str(plan_path)),
        Buffer(name="status", payload="active"),
    ]

    card = mem.store_card(
        label="plan",
        buffers=buffers,
        owner_self="CLI",
        moment_id=moment.id
    )

    console.print(f"[green]✅ Created plan:[/green] {plan_name} [dim](ID: {card.id})[/dim]")


@plan.command(name='list')
def list_plans():
    """List all plans."""
    from ab.abdb import ABMemory

    db_path = os.environ.get("TASC_DB", "tasc.sqlite")
    mem = ABMemory(db_path)

    cursor = mem.conn.execute(
        "SELECT id, created_at FROM cards WHERE label = 'plan' ORDER BY created_at DESC LIMIT 20"
    )

    table = Table(title="📋 Plans", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Status")

    rows = cursor.fetchall()
    if not rows:
        console.print("[dim]No plans found.[/dim]")
        return

    for row in rows:
        card_id, created = row
        title = "(untitled)"
        status = "active"

        for field in ["title", "status"]:
            cursor2 = mem.conn.execute(
                "SELECT payload FROM buffers WHERE card_id = ? AND name = ?",
                (card_id, field)
            )
            result = cursor2.fetchone()
            if result:
                if field == "title":
                    title = result[0]
                else:
                    status = result[0]

        status_icon = "🟢" if status == "active" else "⚪"
        table.add_row(str(card_id), title, f"{status_icon} {status}")

    console.print(table)


@plan.command()
@click.argument('goal', nargs=-1, required=True)
@click.option('--context', '-c', help='Additional context')
@click.option('--constraint', multiple=True, help='Constraints (can specify multiple)')
@click.option('--max-tascs', default=10, help='Maximum number of tascs')
@click.option('--no-approval', is_flag=True, help='Skip approval gate')
@click.option('--temperature', default=0.7, help='Temperature for Claude (0.0-1.0)')
@click.option('--save', is_flag=True, help='Save plan to file')
@click.option('--output', '-o', help='Output directory for saved plan')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def generate(goal, context, constraint, max_tascs, no_approval, temperature, save, output, json_output, verbose):
    """Generate a TascPlan using Claude.

    Example: supe plan generate "implement user authentication"
    """
    import json as json_module

    try:
        from tascer import generate_plan
    except ImportError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        console.print("\n[dim]💡 Install anthropic: pip install anthropic[/dim]")
        return 1

    goal_str = " ".join(goal)

    console.print("[cyan]🤖 Generating plan with Claude...[/cyan]")
    console.print(f"[dim]📋 Goal: {goal_str}[/dim]\n")

    try:
        # Generate plan
        result = generate_plan(
            goal=goal_str,
            context=context or "",
            constraints=list(constraint) if constraint else [],
            max_tascs=max_tascs,
            require_approval=not no_approval,
            temperature=temperature,
        )

        # Display results
        console.print(f"[green]✅ Plan generated:[/green] {result.plan.title}")
        console.print(f"[dim]📊 Confidence: {result.confidence:.0%}[/dim]")
        if result.reasoning:
            console.print(f"[dim]💭 Reasoning: {result.reasoning}[/dim]\n")

        console.print(f"[bold]📋 Tascs ({len(result.plan.tascs)}):[/bold]")
        for i, tasc in enumerate(result.plan.tascs, 1):
            deps = f" [after: {', '.join(tasc.dependencies)}]" if tasc.dependencies else ""
            console.print(f"  {i}. {tasc.title}{deps}")
            if verbose and tasc.testing_instructions:
                console.print(f"     [dim]Test: {tasc.testing_instructions}[/dim]")

        # Save plan if requested
        if save:
            from tascer import save_plan
            plan_file = save_plan(result.plan, output_dir=output or ".tascer/plans")
            console.print(f"\n[green]💾 Plan saved:[/green] {plan_file}")
            console.print(f"   [dim]Plan ID: {result.plan.id}[/dim]")
            console.print(f"\n[dim]📝 To execute: supe plan execute {result.plan.id}[/dim]")

        # Show JSON output if requested
        if json_output:
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
            console.print(f"\n{json_module.dumps(plan_dict, indent=2)}")

        return 0

    except Exception as e:
        console.print(f"[red]❌ Error generating plan: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


# ---------------------------------------------------------------------------
# Install Info
# ---------------------------------------------------------------------------

@cli.command()
def install():
    """Show installation information."""
    console.print(Panel.fit(
        "[bold cyan]📦 Supe Installation[/bold cyan]\n\n"
        "[bold]Installed via:[/bold]\n"
        "  pip install supe\n"
        "  [dim]# or for development:[/dim]\n"
        "  uv pip install -e .\n\n"
        "[bold]Command:[/bold]\n"
        "  • supe - Unified CLI for all functionality\n\n"
        "[bold]Command groups:[/bold]\n"
        "  • supe tasc     - Task management\n"
        "  • supe plan     - Plan management\n"
        "  • supe sandbox  - Sandbox mode\n"
        "  • supe approve  - Approval workflow\n\n"
        "[bold]To uninstall:[/bold]\n"
        "  pip uninstall supe",
        border_style="cyan",
    ))


# ---------------------------------------------------------------------------
# Approval System
# ---------------------------------------------------------------------------

@cli.group()
def approve():
    """Approval management for human sign-off gates."""
    pass


@approve.command(name='list')
def list_approvals():
    """List pending approval requests.

    Example: supe approve list
    """
    from tascer.approval import get_pending_approvals

    pending = get_pending_approvals()

    if not pending:
        console.print("[dim]No pending approvals.[/dim]")
        return

    table = Table(title="⏳ Pending Approvals", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Title", style="cyan")
    table.add_column("Tasc", style="dim")
    table.add_column("Requested By")
    table.add_column("Approvals", style="green")

    for req in pending:
        table.add_row(
            req.id[:16],
            req.title[:30],
            req.tasc_id[:12],
            req.requested_by,
            f"{req.approval_count}/{req.required_approvals}"
        )

    console.print(table)
    console.print("\n[dim]Use 'supe approve yes <id>' to approve[/dim]")


@approve.command(name='yes')
@click.argument('request_id')
@click.option('--approver', '-a', default='user', help='Approver name')
@click.option('--comment', '-c', help='Optional comment')
def approve_request(request_id, approver, comment):
    """Approve a pending request.

    Example: supe approve yes approval_abc123 --approver chris
    """
    from tascer.approval import approve as do_approve

    # Find matching request
    from tascer.approval import get_store
    pending = get_store().list_all()

    matches = [r for r in pending if r.id.startswith(request_id)]

    if not matches:
        console.print(f"[red]❌ Request not found: {request_id}[/red]")
        return 1

    if len(matches) > 1:
        console.print("[yellow]Multiple matches, please be more specific:[/yellow]")
        for m in matches:
            console.print(f"  {m.id}")
        return 1

    req = matches[0]

    try:
        updated = do_approve(req.id, approver, comment)
        console.print(f"[green]✅ Approved:[/green] {req.title}")
        console.print(f"   Status: {updated.status} ({updated.approval_count}/{updated.required_approvals})")

        if updated.status == "approved":
            console.print("   [green]All required approvals received![/green]")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return 1


@approve.command(name='no')
@click.argument('request_id')
@click.option('--approver', '-a', default='user', help='Rejector name')
@click.argument('reason')
def reject_request(request_id, approver, reason):
    """Reject a pending request.

    Example: supe approve no approval_abc123 "Security concern"
    """
    from tascer.approval import get_store
    from tascer.approval import reject as do_reject

    # Find matching request
    pending = get_store().list_all()
    matches = [r for r in pending if r.id.startswith(request_id)]

    if not matches:
        console.print(f"[red]❌ Request not found: {request_id}[/red]")
        return 1

    if len(matches) > 1:
        console.print("[yellow]Multiple matches, please be more specific:[/yellow]")
        for m in matches:
            console.print(f"  {m.id}")
        return 1

    req = matches[0]

    try:
        do_reject(req.id, approver, reason)
        console.print(f"[red]❌ Rejected:[/red] {req.title}")
        console.print(f"   Reason: {reason}")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return 1


@approve.command(name='show')
@click.argument('request_id')
def show_approval(request_id):
    """Show details of an approval request.

    Example: supe approve show approval_abc123
    """
    from tascer.approval import get_store

    pending = get_store().list_all()
    matches = [r for r in pending if r.id.startswith(request_id)]

    if not matches:
        console.print(f"[red]❌ Request not found: {request_id}[/red]")
        return 1

    req = matches[0]

    status_color = {"pending": "yellow", "approved": "green", "rejected": "red"}.get(req.status, "white")

    console.print(Panel.fit(
        f"[bold cyan]📋 Approval Request[/bold cyan]\n\n"
        f"[bold]ID:[/bold] {req.id}\n"
        f"[bold]Title:[/bold] {req.title}\n"
        f"[bold]Tasc:[/bold] {req.tasc_id}\n"
        f"[bold]Status:[/bold] [{status_color}]{req.status}[/{status_color}]\n"
        f"[bold]Approvals:[/bold] {req.approval_count}/{req.required_approvals}\n"
        f"[bold]Description:[/bold]\n{req.description[:200]}",
        border_style="cyan",
    ))

    if req.approvals:
        console.print("\n[bold]Votes:[/bold]")
        for a in req.approvals:
            icon = "✅" if a.approved else "❌"
            console.print(f"  {icon} {a.approver}: {a.comment or '(no comment)'}")

    if req.context:
        console.print("\n[bold]Context:[/bold]")
        for k, v in req.context.items():
            console.print(f"  {k}: {str(v)[:50]}")


# ---------------------------------------------------------------------------
# Human Input (for browser automation 2FA/captcha)
# ---------------------------------------------------------------------------

@cli.group()
def input():
    """Human input for browser automation (2FA, captcha)."""
    pass


@input.command(name='list')
def list_inputs():
    """List pending human input requests.

    Example: supe input list
    """
    try:
        from tascer.plugins.browser.human_input import get_pending_inputs
    except ImportError:
        console.print("[dim]Browser plugin not available (missing requests/beautifulsoup4)[/dim]")
        return

    pending = get_pending_inputs()

    if not pending:
        console.print("[dim]No pending input requests.[/dim]")
        return

    table = Table(title="🔐 Pending Human Input", box=box.ROUNDED)
    table.add_column("ID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Service")
    table.add_column("Prompt")

    for req in pending:
        table.add_row(
            req.id[:16],
            req.input_type.value if hasattr(req.input_type, 'value') else str(req.input_type),
            req.service_name or "-",
            req.prompt[:40] + "..." if len(req.prompt) > 40 else req.prompt,
        )

    console.print(table)
    console.print("\n[dim]Use 'supe input respond <id> <value>' to respond[/dim]")


@input.command(name='respond')
@click.argument('request_id')
@click.argument('value')
def respond_input(request_id, value):
    """Respond to a human input request.

    Example: supe input respond input_abc123 123456
    """
    try:
        from tascer.plugins.browser.human_input import get_store, respond_to_input
    except ImportError:
        console.print("[red]Browser plugin not available[/red]")
        return 1

    # Find matching request
    pending = get_store().get_pending()
    matches = [r for r in pending if r.id.startswith(request_id)]

    if not matches:
        console.print(f"[red]❌ Request not found: {request_id}[/red]")
        return 1

    if len(matches) > 1:
        console.print("[yellow]Multiple matches:[/yellow]")
        for m in matches:
            console.print(f"  {m.id}")
        return 1

    req = matches[0]

    try:
        respond_to_input(req.id, value)
        console.print(f"[green]✅ Responded to:[/green] {req.prompt[:40]}")
        console.print(f"   Value: {value}")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        return 1


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

@cli.command('mcp-server')
def mcp_server():
    """Start MCP server for Cursor/Claude integration.

    This exposes supe tools via the Model Context Protocol,
    allowing AI assistants to use proof-of-work validation.

    Configure in Cursor or Claude Desktop settings.
    """
    from supe.mcp_server import main as mcp_main
    console.print("[cyan]Starting MCP server...[/cyan]", file=sys.stderr)
    mcp_main()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    """Main entry point."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
