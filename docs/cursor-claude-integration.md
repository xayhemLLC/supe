# Cursor & Claude Integration

Supe integrates with both **Cursor** and **Claude Desktop** via the Model Context Protocol (MCP).

## Quick Setup

### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "supe": {
      "command": "/Users/chriscabral/Desktop/super/supe/.venv/bin/python",
      "args": ["-m", "supe.mcp_server"],
      "cwd": "/Users/chriscabral/Desktop/super/supe"
    }
  }
}
```

### For Cursor

Add to Cursor's MCP settings (`~/.cursor/mcp.json` or via Settings → MCP):

```json
{
  "mcpServers": {
    "supe": {
      "command": "/Users/chriscabral/Desktop/super/supe/.venv/bin/python",
      "args": ["-m", "supe.mcp_server"],
      "cwd": "/Users/chriscabral/Desktop/super/supe"
    }
  }
}
```

## Available Tools

Once configured, AI assistants can use these tools:

| Tool | Description |
|------|-------------|
| `supe_prove` | Execute command with proof generation |
| `supe_verify` | Verify an existing proof |
| `supe_status` | Get system status |
| `supe_plan_create` | Create a structured plan |
| `supe_plan_execute` | Execute plan with proofs |
| `supe_tasc_save` | Save work to AB Memory |
| `supe_tasc_list` | List recent tascs |
| `supe_tasc_recall` | Search past work |
| `supe_run_safe` | Run with safety checks |

## Example Usage

When chatting with Claude or Cursor AI:

```
"Prove that the tests pass"
→ Uses supe_prove to run pytest with proof generation

"Create a plan for implementing auth"
→ Uses supe_plan_create to structure the work

"Save this as a tasc called 'auth implementation'"
→ Uses supe_tasc_save to store in AB Memory

"What work have I done on login?"
→ Uses supe_tasc_recall to search history
```

## Testing the MCP Server

```bash
# Test the server starts
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  .venv/bin/python -m supe.mcp_server

# Expected response:
# {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", ...}}
```

## Proof-of-Work Flow

When an AI uses supe tools:

1. **AI requests action** → `supe_prove "pytest tests/"`
2. **Supe executes** → Runs command, captures output
3. **Proof generated** → Cryptographic hash of execution
4. **Result returned** → AI sees proven/not proven + evidence
5. **Proof stored** → `.tascer/proofs/<id>.json`

This creates an auditable trail of AI actions with validation.
