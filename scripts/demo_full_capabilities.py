#!/usr/bin/env python3
"""Comprehensive Demo: All Supe Capabilities.

This script showcases EVERYTHING Supe can do:

1. AB MEMORY ENGINE
   - Moments, Cards, Buffers (hierarchical storage)
   - Neural Memory with Hebbian learning
   - Spreading activation recall
   - Semantic search
   - Card connections

2. TASC SYSTEM
   - Task definitions with dependencies
   - Evidence-based validation
   - Domain inference

3. TASCER VALIDATION
   - TascerAgent (Claude SDK wrapper)
   - Custom validation gates
   - Proof-of-work audit trails
   - Recall system

4. RELATIONS
   - Typed relations between cards
   - Relation graph traversal

5. LLM PROOF-OF-WORK
   - Multiple proof types
   - Cryptographic verification

Run: python scripts/demo_full_capabilities.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


def section(title: str):
    console.print(f"\n{'='*70}")
    console.print(Panel(f"[bold cyan]{title}[/]", border_style="cyan"))
    console.print(f"{'='*70}\n")


def subsection(title: str):
    console.print(f"\n[bold yellow]▸ {title}[/]\n")


# =============================================================================
# PART 1: AB MEMORY ENGINE
# =============================================================================

def demo_ab_memory():
    """Demonstrate AB Memory capabilities."""
    section("PART 1: AB MEMORY ENGINE")

    from ab import ABMemory, Buffer
    from ab import search_cards, semantic_search
    from ab.neural_memory import NeuralMemory

    # Setup
    db_path = ".tascer/demo_full.sqlite"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    ab = ABMemory(db_path)
    console.print(f"[green]✓[/] Created AB Memory at {db_path}\n")

    # -------------------------------------------------------------------------
    # 1.1 Moments, Cards, Buffers
    # -------------------------------------------------------------------------
    subsection("1.1 Hierarchical Storage: Moments → Cards → Buffers")

    moment = ab.create_moment(master_input="RE session: game_client.exe")
    console.print(f"Created Moment #{moment.id}")

    cards_created = []

    # Card 1: Player struct
    card1 = ab.store_card(
        label="analysis:player_struct",
        buffers=[
            Buffer(name="definition", payload=b"struct Player { int health; int mana; }"),
            Buffer(name="offsets", payload=json.dumps({"health": "0x10", "mana": "0x14"}).encode()),
        ],
        moment_id=moment.id,
    )
    cards_created.append(card1)
    console.print(f"  Card #{card1.id}: player_struct (2 buffers)")

    # Card 2: Network protocol
    card2 = ab.store_card(
        label="analysis:network",
        buffers=[Buffer(name="packets", payload=b"MOVE: 0x01, ATTACK: 0x02")],
        moment_id=moment.id,
    )
    cards_created.append(card2)
    console.print(f"  Card #{card2.id}: network (1 buffer)")

    # Card 3: Memory map
    card3 = ab.store_card(
        label="analysis:memory",
        buffers=[Buffer(name="regions", payload=b"code: 0x400000, data: 0x10000000")],
        moment_id=moment.id,
    )
    cards_created.append(card3)
    console.print(f"  Card #{card3.id}: memory (1 buffer)")

    # -------------------------------------------------------------------------
    # 1.2 Keyword Search
    # -------------------------------------------------------------------------
    subsection("1.2 Keyword Search")

    results = search_cards(ab, "player health")
    console.print(f"Search 'player health': {len(results)} results")
    for card, score in results[:3]:
        console.print(f"  [{score:.2f}] {card.label}")

    # -------------------------------------------------------------------------
    # 1.4 Semantic Search
    # -------------------------------------------------------------------------
    subsection("1.3 Semantic Vector Search")

    results = semantic_search(ab, query="network packets", top_k=3)
    console.print(f"Semantic 'network packets':")
    for card, score in results:
        console.print(f"  [{score:.3f}] {card.label}")

    # -------------------------------------------------------------------------
    # 1.5 Neural Memory
    # -------------------------------------------------------------------------
    subsection("1.4 Neural Memory (Hebbian Learning)")

    neural = NeuralMemory()

    for card in cards_created:
        buffers_dict = {b.name: b.payload.decode('utf-8', errors='ignore')[:50]
                       for b in card.buffers}
        neural.add_card(card.id, buffers_dict)

    # Create connections (Hebbian: cells that fire together wire together)
    neural.connect(card1.id, card2.id, initial_strength=0.3)
    neural.connect(card1.id, card2.id)  # Strengthen by reconnecting
    neural.connect(card1.id, card3.id, initial_strength=0.2)

    # Spreading activation through recall
    results = neural.recall("player struct network", top_k=5)
    console.print(f"  Neural recall 'player struct network':")
    for card_id, activation in results[:3]:
        console.print(f"    Card #{card_id}: {activation:.3f}")

    return ab, cards_created, moment


# =============================================================================
# PART 2: TASC SYSTEM
# =============================================================================

def demo_tasc_system(ab):
    """Demonstrate Tasc task management."""
    section("PART 2: TASC SYSTEM")

    from tasc.tasc import Tasc
    from tasc.ab_integration import store_tasc
    from tasc.evidence import Evidence, EvidenceSource
    from tasc.domains import infer_domain_from_title

    subsection("2.1 Create Tascs")

    tasks = [
        Tasc(
            id="task-001",
            status="pending",
            title="Set up analysis environment",
            additional_notes="Install RE tools",
            testing_instructions="ghidra --version",
            desired_outcome="Tools working",
        ),
        Tasc(
            id="task-002",
            status="pending",
            title="Fix security vulnerability",
            additional_notes="CVE in auth",
            testing_instructions="pytest test_auth.py",
            desired_outcome="Auth secure",
            dependencies=["task-001"],
        ),
    ]

    for task in tasks:
        card_id = store_tasc(ab, task)
        console.print(f"  {task.id}: {task.title} → Card #{card_id}")

    subsection("2.2 Domain Inference")

    titles = [
        "Fix crash in login",
        "Design cache architecture",
        "Refactor auth module",
        "Fix security vulnerability",
    ]

    table = Table(show_header=True)
    table.add_column("Task Title")
    table.add_column("Domain")

    for title in titles:
        domain = infer_domain_from_title(title)
        table.add_row(title, f"[cyan]{domain.value}[/]")

    console.print(table)

    subsection("2.3 Evidence-Based Validation")

    evidence = [
        Evidence.create("Tests pass", EvidenceSource.TEST, ["pytest: 42 passed"]),
        Evidence.create("Code reviewed", EvidenceSource.PEER_REVIEW, ["PR #123"]),
        Evidence.create("Security scan clean", EvidenceSource.SECURITY_SCAN, ["snyk: 0 vulns"]),
    ]

    for ev in evidence:
        console.print(f"  [{ev.source.value}] {ev.text}")


# =============================================================================
# PART 3: TASCER VALIDATION
# =============================================================================

async def demo_tascer_validation(ab):
    """Demonstrate Tascer validation system."""
    section("PART 3: TASCER VALIDATION")

    from tascer.sdk_wrapper import (
        TascerAgent,
        TascerAgentOptions,
        ToolValidationConfig,
        RecallConfig,
    )
    from tascer.contracts import GateResult
    import uuid

    subsection("3.1 TascerAgent with Gates")

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
    agent._session_id = "demo_full"

    @agent.register_gate("safe_commands")
    def safe_commands(record, phase) -> GateResult:
        if phase != "pre":
            return GateResult("safe_commands", True, "OK")
        cmd = record.tool_input.get("command", "")
        if "rm -rf" in cmd:
            return GateResult("safe_commands", False, "BLOCKED: dangerous")
        return GateResult("safe_commands", True, "OK")

    @agent.register_gate("read_only")
    def read_only(record, phase) -> GateResult:
        if phase != "pre":
            return GateResult("read_only", True, "OK")
        path = record.tool_input.get("file_path", "")
        if "/game/" in path:
            return GateResult("read_only", False, "BLOCKED: protected path")
        return GateResult("read_only", True, "OK")

    console.print("  Registered gates: safe_commands, read_only")

    subsection("3.2 Validated Execution")

    async def run_tool(tool: str, input_data: dict, expected: str = "OK"):
        tool_use_id = f"tu_{uuid.uuid4().hex[:8]}"
        pre = await agent._pre_tool_hook({"tool_name": tool, "tool_input": input_data}, tool_use_id, None)
        if pre.get("block"):
            console.print(f"  [red]BLOCKED[/] {tool}: {str(input_data)[:40]}")
        else:
            await agent._post_tool_hook({"tool_result": expected}, tool_use_id, None)
            console.print(f"  [green]VALIDATED[/] {tool}: {str(input_data)[:40]}")

    await run_tool("Bash", {"command": "rm -rf /data"})
    await run_tool("Bash", {"command": "ghidra --analyze game.exe"}, "Done")
    await run_tool("Bash", {"command": "strings game.exe"}, "Found 100 strings")
    await run_tool("Write", {"file_path": "/game/cheats.dll"})
    await run_tool("Write", {"file_path": "/tmp/notes.txt"}, "Written")
    await run_tool("Read", {"file_path": "/app/config.json"}, '{"ok": true}')

    subsection("3.3 Audit Trail")

    records = agent.get_validation_report()
    table = Table(show_header=True)
    table.add_column("Tool")
    table.add_column("Status")
    table.add_column("Proof")

    for r in records:
        style = "green" if r.status == "validated" else "red"
        hash_str = r.proof_hash[:12] + "..." if r.proof_hash else "-"
        table.add_row(r.tool_name, f"[{style}]{r.status}[/]", hash_str)

    console.print(table)

    valid = agent.verify_proofs()
    validated = sum(1 for r in records if r.status == "validated")
    blocked = sum(1 for r in records if r.status == "blocked")

    console.print(f"\n  Total: {len(records)} | [green]Validated: {validated}[/] | [red]Blocked: {blocked}[/]")
    console.print(f"  All proofs valid: [{'green' if valid else 'red'}]{valid}[/]")

    subsection("3.4 Recall")

    console.print("  Keyword recall 'game':")
    results = agent.recall("game", top_k=3)
    for r in results:
        console.print(f"    [{r.score:.2f}] {r.tool_name}")

    console.print(f"\n  Session history: {len(agent.recall_session())} executions")

    return agent


# =============================================================================
# PART 4: RELATIONS
# =============================================================================

def demo_relations(ab, cards):
    """Demonstrate Relations."""
    section("PART 4: RELATIONS")

    from tasc.relations import Relation, RelationType, RelationCollection

    subsection("4.1 Typed Relations")

    relations = [
        Relation.create("r1", RelationType.SUPPORTS, cards[0].id, cards[1].id, 0.9),
        Relation.create("r2", RelationType.DEPENDS_ON, cards[0].id, cards[2].id, 0.8),
    ]

    for rel in relations:
        console.print(f"  #{rel.source_card_id} --[{rel.type.value}]--> #{rel.target_card_id}")

    subsection("4.2 Relation Collection")

    collection = RelationCollection(id="demo-collection", description="Demo relations")
    for rel in relations:
        collection.add_relation(rel)

    console.print(f"  Collection: {len(collection.relations)} relations")

    outgoing = collection.get_by_source(cards[0].id)
    console.print(f"  From #{cards[0].id}: {len(outgoing)} outgoing")


# =============================================================================
# PART 5: LLM PROOF-OF-WORK
# =============================================================================

def demo_llm_proof():
    """Demonstrate LLM proof-of-work."""
    section("PART 5: LLM PROOF-OF-WORK")

    from tascer.llm_proof import ProofType, LLMTaskProof, compute_proof_hash, create_plan

    subsection("5.1 Proof Types")

    types = [
        (ProofType.SCRIPT, "Exit code validation"),
        (ProofType.TEST, "Test suite passes"),
        (ProofType.LINT, "Linting passes"),
        (ProofType.LEARNING_SESSION, "Learning outcomes"),
        (ProofType.EXPERIMENT, "Experiment validation"),
    ]

    for ptype, desc in types:
        console.print(f"  • {ptype.value}: {desc}")

    subsection("5.2 Cryptographic Proof")

    # Create proof with consistent timestamp
    timestamp = datetime.now().isoformat()
    proof_data = {
        "task_id": "task-001",
        "plan_id": "plan-001",
        "proven": True,
        "timestamp": timestamp,
        "execution_log": {"command": "pytest", "exit_code": 0},
        "evidence": {"exit_code": 0, "stdout": "42 passed"},
        "gate_results": [],
        "context_snapshot": None,
        "duration_ms": 1234.5,
        "retries": 0,
    }
    proof_hash = compute_proof_hash(proof_data)

    proof = LLMTaskProof(
        task_id="task-001",
        plan_id="plan-001",
        proven=True,
        proof_hash=proof_hash,
        timestamp=timestamp,
        execution_log={"command": "pytest", "exit_code": 0},
        evidence={"exit_code": 0, "stdout": "42 passed"},
        duration_ms=1234.5,
    )

    console.print(f"  Task: {proof.task_id}")
    console.print(f"  Plan: {proof.plan_id}")
    console.print(f"  Hash: {proof.proof_hash}...")
    console.print(f"  Verified: [green]{proof.verify()}[/]")

    subsection("5.3 Structured Plans")

    plan = create_plan(
        title="Security Audit",
        tascs=[
            {"id": "t1", "title": "Run security scan"},
            {"id": "t2", "title": "Review findings"},
        ],
        description="Full security audit workflow",
    )

    console.print(f"  Plan: {plan.title}")
    console.print(f"  Tasks: {len(plan.tascs)}")
    console.print(f"  ID: {plan.id[:16]}...")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]SUPE - FULL CAPABILITIES DEMO[/]\n"
        "[dim]Cognitive Memory • Task Management • Validated Execution[/]",
        border_style="cyan"
    ))

    ab, cards, moment = demo_ab_memory()
    demo_tasc_system(ab)
    await demo_tascer_validation(ab)
    demo_relations(ab, cards)
    demo_llm_proof()

    # Summary
    section("SUMMARY")

    tree = Tree("[bold cyan]Supe Capabilities[/]")

    ab_branch = tree.add("[yellow]AB Memory[/]")
    ab_branch.add("Moments → Cards → Buffers")
    ab_branch.add("Neural Memory (Hebbian learning)")
    ab_branch.add("Spreading activation")
    ab_branch.add("Semantic vector search")

    tasc_branch = tree.add("[yellow]Tasc System[/]")
    tasc_branch.add("Tasks with dependencies")
    tasc_branch.add("14 evidence types")
    tasc_branch.add("7 domain categories")

    tascer_branch = tree.add("[yellow]Tascer Validation[/]")
    tascer_branch.add("Pre/post validation gates")
    tascer_branch.add("SHA256 proof-of-work")
    tascer_branch.add("Neural recall")

    rel_branch = tree.add("[yellow]Relations[/]")
    rel_branch.add("Typed card relations")
    rel_branch.add("Graph traversal")

    proof_branch = tree.add("[yellow]LLM Proof-of-Work[/]")
    proof_branch.add("8 proof types")
    proof_branch.add("Cryptographic verification")

    console.print(tree)

    console.print("\n[bold green]Demo complete![/]")
    console.print("[dim]pip install supe • github.com/xayhemLLC/supe[/]\n")


if __name__ == "__main__":
    asyncio.run(main())
