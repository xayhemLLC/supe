# Browser Automation Without Playwright

This directory contains examples of browser automation that **don't require Playwright**.

## Available Approaches

### 1. CDPBrowser (Recommended - No Playwright!)

**File:** `cdp_browser_demo.py`

Uses Chrome DevTools Protocol (CDP) directly via WebSockets. This is the **lightweight approach** that doesn't require Playwright.

**Requirements:**
- Chrome or Chromium installed
- `websockets` package: `pip install websockets`
- `beautifulsoup4`: `pip install beautifulsoup4`

**Features:**
- ✅ Navigate to pages
- ✅ Execute JavaScript
- ✅ Take screenshots
- ✅ Scrape content
- ✅ Fill forms
- ✅ Scroll and load dynamic content
- ✅ No Playwright dependency!

**Usage:**
```python
from tascer.plugins.browser import CDPBrowser

async with CDPBrowser(headless=True) as browser:
    result = await browser.get("https://example.com")
    print(result.soup.title.string)
    
    # Execute JavaScript
    title = await browser.evaluate("document.title")
    
    # Take screenshot
    await browser.get("https://example.com", take_screenshot=True)
```

**Run the demo:**
```bash
python examples/cdp_browser_demo.py
```

### 2. MCP Browser Tools (Structure Examples)

**Files:** 
- `browser_mcp_experiment.py` - Experiment structure
- `browser_mcp_demo.py` - Demo structure
- `test_mcp_browser.py` - Test structure
- `mcp_browser_live_demo.py` - Live demo template

These files show the **structure** for using MCP (Model Context Protocol) browser tools. Note: The MCP browser tools themselves may use Playwright under the hood, but these examples demonstrate the API structure.

**MCP Browser Tool Capabilities:**
- Navigation (forward/back)
- Page snapshots (accessibility tree)
- Screenshots
- Element interaction (click, type, hover)
- Form filling and dropdown selection
- Console and network monitoring
- Window resizing

**Example MCP Tool Calls:**
```python
# Navigate
await mcp_cursor-ide-browser_browser_navigate(url="https://example.com")

# Get snapshot
snapshot = await mcp_cursor-ide-browser_browser_snapshot()

# Click element
await mcp_cursor-ide-browser_browser_click(
    element="Submit button",
    ref="button[type='submit']"
)

# Type text
await mcp_cursor-ide-browser_browser_type(
    element="Search input",
    ref="input[name='q']",
    text="search query"
)

# Take screenshot
await mcp_cursor-ide-browser_browser_take_screenshot(
    filename="page.png",
    fullPage=True
)
```

## Comparison

| Approach | Playwright Required? | Dependencies | Use Case |
|----------|---------------------|--------------|----------|
| **CDPBrowser** | ❌ No | websockets, beautifulsoup4 | Lightweight, direct Chrome control |
| MCP Browser Tools | ⚠️ May use Playwright | MCP server | Standardized API, may have Playwright dependency |
| JsBrowserSession | ✅ Yes | playwright | Full-featured, requires Playwright |

## Recommended Approach

**Use CDPBrowser** for browser automation without Playwright:

1. ✅ No Playwright installation needed
2. ✅ Direct Chrome DevTools Protocol control
3. ✅ Lightweight and fast
4. ✅ Full JavaScript support
5. ✅ Screenshot and scraping capabilities

## Quick Start

```bash
# Install dependencies
pip install websockets beautifulsoup4

# Run the CDP browser demo
python examples/cdp_browser_demo.py
```

## Examples Included

1. **cdp_browser_demo.py** - Working demo using CDPBrowser (no Playwright)
2. **browser_mcp_experiment.py** - MCP browser tool experiment structure
3. **browser_mcp_demo.py** - MCP browser tool demo structure
4. **test_mcp_browser.py** - MCP browser tool test structure
5. **mcp_browser_live_demo.py** - MCP browser tool live demo template

## Integration with Existing Code

The `CDPBrowser` is already integrated into the codebase:

- **Location:** `tascer/plugins/browser/cdp_browser.py`
- **Usage in abilities:** `tascer/abilities/web_scraper.py`
- **Usage in sensory system:** `supe/sensory.py`

You can use it anywhere in the codebase:

```python
from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE

if CDP_BROWSER_AVAILABLE:
    async with CDPBrowser(headless=True) as browser:
        result = await browser.get("https://example.com")
        # ... use result
```

## Notes

- CDPBrowser finds Chrome automatically (checks standard paths, Playwright cache, system PATH)
- Works with headless or visible browser
- Supports cookie persistence via user data directory
- Can take screenshots and scrape content
- Full JavaScript execution support via `evaluate()`

