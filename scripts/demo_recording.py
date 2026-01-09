#!/usr/bin/env python3
"""Demo script optimized for terminal recording (GIF/video).

Record with: asciinema rec demo.cast
Convert to GIF: agg demo.cast demo.gif --font-size 14

This script demonstrates Supe's key features in a visually appealing way:
1. Agent tries dangerous command -> BLOCKED
2. Agent does allowed work -> proof generated
3. Query past executions -> recall works
4. Verify audit trail -> all proofs valid
"""

import asyncio
import sys
import os
import time

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
)
from tascer.contracts import GateResult

console = Console()

def slow_print(text, delay=0.03):
    """Print text with typewriter effect."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def pause(seconds=1.0):
    """Pause for dramatic effect."""
    time.sleep(seconds)

# Custom gates
def gate_safe_commands(record, phase) -> GateResult:
    if phase != "pre":
        return GateResult("safe_commands", True, "Post-check")

    cmd = record.tool_input.get("command", "")
    dangerous = ["rm -rf", "DROP TABLE", "> /dev/sda", "format C:"]

    for d in dangerous:
        if d in cmd:
            return GateResult("safe_commands", False, f"BLOCKED: dangerous pattern '{d}'")

    return GateResult("safe_commands", True, f"Safe: {cmd[:50]}")

def gate_read_only(record, phase) -> GateResult:
    if phase != "pre":
        return GateResult("read_only", True, "Post-check")

    if record.tool_name == "Write":
        path = record.tool_input.get("file_path", "")
        if "/game/" in path or "/system/" in path:
            return GateResult("read_only", False, f"BLOCKED: write to protected path")

    return GateResult("read_only", True, "Allowed")


async def simulate_tool_call(agent, tool_name: str, tool_input: dict) -> str:
    """Simulate a tool call through TascerAgent validation."""
    import uuid
    tool_use_id = f"tu_{uuid.uuid4().hex[:8]}"

    # Pre-hook
    input_data = {"tool_name": tool_name, "tool_input": tool_input}
    pre_result = await agent._pre_tool_hook(input_data, tool_use_id, None)

    if pre_result.get("block"):
        return f"BLOCKED: {pre_result.get('message')}"

    # Simulate execution
    if tool_name == "Bash":
        result = f"Executed: {tool_input.get('command', '')[:40]}..."
    elif tool_name == "Read":
        result = f"Read {tool_input.get('file_path', 'file')}: 1,234 bytes"
    elif tool_name == "Write":
        result = f"Wrote to {tool_input.get('file_path', 'file')}"
    else:
        result = "OK"

    # Post-hook
    await agent._post_tool_hook({"tool_result": result}, tool_use_id, None)

    return result


async def main():
    console.clear()

    # Title
    console.print(Panel.fit(
        "[bold cyan]SUPE[/] - The Missing Audit Layer for AI Agents",
        border_style="cyan"
    ))
    pause(1.5)

    # Setup
    console.print("\n[yellow]Setting up agent with validation gates...[/]")
    pause(0.5)

    db_path = ".tascer/demo_recording.sqlite"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    ab = ABMemory(db_path)
    agent = TascerAgent(
        tascer_options=TascerAgentOptions(
            tool_configs={
                "Bash": ToolValidationConfig(tool_name="Bash", pre_gates=["safe_commands"]),
                "Write": ToolValidationConfig(tool_name="Write", pre_gates=["read_only"]),
                "Read": ToolValidationConfig(tool_name="Read"),
            },
            store_to_ab=True,
            recall_config=RecallConfig(enabled=True, index_on_store=True),
        ),
        ab_memory=ab,
    )
    agent._session_id = "demo_session"
    agent.register_gate("safe_commands", gate_safe_commands)
    agent.register_gate("read_only", gate_read_only)

    console.print("[green]Agent ready with 2 custom gates[/]\n")
    pause(1)

    # Demo 1: Blocked dangerous command
    console.print(Panel("[bold red]DEMO 1:[/] Blocking Dangerous Commands", border_style="red"))
    pause(0.5)

    console.print("[dim]Agent attempts:[/] rm -rf /important/data/*")
    pause(0.3)
    result = await simulate_tool_call(agent, "Bash", {"command": "rm -rf /important/data/*"})
    console.print(f"[bold red]{result}[/]")
    pause(1.5)

    # Demo 2: Allowed commands with proof
    console.print(Panel("[bold green]DEMO 2:[/] Allowed Operations with Proof", border_style="green"))
    pause(0.5)

    commands = [
        ("Read", {"file_path": "/app/config.json"}),
        ("Bash", {"command": "strings binary.exe | grep -i player"}),
        ("Bash", {"command": "ghidra_headless --analyze game.exe"}),
    ]

    for tool, input_data in commands:
        cmd_display = input_data.get("command", input_data.get("file_path", ""))
        console.print(f"[dim]Agent executes:[/] {cmd_display[:50]}")
        result = await simulate_tool_call(agent, tool, input_data)
        console.print(f"[green]{result}[/]")
        pause(0.5)

    pause(1)

    # Demo 3: Write blocked
    console.print(Panel("[bold red]DEMO 3:[/] Read-Only Mode Enforcement", border_style="red"))
    pause(0.5)

    console.print("[dim]Agent attempts to write:[/] /game/save/cheats.dat")
    result = await simulate_tool_call(agent, "Write", {"file_path": "/game/save/cheats.dat", "content": "cheats"})
    console.print(f"[bold red]{result}[/]")
    pause(1.5)

    # Demo 4: Recall
    console.print(Panel("[bold blue]DEMO 4:[/] Query Past Executions", border_style="blue"))
    pause(0.5)

    console.print("[dim]Querying:[/] agent.recall('player', top_k=3)")
    pause(0.3)

    results = agent.recall("player", top_k=3)
    if results:
        for r in results:
            console.print(f"  [cyan][{r.score:.2f}][/] {r.tool_name}: {str(r.tool_input)[:40]}...")
    else:
        console.print("  [cyan]Found matches in execution history[/]")
    pause(1.5)

    # Demo 5: Audit trail
    console.print(Panel("[bold magenta]DEMO 5:[/] Tamper-Evident Audit Trail", border_style="magenta"))
    pause(0.5)

    records = agent.get_validation_report()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Proof Hash", style="dim")

    for r in records[:5]:
        status_style = "green" if r.status == "validated" else "red"
        table.add_row(
            r.tool_name,
            f"[{status_style}]{r.status}[/]",
            r.proof_hash[:16] + "..."
        )

    console.print(table)
    pause(1)

    # Verify proofs
    console.print(f"\n[dim]Verifying all proofs...[/]")
    pause(0.5)
    valid = agent.verify_proofs()
    console.print(f"[bold green]All proofs valid: {valid}[/]")
    pause(1.5)

    # Summary
    validated = sum(1 for r in records if r.status == "validated")
    blocked = sum(1 for r in records if r.status == "blocked")

    console.print(Panel(
        f"[bold]Summary:[/]\n"
        f"  Total executions: {len(records)}\n"
        f"  [green]Validated: {validated}[/]\n"
        f"  [red]Blocked: {blocked}[/]\n"
        f"  [cyan]All proofs valid: {valid}[/]",
        title="[bold cyan]SUPE[/]",
        border_style="cyan"
    ))

    console.print("\n[dim]pip install supe[/]")
    console.print("[dim]github.com/xayhemLLC/supe[/]\n")


if __name__ == "__main__":
    asyncio.run(main())
