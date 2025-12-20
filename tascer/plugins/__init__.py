"""Tasc Plugin System - Extensible integrations.

Plugins allow Tasc to integrate with external systems:
- Discord bots
- Slack
- Claude Code / Cursor (via MCP)
- GitHub Actions
- Custom webhooks
"""

import abc
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type


class PluginStatus(Enum):
    """Plugin lifecycle status."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginInfo:
    """Metadata about a plugin."""
    
    name: str
    version: str
    description: str
    author: str = ""
    requires: List[str] = field(default_factory=list)  # Dependencies
    capabilities: List[str] = field(default_factory=list)  # What it provides


@dataclass
class PluginEvent:
    """Event that plugins can subscribe to."""
    
    event_type: str
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)


class Plugin(abc.ABC):
    """Base class for all Tasc plugins.
    
    Plugins can:
    - Provide new actions
    - Listen to events
    - Inject context
    - Transform outputs
    """
    
    def __init__(self):
        self._status = PluginStatus.UNLOADED
        self._error: Optional[str] = None
    
    @property
    @abc.abstractmethod
    def info(self) -> PluginInfo:
        """Return plugin metadata."""
        pass
    
    @property
    def status(self) -> PluginStatus:
        return self._status
    
    async def initialize(self) -> bool:
        """Initialize the plugin. Override to add setup logic."""
        self._status = PluginStatus.READY
        return True
    
    async def shutdown(self) -> None:
        """Shutdown the plugin. Override to add cleanup logic."""
        self._status = PluginStatus.UNLOADED
    
    def on_event(self, event: PluginEvent) -> Optional[Dict[str, Any]]:
        """Handle an event. Override to react to events."""
        return None
    
    def get_actions(self) -> Dict[str, Callable]:
        """Return actions this plugin provides. Override to add actions."""
        return {}
    
    def get_context(self) -> Dict[str, Any]:
        """Return context to inject into prompts. Override to add context."""
        return {}


class PluginRegistry:
    """Manages plugin lifecycle and discovery."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._event_handlers: Dict[str, List[Plugin]] = {}
        self._actions: Dict[str, Callable] = {}
    
    def register(self, plugin: Plugin) -> bool:
        """Register a plugin."""
        info = plugin.info
        
        if info.name in self._plugins:
            return False
        
        self._plugins[info.name] = plugin
        
        # Register actions
        for action_name, handler in plugin.get_actions().items():
            full_name = f"{info.name}.{action_name}"
            self._actions[full_name] = handler
        
        return True
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all registered plugins."""
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = await plugin.initialize()
            except Exception as e:
                plugin._status = PluginStatus.ERROR
                plugin._error = str(e)
                results[name] = False
        return results
    
    async def shutdown_all(self) -> None:
        """Shutdown all plugins."""
        for plugin in self._plugins.values():
            await plugin.shutdown()
    
    def emit_event(self, event: PluginEvent) -> List[Dict[str, Any]]:
        """Emit an event to all plugins."""
        responses = []
        for plugin in self._plugins.values():
            if plugin.status == PluginStatus.READY:
                result = plugin.on_event(event)
                if result:
                    responses.append(result)
        return responses
    
    def get_action(self, name: str) -> Optional[Callable]:
        """Get an action by name."""
        return self._actions.get(name)
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all registered plugins."""
        return [p.info for p in self._plugins.values()]
    
    def get_combined_context(self) -> Dict[str, Any]:
        """Get combined context from all plugins."""
        context = {}
        for plugin in self._plugins.values():
            if plugin.status == PluginStatus.READY:
                context[plugin.info.name] = plugin.get_context()
        return context


# Global registry
_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_plugin(plugin: Plugin) -> bool:
    """Convenience function to register a plugin."""
    return get_plugin_registry().register(plugin)
