"""MCP Server - Run Tasc as an MCP server.

This allows Claude Code and Cursor to use Tasc as a tool provider.

Usage:
    python -m tascer.plugins.mcp_server

Or add to Claude Code config (~/.config/claude/mcp.json):
    {
        "mcpServers": {
            "tascer": {
                "command": "python",
                "args": ["-m", "tascer.plugins.mcp_server"]
            }
        }
    }
"""

import json
import sys
from typing import Any, Dict


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle an MCP request."""
    from .mcp_plugin import MCPPlugin
    
    plugin = MCPPlugin()
    
    method = request.get("method", "")
    
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "tascer",
                "version": "1.0.0",
            },
            "capabilities": {
                "tools": {},
            },
        }
    
    elif method == "tools/list":
        manifest = plugin.get_mcp_manifest()
        return {
            "tools": manifest["tools"],
        }
    
    elif method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        result = plugin.handle_tool_call(tool_name, arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, default=str),
                }
            ],
        }
    
    return {"error": f"Unknown method: {method}"}


def main():
    """Run the MCP server (JSON-RPC over stdio)."""
    print("Tasc MCP Server starting...", file=sys.stderr)
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            response["jsonrpc"] = "2.0"
            response["id"] = request.get("id")
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": str(e)},
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
