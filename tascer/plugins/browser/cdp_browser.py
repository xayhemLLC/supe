"""Chrome DevTools Protocol (CDP) Browser.

A lightweight approach to control Chrome directly without Playwright/Selenium.
Uses the Chrome DevTools Protocol over WebSocket.

Requirements:
- Chrome or Chromium installed
- No additional Python packages needed (just websockets)

This is our OWN implementation - no Playwright dependency!
"""

import asyncio
import base64
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from bs4 import BeautifulSoup

from .human_input import InputType, request_human_input


@dataclass
class CDPPageResult:
    """Result from CDP browser."""
    url: str
    status_code: int = 200
    soup: Optional[BeautifulSoup] = None
    text: str = ""
    screenshot_data: Optional[bytes] = None
    screenshot_path: Optional[str] = None
    js_executed: bool = True
    
    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class CDPBrowser:
    """Chrome browser controlled via Chrome DevTools Protocol.
    
    This is our OWN implementation - no Playwright needed!
    Just requires Chrome/Chromium installed.
    
    Example:
        async with CDPBrowser() as browser:
            result = await browser.get("https://example.com")
            print(result.soup.title.text)
            
            # Execute custom JavaScript
            title = await browser.evaluate("document.title")
    """
    
    # Find Chrome/Chromium executable
    CHROME_PATHS = [
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    
    def __init__(
        self,
        headless: bool = True,
        user_data_dir: Optional[str] = None,
        screenshot_dir: str = ".tascer/screenshots",
    ):
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets package required: pip install websockets")
        
        self.headless = headless
        self.user_data_dir = user_data_dir or tempfile.mkdtemp(prefix="cdp_")
        self.screenshot_dir = screenshot_dir
        
        os.makedirs(screenshot_dir, exist_ok=True)
        
        self._process: Optional[subprocess.Popen] = None
        self._ws = None
        self._ws_url: Optional[str] = None
        self._message_id = 0
        self._session_id: Optional[str] = None
        self._current_url: Optional[str] = None
        self._viewport: Dict[str, int] = {"width": 1280, "height": 720}
    
    def get_state(self) -> Dict[str, Any]:
        """Return current browser state for context capture.
        
        Used for AB-style plugin context integration:
        
            context = capture_context(tasc_id="scrape_hn")
            context.plugin_state = browser.get_state()
        
        Returns:
            Dictionary with browser state including configuration and current URL.
        """
        return {
            "browser_type": "cdp",
            "chrome_path": self.find_chrome(),
            "headless": self.headless,
            "url": self._current_url,
            "viewport": self._viewport,
            "user_data_dir": self.user_data_dir,
            "screenshot_dir": self.screenshot_dir,
            "connected": self._ws is not None,
            "session_id": self._session_id,
        }
    
    @classmethod
    def find_chrome(cls) -> Optional[str]:
        """Find Chrome/Chromium executable.
        
        Checks in order:
        1. Standard Chrome/Chromium paths
        2. Playwright's cached Chromium
        3. System PATH
        """
        # Check standard paths first
        for path in cls.CHROME_PATHS:
            if os.path.exists(path):
                return path
        
        # Check Playwright's cached Chromium (macOS)
        playwright_cache = os.path.expanduser("~/Library/Caches/ms-playwright")
        if os.path.exists(playwright_cache):
            for item in sorted(os.listdir(playwright_cache), reverse=True):
                if item.startswith("chromium-"):
                    # macOS ARM64 path
                    chrome_path = os.path.join(
                        playwright_cache, item,
                        "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
                    )
                    if os.path.exists(chrome_path):
                        return chrome_path
                    
                    # macOS Intel path
                    chrome_path = os.path.join(
                        playwright_cache, item,
                        "chrome-mac/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
                    )
                    if os.path.exists(chrome_path):
                        return chrome_path
        
        # Check Linux Playwright cache
        linux_cache = os.path.expanduser("~/.cache/ms-playwright")
        if os.path.exists(linux_cache):
            for item in sorted(os.listdir(linux_cache), reverse=True):
                if item.startswith("chromium-"):
                    chrome_path = os.path.join(linux_cache, item, "chrome-linux/chrome")
                    if os.path.exists(chrome_path):
                        return chrome_path
        
        # Try which command
        try:
            result = subprocess.run(
                ["which", "google-chrome", "chromium", "chromium-browser"],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        
        return None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    async def start(self):
        """Start Chrome with remote debugging enabled."""
        chrome_path = self.find_chrome()
        if not chrome_path:
            raise RuntimeError(
                "Chrome/Chromium not found. Install Chrome or set path manually."
            )
        
        # Find a free port
        import socket
        with socket.socket() as s:
            s.bind(('', 0))
            port = s.getsockname()[1]
        
        # Launch Chrome
        args = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-client-side-phishing-detection",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-hang-monitor",
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--disable-translate",
            "--metrics-recording-only",
            "--safebrowsing-disable-auto-update",
        ]
        
        if self.headless:
            args.append("--headless=new")
        
        self._process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        
        # Wait for Chrome to start and get WebSocket URL
        import urllib.request
        for _ in range(50):  # 5 second timeout
            try:
                response = urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version")
                data = json.loads(response.read())
                self._ws_url = data["webSocketDebuggerUrl"]
                break
            except Exception:
                await asyncio.sleep(0.1)
        
        if not self._ws_url:
            raise RuntimeError("Failed to connect to Chrome")
        
        # Connect via WebSocket
        self._ws = await websockets.connect(self._ws_url)
        
        # Create a new target (tab)
        result = await self._send("Target.createTarget", {"url": "about:blank"})
        target_id = result["targetId"]
        
        # Attach to the target
        result = await self._send("Target.attachToTarget", {
            "targetId": target_id,
            "flatten": True,
        })
        self._session_id = result["sessionId"]
        
        # Enable necessary domains
        await self._send_session("Page.enable")
        await self._send_session("Network.enable")
        await self._send_session("Runtime.enable")
    
    async def close(self):
        """Close browser."""
        if self._ws:
            await self._ws.close()
        if self._process:
            self._process.terminate()
            self._process.wait()
    
    async def _send(self, method: str, params: Dict = None) -> Dict:
        """Send CDP command (browser-level)."""
        self._message_id += 1
        message = {
            "id": self._message_id,
            "method": method,
            "params": params or {},
        }
        await self._ws.send(json.dumps(message))
        
        # Wait for response
        while True:
            response = json.loads(await self._ws.recv())
            if response.get("id") == self._message_id:
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response.get("result", {})
    
    async def _send_session(self, method: str, params: Dict = None) -> Dict:
        """Send CDP command (session-level, for page control)."""
        self._message_id += 1
        message = {
            "id": self._message_id,
            "method": method,
            "params": params or {},
            "sessionId": self._session_id,
        }
        await self._ws.send(json.dumps(message))
        
        # Wait for response
        while True:
            response = json.loads(await self._ws.recv())
            if response.get("id") == self._message_id:
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response.get("result", {})
    
    async def get(
        self,
        url: str,
        wait_time_ms: int = 3000,
        take_screenshot: bool = False,
    ) -> CDPPageResult:
        """Navigate to URL and wait for content."""
        # Navigate
        await self._send_session("Page.navigate", {"url": url})
        self._current_url = url  # Track current URL for state capture
        
        # Wait for load
        await asyncio.sleep(wait_time_ms / 1000)
        
        # Get HTML
        result = await self._send_session("Runtime.evaluate", {
            "expression": "document.documentElement.outerHTML",
            "returnByValue": True,
        })
        html = result.get("result", {}).get("value", "")
        
        screenshot_path = None
        screenshot_data = None
        if take_screenshot:
            screenshot_path, screenshot_data = await self._take_screenshot()
        
        return CDPPageResult(
            url=url,
            status_code=200,
            soup=BeautifulSoup(html, 'html.parser'),
            text=html,
            screenshot_path=screenshot_path,
            screenshot_data=screenshot_data,
        )
    
    async def scroll_and_get(
        self,
        url: str,
        scroll_count: int = 5,
        scroll_delay_ms: int = 1000,
    ) -> CDPPageResult:
        """Navigate and scroll for infinite scroll pages."""
        result = await self.get(url)
        
        for _ in range(scroll_count):
            await self._send_session("Runtime.evaluate", {
                "expression": "window.scrollTo(0, document.body.scrollHeight)",
            })
            await asyncio.sleep(scroll_delay_ms / 1000)
        
        # Get final HTML
        html_result = await self._send_session("Runtime.evaluate", {
            "expression": "document.documentElement.outerHTML",
            "returnByValue": True,
        })
        html = html_result.get("result", {}).get("value", "")
        
        return CDPPageResult(
            url=url,
            status_code=200,
            soup=BeautifulSoup(html, 'html.parser'),
            text=html,
        )
    
    async def evaluate(self, js_code: str) -> Any:
        """Execute JavaScript and return result."""
        result = await self._send_session("Runtime.evaluate", {
            "expression": js_code,
            "returnByValue": True,
        })
        return result.get("result", {}).get("value")
    
    async def click(self, selector: str):
        """Click an element by CSS selector."""
        await self._send_session("Runtime.evaluate", {
            "expression": f"document.querySelector('{selector}').click()",
        })
    
    async def fill(self, selector: str, text: str):
        """Fill an input field."""
        await self._send_session("Runtime.evaluate", {
            "expression": f"""
                const el = document.querySelector('{selector}');
                el.value = '{text}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            """,
        })
    
    async def _take_screenshot(self) -> tuple[str, bytes]:
        """Take a screenshot."""
        result = await self._send_session("Page.captureScreenshot", {
            "format": "png",
        })
        data = base64.b64decode(result["data"])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.screenshot_dir, f"cdp_{timestamp}.png")
        with open(path, 'wb') as f:
            f.write(data)
        
        return path, data
    
    async def get_cookies(self) -> List[Dict]:
        """Get all cookies."""
        result = await self._send_session("Network.getAllCookies")
        return result.get("cookies", [])
    
    async def set_cookie(self, name: str, value: str, domain: str, **kwargs):
        """Set a cookie."""
        await self._send_session("Network.setCookie", {
            "name": name,
            "value": value,
            "domain": domain,
            **kwargs,
        })


class SyncCDPBrowser:
    """Synchronous wrapper for CDPBrowser.
    
    Example:
        with SyncCDPBrowser() as browser:
            result = browser.get("https://example.com")
            print(result.soup.title.text)
    """
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._browser: Optional[CDPBrowser] = None
        self._loop = asyncio.new_event_loop()
    
    def __enter__(self):
        self._browser = CDPBrowser(**self.kwargs)
        self._loop.run_until_complete(self._browser.start())
        return self
    
    def __exit__(self, *args):
        if self._browser:
            self._loop.run_until_complete(self._browser.close())
        self._loop.close()
    
    def get(self, url: str, **kwargs) -> CDPPageResult:
        return self._loop.run_until_complete(self._browser.get(url, **kwargs))
    
    def scroll_and_get(self, url: str, **kwargs) -> CDPPageResult:
        return self._loop.run_until_complete(self._browser.scroll_and_get(url, **kwargs))
    
    def evaluate(self, js_code: str) -> Any:
        return self._loop.run_until_complete(self._browser.evaluate(js_code))
    
    def click(self, selector: str):
        return self._loop.run_until_complete(self._browser.click(selector))
    
    def fill(self, selector: str, text: str):
        return self._loop.run_until_complete(self._browser.fill(selector, text))
