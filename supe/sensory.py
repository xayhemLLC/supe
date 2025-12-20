"""Sensory Organs for the Supe.

Sensory organs gather input from external sources:
- BrowserOrgan: Scrapes web content via CDPBrowser
- ClaudeOrgan: Uses Claude CLI in headless mode with JSON output

The sensory track receives raw data from organs, gets flushed each moment.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import subprocess


@dataclass
class SensoryInput:
    """Raw input from a sensory organ.
    
    This is ephemeral - flushed after each moment.
    """
    
    organ_name: str
    input_type: str  # 'html', 'json', 'text', 'image', etc.
    data: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SensoryOrgan(ABC):
    """Base class for sensory organs.
    
    A sensory organ gathers input from an external source.
    """
    
    name: str
    organ_type: str
    
    @abstractmethod
    async def sense(self, **kwargs) -> SensoryInput:
        """Gather sensory input.
        
        Returns:
            SensoryInput with raw data.
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get organ configuration for persistence."""
        pass


class BrowserOrgan(SensoryOrgan):
    """Sensory organ that gathers input via browser automation.
    
    Example:
        organ = BrowserOrgan()
        input = await organ.sense(url="https://discord.com/developers/docs/change-log")
    """
    
    name = "browser"
    organ_type = "browser"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
    
    async def sense(
        self, 
        url: str,
        wait_ms: int = 3000,
        take_screenshot: bool = False,
    ) -> SensoryInput:
        """Sense a web page via browser.
        
        Args:
            url: URL to navigate to.
            wait_ms: Time to wait for page load.
            take_screenshot: Whether to capture screenshot.
        
        Returns:
            SensoryInput with HTML content.
        """
        from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE
        
        if not CDP_BROWSER_AVAILABLE:
            raise RuntimeError("CDPBrowser not available")
        
        async with CDPBrowser(headless=self.headless) as browser:
            result = await browser.get(url, wait_time_ms=wait_ms, take_screenshot=take_screenshot)
            
            return SensoryInput(
                organ_name=self.name,
                input_type="html",
                data=result.text.encode("utf-8"),
                metadata={
                    "url": url,
                    "status_code": result.status_code,
                    "title": result.soup.title.string if result.soup.title else None,
                    "screenshot_path": result.screenshot_path,
                },
            )
    
    def get_config(self) -> Dict[str, Any]:
        return {"headless": self.headless}


class ClaudeOrgan(SensoryOrgan):
    """Sensory organ that uses Claude CLI in headless mode.
    
    Uses `claude` CLI with JSON output for structured responses.
    
    Example:
        organ = ClaudeOrgan()
        input = await organ.sense(prompt="Summarize the key changes in Discord's latest changelog")
    """
    
    name = "claude"
    organ_type = "llm"
    
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
    
    async def sense(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> SensoryInput:
        """Sense via Claude CLI.
        
        Args:
            prompt: The prompt to send.
            system_prompt: Optional system prompt.
            max_tokens: Maximum response tokens.
        
        Returns:
            SensoryInput with JSON response.
        """
        import asyncio
        
        # Build command
        cmd = [
            "claude",
            "--print",
            "--output-format", "json",
            "--max-tokens", str(max_tokens),
        ]
        
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        
        cmd.append(prompt)
        
        # Run async
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {stderr.decode()}")
        
        return SensoryInput(
            organ_name=self.name,
            input_type="json",
            data=stdout,
            metadata={
                "model": self.model,
                "prompt_length": len(prompt),
                "returncode": proc.returncode,
            },
        )
    
    def get_config(self) -> Dict[str, Any]:
        return {"model": self.model}


class FileOrgan(SensoryOrgan):
    """Sensory organ that reads files.
    
    Example:
        organ = FileOrgan()
        input = await organ.sense(path="/path/to/file.txt")
    """
    
    name = "file"
    organ_type = "filesystem"
    
    async def sense(self, path: str) -> SensoryInput:
        """Read a file.
        
        Args:
            path: Path to file.
        
        Returns:
            SensoryInput with file content.
        """
        import aiofiles
        import os
        
        try:
            # Determine if binary or text
            ext = os.path.splitext(path)[1].lower()
            binary_exts = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar'}
            
            if ext in binary_exts:
                async with aiofiles.open(path, 'rb') as f:
                    data = await f.read()
                input_type = "binary"
            else:
                async with aiofiles.open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = await f.read()
                data = text.encode('utf-8')
                input_type = "text"
            
            return SensoryInput(
                organ_name=self.name,
                input_type=input_type,
                data=data,
                metadata={
                    "path": path,
                    "size_bytes": len(data),
                    "extension": ext,
                },
            )
        except Exception as e:
            # Fallback for missing aiofiles
            with open(path, 'rb') as f:
                data = f.read()
            return SensoryInput(
                organ_name=self.name,
                input_type="binary",
                data=data,
                metadata={"path": path, "size_bytes": len(data)},
            )
    
    def get_config(self) -> Dict[str, Any]:
        return {}


class TerminalOrgan(SensoryOrgan):
    """Sensory organ that runs terminal commands.
    
    Example:
        organ = TerminalOrgan()
        input = await organ.sense(command="git status")
    """
    
    name = "terminal"
    organ_type = "shell"
    
    async def sense(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 30,
    ) -> SensoryInput:
        """Run a terminal command and capture output.
        
        Args:
            command: Command to run.
            cwd: Working directory.
            timeout: Timeout in seconds.
        
        Returns:
            SensoryInput with command output.
        """
        import asyncio
        
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"Command timed out: {command}")
        
        output = stdout + stderr
        
        return SensoryInput(
            organ_name=self.name,
            input_type="text",
            data=output,
            metadata={
                "command": command,
                "cwd": cwd,
                "returncode": proc.returncode,
                "success": proc.returncode == 0,
            },
        )
    
    def get_config(self) -> Dict[str, Any]:
        return {}


class ClipboardOrgan(SensoryOrgan):
    """Sensory organ that reads system clipboard.
    
    Example:
        organ = ClipboardOrgan()
        input = await organ.sense()
    """
    
    name = "clipboard"
    organ_type = "system"
    
    async def sense(self) -> SensoryInput:
        """Read clipboard contents.
        
        Returns:
            SensoryInput with clipboard text.
        """
        import subprocess
        
        # macOS
        try:
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return SensoryInput(
                    organ_name=self.name,
                    input_type="text",
                    data=result.stdout,
                    metadata={"source": "pbpaste"},
                )
        except:
            pass
        
        # Linux (xclip)
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                return SensoryInput(
                    organ_name=self.name,
                    input_type="text",
                    data=result.stdout,
                    metadata={"source": "xclip"},
                )
        except:
            pass
        
        return SensoryInput(
            organ_name=self.name,
            input_type="text",
            data=b"",
            metadata={"error": "No clipboard access"},
        )
    
    def get_config(self) -> Dict[str, Any]:
        return {}


class SensorySystem:
    """Manages all sensory organs for a Supe.
    
    Example:
        system = SensorySystem()
        system.register(BrowserOrgan())
        system.register(ClaudeOrgan())
        
        # Gather from specific organ
        input = await system.sense("browser", url="https://example.com")
    """
    
    def __init__(self):
        self._organs: Dict[str, SensoryOrgan] = {}
    
    def register(self, organ: SensoryOrgan) -> None:
        """Register a sensory organ."""
        self._organs[organ.name] = organ
    
    def get(self, name: str) -> Optional[SensoryOrgan]:
        """Get an organ by name."""
        return self._organs.get(name)
    
    def list_organs(self) -> List[str]:
        """List registered organ names."""
        return list(self._organs.keys())
    
    async def sense(self, organ_name: str, **kwargs) -> SensoryInput:
        """Gather input from a specific organ.
        
        Args:
            organ_name: Name of the organ to use.
            **kwargs: Passed to the organ's sense() method.
        
        Returns:
            SensoryInput from the organ.
        """
        organ = self._organs.get(organ_name)
        if not organ:
            raise KeyError(f"Unknown organ: {organ_name}")
        return await organ.sense(**kwargs)
    
    async def gather_all(self, **organ_kwargs: Dict[str, Any]) -> List[SensoryInput]:
        """Gather input from all active organs.
        
        Args:
            organ_kwargs: Dict of organ_name -> kwargs for each organ.
        
        Returns:
            List of SensoryInput from all organs.
        """
        inputs = []
        for name, organ in self._organs.items():
            if name in organ_kwargs:
                try:
                    input = await organ.sense(**organ_kwargs[name])
                    inputs.append(input)
                except Exception as e:
                    # Log but don't fail
                    print(f"Warning: {name} organ failed: {e}")
        return inputs
