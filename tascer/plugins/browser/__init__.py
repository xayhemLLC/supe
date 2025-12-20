"""Browser Automation Plugin.

Provides session-based web automation with human-in-the-loop support
for 2FA codes, captchas, and other interactive challenges.

Components:
    session.py       - BrowserSession with cookie persistence (requests)
    js_browser.py    - JsBrowserSession with full JS support (Playwright)
    cdp_browser.py   - CDPBrowser - OUR OWN Chrome control via CDP (websockets)
    human_input.py   - Human-in-the-loop for 2FA/captcha
    api_keys.py      - API key management
"""

from .session import BrowserSession, PageResult
from .human_input import (
    HumanInputRequest,
    InputType,
    request_human_input,
    wait_for_human_input,
)
from .api_keys import APIKeyManager

# Optional: Playwright-based browser (requires playwright package)
try:
    from .js_browser import JsBrowserSession, SyncJsBrowser, JsPageResult
    JS_BROWSER_AVAILABLE = True
except ImportError:
    JS_BROWSER_AVAILABLE = False
    JsBrowserSession = None
    SyncJsBrowser = None
    JsPageResult = None

# Optional: CDP-based browser (requires only websockets - our own implementation!)
try:
    from .cdp_browser import CDPBrowser, SyncCDPBrowser, CDPPageResult
    CDP_BROWSER_AVAILABLE = True
except ImportError:
    CDP_BROWSER_AVAILABLE = False
    CDPBrowser = None
    SyncCDPBrowser = None
    CDPPageResult = None

__all__ = [
    # Requests-based (fast, no JS)
    "BrowserSession",
    "PageResult",
    # Playwright-based (full JS support)
    "JsBrowserSession",
    "SyncJsBrowser",
    "JsPageResult",
    "JS_BROWSER_AVAILABLE",
    # CDP-based (our own JS support - no Playwright!)
    "CDPBrowser",
    "SyncCDPBrowser",
    "CDPPageResult",
    "CDP_BROWSER_AVAILABLE",
    # Human input
    "HumanInputRequest",
    "InputType",
    "request_human_input",
    "wait_for_human_input",
    # API keys
    "APIKeyManager",
]


