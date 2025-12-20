"""Tests for Tasc Plugin System."""
import pytest
import asyncio
from datetime import datetime


class TestPluginBase:
    """Test base Plugin class."""
    
    def test_create_plugin(self):
        """Test creating a basic plugin."""
        from tascer.plugins import Plugin, PluginInfo, PluginStatus
        
        class TestPlugin(Plugin):
            @property
            def info(self):
                return PluginInfo(
                    name="test",
                    version="1.0.0",
                    description="Test plugin",
                )
        
        plugin = TestPlugin()
        assert plugin.info.name == "test"
        assert plugin.info.version == "1.0.0"
        assert plugin.status == PluginStatus.UNLOADED
    
    def test_plugin_actions(self):
        """Test plugin with custom actions."""
        from tascer.plugins import Plugin, PluginInfo
        
        class MathPlugin(Plugin):
            @property
            def info(self):
                return PluginInfo(name="math", version="1.0.0", description="Math ops")
            
            def get_actions(self):
                return {
                    "add": lambda a, b: a + b,
                    "multiply": lambda a, b: a * b,
                }
        
        plugin = MathPlugin()
        actions = plugin.get_actions()
        
        assert "add" in actions
        assert "multiply" in actions
        assert actions["add"](2, 3) == 5
        assert actions["multiply"](4, 5) == 20
    
    def test_plugin_context(self):
        """Test plugin context injection."""
        from tascer.plugins import Plugin, PluginInfo
        
        class ContextPlugin(Plugin):
            @property
            def info(self):
                return PluginInfo(name="ctx", version="1.0.0", description="Context")
            
            def get_context(self):
                return {"setting": "value", "enabled": True}
        
        plugin = ContextPlugin()
        ctx = plugin.get_context()
        
        assert ctx["setting"] == "value"
        assert ctx["enabled"] is True


class TestPluginRegistry:
    """Test PluginRegistry."""
    
    def test_register_plugin(self):
        """Test registering a plugin."""
        from tascer.plugins import Plugin, PluginInfo, PluginRegistry
        
        class DemoPlugin(Plugin):
            @property
            def info(self):
                return PluginInfo(name="demo", version="1.0.0", description="Demo")
        
        registry = PluginRegistry()
        result = registry.register(DemoPlugin())
        
        assert result is True
        assert len(registry.list_plugins()) == 1
    
    def test_register_duplicate_fails(self):
        """Test registering same plugin twice fails."""
        from tascer.plugins import Plugin, PluginInfo, PluginRegistry
        
        class DemoPlugin(Plugin):
            @property
            def info(self):
                return PluginInfo(name="demo", version="1.0.0", description="Demo")
        
        registry = PluginRegistry()
        registry.register(DemoPlugin())
        result = registry.register(DemoPlugin())
        
        assert result is False
    
    def test_get_action(self):
        """Test getting plugin action."""
        from tascer.plugins import Plugin, PluginInfo, PluginRegistry
        
        class GreetPlugin(Plugin):
            @property
            def info(self):
                return PluginInfo(name="greet", version="1.0.0", description="Greet")
            
            def get_actions(self):
                return {"hello": lambda name: f"Hello, {name}!"}
        
        registry = PluginRegistry()
        registry.register(GreetPlugin())
        
        action = registry.get_action("greet.hello")
        assert action is not None
        assert action("World") == "Hello, World!"
    
    def test_emit_event(self):
        """Test emitting events to plugins."""
        from tascer.plugins import Plugin, PluginInfo, PluginRegistry, PluginEvent, PluginStatus
        
        class EventPlugin(Plugin):
            def __init__(self):
                super().__init__()
                self.received_events = []
                self._status = PluginStatus.READY
            
            @property
            def info(self):
                return PluginInfo(name="event", version="1.0.0", description="Event")
            
            def on_event(self, event):
                self.received_events.append(event)
                return {"received": True}
        
        plugin = EventPlugin()
        registry = PluginRegistry()
        registry.register(plugin)
        
        event = PluginEvent(
            event_type="test",
            timestamp=datetime.now(),
            source="test",
            data={"key": "value"},
        )
        
        responses = registry.emit_event(event)
        
        assert len(responses) == 1
        assert responses[0]["received"] is True
        assert len(plugin.received_events) == 1
    
    def test_combined_context(self):
        """Test getting combined context from all plugins."""
        from tascer.plugins import Plugin, PluginInfo, PluginRegistry, PluginStatus
        
        class Plugin1(Plugin):
            def __init__(self):
                super().__init__()
                self._status = PluginStatus.READY
            
            @property
            def info(self):
                return PluginInfo(name="p1", version="1.0.0", description="P1")
            
            def get_context(self):
                return {"from": "p1"}
        
        class Plugin2(Plugin):
            def __init__(self):
                super().__init__()
                self._status = PluginStatus.READY
            
            @property
            def info(self):
                return PluginInfo(name="p2", version="1.0.0", description="P2")
            
            def get_context(self):
                return {"from": "p2"}
        
        registry = PluginRegistry()
        registry.register(Plugin1())
        registry.register(Plugin2())
        
        context = registry.get_combined_context()
        
        assert "p1" in context
        assert "p2" in context
        assert context["p1"]["from"] == "p1"
        assert context["p2"]["from"] == "p2"


class TestDiscordPlugin:
    """Test Discord plugin."""
    
    def test_plugin_info(self):
        """Test Discord plugin info."""
        from tascer.plugins.discord_plugin import DiscordPlugin
        
        plugin = DiscordPlugin()
        
        assert plugin.info.name == "discord"
        assert "messaging" in plugin.info.capabilities
    
    def test_plugin_actions(self):
        """Test Discord plugin provides actions."""
        from tascer.plugins.discord_plugin import DiscordPlugin
        
        plugin = DiscordPlugin()
        actions = plugin.get_actions()
        
        assert "send" in actions
        assert "status" in actions
        assert "upload" in actions
    
    def test_plugin_context(self):
        """Test Discord plugin context."""
        from tascer.plugins.discord_plugin import DiscordPlugin
        
        plugin = DiscordPlugin()
        context = plugin.get_context()
        
        assert "available" in context
        assert "status" in context


class TestMCPPlugin:
    """Test MCP plugin."""
    
    def test_plugin_info(self):
        """Test MCP plugin info."""
        from tascer.plugins.mcp_plugin import MCPPlugin
        
        plugin = MCPPlugin()
        
        assert plugin.info.name == "mcp"
        assert "mcp_server" in plugin.info.capabilities
    
    def test_register_tools(self):
        """Test MCP tool registration."""
        from tascer.plugins.mcp_plugin import MCPPlugin
        
        plugin = MCPPlugin()
        plugin._register_tools()
        
        manifest = plugin.get_mcp_manifest()
        
        assert len(manifest["tools"]) > 0
        tool_names = [t["name"] for t in manifest["tools"]]
        assert "tascer_terminal_run" in tool_names
        assert "tascer_check_legality" in tool_names
    
    def test_handle_legality_check(self):
        """Test MCP legality check tool."""
        from tascer.plugins.mcp_plugin import MCPPlugin
        
        plugin = MCPPlugin()
        plugin._register_tools()
        
        # Safe command
        result = plugin.handle_tool_call("tascer_check_legality", {
            "action": "terminal.run",
            "command": "echo hello",
        })
        assert result["is_legal"] is True
        
        # Dangerous command
        result = plugin.handle_tool_call("tascer_check_legality", {
            "action": "terminal.run",
            "command": "rm -rf /",
        })
        assert result["is_legal"] is False
    
    def test_generate_config(self):
        """Test config generation."""
        from tascer.plugins.mcp_plugin import generate_mcp_config
        
        import json
        config = json.loads(generate_mcp_config())
        
        assert "mcpServers" in config
        assert "tascer" in config["mcpServers"]


class TestSlackPlugin:
    """Test Slack plugin."""
    
    def test_plugin_info(self):
        """Test Slack plugin info."""
        from tascer.plugins.slack_plugin import SlackPlugin
        
        plugin = SlackPlugin()
        
        assert plugin.info.name == "slack"
        assert "messaging" in plugin.info.capabilities
    
    def test_plugin_actions(self):
        """Test Slack plugin provides actions."""
        from tascer.plugins.slack_plugin import SlackPlugin
        
        plugin = SlackPlugin()
        actions = plugin.get_actions()
        
        assert "send" in actions
        assert "alert" in actions
        assert "status" in actions


class TestGitHubPlugin:
    """Test GitHub plugin."""
    
    def test_plugin_info(self):
        """Test GitHub plugin info."""
        from tascer.plugins.github_plugin import GitHubPlugin
        
        plugin = GitHubPlugin()
        
        assert plugin.info.name == "github"
        assert "issues" in plugin.info.capabilities
    
    def test_plugin_actions(self):
        """Test GitHub plugin provides actions."""
        from tascer.plugins.github_plugin import GitHubPlugin
        
        plugin = GitHubPlugin()
        actions = plugin.get_actions()
        
        assert "comment" in actions
        assert "status" in actions
        assert "issue" in actions
        assert "workflow" in actions


class TestWebhookPlugin:
    """Test Webhook plugin."""
    
    def test_plugin_info(self):
        """Test Webhook plugin info."""
        from tascer.plugins.webhook_plugin import WebhookPlugin
        
        plugin = WebhookPlugin()
        
        assert plugin.info.name == "webhook"
        assert "http" in plugin.info.capabilities
    
    def test_register_webhook(self):
        """Test registering a webhook."""
        from tascer.plugins.webhook_plugin import WebhookPlugin
        
        plugin = WebhookPlugin()
        result = plugin.register_webhook(
            name="test",
            url="https://example.com/webhook",
            events=["task_complete"],
        )
        
        assert result is True
        webhooks = plugin.list_webhooks()
        assert len(webhooks) == 1
        assert webhooks[0]["name"] == "test"
    
    def test_list_webhooks(self):
        """Test listing webhooks."""
        from tascer.plugins.webhook_plugin import WebhookPlugin
        
        plugin = WebhookPlugin()
        plugin.register_webhook("w1", "https://a.com", ["*"])
        plugin.register_webhook("w2", "https://b.com", ["error"])
        
        webhooks = plugin.list_webhooks()
        
        assert len(webhooks) == 2
        names = [w["name"] for w in webhooks]
        assert "w1" in names
        assert "w2" in names
