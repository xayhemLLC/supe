#!/usr/bin/env python3
"""Tasc TUI: Beautiful ASCII Terminal User Interface.

Features:
- Dashboard with Tascs, energy, evolution
- Interactive navigation
- Live evolution visualization
- Self-evolution display
"""

import sys
import os
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ab.abdb import ABMemory
from ab.energy import EnergyNetwork
from ab.genesis import Genesis, PersonalCoder, MetaEvolution


# ---------------------------------------------------------------------------
# ASCII Art Components
# ---------------------------------------------------------------------------

LOGO = """
╔════════════════════════════════════════════════════════════════════════╗
║  ████████╗ █████╗ ███████╗ ██████╗                                     ║
║  ╚══██╔══╝██╔══██╗██╔════╝██╔════╝   🧬 Self-Evolving Intelligence     ║
║     ██║   ███████║███████╗██║                                          ║
║     ██║   ██╔══██║╚════██║██║        ⚡ Energy: {energy:>6.1f}                   ║
║     ██║   ██║  ██║███████║╚██████╗   📊 Tascs:  {tascs:>6}                   ║
║     ╚═╝   ╚═╝  ╚═╝╚══════╝ ╚═════╝   🔄 Gen:    {gen:>6}                   ║
╚════════════════════════════════════════════════════════════════════════╝
"""

MENU = """
┌─────────────────────────────────────────────────────────────────────────┐
│  [1] 📋 List Tascs    [2] 💾 Save New    [3] 🔍 Search    [4] ⚡ Energy  │
│  [5] 🧬 Evolve        [6] 🤖 Genesis     [7] 📊 Stats     [q] Quit      │
└─────────────────────────────────────────────────────────────────────────┘
"""


def box(title: str, content: str, width: int = 70) -> str:
    """Create an ASCII box around content."""
    lines = content.split('\n')
    result = [f"┌─ {title} " + "─" * (width - len(title) - 4) + "┐"]
    for line in lines:
        padded = line[:width-4].ljust(width-4)
        result.append(f"│ {padded} │")
    result.append("└" + "─" * (width-2) + "┘")
    return '\n'.join(result)


def progress_bar(value: float, max_val: float, width: int = 30, fill: str = "█", empty: str = "░") -> str:
    """Create an ASCII progress bar."""
    ratio = min(1.0, value / max(0.01, max_val))
    filled = int(ratio * width)
    return f"[{fill * filled}{empty * (width - filled)}] {value:.1f}/{max_val:.0f}"


def energy_graph(energies: dict, width: int = 40) -> str:
    """Create an ASCII energy distribution graph."""
    if not energies:
        return "  No energy data"
    
    max_e = max(energies.values()) or 1
    lines = []
    for name, energy in sorted(energies.items()):
        bar_len = int((energy / max_e) * width)
        bar = "█" * bar_len + "░" * (width - bar_len)
        lines.append(f"  {name:12} │{bar}│ {energy:.1f}")
    return '\n'.join(lines)


def evolution_animation(generation: int, fitness: float, frame: int = 0) -> str:
    """Create animated evolution visualization."""
    dna_frames = ["🧬", "🔬", "⚗️", "🧪"]
    waves = ["∿∿∿", "∿∿∿∿", "∿∿∿∿∿", "∿∿∿∿"]
    
    icon = dna_frames[frame % len(dna_frames)]
    wave = waves[frame % len(waves)]
    
    return f"""
    {icon} Generation {generation}
    
    Fitness: {progress_bar(fitness, 100)}
    
    {wave} Evolution in progress {wave}
    """


# ---------------------------------------------------------------------------
# TUI Application
# ---------------------------------------------------------------------------

class TascTUI:
    """Interactive Terminal User Interface for Tasc."""
    
    def __init__(self):
        self.running = True
        self.db_path = os.environ.get("TASC_DB", "tasc.sqlite")
        self.genesis = Genesis()
        self.current_view = "dashboard"
        
    def get_memory(self) -> ABMemory:
        return ABMemory(self.db_path)
    
    def clear(self):
        """Clear the terminal."""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def get_stats(self) -> dict:
        """Get current system stats."""
        mem = self.get_memory()
        conn = mem.conn
        
        # Count tascs
        cursor = conn.execute("SELECT COUNT(*) FROM cards")
        tasc_count = cursor.fetchone()[0]
        
        return {
            "tascs": tasc_count,
            "energy": sum(self.genesis.personal.get_style_profile().values()),
            "gen": self.genesis.meta.generation,
        }
    
    def render_dashboard(self):
        """Render the main dashboard."""
        stats = self.get_stats()
        print(LOGO.format(**stats))
        print(MENU)
    
    def render_tascs(self):
        """Render Tasc list."""
        mem = self.get_memory()
        conn = mem.conn
        
        cursor = conn.execute(
            "SELECT id, label, owner_self, created_at FROM cards ORDER BY created_at DESC LIMIT 10"
        )
        rows = cursor.fetchall()
        
        content = ""
        for row in rows:
            card_id, label, owner, created = row
            # Get title
            title_cursor = conn.execute(
                "SELECT payload FROM buffers WHERE card_id = ? AND name = 'title'",
                (card_id,)
            )
            title_row = title_cursor.fetchone()
            title = title_row[0][:35] if title_row else "(untitled)"
            content += f"  [{card_id:3}] {label:8} │ {title:35} │ {owner}\n"
        
        if not content:
            content = "  No Tascs yet. Press [2] to save one!"
        
        print(box("📋 Recent Tascs", content.rstrip()))
    
    def render_energy(self):
        """Render energy distribution."""
        energies = self.genesis.personal.get_style_profile()
        graph = energy_graph(energies)
        print(box("⚡ Energy Distribution", graph))
        
        # Show meta-evolution operators
        op_info = ""
        for op in self.genesis.meta.operators:
            scores = self.genesis.meta.operator_scores.get(op.name, [])
            avg = sum(scores[-5:]) / len(scores[-5:]) if scores else 0
            op_info += f"  {op.name:15} rate={op.rate:.2f} power={op.power:.2f} → avg={avg:.1f}\n"
        
        print(box("🔄 Meta-Evolution Operators", op_info.rstrip()))
    
    def render_evolution(self, generations: int = 10):
        """Run and visualize evolution."""
        problems = [(2, 4), (3, 9), (5, 10), (0, 0)]
        
        print(box("🧬 Evolution Engine", "Starting evolution..."))
        print()
        
        for gen in range(generations):
            # Run evolution cycle
            problem = random.choice(problems)
            result = self.genesis.run_evolution_cycle(problem)
            
            # Clear and re-render
            self.clear()
            
            anim = evolution_animation(result['cycle'], result['fitness'], gen)
            print(box("🧬 Evolution Engine", anim))
            
            # Show live stats
            stats = f"""
  Problem: f({problem[0]}) = {problem[1]}
  Result:  {result['result']:.2f}
  Error:   {result['error']:.2f}
  
  Operator: {result['operator']}
  Approach: {result['approach'][:50]}
            """
            print(box("📊 Current Cycle", stats.strip()))
            
            time.sleep(0.3)
        
        print("\n  ✅ Evolution complete!")
    
    def render_genesis(self):
        """Render full Genesis status."""
        status = self.genesis.full_status()
        # Split and box each section
        for line in status.split('\n'):
            print(line)
    
    def save_new_tasc(self):
        """Interactively save a new Tasc."""
        print(box("💾 Save New Tasc", ""))
        name = input("  Name: ").strip()
        if not name:
            print("  Cancelled.")
            return
        
        desc = input("  Description (optional): ").strip()
        
        from tasc.cli import cmd_save
        import argparse
        args = argparse.Namespace(name=name, desc=desc, type="work", files=None)
        cmd_save(args)
    
    def search_tascs(self):
        """Search for Tascs."""
        print(box("🔍 Search Tascs", ""))
        query = input("  Query: ").strip()
        if not query:
            return
        
        from tasc.cli import cmd_recall
        import argparse
        args = argparse.Namespace(query=query)
        cmd_recall(args)
    
    def render_stats(self):
        """Render detailed statistics."""
        stats = self.get_stats()
        
        stat_content = f"""
  Total Tascs:     {stats['tascs']}
  Total Energy:    {stats['energy']:.1f}
  Evolution Gen:   {stats['gen']}
  
  PersonalCoder:
    Patterns:      {len(self.genesis.personal.patterns)}
    Corrections:   {len(self.genesis.personal.correction_history)}
  
  SelfModifyingTasc:
    Limitations:   {len(self.genesis.self_mod.known_limitations)}
    Proposals:     {len(self.genesis.self_mod.upgrade_proposals)}
    Applied:       {len(self.genesis.self_mod.applied_upgrades)}
        """
        print(box("📊 System Statistics", stat_content.strip()))
    
    def handle_input(self):
        """Handle user input."""
        choice = input("\n  > ").strip().lower()
        
        if choice == '1':
            self.render_tascs()
        elif choice == '2':
            self.save_new_tasc()
        elif choice == '3':
            self.search_tascs()
        elif choice == '4':
            self.render_energy()
        elif choice == '5':
            self.render_evolution()
        elif choice == '6':
            self.render_genesis()
        elif choice == '7':
            self.render_stats()
        elif choice in ('q', 'quit', 'exit'):
            self.running = False
        else:
            print("  Invalid choice. Try again.")
        
        if self.running and choice not in ('q', 'quit', 'exit'):
            input("\n  Press Enter to continue...")
    
    def run(self):
        """Main loop."""
        while self.running:
            self.clear()
            self.render_dashboard()
            self.handle_input()
        
        self.clear()
        print("\n  👋 Goodbye!\n")


def main():
    """Entry point for TUI."""
    tui = TascTUI()
    try:
        tui.run()
    except KeyboardInterrupt:
        print("\n\n  👋 Interrupted. Goodbye!\n")


if __name__ == "__main__":
    main()
