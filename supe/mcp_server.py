#!/usr/bin/env python3
"""Supe MCP Server - Expose supe tools to Cursor and Claude.

This MCP server allows AI assistants (Cursor, Claude Desktop) to use
supe's proof-of-work system for validated task execution.

Usage:
    # Run directly
    python -m supe.mcp_server
    
    # Or via CLI
    supe mcp-server
"""

import json
import sys
import os
from typing import Any, Dict, List, Optional

# MCP protocol implementation
# Using stdio transport for simplicity

def send_response(id: Any, result: Any = None, error: Any = None):
    """Send a JSON-RPC response."""
    response = {"jsonrpc": "2.0", "id": id}
    if error:
        response["error"] = error
    else:
        response["result"] = result
    print(json.dumps(response), flush=True)


def send_notification(method: str, params: Any = None):
    """Send a JSON-RPC notification."""
    notification = {"jsonrpc": "2.0", "method": method}
    if params:
        notification["params"] = params
    print(json.dumps(notification), flush=True)


# Tool definitions
TOOLS = [
    {
        "name": "supe_prove",
        "description": "Execute a command with proof generation. Returns cryptographic proof of execution including exit code, output, and validation gates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute and prove"
                },
                "expected_outputs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of files expected to exist after execution"
                },
                "tag": {
                    "type": "string",
                    "description": "Optional tag for the proof"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "supe_verify",
        "description": "Verify an existing proof by its ID or path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "proof_id": {
                    "type": "string",
                    "description": "Proof ID or path to proof file"
                }
            },
            "required": ["proof_id"]
        }
    },
    {
        "name": "supe_status",
        "description": "Get the current status of the supe system.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "supe_plan_create",
        "description": "Create a structured plan with tasks and subtasks for proof-of-work execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Plan title"
                },
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "command": {"type": "string"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["title"]
                    },
                    "description": "List of tasks in the plan"
                }
            },
            "required": ["title", "tasks"]
        }
    },
    {
        "name": "supe_plan_execute",
        "description": "Execute all tasks in a plan with proof generation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_path": {
                    "type": "string",
                    "description": "Path to saved plan JSON file"
                }
            },
            "required": ["plan_path"]
        }
    },
    {
        "name": "supe_tasc_save",
        "description": "Save current work as a tasc in AB Memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the tasc"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description"
                },
                "type": {
                    "type": "string",
                    "enum": ["work", "bug", "feature"],
                    "description": "Type of work"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "supe_tasc_list",
        "description": "List recent tascs from AB Memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of tascs to return",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "supe_tasc_recall",
        "description": "Search for past work by query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "supe_run_safe",
        "description": "Run a command with safety checks (legality verification).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to run"
                },
                "force": {
                    "type": "boolean",
                    "description": "Override safety checks",
                    "default": False
                }
            },
            "required": ["command"]
        }
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool and return the result."""
    
    if name == "supe_prove":
        from tascer.proofs import prove_llm_task, save_llm_proof
        
        command = arguments["command"]
        expected_outputs = arguments.get("expected_outputs", [])
        tag = arguments.get("tag", "mcp_proof")
        
        # prove_llm_task now returns TascValidation
        validation = prove_llm_task(
            task_id=tag,
            command=command,
            expected_outputs=expected_outputs,
        )
        
        # Save validation as proof
        proof_path = save_llm_proof(validation)
        
        return {
            "validated": validation.validated,
            "proof_hash": validation.proof_hash,
            "exit_code": validation.exit_code,
            "command": validation.command_executed,
            "proof_path": proof_path,
            "duration_ms": validation.duration_ms,
            "gates_passed": sum(1 for g in validation.gate_results if g.passed),
            "gates_total": len(validation.gate_results),
            "error": validation.error_message,
        }
    
    elif name == "supe_verify":
        from tascer.proofs import load_llm_proof
        
        proof_id = arguments["proof_id"]
        proof_dir = ".tascer/proofs"
        
        # Find proof file
        if os.path.exists(proof_id):
            proof_path = proof_id
        else:
            proof_path = os.path.join(proof_dir, f"{proof_id}.json")
            if not os.path.exists(proof_path):
                return {"error": f"Proof not found: {proof_id}"}
        
        # load_llm_proof now returns TascValidation
        validation = load_llm_proof(proof_path)
        is_valid = validation.verify()
        
        return {
            "valid": is_valid,
            "validated": validation.validated,
            "proof_hash": validation.proof_hash,
            "tasc_id": validation.tasc_id,
            "command": validation.command_executed,
        }
    
    elif name == "supe_status":
        db_path = os.environ.get("TASC_DB", "tasc.sqlite")
        proofs_dir = ".tascer/proofs"
        
        return {
            "ab_memory": {
                "active": os.path.exists(db_path),
                "path": db_path,
            },
            "tascer": {
                "configured": os.path.exists(".tascer"),
            },
            "proofs": {
                "count": len(os.listdir(proofs_dir)) if os.path.exists(proofs_dir) else 0,
                "path": proofs_dir,
            }
        }
    
    elif name == "supe_plan_create":
        from tascer import create_plan, save_plan
        
        title = arguments["title"]
        tasks = arguments["tasks"]
        
        # Convert tasks to new Tasc format (using testing_instructions)
        tasc_defs = []
        for i, t in enumerate(tasks):
            tasc_def = {
                "id": f"tasc_{i+1}",
                "title": t["title"],
                "testing_instructions": t.get("command", ""),
                "dependencies": t.get("dependencies", []),
            }
            tasc_defs.append(tasc_def)
        
        plan = create_plan(title=title, tascs=tasc_defs)
        
        # Save plan
        os.makedirs(".tascer/plans", exist_ok=True)
        plan_path = f".tascer/plans/{plan.id}.json"
        save_plan(plan, plan_path)
        
        return {
            "plan_id": plan.id,
            "title": plan.title,
            "tasc_count": len(plan.tascs),
            "plan_path": plan_path,
        }
    
    elif name == "supe_plan_execute":
        from tascer import load_plan, execute_plan
        
        plan_path = arguments["plan_path"]
        plan = load_plan(plan_path)
        
        report = execute_plan(plan)
        
        return {
            "verified": report.verified,
            "total_tasks": report.total_tasks,
            "proven_tasks": report.proven_tasks,
            "failed_tasks": report.failed_tasks,
            "overall_proof_hash": report.overall_proof_hash,
        }
    
    elif name == "supe_tasc_save":
        from ab.abdb import ABMemory
        from ab.models import Buffer
        from datetime import datetime
        
        name_arg = arguments["name"]
        desc = arguments.get("description", "")
        task_type = arguments.get("type", "work")
        
        db_path = os.environ.get("TASC_DB", "tasc.sqlite")
        mem = ABMemory(db_path)
        
        moment = mem.create_moment(
            master_input=f"Save: {name_arg}",
            master_output="Saved via MCP"
        )
        
        buffers = [
            Buffer(name="title", payload=name_arg),
            Buffer(name="timestamp", payload=datetime.now().isoformat()),
            Buffer(name="type", payload=task_type),
        ]
        if desc:
            buffers.append(Buffer(name="description", payload=desc))
        
        card = mem.store_card(
            label="tasc",
            buffers=buffers,
            owner_self="MCP",
            moment_id=moment.id
        )
        
        return {"card_id": card.id, "name": name_arg}
    
    elif name == "supe_tasc_list":
        from ab.abdb import ABMemory
        
        limit = arguments.get("limit", 20)
        db_path = os.environ.get("TASC_DB", "tasc.sqlite")
        mem = ABMemory(db_path)
        
        cursor = mem.conn.execute(
            "SELECT id, label, owner_self, created_at FROM cards ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        
        results = []
        for row in cursor.fetchall():
            card_id, label, owner, created = row
            title_cursor = mem.conn.execute(
                "SELECT payload FROM buffers WHERE card_id = ? AND name = 'title'",
                (card_id,)
            )
            title_row = title_cursor.fetchone()
            title = title_row[0] if title_row else "(untitled)"
            
            results.append({
                "id": card_id,
                "label": label,
                "title": title,
                "owner": owner,
            })
        
        return {"tascs": results, "count": len(results)}
    
    elif name == "supe_tasc_recall":
        from ab.abdb import ABMemory
        
        query = arguments["query"]
        db_path = os.environ.get("TASC_DB", "tasc.sqlite")
        mem = ABMemory(db_path)
        
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
        
        results = []
        for card_id, label, buf_name, payload in cursor.fetchall():
            results.append({
                "card_id": card_id,
                "label": label,
                "buffer": buf_name,
                "snippet": str(payload)[:100],
            })
        
        return {"results": results, "count": len(results)}
    
    elif name == "supe_run_safe":
        from tascer.overlord.legality import check_action_legality
        from tascer.primitives import run_and_observe
        
        command = arguments["command"]
        force = arguments.get("force", False)
        
        # Check legality
        legality = check_action_legality(
            action_id="terminal.run",
            inputs={"command": command},
            permissions={"terminal"},
            has_checkpoint=force,
        )
        
        if not legality.is_legal and not force:
            return {
                "blocked": True,
                "reason": legality.violations[0] if legality.violations else "Unknown",
                "warnings": legality.warnings,
            }
        
        # Execute
        result = run_and_observe(command, shell=True, timeout_sec=60)
        
        return {
            "blocked": False,
            "exit_code": result.exit_code,
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:500],
            "duration_ms": result.duration_ms,
        }
    
    else:
        return {"error": f"Unknown tool: {name}"}


def handle_request(request: Dict[str, Any]):
    """Handle an incoming JSON-RPC request."""
    method = request.get("method")
    params = request.get("params", {})
    req_id = request.get("id")
    
    if method == "initialize":
        send_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "supe-mcp-server",
                "version": "0.1.0",
            }
        })
    
    elif method == "notifications/initialized":
        # Client acknowledged initialization
        pass
    
    elif method == "tools/list":
        send_response(req_id, {"tools": TOOLS})
    
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        try:
            result = handle_tool_call(tool_name, tool_args)
            send_response(req_id, {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)}
                ]
            })
        except Exception as e:
            send_response(req_id, {
                "content": [
                    {"type": "text", "text": f"Error: {str(e)}"}
                ],
                "isError": True
            })
    
    elif method == "ping":
        send_response(req_id, {})
    
    else:
        if req_id is not None:
            send_response(req_id, error={
                "code": -32601,
                "message": f"Method not found: {method}"
            })


def main():
    """Main MCP server loop."""
    # Add project to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Read JSON-RPC messages from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            handle_request(request)
        except json.JSONDecodeError as e:
            send_response(None, error={
                "code": -32700,
                "message": f"Parse error: {e}"
            })
        except Exception as e:
            send_response(None, error={
                "code": -32603,
                "message": f"Internal error: {e}"
            })


if __name__ == "__main__":
    main()
