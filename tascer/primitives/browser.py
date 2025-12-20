"""Browser primitives with Playwright support.

ACTIONS:
- browser.capture: Screenshot, console, network, DOM snapshot
- browser.evaluate: Read-only JavaScript expressions
- browser.interact: Click, type, navigate (mutation)

Requires: pip install playwright && playwright install chromium
"""

import base64
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Try to import playwright
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # Define type placeholders for when playwright isn't installed
    Page = Any  # type: ignore
    Browser = Any  # type: ignore
    BrowserContext = Any  # type: ignore
    sync_playwright = None  # type: ignore


@dataclass
class BrowserState:
    """Captured browser state."""
    
    url: str
    title: str
    viewport: Dict[str, int]  # width, height
    timestamp: datetime
    screenshot_path: Optional[str] = None
    screenshot_base64: Optional[str] = None
    console_logs: List[Dict[str, Any]] = field(default_factory=list)
    network_summary: List[Dict[str, Any]] = field(default_factory=list)
    dom_snapshot: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "viewport": self.viewport,
            "timestamp": self.timestamp.isoformat(),
            "screenshot_path": self.screenshot_path,
            "console_logs": self.console_logs,
            "network_summary": self.network_summary,
            "dom_snapshot": self.dom_snapshot[:500] if self.dom_snapshot else None,
        }


@dataclass
class EvaluateResult:
    """Result of JavaScript evaluation."""
    
    result: Any
    result_type: str
    error: Optional[str] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result,
            "result_type": self.result_type,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class InteractionResult:
    """Result of browser interaction."""
    
    action: str  # click, type, navigate, etc.
    target: str  # selector or URL
    success: bool
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "success": self.success,
            "screenshot_before": self.screenshot_before,
            "screenshot_after": self.screenshot_after,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class BrowserNotAvailableError(Exception):
    """Raised when browser primitives are called but not configured."""
    pass


class BrowserManager:
    """Manages browser instance for primitives."""
    
    _instance: Optional["BrowserManager"] = None
    
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._console_logs: List[Dict[str, Any]] = []
        self._network_logs: List[Dict[str, Any]] = []
    
    @classmethod
    def get_instance(cls) -> "BrowserManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def ensure_browser(self):
        """Ensure browser is running and return page."""
        if not PLAYWRIGHT_AVAILABLE:
            raise BrowserNotAvailableError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        
        if self._page is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._context = self._browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            self._page = self._context.new_page()
            
            # Setup console logging
            self._page.on("console", self._on_console)
            self._page.on("request", self._on_request)
            self._page.on("response", self._on_response)
        
        return self._page
    
    def _on_console(self, msg):
        """Handle console messages."""
        self._console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "timestamp": datetime.now().isoformat(),
        })
    
    def _on_request(self, request):
        """Handle network requests."""
        self._network_logs.append({
            "type": "request",
            "url": request.url,
            "method": request.method,
            "timestamp": datetime.now().isoformat(),
        })
    
    def _on_response(self, response):
        """Handle network responses."""
        self._network_logs.append({
            "type": "response",
            "url": response.url,
            "status": response.status,
            "timestamp": datetime.now().isoformat(),
        })
    
    def get_console_logs(self) -> List[Dict[str, Any]]:
        """Get and clear console logs."""
        logs = self._console_logs.copy()
        self._console_logs.clear()
        return logs
    
    def get_network_logs(self) -> List[Dict[str, Any]]:
        """Get and clear network logs."""
        logs = self._network_logs.copy()
        self._network_logs.clear()
        return logs
    
    def close(self):
        """Close browser."""
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None


def browser_capture(
    url: Optional[str] = None,
    capture_screenshot: bool = True,
    capture_console: bool = True,
    capture_network: bool = True,
    capture_dom: bool = False,
    screenshot_dir: str = "./screenshots",
) -> BrowserState:
    """Capture browser state.
    
    ACTION: browser.capture
    
    Args:
        url: URL to navigate to first (optional).
        capture_screenshot: Include screenshot.
        capture_console: Include console logs.
        capture_network: Include network summary.
        capture_dom: Include DOM snapshot.
        screenshot_dir: Directory for screenshots.
    
    Returns:
        BrowserState with captured data.
    
    Raises:
        BrowserNotAvailableError: Browser not configured.
    """
    manager = BrowserManager.get_instance()
    page = manager.ensure_browser()
    
    # Navigate if URL provided
    if url:
        page.goto(url, wait_until="networkidle")
    
    # Get basic state
    current_url = page.url
    title = page.title()
    viewport = page.viewport_size or {"width": 1280, "height": 720}
    
    # Capture screenshot
    screenshot_path = None
    screenshot_base64 = None
    if capture_screenshot:
        os.makedirs(screenshot_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(screenshot_dir, f"capture_{timestamp}.png")
        page.screenshot(path=screenshot_path)
        
        # Also capture as base64
        screenshot_bytes = page.screenshot()
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
    
    # Get console logs
    console_logs = manager.get_console_logs() if capture_console else []
    
    # Get network summary
    network_summary = manager.get_network_logs() if capture_network else []
    
    # Capture DOM
    dom_snapshot = None
    if capture_dom:
        dom_snapshot = page.content()
    
    return BrowserState(
        url=current_url,
        title=title,
        viewport=viewport,
        timestamp=datetime.now(),
        screenshot_path=screenshot_path,
        screenshot_base64=screenshot_base64,
        console_logs=console_logs,
        network_summary=network_summary,
        dom_snapshot=dom_snapshot,
    )


def browser_evaluate(
    expression: str,
    context: Optional[Dict[str, Any]] = None,
) -> EvaluateResult:
    """Evaluate JavaScript expression in browser.
    
    ACTION: browser.evaluate
    
    Args:
        expression: JavaScript expression to evaluate.
        context: Variables to inject into evaluation context.
    
    Returns:
        EvaluateResult with result or error.
    
    Raises:
        BrowserNotAvailableError: Browser not configured.
    """
    manager = BrowserManager.get_instance()
    page = manager.ensure_browser()
    
    start_time = time.perf_counter()
    
    try:
        # Evaluate expression
        if context:
            # Inject context variables
            for key, value in context.items():
                page.evaluate(f"window.{key} = {value!r}")
        
        result = page.evaluate(expression)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        return EvaluateResult(
            result=result,
            result_type=type(result).__name__,
            duration_ms=duration_ms,
        )
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return EvaluateResult(
            result=None,
            result_type="error",
            error=str(e),
            duration_ms=duration_ms,
        )


def browser_interact(
    action: str,
    target: str,
    value: Optional[str] = None,
    wait_after_ms: int = 500,
    capture_before_after: bool = True,
    screenshot_dir: str = "./screenshots",
) -> InteractionResult:
    """Interact with browser (click, type, navigate).
    
    ACTION: browser.interact
    
    Args:
        action: Interaction type (click, type, navigate, scroll, etc.).
        target: Selector for click/type, URL for navigate.
        value: Value to type (for type action).
        wait_after_ms: Wait time after action.
        capture_before_after: Capture screenshots before/after.
        screenshot_dir: Directory for screenshots.
    
    Returns:
        InteractionResult with success status.
    
    Raises:
        BrowserNotAvailableError: Browser not configured.
    """
    manager = BrowserManager.get_instance()
    page = manager.ensure_browser()
    
    start_time = time.perf_counter()
    
    # Capture before
    screenshot_before = None
    if capture_before_after:
        os.makedirs(screenshot_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_before = os.path.join(screenshot_dir, f"before_{timestamp}.png")
        page.screenshot(path=screenshot_before)
    
    try:
        if action == "click":
            page.click(target)
        
        elif action == "type":
            if value is None:
                raise ValueError("Value required for type action")
            page.fill(target, value)
        
        elif action == "navigate":
            page.goto(target, wait_until="networkidle")
        
        elif action == "scroll":
            page.evaluate(f"window.scrollBy(0, {value or 500})")
        
        elif action == "hover":
            page.hover(target)
        
        elif action == "select":
            if value is None:
                raise ValueError("Value required for select action")
            page.select_option(target, value)
        
        elif action == "press":
            if value is None:
                raise ValueError("Key required for press action")
            page.keyboard.press(value)
        
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Wait after action
        page.wait_for_timeout(wait_after_ms)
        
        # Capture after
        screenshot_after = None
        if capture_before_after:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_after = os.path.join(screenshot_dir, f"after_{timestamp}.png")
            page.screenshot(path=screenshot_after)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        return InteractionResult(
            action=action,
            target=target,
            success=True,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            duration_ms=duration_ms,
        )
    
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return InteractionResult(
            action=action,
            target=target,
            success=False,
            screenshot_before=screenshot_before,
            error=str(e),
            duration_ms=duration_ms,
        )


def browser_close():
    """Close the browser instance."""
    BrowserManager.get_instance().close()


def is_browser_available() -> bool:
    """Check if browser is available."""
    return PLAYWRIGHT_AVAILABLE
