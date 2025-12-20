"""JavaScript Browser Session using Playwright.

Handles JS-heavy sites by running a real browser (headless).

Limitations addressed:
- JavaScript rendering
- Infinite scroll
- AJAX content
- Anti-bot JavaScript challenges
- Cloudflare/captcha challenges

Requires: playwright
Install: pip install playwright && playwright install chromium
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

# Try to import playwright
try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any
    Browser = Any

from bs4 import BeautifulSoup

from .human_input import (
    InputType,
    request_human_input,
    wait_for_human_input,
)


@dataclass
class JsPageResult:
    """Result from a JavaScript-rendered page."""
    url: str
    status_code: int
    soup: Optional[BeautifulSoup] = None
    text: str = ""
    
    # JS-specific
    js_executed: bool = True
    wait_time_ms: float = 0
    screenshot_path: Optional[str] = None
    
    # Challenge detection
    requires_2fa: bool = False
    requires_captcha: bool = False
    challenge_type: Optional[str] = None
    
    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class JsBrowserSession:
    """Browser session with full JavaScript support.
    
    Uses Playwright to run a real headless browser, enabling:
    - JavaScript execution
    - AJAX/XHR requests
    - Infinite scroll
    - Dynamic content loading
    - Screenshot capture
    - Cookie persistence
    
    Example:
        async with JsBrowserSession("mysite") as browser:
            result = await browser.get("https://example.com")
            print(result.soup.title.text)
            
            # Scroll to load infinite content
            result = await browser.scroll_and_get(
                "https://quotes.toscrape.com/scroll",
                scroll_count=5
            )
    """
    
    # Challenge detection patterns
    CAPTCHA_PATTERNS = [
        "captcha", "recaptcha", "hcaptcha", "turnstile",
        "verify you are human", "checking your browser",
        "just a moment", "ray id",  # Cloudflare
    ]
    
    TWO_FA_PATTERNS = [
        "two-factor", "2fa", "verification code", "authenticator",
        "security code", "enter code",
    ]
    
    def __init__(
        self,
        name: str,
        headless: bool = True,
        cookie_dir: str = ".tascer/cookies",
        screenshot_dir: str = ".tascer/screenshots",
        timeout_ms: int = 30000,
    ):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. Install with:\n"
                "  pip install playwright && playwright install chromium"
            )
        
        self.name = name
        self.headless = headless
        self.cookie_dir = cookie_dir
        self.screenshot_dir = screenshot_dir
        self.timeout_ms = timeout_ms
        self.cookie_file = os.path.join(cookie_dir, f"{name}_js.json")
        
        os.makedirs(cookie_dir, exist_ok=True)
        os.makedirs(screenshot_dir, exist_ok=True)
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context = None
        self._page: Optional[Page] = None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    async def start(self):
        """Start the browser."""
        self._playwright = await async_playwright().start()
        
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )
        
        # Create context with cookies
        storage_state = None
        if os.path.exists(self.cookie_file):
            storage_state = self.cookie_file
        
        self._context = await self._browser.new_context(
            storage_state=storage_state,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        
        self._page = await self._context.new_page()
    
    async def close(self):
        """Close browser and save cookies."""
        if self._context:
            await self._context.storage_state(path=self.cookie_file)
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    def _detect_challenge(self, text: str) -> tuple[bool, bool, Optional[str]]:
        """Detect if page shows a challenge."""
        text_lower = text.lower()
        
        requires_captcha = any(p in text_lower for p in self.CAPTCHA_PATTERNS)
        requires_2fa = any(p in text_lower for p in self.TWO_FA_PATTERNS)
        
        challenge_type = None
        if requires_captcha:
            challenge_type = "captcha"
        elif requires_2fa:
            challenge_type = "2fa"
        
        return requires_2fa, requires_captcha, challenge_type
    
    async def get(
        self,
        url: str,
        wait_for: str = "networkidle",  # "load", "domcontentloaded", "networkidle"
        wait_selector: Optional[str] = None,
        take_screenshot: bool = False,
    ) -> JsPageResult:
        """Navigate to URL and wait for JS to execute.
        
        Args:
            url: URL to navigate to
            wait_for: Wait strategy ("load", "domcontentloaded", "networkidle")
            wait_selector: Optional CSS selector to wait for
            take_screenshot: Save a screenshot
        """
        import time
        start_time = time.time()
        
        response = await self._page.goto(url, wait_until=wait_for, timeout=self.timeout_ms)
        
        if wait_selector:
            await self._page.wait_for_selector(wait_selector, timeout=self.timeout_ms)
        
        content = await self._page.content()
        wait_time_ms = (time.time() - start_time) * 1000
        
        requires_2fa, requires_captcha, challenge_type = self._detect_challenge(content)
        
        # Handle challenges
        if requires_captcha:
            screenshot_path = await self._take_screenshot("captcha")
            
            # Request human help
            input_request = request_human_input(
                input_type=InputType.CAPTCHA_CLICK,
                prompt="Please solve the captcha challenge",
                service_name=self.name,
                page_url=url,
                screenshot_path=screenshot_path,
            )
            
            return JsPageResult(
                url=url,
                status_code=response.status if response else 0,
                soup=BeautifulSoup(content, 'html.parser'),
                text=content,
                wait_time_ms=wait_time_ms,
                requires_captcha=True,
                challenge_type="captcha",
            )
        
        screenshot_path = None
        if take_screenshot:
            screenshot_path = await self._take_screenshot("page")
        
        return JsPageResult(
            url=url,
            status_code=response.status if response else 0,
            soup=BeautifulSoup(content, 'html.parser'),
            text=content,
            wait_time_ms=wait_time_ms,
            screenshot_path=screenshot_path,
            requires_2fa=requires_2fa,
            requires_captcha=requires_captcha,
            challenge_type=challenge_type,
        )
    
    async def scroll_and_get(
        self,
        url: str,
        scroll_count: int = 5,
        scroll_delay_ms: int = 1000,
        wait_selector: Optional[str] = None,
    ) -> JsPageResult:
        """Navigate and scroll to load infinite content.
        
        Args:
            url: URL to navigate to
            scroll_count: Number of times to scroll
            scroll_delay_ms: Delay between scrolls (for content to load)
            wait_selector: Selector to wait for after each scroll
        """
        result = await self.get(url)
        
        for i in range(scroll_count):
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(scroll_delay_ms / 1000)
            
            if wait_selector:
                try:
                    await self._page.wait_for_selector(wait_selector, timeout=5000)
                except Exception:
                    pass  # Selector might not appear if no new content
        
        content = await self._page.content()
        
        return JsPageResult(
            url=url,
            status_code=result.status_code,
            soup=BeautifulSoup(content, 'html.parser'),
            text=content,
            wait_time_ms=result.wait_time_ms,
        )
    
    async def click(self, selector: str, wait_after_ms: int = 1000):
        """Click an element."""
        await self._page.click(selector)
        await asyncio.sleep(wait_after_ms / 1000)
    
    async def fill(self, selector: str, text: str):
        """Fill a form field."""
        await self._page.fill(selector, text)
    
    async def type_text(self, selector: str, text: str, delay_ms: int = 50):
        """Type text character by character (more human-like)."""
        await self._page.type(selector, text, delay=delay_ms)
    
    async def login(
        self,
        url: str,
        username: str,
        password: str,
        username_selector: str = "input[name='username'], input[type='email'], #username, #email",
        password_selector: str = "input[name='password'], input[type='password'], #password",
        submit_selector: str = "button[type='submit'], input[type='submit'], button:has-text('Log in'), button:has-text('Sign in')",
        wait_for_navigation: bool = True,
    ) -> JsPageResult:
        """Login to a website with full JS support."""
        # Navigate to login page
        await self.get(url)
        
        # Fill credentials
        await self._page.fill(username_selector, username)
        await self._page.fill(password_selector, password)
        
        # Click submit
        if wait_for_navigation:
            async with self._page.expect_navigation():
                await self._page.click(submit_selector)
        else:
            await self._page.click(submit_selector)
            await asyncio.sleep(2)
        
        content = await self._page.content()
        requires_2fa, requires_captcha, challenge_type = self._detect_challenge(content)
        
        # Handle 2FA
        if requires_2fa:
            screenshot_path = await self._take_screenshot("2fa")
            
            input_request = request_human_input(
                input_type=InputType.TWO_FA_CODE,
                prompt=f"Enter 2FA code for {self.name}",
                service_name=self.name,
                page_url=url,
                screenshot_path=screenshot_path,
            )
            
            print(f"🔐 2FA required! Request ID: {input_request.id}")
            print(f"   Use: supe input respond {input_request.id} <code>")
            
            try:
                code = wait_for_human_input(input_request.id, timeout=300)
                
                # Try to find and fill the 2FA field
                await self._page.fill(
                    "input[name='code'], input[name='otp'], input[type='number'], input[name='totp']",
                    code
                )
                await self._page.click(submit_selector)
                await asyncio.sleep(2)
                
                content = await self._page.content()
            except TimeoutError:
                pass
        
        return JsPageResult(
            url=self._page.url,
            status_code=200,
            soup=BeautifulSoup(content, 'html.parser'),
            text=content,
            requires_2fa=requires_2fa,
            requires_captcha=requires_captcha,
            challenge_type=challenge_type,
        )
    
    async def wait_for_selector(self, selector: str, timeout_ms: int = None):
        """Wait for an element to appear."""
        await self._page.wait_for_selector(selector, timeout=timeout_ms or self.timeout_ms)
    
    async def evaluate(self, js_code: str) -> Any:
        """Execute JavaScript and return result."""
        return await self._page.evaluate(js_code)
    
    async def _take_screenshot(self, name: str) -> str:
        """Take a screenshot and save it."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.screenshot_dir, f"{self.name}_{name}_{timestamp}.png")
        await self._page.screenshot(path=path)
        return path
    
    async def extract(self, selector: str) -> List[str]:
        """Extract text from elements matching selector."""
        elements = await self._page.query_selector_all(selector)
        return [await el.inner_text() for el in elements]
    
    async def get_attribute(self, selector: str, attribute: str) -> List[str]:
        """Get attribute values from elements."""
        elements = await self._page.query_selector_all(selector)
        return [await el.get_attribute(attribute) for el in elements]


# Synchronous wrapper for convenience
def run_js_browser(coro):
    """Run async JsBrowserSession code synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


class SyncJsBrowser:
    """Synchronous wrapper for JsBrowserSession.
    
    Example:
        with SyncJsBrowser("mysite") as browser:
            result = browser.get("https://example.com")
            print(result.soup.title.text)
    """
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.kwargs = kwargs
        self._session: Optional[JsBrowserSession] = None
        self._loop = asyncio.new_event_loop()
    
    def __enter__(self):
        self._session = JsBrowserSession(self.name, **self.kwargs)
        self._loop.run_until_complete(self._session.start())
        return self
    
    def __exit__(self, *args):
        if self._session:
            self._loop.run_until_complete(self._session.close())
        self._loop.close()
    
    def get(self, url: str, **kwargs) -> JsPageResult:
        return self._loop.run_until_complete(self._session.get(url, **kwargs))
    
    def scroll_and_get(self, url: str, **kwargs) -> JsPageResult:
        return self._loop.run_until_complete(self._session.scroll_and_get(url, **kwargs))
    
    def login(self, url: str, username: str, password: str, **kwargs) -> JsPageResult:
        return self._loop.run_until_complete(
            self._session.login(url, username, password, **kwargs)
        )
    
    def click(self, selector: str, **kwargs):
        return self._loop.run_until_complete(self._session.click(selector, **kwargs))
    
    def fill(self, selector: str, text: str):
        return self._loop.run_until_complete(self._session.fill(selector, text))
