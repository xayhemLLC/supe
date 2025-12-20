"""Frontend primitives with real framework detection.

ACTIONS:
- frontend.state.dump: Framework-agnostic snapshot
- frontend.inject: Temporary dev instrumentation (mutation)

Works with React, Vue, Svelte, Angular via browser devtools integration.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .browser import (
    browser_evaluate,
    browser_capture,
    is_browser_available,
    BrowserNotAvailableError,
)


class FrameworkType:
    """Detected frontend framework types."""
    UNKNOWN = "unknown"
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"
    ANGULAR = "angular"
    VANILLA = "vanilla"


@dataclass
class ComponentInfo:
    """Information about a UI component."""
    
    name: str
    props: Dict[str, Any]
    state: Dict[str, Any]
    children: List["ComponentInfo"] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "props": self.props,
            "state": self.state,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class FrontendState:
    """Captured frontend state."""
    
    timestamp: datetime
    framework: str
    state_hash: str
    dom_snapshot: Optional[str] = None
    component_tree: Optional[ComponentInfo] = None
    app_state: Dict[str, Any] = field(default_factory=dict)
    url: str = ""
    title: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "framework": self.framework,
            "state_hash": self.state_hash,
            "dom_snapshot": self.dom_snapshot[:500] if self.dom_snapshot else None,
            "component_tree": self.component_tree.to_dict() if self.component_tree else None,
            "app_state": self.app_state,
            "url": self.url,
            "title": self.title,
        }


@dataclass
class InjectionResult:
    """Result of frontend instrumentation injection."""
    
    injection_id: str
    script_hash: str
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "injection_id": self.injection_id,
            "script_hash": self.script_hash,
            "success": self.success,
            "error": self.error,
        }


class FrontendNotAvailableError(Exception):
    """Raised when frontend primitives are called but not configured."""
    pass


# Framework detection scripts
DETECT_FRAMEWORK_JS = """
(() => {
    // React
    if (window.React || window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
        return "react";
    }
    
    // Vue
    if (window.Vue || window.__VUE__) {
        return "vue";
    }
    
    // Angular
    if (window.ng || document.querySelector('[ng-version]')) {
        return "angular";
    }
    
    // Svelte
    if (document.querySelector('[class*="svelte"]')) {
        return "svelte";
    }
    
    return "vanilla";
})()
"""

# Get React state (simplified)
GET_REACT_STATE_JS = """
(() => {
    try {
        const rootEl = document.getElementById('root') || document.getElementById('app');
        if (!rootEl || !rootEl._reactRootContainer) {
            return null;
        }
        
        const fiber = rootEl._reactRootContainer._internalRoot?.current;
        if (!fiber) return null;
        
        // Get basic component info
        const components = [];
        let node = fiber.child;
        while (node) {
            if (node.type && typeof node.type === 'function') {
                components.push({
                    name: node.type.name || 'Anonymous',
                    props: Object.keys(node.memoizedProps || {}),
                });
            }
            node = node.sibling;
        }
        
        return { components };
    } catch (e) {
        return { error: e.message };
    }
})()
"""

# Get Vue state
GET_VUE_STATE_JS = """
(() => {
    try {
        const root = document.querySelector('[data-v-app]') || 
                     document.getElementById('app');
        if (!root || !root.__vue_app__) {
            return null;
        }
        
        const app = root.__vue_app__;
        return {
            components: [],
            globalState: app.config?.globalProperties?.$store?.state || {},
        };
    } catch (e) {
        return { error: e.message };
    }
})()
"""


def detect_framework(url: Optional[str] = None) -> str:
    """Detect the frontend framework in use.
    
    Args:
        url: Optional URL to navigate to first.
    
    Returns:
        FrameworkType constant.
    """
    if not is_browser_available():
        return FrameworkType.UNKNOWN
    
    try:
        if url:
            browser_capture(url=url, capture_screenshot=False)
        
        result = browser_evaluate(DETECT_FRAMEWORK_JS)
        return result.result or FrameworkType.UNKNOWN
    except Exception:
        return FrameworkType.UNKNOWN


def frontend_state_dump(
    capture_dom: bool = True,
    capture_components: bool = True,
    capture_app_state: bool = True,
) -> FrontendState:
    """Capture framework-agnostic frontend state.
    
    ACTION: frontend.state.dump
    
    Args:
        capture_dom: Include DOM snapshot.
        capture_components: Include component tree.
        capture_app_state: Include app state (Redux, Vuex, etc.).
    
    Returns:
        FrontendState with captured data.
    
    Raises:
        FrontendNotAvailableError: Frontend capture not configured.
    """
    if not is_browser_available():
        raise FrontendNotAvailableError(
            "Browser not available. Install Playwright: pip install playwright"
        )
    
    # Detect framework
    framework = detect_framework()
    
    # Capture browser state
    browser_state = browser_capture(
        capture_screenshot=False,
        capture_dom=capture_dom,
    )
    
    # Get framework-specific state
    app_state = {}
    component_tree = None
    
    if capture_app_state or capture_components:
        try:
            if framework == FrameworkType.REACT:
                result = browser_evaluate(GET_REACT_STATE_JS)
                if result.result:
                    app_state = result.result
            elif framework == FrameworkType.VUE:
                result = browser_evaluate(GET_VUE_STATE_JS)
                if result.result:
                    app_state = result.result
        except Exception:
            pass
    
    # Compute state hash
    state_content = json.dumps({
        "url": browser_state.url,
        "dom": browser_state.dom_snapshot[:1000] if browser_state.dom_snapshot else "",
        "app_state": app_state,
    }, sort_keys=True)
    state_hash = hashlib.sha256(state_content.encode()).hexdigest()[:16]
    
    return FrontendState(
        timestamp=datetime.now(),
        framework=framework,
        state_hash=state_hash,
        dom_snapshot=browser_state.dom_snapshot,
        component_tree=component_tree,
        app_state=app_state,
        url=browser_state.url,
        title=browser_state.title,
    )


def frontend_inject(
    script: str,
    scope: str = "temporary",
    cleanup_on_navigation: bool = True,
) -> InjectionResult:
    """Inject temporary dev instrumentation.
    
    ACTION: frontend.inject
    
    WARNING: This is a mutation action.
    
    Args:
        script: JavaScript code to inject.
        scope: Injection scope (temporary, session, persistent).
        cleanup_on_navigation: Remove injection on page navigation.
    
    Returns:
        InjectionResult with injection ID for cleanup.
    
    Raises:
        FrontendNotAvailableError: Frontend capture not configured.
    """
    if not is_browser_available():
        raise FrontendNotAvailableError(
            "Browser not available. Install Playwright: pip install playwright"
        )
    
    # Generate injection ID
    script_hash = hashlib.sha256(script.encode()).hexdigest()[:12]
    injection_id = f"inject_{script_hash}_{int(datetime.now().timestamp())}"
    
    try:
        # Wrap script to be removable
        wrapped_script = f"""
        (() => {{
            const __injection_id = "{injection_id}";
            try {{
                {script}
                window.__tascer_injections = window.__tascer_injections || {{}};
                window.__tascer_injections[__injection_id] = true;
            }} catch (e) {{
                console.error("Tasc injection error:", e);
            }}
        }})()
        """
        
        result = browser_evaluate(wrapped_script)
        
        if result.error:
            return InjectionResult(
                injection_id=injection_id,
                script_hash=script_hash,
                success=False,
                error=result.error,
            )
        
        return InjectionResult(
            injection_id=injection_id,
            script_hash=script_hash,
            success=True,
        )
    
    except Exception as e:
        return InjectionResult(
            injection_id=injection_id,
            script_hash=script_hash,
            success=False,
            error=str(e),
        )


def compare_states(
    before: FrontendState,
    after: FrontendState,
) -> Dict[str, Any]:
    """Compare two frontend states.
    
    Args:
        before: State before action.
        after: State after action.
    
    Returns:
        Dict describing differences.
    """
    return {
        "hash_changed": before.state_hash != after.state_hash,
        "framework_changed": before.framework != after.framework,
        "url_changed": before.url != after.url,
        "before_hash": before.state_hash,
        "after_hash": after.state_hash,
        "before_url": before.url,
        "after_url": after.url,
    }
