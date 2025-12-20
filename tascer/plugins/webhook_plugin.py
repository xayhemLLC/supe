"""Webhook Plugin for Tasc.

A generic webhook plugin for sending events to any HTTP endpoint.
Perfect for custom integrations, monitoring, and automation.
"""

import json
import hashlib
import hmac
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from . import Plugin, PluginInfo, PluginEvent, PluginStatus


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""
    
    name: str
    url: str
    events: List[str]  # Event types to send
    secret: Optional[str] = None  # For HMAC signing
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class WebhookPlugin(Plugin):
    """Generic webhook integration for Tasc.
    
    Provides actions:
    - webhook.send: Send data to a webhook
    - webhook.register: Register a new webhook
    - webhook.trigger: Trigger webhook for event
    
    Events automatically forwarded:
    - task_start, task_complete, error, checkpoint, etc.
    """
    
    def __init__(self):
        super().__init__()
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._event_log: List[Dict[str, Any]] = []
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="webhook",
            version="1.0.0",
            description="Generic webhook integration for custom endpoints",
            author="Tasc",
            requires=[],
            capabilities=["http", "events", "signing"],
        )
    
    async def initialize(self) -> bool:
        """Initialize webhook plugin."""
        # Load webhooks from environment
        webhook_url = os.environ.get("TASCER_WEBHOOK_URL")
        if webhook_url:
            self.register_webhook(
                name="default",
                url=webhook_url,
                events=["*"],
                secret=os.environ.get("TASCER_WEBHOOK_SECRET"),
            )
        
        self._status = PluginStatus.READY
        return True
    
    def get_actions(self) -> Dict[str, Callable]:
        """Return webhook actions."""
        return {
            "send": self.send_webhook,
            "register": self.register_webhook,
            "trigger": self.trigger_event,
            "list": self.list_webhooks,
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Return webhook context."""
        return {
            "webhooks_registered": len(self._webhooks),
            "events_sent": len(self._event_log),
        }
    
    def register_webhook(
        self,
        name: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Register a new webhook endpoint.
        
        ACTION: webhook.register
        
        Args:
            name: Unique name for this webhook.
            url: HTTP endpoint URL.
            events: List of event types to forward (use "*" for all).
            secret: Optional secret for HMAC signature.
            headers: Optional custom headers.
        """
        self._webhooks[name] = WebhookConfig(
            name=name,
            url=url,
            events=events,
            secret=secret,
            headers=headers or {},
        )
        return True
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List registered webhooks.
        
        ACTION: webhook.list
        """
        return [
            {
                "name": w.name,
                "url": w.url[:50] + "..." if len(w.url) > 50 else w.url,
                "events": w.events,
                "enabled": w.enabled,
            }
            for w in self._webhooks.values()
        ]
    
    def send_webhook(
        self,
        name: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send data to a specific webhook.
        
        ACTION: webhook.send
        """
        webhook = self._webhooks.get(name)
        if not webhook:
            return {"error": f"Webhook '{name}' not found"}
        
        if not webhook.enabled:
            return {"error": f"Webhook '{name}' is disabled"}
        
        return self._send_to_webhook(webhook, data)
    
    def trigger_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Trigger all webhooks subscribed to an event.
        
        ACTION: webhook.trigger
        """
        results = []
        
        for webhook in self._webhooks.values():
            if not webhook.enabled:
                continue
            
            if "*" in webhook.events or event_type in webhook.events:
                payload = {
                    "event": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "data": data,
                }
                result = self._send_to_webhook(webhook, payload)
                results.append({"webhook": webhook.name, **result})
        
        return results
    
    def _send_to_webhook(
        self,
        webhook: WebhookConfig,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send data to a webhook endpoint."""
        payload = json.dumps(data, default=str).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Tasc/1.0",
            "X-Tasc-Event": data.get("event", "unknown"),
            **webhook.headers,
        }
        
        # Add HMAC signature if secret is configured
        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode("utf-8"),
                payload,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Tasc-Signature"] = f"sha256={signature}"
        
        try:
            req = Request(webhook.url, data=payload, headers=headers, method="POST")
            with urlopen(req, timeout=10) as response:
                self._event_log.append({
                    "webhook": webhook.name,
                    "event": data.get("event"),
                    "status": response.status,
                    "timestamp": datetime.now().isoformat(),
                })
                return {"success": True, "status": response.status}
        except URLError as e:
            return {"success": False, "error": str(e)}
    
    def on_event(self, event: PluginEvent) -> Optional[Dict[str, Any]]:
        """Forward Tasc events to webhooks."""
        results = self.trigger_event(event.event_type, event.data)
        return {"webhooks_triggered": len(results)} if results else None
