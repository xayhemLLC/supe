#!/usr/bin/env python3
"""TascerAgent Demo: Reverse Engineering Workflow

This script demonstrates a complete RE workflow using TascerAgent:
1. Analyzing binary files with validation gates
2. Discovering struct definitions
3. Running analysis tools (Ghidra-style)
4. Querying past analysis via recall
5. Generating audit trails with proof verification

Run: python scripts/demo_tascer_re_workflow.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ab import ABMemory
from tascer.sdk_wrapper import (
    TascerAgent,
    TascerAgentOptions,
    ToolValidationConfig,
    RecallConfig,
)
from tascer.contracts import GateResult


# =============================================================================
# Custom RE Gates
# =============================================================================

def gate_read_only_mode(record, phase) -> GateResult:
    """Block any write operations to game directory."""
    if phase != "pre":
        return GateResult(
            gate_name="read_only_mode",
            passed=True,
            message="Post-check skipped",
        )

    tool = record.tool_name
    if tool in ["Write", "Edit"]:
        file_path = record.tool_input.get("file_path", "")
        if "/game/" in file_path or "/binary/" in file_path:
            return GateResult(
                gate_name="read_only_mode",
                passed=False,
                message=f"Write blocked: RE mode is read-only for game files",
            )
    return GateResult(
        gate_name="read_only_mode",
        passed=True,
        message="Read operation allowed",
    )


def gate_command_whitelist(record, phase) -> GateResult:
    """Only allow whitelisted RE commands."""
    if phase != "pre":
        return GateResult(
            gate_name="command_whitelist",
            passed=True,
            message="Post-check skipped",
        )

    if record.tool_name != "Bash":
        return GateResult(
            gate_name="command_whitelist",
            passed=True,
            message="Not a Bash command",
        )

    command = record.tool_input.get("command", "")
    allowed_prefixes = [
        "ghidra", "radare2", "r2", "objdump", "readelf", "nm", "strings",
        "hexdump", "xxd", "file", "ldd", "checksec", "rabin2",
    ]

    cmd_start = command.split()[0] if command.split() else ""
    if any(cmd_start.startswith(prefix) for prefix in allowed_prefixes):
        return GateResult(
            gate_name="command_whitelist",
            passed=True,
            message=f"Command allowed: {cmd_start}",
        )

    # Also allow analysis scripts
    if "analyze" in command.lower() or "disasm" in command.lower():
        return GateResult(
            gate_name="command_whitelist",
            passed=True,
            message="Analysis command allowed",
        )

    return GateResult(
        gate_name="command_whitelist",
        passed=False,
        message=f"Command not in RE whitelist: {cmd_start}",
    )


# =============================================================================
# Simulated Tool Execution
# =============================================================================

async def execute_tool(agent: TascerAgent, tool_name: str, tool_input: dict, tool_output: any):
    """Simulate a tool execution through the agent hooks."""
    import uuid

    tool_use_id = f"tu_{uuid.uuid4().hex[:8]}"

    # Pre-hook
    input_data = {"tool_name": tool_name, "tool_input": tool_input}
    pre_result = await agent._pre_tool_hook(input_data, tool_use_id, None)

    if pre_result.get("block"):
        return {"blocked": True, "message": pre_result.get("message")}

    # Post-hook
    result_data = {"tool_result": tool_output}
    await agent._post_tool_hook(result_data, tool_use_id, None)

    return {"blocked": False, "output": tool_output}


# =============================================================================
# Simulated RE Data
# =============================================================================

PLAYER_STRUCT = """
struct Player {
    uint32_t entity_id;      // 0x00
    float position[3];       // 0x04 - x, y, z
    float velocity[3];       // 0x10
    int32_t health;          // 0x1C
    int32_t max_health;      // 0x20
    uint8_t team;            // 0x24
    uint8_t flags;           // 0x25
    char name[32];           // 0x26
    void* inventory_ptr;     // 0x48
    uint64_t last_update;    // 0x50
};  // Total: 0x58 bytes
"""

WEAPON_STRUCT = """
struct Weapon {
    uint32_t weapon_id;      // 0x00
    uint32_t ammo_current;   // 0x04
    uint32_t ammo_reserve;   // 0x08
    float damage;            // 0x0C
    float fire_rate;         // 0x10
    float reload_time;       // 0x14
    uint8_t weapon_type;     // 0x18
    uint8_t rarity;          // 0x19
    char name[24];           // 0x1A
};  // Total: 0x32 bytes
"""

GHIDRA_ANALYSIS = """
=== Ghidra Analysis Report ===
Binary: game_client.exe
Architecture: x86_64
Entry Point: 0x140001000

Functions Found: 12,847
Strings Found: 8,234
Cross-references: 45,123

Key Functions:
  0x14002A100: Player::Update(float deltaTime)
  0x14002A400: Player::TakeDamage(int amount, Entity* source)
  0x14002B000: Weapon::Fire(Vector3 direction)
  0x14002B300: Weapon::Reload()
  0x14003C000: NetworkManager::SendPacket(Packet* pkt)

Suspicious Patterns:
  - Anti-debug check at 0x140001050
  - Integrity check at 0x140001200
  - Encrypted strings table at 0x140500000
"""

MEMORY_DUMP = """
Memory Region: 0x7FF600000000 - 0x7FF600010000
Player Instance Found at: 0x7FF600004A80

Offset  | Value           | Interpretation
--------|-----------------|----------------
0x00    | 0x00001337      | entity_id = 4919
0x04    | 42.5, 100.2, 8.0| position (x,y,z)
0x10    | 0.0, 0.0, 0.0   | velocity (stationary)
0x1C    | 85              | health = 85
0x20    | 100             | max_health = 100
0x24    | 0x01            | team = 1 (Blue)
0x25    | 0x03            | flags = ALIVE | CAN_SHOOT
0x26    | "ProGamer42"    | player name
0x48    | 0x7FF600008000  | inventory pointer
"""


# =============================================================================
# Main Demo
# =============================================================================

async def main():
    print("=" * 70)
    print("  TascerAgent Demo: Reverse Engineering Workflow")
    print("=" * 70)
    print()

    # Setup
    db_path = ".tascer/re_demo.sqlite"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    ab = ABMemory(db_path)

    # Create agent with RE-specific configuration
    agent = TascerAgent(
        tascer_options=TascerAgentOptions(
            tool_configs={
                "Read": ToolValidationConfig(
                    tool_name="Read",
                    pre_gates=["read_only_mode"],
                ),
                "Bash": ToolValidationConfig(
                    tool_name="Bash",
                    pre_gates=["command_whitelist"],
                    post_gates=["exit_code_zero"],
                ),
                "Write": ToolValidationConfig(
                    tool_name="Write",
                    pre_gates=["read_only_mode"],
                ),
                "Edit": ToolValidationConfig(
                    tool_name="Edit",
                    pre_gates=["read_only_mode"],
                ),
            },
            capture_git_state=False,
            capture_env=False,
            store_to_ab=True,
            recall_config=RecallConfig(
                enabled=True,
                index_on_store=True,
                default_top_k=5,
            ),
        ),
        ab_memory=ab,
    )
    agent._session_id = f"re_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Register custom gates
    agent.register_gate("read_only_mode", gate_read_only_mode)
    agent.register_gate("command_whitelist", gate_command_whitelist)

    print(f"[Setup] Created TascerAgent with RE configuration")
    print(f"[Setup] Session: {agent._session_id}")
    print(f"[Setup] Database: {db_path}")
    print()

    # =========================================================================
    # Phase 1: Initial Binary Analysis
    # =========================================================================
    print("-" * 70)
    print("PHASE 1: Initial Binary Analysis")
    print("-" * 70)
    print()

    # Read binary header
    print("[1.1] Reading binary header...")
    result = await execute_tool(
        agent, "Read",
        {"file_path": "/game/binaries/game_client.exe", "offset": 0, "limit": 1024},
        "MZ...PE header... x86_64 executable, compiled 2025-12-15",
    )
    print(f"      Result: Binary identified as x86_64 PE executable")

    # Run Ghidra analysis
    print("[1.2] Running Ghidra headless analysis...")
    result = await execute_tool(
        agent, "Bash",
        {"command": "ghidra_headless /analysis game_client.exe --analyze"},
        {"exit_code": 0, "stdout": GHIDRA_ANALYSIS},
    )
    print(f"      Result: Found 12,847 functions, 8,234 strings")

    # Find Player struct
    print("[1.3] Reading Player struct definition at 0x14002A100...")
    result = await execute_tool(
        agent, "Read",
        {"file_path": "/analysis/structs/player.h", "struct": "Player"},
        PLAYER_STRUCT,
    )
    print(f"      Result: Player struct is 0x58 bytes")

    # Find Weapon struct
    print("[1.4] Reading Weapon struct definition...")
    result = await execute_tool(
        agent, "Read",
        {"file_path": "/analysis/structs/weapon.h", "struct": "Weapon"},
        WEAPON_STRUCT,
    )
    print(f"      Result: Weapon struct is 0x32 bytes")

    print()

    # =========================================================================
    # Phase 2: Memory Analysis
    # =========================================================================
    print("-" * 70)
    print("PHASE 2: Memory Analysis")
    print("-" * 70)
    print()

    # Dump memory region
    print("[2.1] Analyzing memory dump for Player instances...")
    result = await execute_tool(
        agent, "Bash",
        {"command": "radare2 -c 'px 0x100 @ 0x7FF600004A80' memdump.bin"},
        {"exit_code": 0, "stdout": MEMORY_DUMP},
    )
    print(f"      Result: Found Player instance at 0x7FF600004A80")
    print(f"      Player: 'ProGamer42', health=85/100, team=Blue")

    # Cross-reference check
    print("[2.2] Finding cross-references to Player::TakeDamage...")
    result = await execute_tool(
        agent, "Bash",
        {"command": "r2 -c 'axt @ 0x14002A400' game_client.exe"},
        {"exit_code": 0, "stdout": "Found 23 xrefs to Player::TakeDamage"},
    )
    print(f"      Result: 23 cross-references found")

    print()

    # =========================================================================
    # Phase 3: Security Gate Demo
    # =========================================================================
    print("-" * 70)
    print("PHASE 3: Security Gates Demo")
    print("-" * 70)
    print()

    # Try to write to game directory (should be blocked)
    print("[3.1] Attempting to patch game binary (should be BLOCKED)...")
    result = await execute_tool(
        agent, "Edit",
        {"file_path": "/game/binaries/game_client.exe", "offset": 0x1000, "bytes": "90909090"},
        None,
    )
    if result.get("blocked"):
        print(f"      BLOCKED: {result['message']}")

    # Try non-whitelisted command (should be blocked)
    print("[3.2] Attempting rm command (should be BLOCKED)...")
    result = await execute_tool(
        agent, "Bash",
        {"command": "rm -rf /important_files"},
        None,
    )
    if result.get("blocked"):
        print(f"      BLOCKED: {result['message']}")

    # Whitelisted command works
    print("[3.3] Running strings analysis (whitelisted)...")
    result = await execute_tool(
        agent, "Bash",
        {"command": "strings -n 10 game_client.exe | grep -i player"},
        {"exit_code": 0, "stdout": "PlayerManager\nPlayer::Update\nPlayerInventory"},
    )
    print(f"      Result: Found 3 player-related strings")

    print()

    # =========================================================================
    # Phase 4: Recall Demo
    # =========================================================================
    print("-" * 70)
    print("PHASE 4: Recall - Querying Past Analysis")
    print("-" * 70)
    print()

    # Search for struct-related analysis
    print("[4.1] Recall: 'What structs did I find?'")
    results = agent.recall("struct Player Weapon", top_k=5)
    for r in results:
        print(f"      [{r.score:.2f}] {r.tool_name}: {_truncate(str(r.tool_input), 60)}")
    print()

    # Search for memory analysis
    print("[4.2] Recall: 'memory dump analysis'")
    results = agent.recall("memory dump 0x7FF", top_k=3)
    for r in results:
        print(f"      [{r.score:.2f}] {r.tool_name}: {_truncate(str(r.tool_input), 60)}")
    print()

    # Get all Bash executions
    print("[4.3] Recall Tool: All Bash commands")
    results = agent.recall_tool("Bash", top_k=10)
    for r in results:
        cmd = r.tool_input.get("command", "N/A")
        print(f"      - {_truncate(cmd, 55)}")
    print()

    # Find similar to a pattern
    print("[4.4] Recall Similar: Find analysis like 'player.h'")
    results = agent.recall_similar({"file_path": "/analysis/structs/player.h"}, top_k=3)
    for r in results:
        print(f"      [{r.score:.2f}] {r.tool_name}: {_truncate(str(r.tool_input), 50)}")
    print()

    # =========================================================================
    # Phase 5: Audit Trail
    # =========================================================================
    print("-" * 70)
    print("PHASE 5: Audit Trail & Proof Verification")
    print("-" * 70)
    print()

    # Validation report
    print("[5.1] Execution Summary:")
    records = agent.get_validation_report()
    validated = sum(1 for r in records if r.status == "validated")
    blocked = sum(1 for r in records if r.status == "blocked")
    failed = sum(1 for r in records if r.status == "failed")
    print(f"      Total: {len(records)} executions")
    print(f"      Validated: {validated} | Blocked: {blocked} | Failed: {failed}")
    print()

    # Proof verification
    print("[5.2] Cryptographic Proof Verification:")
    proofs_valid = agent.verify_proofs()
    print(f"      All proofs valid: {proofs_valid}")
    print()

    # Show proof hashes
    print("[5.3] Proof Hashes (first 5):")
    for r in records[:5]:
        status = "✓" if r.status == "validated" else "✗" if r.status == "blocked" else "!"
        print(f"      {status} {r.tool_name:8} | {r.proof_hash[:16]}... | {r.status}")
    print()

    # Export report
    report_path = ".tascer/re_audit_report.json"
    agent.export_report(report_path)
    print(f"[5.4] Exported full audit report to: {report_path}")
    print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 70)
    print("  Demo Complete!")
    print("=" * 70)
    print()
    print("This demo showed:")
    print("  1. TascerAgent validating RE tool executions")
    print("  2. Custom gates (read_only_mode, command_whitelist)")
    print("  3. Recall system finding past analysis")
    print("  4. Cryptographic proofs for audit trails")
    print()
    print(f"Database: {db_path}")
    print(f"Report:   {report_path}")
    print()


def _truncate(s: str, max_len: int) -> str:
    """Truncate string with ellipsis."""
    return s[:max_len] + "..." if len(s) > max_len else s


if __name__ == "__main__":
    asyncio.run(main())
