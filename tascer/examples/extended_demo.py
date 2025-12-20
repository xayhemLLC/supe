#!/usr/bin/env python3
"""Tasc Extended Demo - Plugin System, Integrations & More"""
import os
import json
import tempfile
from datetime import datetime

def main():
    print("=" * 70)
    print("🚀 Tasc Extended Demo")
    print("   Plugin System • Sandbox Mode • Audit Export • MCP Integration")
    print("=" * 70)
    print()

    # ============================================================
    # DEMO 1: Plugin System
    # ============================================================
    print("🔌 DEMO 1: Plugin System")
    print("-" * 50)

    from tascer.plugins import Plugin, PluginInfo, PluginRegistry, PluginStatus

    class WeatherPlugin(Plugin):
        @property
        def info(self):
            return PluginInfo(
                name="weather", version="1.0.0",
                description="Get weather (demo plugin)",
                capabilities=["weather_api"],
            )
        
        async def initialize(self):
            self._status = PluginStatus.READY
            return True
        
        def get_actions(self):
            return {
                "current": lambda city: f"☀️ {city}: 72°F, Sunny",
                "forecast": lambda city: f"📅 {city}: Looking good!",
            }

    registry = PluginRegistry()
    registry.register(WeatherPlugin())

    print(f"  ✓ Plugins: {len(registry.list_plugins())}")
    for p in registry.list_plugins():
        print(f"    • {p.name} v{p.version}: {p.description}")
    
    action = registry.get_action("weather.current")
    print(f"  ✓ Call action: {action('San Francisco')}")
    print()

    # ============================================================
    # DEMO 2: MCP Integration
    # ============================================================
    print("🤖 DEMO 2: MCP Integration (Claude Code / Cursor)")
    print("-" * 50)

    from tascer.plugins.mcp_plugin import MCPPlugin

    mcp = MCPPlugin()
    # Must call _register_tools directly since initialize is async
    mcp._register_tools()
    manifest = mcp.get_mcp_manifest()

    print(f"  MCP Server: {manifest['name']} v{manifest['version']}")
    print(f"  Tools ({len(manifest['tools'])}):")
    for tool in manifest['tools']:
        print(f"    • {tool['name']}")
    print()

    print("  📋 Claude Code config (~/.config/claude/mcp.json):")
    print('    {"mcpServers": {"tascer": {"command": "python", "args": ["-m", "tascer.plugins.mcp_server"]}}}')
    print()

    # Test tool
    result = mcp.handle_tool_call("tascer_check_legality", {
        "action": "terminal.run", "command": "echo hello"
    })
    print(f"  Test: 'echo hello' → legal={result['is_legal']}")
    
    result = mcp.handle_tool_call("tascer_check_legality", {
        "action": "terminal.run", "command": "rm -rf /"
    })
    print(f"  Test: 'rm -rf /' → legal={result['is_legal']} 🚫 BLOCKED")
    print()

    # ============================================================
    # DEMO 3: Discord Plugin
    # ============================================================
    print("💬 DEMO 3: Discord Bot Plugin")
    print("-" * 50)

    from tascer.plugins.discord_plugin import DiscordPlugin

    discord = DiscordPlugin(command_prefix="!")
    print(f"  Plugin: {discord.info.name} v{discord.info.version}")
    print(f"  Actions: discord.send, discord.status, discord.upload")
    print()
    print("  Commands (when DISCORD_BOT_TOKEN is set):")
    print("    !tasc echo hello  → Run Tasc command")
    print("    !status           → Get task status")
    print()

    # ============================================================
    # DEMO 4: Sandbox Mode
    # ============================================================
    print("🏖️ DEMO 4: Sandbox Mode - Safe Exploration")
    print("-" * 50)

    from tascer.primitives.sandbox import sandbox_enter, sandbox_exit, is_in_sandbox

    with tempfile.TemporaryDirectory() as project:
        # Create files
        for f in ["app.py", "config.yaml", "README.md"]:
            with open(os.path.join(project, f), "w") as file:
                file.write(f"# Original {f}\n")
        
        print(f"  Project files: {os.listdir(project)}")
        
        # Enter sandbox
        result = sandbox_enter(project, "Risky experiment")
        print(f"  ✓ Entered sandbox: {result.sandbox_id}")
        print(f"    Method: {result.isolation_method}")
        print(f"    In sandbox: {is_in_sandbox()}")
        
        # Destroy in sandbox
        sandbox_dir = result.sandbox_dir
        os.remove(os.path.join(sandbox_dir, "app.py"))
        os.remove(os.path.join(sandbox_dir, "config.yaml"))
        with open(os.path.join(sandbox_dir, "README.md"), "w") as f:
            f.write("CORRUPTED!")
        
        print(f"  ⚠️ Destroyed sandbox files: {os.listdir(sandbox_dir)}")
        
        # Discard
        sandbox_exit("discard")
        print(f"  ✓ Exited sandbox (discarded)")
        print(f"  ✓ Original intact: {os.listdir(project)}")
    print()

    # ============================================================
    # DEMO 5: Audit Export
    # ============================================================
    print("📝 DEMO 5: Audit Export - Evidence Trail")
    print("-" * 50)

    from tascer.ledgers import LedgerStorage
    from tascer.ledgers.exe import StopReason, ConfidenceScore
    from tascer.audit import export_to_markdown

    with tempfile.TemporaryDirectory() as output:
        storage = LedgerStorage(run_id="investigate_001", output_dir=output)
        
        storage.exe.record_narrative("Hypothesis: Login slow due to DB")
        storage.moments.record_context({"branch": "main"})
        storage.exe.record_proposal(
            "terminal.run", "Profile login",
            confidence=ConfidenceScore(0.85, calibration_note="Known pattern"),
        )
        storage.moments.record_action_result("terminal.run", {
            "finding": "DB query 3.2s", "fix": "Add index"
        })
        storage.exe.record_stop(StopReason.GOAL_ACHIEVED, "Found it!")
        
        path = export_to_markdown(
            storage=storage, output_dir=output,
            hypothesis="Login slow due to missing index"
        )
        
        print(f"  Created: {os.path.basename(path)}")
        
        with open(path) as f:
            lines = f.read().split("\n")
        
        print("  " + "─" * 45)
        for line in lines[:18]:
            print(f"  │ {line[:50]}")
        print("  │ ...")
        print("  " + "─" * 45)
    print()

    # ============================================================
    # DEMO 6: Full Flow
    # ============================================================
    print("🔗 DEMO 6: Full Integration Flow")
    print("-" * 50)

    from tascer.action_registry import get_registry
    from tascer.checkpoint import CheckpointManager
    from tascer.overlord.decision import StopConditionState, should_stop
    from tascer.primitives import run_and_observe

    with tempfile.TemporaryDirectory() as ws:
        reg = get_registry()
        reg.load()
        print(f"  1️⃣ Actions: {len(reg.list_all())} loaded")
        
        mgr = CheckpointManager("agent", ws, ws)
        cp = mgr.create("Start")
        print(f"  2️⃣ Checkpoint: {cp.checkpoint_id}")
        
        storage = LedgerStorage("agent", ws)
        storage.exe.record_narrative("Fix the bug")
        print(f"  3️⃣ Ledgers: initialized")
        
        res = run_and_observe("echo 'Fixed!'", shell=True)
        print(f"  4️⃣ Action: {res.stdout.strip()}")
        
        state = StopConditionState(
            legal_actions={"terminal.run"},
            actions_taken=1,
            goal_achieved=True,
        )
        dec = should_stop(state)
        print(f"  5️⃣ Overlord: {'STOP ✓' if dec else 'CONTINUE'}")

    print()
    print("=" * 70)
    print("🎉 Demo Complete!")
    print()
    print("New features added:")
    print("  🔌 Plugin system      - Create custom plugins")
    print("  💬 Discord plugin     - !tasc commands in Discord")
    print("  🤖 MCP plugin         - Claude Code / Cursor integration")
    print("  🏖️ Sandbox mode       - Safe exploration, discard changes")
    print("  📝 Audit export       - Markdown evidence trails")
    print("=" * 70)

if __name__ == "__main__":
    main()
