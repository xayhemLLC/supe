# Tasc Plugin Development Guide

Tasc's plugin system allows you to extend functionality with custom integrations.

## Quick Start

```python
from tascer.plugins import Plugin, PluginInfo, PluginRegistry

class MyPlugin(Plugin):
    @property
    def info(self):
        return PluginInfo(
            name="my_plugin",
            version="1.0.0",
            description="My custom plugin",
            capabilities=["custom_feature"],
        )
    
    def get_actions(self):
        return {
            "hello": lambda name: f"Hello, {name}!",
        }

# Register and use
registry = PluginRegistry()
registry.register(MyPlugin())

action = registry.get_action("my_plugin.hello")
print(action("World"))  # Hello, World!
```

## Available Plugins

| Plugin | Purpose | Config |
|--------|---------|--------|
| `mcp` | Claude Code / Cursor integration | Add to mcp.json |
| `discord` | Discord bot commands | `DISCORD_BOT_TOKEN` |
| `slack` | Slack notifications | `SLACK_WEBHOOK_URL` |
| `github` | GitHub issues, PRs, workflows | `GITHUB_TOKEN` |
| `webhook` | Generic HTTP webhooks | `TASCER_WEBHOOK_URL` |
| `metrics` | Prometheus observability | Port 9090 |

## Plugin Lifecycle

```python
class MyPlugin(Plugin):
    async def initialize(self) -> bool:
        """Called when plugin is loaded. Return True if successful."""
        self._status = PluginStatus.READY
        return True
    
    async def shutdown(self) -> None:
        """Called when plugin is unloaded."""
        pass
```

## Providing Actions

Actions are functions that can be called via the registry:

```python
def get_actions(self):
    return {
        "action_name": self.my_action,
        "another": lambda x: x * 2,
    }

def my_action(self, param: str) -> str:
    return f"Result: {param}"
```

Actions are accessed as `plugin_name.action_name`:

```python
action = registry.get_action("my_plugin.action_name")
result = action("input")
```

## Context Injection

Plugins can inject context into prompts:

```python
def get_context(self) -> Dict[str, Any]:
    return {
        "api_key_configured": bool(self.api_key),
        "current_status": self.status,
        "instructions": "Use my_plugin.action for X",
    }
```

## Event Handling

Plugins can react to Tasc events:

```python
def on_event(self, event: PluginEvent) -> Optional[Dict[str, Any]]:
    if event.event_type == "task_complete":
        self.send_notification(event.data)
    elif event.event_type == "error":
        self.alert_team(event.data)
    return {"handled": True}
```

### Event Types

- `task_start` - Task begins
- `task_complete` - Task finishes
- `action_start` - Action execution starting
- `action_complete` - Action execution finished
- `checkpoint` - Checkpoint created
- `rollback` - Rollback performed
- `error` - Error occurred
- `legality_check` - Safety check performed

## Example: Webhook Plugin

```python
from tascer.plugins import Plugin, PluginInfo, PluginEvent
import json
from urllib.request import Request, urlopen

class NotifyPlugin(Plugin):
    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
    
    @property
    def info(self):
        return PluginInfo(
            name="notify",
            version="1.0.0",
            description="Send notifications",
            capabilities=["notifications"],
        )
    
    def get_actions(self):
        return {
            "send": self.send_notification,
        }
    
    def send_notification(self, message: str) -> bool:
        data = json.dumps({"text": message}).encode()
        req = Request(self.webhook_url, data=data)
        req.add_header("Content-Type", "application/json")
        with urlopen(req) as resp:
            return resp.status == 200
    
    def on_event(self, event: PluginEvent):
        if event.event_type in ("error", "task_complete"):
            self.send_notification(f"{event.event_type}: {event.data}")
```

## MCP Integration for AI Assistants

The MCP plugin exposes Tasc to Claude Code and Cursor:

```json
// ~/.config/claude/mcp.json
{
  "mcpServers": {
    "tascer": {
      "command": "python",
      "args": ["-m", "tascer.plugins.mcp_server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

Available MCP tools:
- `tascer_terminal_run` - Execute commands safely
- `tascer_file_read` - Read files with verification
- `tascer_checkpoint_create` - Create rollback point
- `tascer_checkpoint_rollback` - Undo changes
- `tascer_browser_capture` - Screenshot web pages
- `tascer_check_legality` - Verify action is safe

## Testing Plugins

```python
import pytest
from tascer.plugins import PluginRegistry

def test_my_plugin():
    from my_plugin import MyPlugin
    
    registry = PluginRegistry()
    registry.register(MyPlugin())
    
    action = registry.get_action("my_plugin.hello")
    assert action("Test") == "Hello, Test!"
```
