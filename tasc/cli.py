#!/usr/bin/env python3
"""Tasc CLI: Super simple, super powerful.

Commands:
    t save <name>           Save current work as a Tasc
    t plan <file>           Add a plan to track
    t evolve <target>       Evolve solutions for a problem
    t list                  List all Tascs
    t recall <query>        Find relevant past work
    t status                Show current energy/state
    t hook <type>           Install git hooks
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ab.abdb import ABMemory
from ab.models import Buffer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_memory() -> ABMemory:
    """Get or create the AB memory database."""
    db_path = os.environ.get("TASC_DB", "tasc.sqlite")
    return ABMemory(db_path)


def print_header(text: str):
    """Print a styled header."""
    print(f"\n🔹 {text}")
    print("─" * 40)


def print_success(text: str):
    print(f"✅ {text}")


def print_error(text: str):
    print(f"❌ {text}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_save(args):
    """Save current work as a Tasc."""
    name = args.name or f"tasc-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    mem = get_memory()
    
    # Create moment for this save
    moment = mem.create_moment(
        master_input=f"Save: {name}",
        master_output="Saved via CLI"
    )
    
    # Gather context
    buffers = [
        Buffer(name="title", payload=name),
        Buffer(name="timestamp", payload=datetime.now().isoformat()),
        Buffer(name="type", payload=args.type or "work"),
    ]
    
    # Add description if provided
    if args.desc:
        buffers.append(Buffer(name="description", payload=args.desc))
    
    # Add files if provided
    if args.files:
        buffers.append(Buffer(name="files", payload=",".join(args.files)))
    
    # Store the card
    card = mem.store_card(
        label="tasc",
        buffers=buffers,
        owner_self="CLI",
        moment_id=moment.id
    )
    
    print_success(f"Saved Tasc: {name} (ID: {card.id})")


def cmd_plan(args):
    """Add a plan to track."""
    plan_file = Path(args.file)
    
    if not plan_file.exists():
        print_error(f"Plan file not found: {plan_file}")
        return
    
    plan_content = plan_file.read_text()
    plan_name = args.name or plan_file.stem
    
    mem = get_memory()
    moment = mem.create_moment(
        master_input=f"Plan: {plan_name}",
        master_output="Added plan"
    )
    
    buffers = [
        Buffer(name="title", payload=plan_name),
        Buffer(name="type", payload="plan"),
        Buffer(name="content", payload=plan_content),
        Buffer(name="file", payload=str(plan_file)),
        Buffer(name="status", payload="active"),
    ]
    
    card = mem.store_card(
        label="plan",
        buffers=buffers,
        owner_self="CLI",
        moment_id=moment.id
    )
    
    print_success(f"Added plan: {plan_name} (ID: {card.id})")


def cmd_evolve(args):
    """Evolve solutions for a problem."""
    from ab.code_dna import create_random_code_dna, mutate_code, crossover_code
    
    target = args.target
    generations = args.gen or 10
    population = args.pop or 16
    
    print_header(f"Evolving solutions for: {target}")
    print(f"Population: {population} | Generations: {generations}")
    
    # Simple evolution loop
    agents = [create_random_code_dna() for _ in range(population)]
    
    for gen in range(generations):
        # Evaluate (placeholder - just count instructions)
        scores = []
        for dna in agents:
            code = dna.to_python_code()
            # Simple fitness: shorter is better, must compile
            try:
                compile(code, "<string>", "exec")
                score = 100 - len(code) / 10
            except:
                score = 0
            scores.append(score)
        
        # Sort by score
        ranked = sorted(zip(scores, agents), key=lambda x: -x[0])
        best_score = ranked[0][0]
        
        if gen % 5 == 0 or gen == generations - 1:
            print(f"  Gen {gen+1}: Best score = {best_score:.1f}")
        
        # Selection + crossover
        survivors = [a for _, a in ranked[:population//2]]
        offspring = []
        for i in range(0, len(survivors)-1, 2):
            child = crossover_code(survivors[i], survivors[i+1])
            child = mutate_code(child, rate=0.2)
            offspring.append(child)
        
        agents = survivors + offspring + [create_random_code_dna() for _ in range(population - len(survivors) - len(offspring))]
    
    # Show best
    best = ranked[0][1]
    print_header("Best Solution")
    print(best.to_python_code())
    
    print_success(f"Evolution complete!")


def cmd_list(args):
    """List all Tascs."""
    mem = get_memory()
    
    # Query recent cards
    conn = mem.conn
    cursor = conn.execute(
        "SELECT id, label, owner_self, created_at FROM cards ORDER BY created_at DESC LIMIT ?",
        (args.limit or 20,)
    )
    
    print_header("Recent Tascs")
    
    rows = cursor.fetchall()
    if not rows:
        print("  No Tascs found.")
        return
    
    for row in rows:
        card_id, label, owner, created = row
        # Get title buffer if exists
        title_cursor = conn.execute(
            "SELECT payload FROM buffers WHERE card_id = ? AND name = 'title'",
            (card_id,)
        )
        title_row = title_cursor.fetchone()
        title = title_row[0] if title_row else "(untitled)"
        
        print(f"  [{card_id:3}] {label:8} | {title[:30]:30} | {owner}")


def cmd_recall(args):
    """Find relevant past work."""
    query = args.query
    
    mem = get_memory()
    
    print_header(f"Searching for: {query}")
    
    # Simple text search in buffers
    conn = mem.conn
    cursor = conn.execute(
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
        print("  No matches found.")
        return
    
    for card_id, label, buf_name, payload in results:
        snippet = payload[:60].replace("\n", " ")
        print(f"  [{card_id}] {label}/{buf_name}: {snippet}...")


def cmd_status(args):
    """Show current energy/state."""
    try:
        from ab.energy import EnergyNetwork
        from ab.genesis import Genesis
        
        print_header("System Status")
        
        # Quick status
        genesis = Genesis()
        print(genesis.personal.status())
        
    except Exception as e:
        print_error(f"Could not load status: {e}")


def cmd_hook(args):
    """Install git hooks."""
    hook_type = args.type
    
    git_dir = Path(".git")
    if not git_dir.exists():
        print_error("Not a git repository")
        return
    
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    if hook_type == "commit":
        hook_file = hooks_dir / "post-commit"
        hook_content = """#!/bin/bash
# Tasc post-commit hook
python -c "
import sys
sys.path.insert(0, '.')
from tasc.cli import auto_record_commit
auto_record_commit()
" 2>/dev/null || true
"""
        hook_file.write_text(hook_content)
        hook_file.chmod(0o755)
        print_success(f"Installed post-commit hook")
    
    else:
        print_error(f"Unknown hook type: {hook_type}")


def cmd_ui(args):
    """Launch interactive TUI."""
    from tasc.tui import main as tui_main
    tui_main()


def auto_record_commit():
    """Called by git hook to record commits."""
    import subprocess
    
    try:
        # Get last commit info
        msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"]).decode().strip()
        files = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1"]).decode().strip()
        
        mem = get_memory()
        moment = mem.create_moment(
            master_input=f"Commit: {msg[:50]}",
            master_output="Auto-recorded"
        )
        
        buffers = [
            Buffer(name="type", payload="commit"),
            Buffer(name="message", payload=msg),
            Buffer(name="files", payload=files),
            Buffer(name="timestamp", payload=datetime.now().isoformat()),
        ]
        
        mem.store_card(
            label="commit",
            buffers=buffers,
            owner_self="GitHook",
            moment_id=moment.id
        )
    except:
        pass  # Silently fail in hook


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="tasc",
        description="🔹 Tasc: Super simple, super powerful.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  t save "auth fix"          Save current work
  t plan design.md           Track a plan
  t evolve auth.py           Evolve solutions
  t list                     Show all tascs  
  t recall "login"           Find past work
  t hook commit              Install git hook
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # save
    p_save = subparsers.add_parser("save", aliases=["s"], help="Save work as Tasc")
    p_save.add_argument("name", nargs="?", help="Name for the Tasc")
    p_save.add_argument("-d", "--desc", help="Description")
    p_save.add_argument("-t", "--type", help="Type (work, bug, feature)")
    p_save.add_argument("-f", "--files", nargs="+", help="Related files")
    
    # plan
    p_plan = subparsers.add_parser("plan", aliases=["p"], help="Add a plan")
    p_plan.add_argument("file", help="Plan file (markdown)")
    p_plan.add_argument("-n", "--name", help="Plan name")
    
    # evolve
    p_evolve = subparsers.add_parser("evolve", aliases=["e"], help="Evolve solutions")
    p_evolve.add_argument("target", help="Target file or problem")
    p_evolve.add_argument("-g", "--gen", type=int, help="Generations (default 10)")
    p_evolve.add_argument("-p", "--pop", type=int, help="Population (default 16)")
    
    # list
    p_list = subparsers.add_parser("list", aliases=["ls", "l"], help="List Tascs")
    p_list.add_argument("-n", "--limit", type=int, help="Max items")
    
    # recall
    p_recall = subparsers.add_parser("recall", aliases=["r", "find", "f"], help="Find past work")
    p_recall.add_argument("query", help="Search query")
    
    # status
    p_status = subparsers.add_parser("status", aliases=["st"], help="Show status")
    
    # hook
    p_hook = subparsers.add_parser("hook", help="Install hooks")
    p_hook.add_argument("type", choices=["commit"], help="Hook type")
    
    # ui
    p_ui = subparsers.add_parser("ui", help="Launch interactive TUI")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Dispatch
    commands = {
        "save": cmd_save, "s": cmd_save,
        "plan": cmd_plan, "p": cmd_plan,
        "evolve": cmd_evolve, "e": cmd_evolve,
        "list": cmd_list, "ls": cmd_list, "l": cmd_list,
        "recall": cmd_recall, "r": cmd_recall, "find": cmd_recall, "f": cmd_recall,
        "status": cmd_status, "st": cmd_status,
        "hook": cmd_hook,
        "ui": cmd_ui,
    }
    
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
