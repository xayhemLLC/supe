"""Discord Integration Plugin for Tasc.

Enables Tasc to:
- Send messages to Discord channels
- Receive commands from Discord
- Report task status
- Share evidence (screenshots, logs)
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from . import Plugin, PluginInfo, PluginEvent, PluginStatus

# Try to import discord.py
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False


@dataclass
class DiscordMessage:
    """A message to/from Discord."""
    
    channel_id: int
    content: str
    author: str = "tascer"
    attachments: List[str] = field(default_factory=list)
    embed: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class DiscordPlugin(Plugin):
    """Discord integration for Tasc.
    
    Provides actions:
    - discord.send: Send a message to a channel
    - discord.status: Update bot status
    - discord.upload: Upload a file/screenshot
    
    Listens for:
    - !tasc <command> - Execute Tasc commands
    - !status - Get current task status
    - !screenshot - Request a screenshot
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        command_prefix: str = "!",
        default_channel: Optional[int] = None,
    ):
        super().__init__()
        self.token = token or os.environ.get("DISCORD_BOT_TOKEN")
        self.command_prefix = command_prefix
        self.default_channel = default_channel
        
        self._bot = None
        self._message_queue: List[DiscordMessage] = []
        self._command_handlers: Dict[str, Callable] = {}
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="discord",
            version="1.0.0",
            description="Discord bot integration for Tasc",
            author="Tasc",
            requires=["discord.py"],
            capabilities=["messaging", "file_upload", "commands"],
        )
    
    async def initialize(self) -> bool:
        """Initialize the Discord bot."""
        if not DISCORD_AVAILABLE:
            self._status = PluginStatus.ERROR
            self._error = "discord.py not installed. Run: pip install discord.py"
            return False
        
        if not self.token:
            self._status = PluginStatus.ERROR
            self._error = "No Discord token provided. Set DISCORD_BOT_TOKEN env var."
            return False
        
        # Create bot with intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        self._bot = commands.Bot(
            command_prefix=self.command_prefix,
            intents=intents,
        )
        
        # Register commands
        self._setup_commands()
        
        self._status = PluginStatus.READY
        return True
    
    def _setup_commands(self):
        """Set up Discord commands."""
        bot = self._bot
        
        @bot.command(name="tasc")
        async def tasc_command(ctx, *, command: str = ""):
            """Execute a Tasc command."""
            await ctx.send(f"🤖 Executing: `{command}`")
            # This would integrate with the Overlord
            result = self._execute_command(command)
            await ctx.send(f"✅ Result: {result}")
        
        @bot.command(name="status")
        async def status_command(ctx):
            """Get current Tasc status."""
            status = self.get_context()
            embed = discord.Embed(
                title="Tasc Status",
                color=0x00ff00,
            )
            embed.add_field(name="Status", value=status.get("status", "idle"))
            embed.add_field(name="Actions", value=status.get("actions_taken", 0))
            await ctx.send(embed=embed)
    
    def _execute_command(self, command: str) -> str:
        """Execute a command (stub for integration)."""
        # This would connect to the Overlord
        return f"Command '{command}' acknowledged"
    
    async def shutdown(self) -> None:
        """Shutdown the bot."""
        if self._bot:
            await self._bot.close()
        self._status = PluginStatus.UNLOADED
    
    def get_actions(self) -> Dict[str, Callable]:
        """Return Discord actions."""
        return {
            "send": self.send_message,
            "status": self.update_status,
            "upload": self.upload_file,
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Return Discord context."""
        return {
            "available": DISCORD_AVAILABLE,
            "connected": self._bot is not None,
            "status": self._status.value,
            "pending_messages": len(self._message_queue),
        }
    
    async def send_message(
        self,
        content: str,
        channel_id: Optional[int] = None,
        embed: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a message to Discord.
        
        ACTION: discord.send
        """
        if not self._bot or self._status != PluginStatus.READY:
            # Queue for later
            self._message_queue.append(DiscordMessage(
                channel_id=channel_id or self.default_channel or 0,
                content=content,
                embed=embed,
            ))
            return False
        
        try:
            channel = self._bot.get_channel(channel_id or self.default_channel)
            if channel:
                if embed:
                    discord_embed = discord.Embed.from_dict(embed)
                    await channel.send(content, embed=discord_embed)
                else:
                    await channel.send(content)
                return True
        except Exception:
            pass
        return False
    
    async def update_status(self, status: str) -> bool:
        """Update bot status.
        
        ACTION: discord.status
        """
        if not self._bot:
            return False
        try:
            await self._bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=status,
                )
            )
            return True
        except Exception:
            return False
    
    async def upload_file(
        self,
        file_path: str,
        channel_id: Optional[int] = None,
        message: str = "",
    ) -> bool:
        """Upload a file to Discord.
        
        ACTION: discord.upload
        """
        if not self._bot or not os.path.exists(file_path):
            return False
        
        try:
            channel = self._bot.get_channel(channel_id or self.default_channel)
            if channel:
                await channel.send(message, file=discord.File(file_path))
                return True
        except Exception:
            pass
        return False
    
    def on_event(self, event: PluginEvent) -> Optional[Dict[str, Any]]:
        """React to Tasc events."""
        if event.event_type == "task_complete":
            # Could notify Discord
            pass
        elif event.event_type == "error":
            # Could alert Discord
            pass
        return None
