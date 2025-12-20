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
    # Action registration
    "register_actions",
    "BROWSER_ACTIONS",
]


# ---------------------------------------------------------------------------
# Plugin Action Registration
# ---------------------------------------------------------------------------

def _create_browser_actions():
    """Create browser action metadata.
    
    Imported lazily to avoid circular imports.
    """
    from tascer.action_registry import ActionMetadata, ActionCategory, RiskLevel
    
    return [
        ActionMetadata(
            id="browser.get",
            name="Browser GET",
            description="Navigate to URL and capture page content, screenshot, and network logs",
            category=ActionCategory.OBSERVATION,
            mutates_state=False,
            risk_level=RiskLevel.LOW,
            permissions_required=["browser", "network"],
            evidence_produced=["html", "screenshot", "network_log", "console_log"],
            rollback_supported=False,
        ),
        ActionMetadata(
            id="browser.scrape",
            name="Browser Scrape",
            description="Extract data from page using CSS selectors",
            category=ActionCategory.OBSERVATION,
            mutates_state=False,
            risk_level=RiskLevel.LOW,
            permissions_required=["browser"],
            evidence_produced=["extracted_data", "html"],
        ),
        ActionMetadata(
            id="browser.scroll",
            name="Browser Scroll",
            description="Scroll page to load dynamic content (infinite scroll)",
            category=ActionCategory.OBSERVATION,
            mutates_state=False,
            risk_level=RiskLevel.LOW,
            permissions_required=["browser"],
            evidence_produced=["html", "screenshot"],
        ),
        ActionMetadata(
            id="browser.click",
            name="Browser Click",
            description="Click an element on the page",
            category=ActionCategory.MUTATION,
            mutates_state=True,
            risk_level=RiskLevel.MEDIUM,
            permissions_required=["browser"],
            evidence_produced=["screenshot_before", "screenshot_after"],
        ),
        ActionMetadata(
            id="browser.fill",
            name="Browser Fill Form",
            description="Fill a form field with text",
            category=ActionCategory.MUTATION,
            mutates_state=True,
            risk_level=RiskLevel.MEDIUM,
            permissions_required=["browser"],
            evidence_produced=["screenshot"],
        ),
        ActionMetadata(
            id="browser.evaluate",
            name="Browser Evaluate JS",
            description="Evaluate JavaScript expression in page context",
            category=ActionCategory.OBSERVATION,
            mutates_state=False,
            risk_level=RiskLevel.LOW,
            permissions_required=["browser", "javascript"],
            evidence_produced=["result"],
        ),
        ActionMetadata(
            id="browser.screenshot",
            name="Browser Screenshot",
            description="Take a screenshot of the current page",
            category=ActionCategory.OBSERVATION,
            mutates_state=False,
            risk_level=RiskLevel.LOW,
            permissions_required=["browser"],
            evidence_produced=["screenshot"],
        ),
    ]


# Lazy-loaded actions
BROWSER_ACTIONS = None


def register_actions(registry) -> None:
    """Register browser plugin actions with the action registry.
    
    Call this when initializing the plugin:
    
        from tascer.action_registry import get_registry
        from tascer.plugins.browser import register_actions
        
        registry = get_registry()
        register_actions(registry)
    
    Args:
        registry: ActionRegistry instance to register with.
    """
    global BROWSER_ACTIONS
    if BROWSER_ACTIONS is None:
        BROWSER_ACTIONS = _create_browser_actions()
    
    registry.register_actions(BROWSER_ACTIONS)
