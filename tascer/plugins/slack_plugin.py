"""Slack Integration Plugin for Tasc.

Enables Tasc to:
- Send messages to Slack channels
- Post evidence (screenshots, logs, reports)
- Receive slash commands
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from . import Plugin, PluginInfo, PluginEvent, PluginStatus


@dataclass
class SlackMessage:
    """A Slack message."""
    
    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None


class SlackPlugin(Plugin):
    """Slack integration for Tasc.
    
    Provides actions:
    - slack.send: Send a message
    - slack.upload: Upload a file
    - slack.status: Post status update
    - slack.alert: Send alert with mention
    
    Configuration:
        Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN env var.
    """
    
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: str = "#general",
    ):
        super().__init__()
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")
        self.default_channel = default_channel
        self._message_queue: List[SlackMessage] = []
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="slack",
            version="1.0.0",
            description="Slack integration for notifications and alerts",
            author="Tasc",
            requires=[],
            capabilities=["messaging", "file_upload", "alerts"],
        )
    
    async def initialize(self) -> bool:
        """Initialize Slack connection."""
        if not self.webhook_url and not self.bot_token:
            self._status = PluginStatus.ERROR
            self._error = "No Slack credentials. Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN."
            return False
        
        self._status = PluginStatus.READY
        return True
    
    def get_actions(self) -> Dict[str, Callable]:
        """Return Slack actions."""
        return {
            "send": self.send_message,
            "upload": self.upload_file,
            "status": self.post_status,
            "alert": self.send_alert,
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Return Slack context."""
        return {
            "configured": bool(self.webhook_url or self.bot_token),
            "default_channel": self.default_channel,
            "pending_messages": len(self._message_queue),
        }
    
    def send_message(
        self,
        text: str,
        channel: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Send a message to Slack.
        
        ACTION: slack.send
        """
        payload = {
            "channel": channel or self.default_channel,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks
        
        return self._post_to_slack(payload)
    
    def post_status(
        self,
        title: str,
        status: str,
        details: Optional[str] = None,
        color: str = "#36a64f",
    ) -> bool:
        """Post a status update with formatting.
        
        ACTION: slack.status
        """
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🤖 Tasc: {title}"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{datetime.now().strftime('%H:%M:%S')}"},
                ]
            },
        ]
        
        if details:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": details}
            })
        
        return self.send_message(title, blocks=blocks)
    
    def send_alert(
        self,
        message: str,
        mention: str = "@channel",
        severity: str = "warning",
    ) -> bool:
        """Send an alert with mention.
        
        ACTION: slack.alert
        """
        emoji = {"error": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(severity, "⚠️")
        text = f"{emoji} {mention} {message}"
        return self.send_message(text)
    
    def upload_file(
        self,
        file_path: str,
        channel: Optional[str] = None,
        title: Optional[str] = None,
    ) -> bool:
        """Upload a file to Slack.
        
        ACTION: slack.upload
        
        Note: Requires bot token, not webhook.
        """
        if not self.bot_token:
            return False
        
        # File upload requires multipart form - simplified stub
        # In production, use requests or httpx library
        return False
    
    def _post_to_slack(self, payload: Dict[str, Any]) -> bool:
        """Post to Slack webhook."""
        if not self.webhook_url:
            self._message_queue.append(SlackMessage(
                channel=payload.get("channel", self.default_channel),
                text=payload.get("text", ""),
                blocks=payload.get("blocks"),
            ))
            return False
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=10) as response:
                return response.status == 200
        except URLError:
            return False
    
    def on_event(self, event: PluginEvent) -> Optional[Dict[str, Any]]:
        """React to Tasc events."""
        if event.event_type == "task_complete":
            self.post_status(
                "Task Complete",
                event.data.get("status", "Done"),
                event.data.get("summary"),
            )
        elif event.event_type == "error":
            self.send_alert(
                event.data.get("message", "Unknown error"),
                severity="error",
            )
        return None
