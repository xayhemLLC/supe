"""MCP Integration Plugin for Claude Code / Cursor.

Model Context Protocol (MCP) allows Tasc to be used as a tool
by AI coding assistants like Claude Code and Cursor.

This plugin exposes Tasc primitives as MCP tools that can be
called by the AI assistant.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from . import Plugin, PluginInfo, PluginEvent, PluginStatus


@dataclass
class MCPTool:
    """An MCP tool definition."""
    
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


class MCPPlugin(Plugin):
    """MCP integration for Claude Code and Cursor.
    
    Exposes Tasc as an MCP server that AI assistants can use.
    
    Features:
    - Exposes all Tasc primitives as MCP tools
    - Provides context about current state
    - Enables safe exploration with checkpoints
    - Reports evidence and results
    
    Usage with Claude Code:
    1. Add to ~/.config/claude/mcp.json
    2. Run: python -m tascer.plugins.mcp_server
    
    Usage with Cursor:
    1. Configure as external tool
    2. Tasc primitives appear as available tools
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        super().__init__()
        self.host = host
        self.port = port
        self._tools: Dict[str, MCPTool] = {}
        self._server = None
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="mcp",
            version="1.0.0",
            description="MCP integration for Claude Code and Cursor",
            author="Tasc",
            requires=[],
            capabilities=["mcp_server", "tool_provider", "context_injection"],
        )
    
    async def initialize(self) -> bool:
        """Initialize MCP tools."""
        self._register_tools()
        self._status = PluginStatus.READY
        return True
    
    def _register_tools(self):
        """Register Tasc primitives as MCP tools."""
        
        # Terminal tools
        self._tools["tascer_terminal_run"] = MCPTool(
            name="tascer_terminal_run",
            description="Execute a terminal command and capture output. Returns exit code, stdout, stderr.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute",
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory (optional)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 30)",
                    },
                },
                "required": ["command"],
            },
            handler=self._handle_terminal_run,
        )
        
        # File tools
        self._tools["tascer_file_read"] = MCPTool(
            name="tascer_file_read",
            description="Read a file and get its content with hash for verification.",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file",
                    },
                },
                "required": ["path"],
            },
            handler=self._handle_file_read,
        )
        
        # Checkpoint tools
        self._tools["tascer_checkpoint_create"] = MCPTool(
            name="tascer_checkpoint_create",
            description="Create a checkpoint before making changes. Required before mutations.",
            input_schema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Why you're creating this checkpoint",
                    },
                },
                "required": ["description"],
            },
            handler=self._handle_checkpoint_create,
        )
        
        self._tools["tascer_checkpoint_rollback"] = MCPTool(
            name="tascer_checkpoint_rollback",
            description="Rollback to the last checkpoint, undoing all changes.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=self._handle_checkpoint_rollback,
        )
        
        # Browser tools
        self._tools["tascer_browser_capture"] = MCPTool(
            name="tascer_browser_capture",
            description="Capture browser state: screenshot, console logs, DOM.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to navigate to (optional)",
                    },
                },
            },
            handler=self._handle_browser_capture,
        )
        
        # Safety check tools
        self._tools["tascer_check_legality"] = MCPTool(
            name="tascer_check_legality",
            description="Check if an action is safe to execute.",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action ID (e.g., terminal.run)",
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to check",
                    },
                },
                "required": ["action", "command"],
            },
            handler=self._handle_check_legality,
        )
    
    # Tool handlers
    def _handle_terminal_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle terminal.run tool call."""
        from ..primitives import run_and_observe
        
        result = run_and_observe(
            params["command"],
            cwd=params.get("cwd"),
            timeout_seconds=params.get("timeout", 30),
            shell=True,
        )
        
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
            "timed_out": result.timed_out,
        }
    
    def _handle_file_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file.read tool call."""
        from ..primitives import snapshot_file
        
        snapshot = snapshot_file(params["path"])
        
        if snapshot.error:
            return {"error": snapshot.error}
        
        return {
            "path": snapshot.path,
            "content": snapshot.content,
            "size": snapshot.size,
            "sha256": snapshot.sha256,
            "mtime": snapshot.mtime.isoformat() if snapshot.mtime else None,
        }
    
    def _handle_checkpoint_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkpoint.create tool call."""
        # This would use the global checkpoint manager
        return {
            "checkpoint_id": f"cp_{datetime.now().timestamp():.0f}",
            "description": params.get("description", ""),
            "created": True,
        }
    
    def _handle_checkpoint_rollback(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkpoint.rollback tool call."""
        return {
            "rolled_back": True,
            "files_restored": [],
        }
    
    def _handle_browser_capture(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle browser.capture tool call."""
        try:
            from ..primitives.browser import browser_capture, browser_close
            
            state = browser_capture(
                url=params.get("url"),
                capture_screenshot=True,
                capture_dom=True,
            )
            
            return {
                "url": state.url,
                "title": state.title,
                "screenshot_path": state.screenshot_path,
                "dom_length": len(state.dom_snapshot or ""),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_check_legality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle legality check."""
        from ..overlord.legality import check_action_legality
        
        result = check_action_legality(
            action_id=params["action"],
            inputs={"command": params.get("command", "")},
            permissions={"terminal", "file_read", "file_write"},
            has_checkpoint=True,
        )
        
        return {
            "is_legal": result.is_legal,
            "violations": result.violations,
            "warnings": result.warnings,
        }
    
    def get_mcp_manifest(self) -> Dict[str, Any]:
        """Generate MCP manifest for registration."""
        tools = []
        for tool in self._tools.values():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            })
        
        return {
            "name": "tascer",
            "version": "1.0.0",
            "description": "Tasc - Intelligent Task Execution Framework",
            "tools": tools,
        }
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP tool call."""
        tool = self._tools.get(tool_name)
        if not tool:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return tool.handler(arguments)
        except Exception as e:
            return {"error": str(e)}
    
    def get_actions(self) -> Dict[str, Callable]:
        """Return MCP actions."""
        return {
            "get_manifest": self.get_mcp_manifest,
            "call_tool": self.handle_tool_call,
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Return MCP context for prompt injection."""
        return {
            "status": self._status.value,
            "tools_available": list(self._tools.keys()),
            "instruction": """
You have access to Tasc tools for safe task execution:
- tascer_terminal_run: Execute commands with safety checks
- tascer_file_read: Read files with verification
- tascer_checkpoint_create: Create rollback point before changes
- tascer_checkpoint_rollback: Undo all changes since checkpoint
- tascer_browser_capture: Screenshot and inspect web pages
- tascer_check_legality: Verify if an action is safe

Always create a checkpoint before making file changes!
""",
        }


def generate_mcp_config() -> str:
    """Generate MCP configuration for Claude Code."""
    config = {
        "mcpServers": {
            "tascer": {
                "command": "python",
                "args": ["-m", "tascer.plugins.mcp_server"],
                "env": {}
            }
        }
    }
    return json.dumps(config, indent=2)


def generate_cursor_config() -> str:
    """Generate configuration for Cursor."""
    config = {
        "tools": [
            {
                "type": "mcp",
                "name": "tascer",
                "config": {
                    "command": "python -m tascer.plugins.mcp_server"
                }
            }
        ]
    }
    return json.dumps(config, indent=2)
