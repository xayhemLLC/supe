---
description: How to use the browser automation plugin for web scraping and automation
---

# Browser Plugin Workflow

Guide for using the browser automation plugin with human-in-the-loop support.

---

## Prerequisites

### Quick Start (Recommended)
```bash
# CDPBrowser only needs websockets + Chrome
pip install websockets beautifulsoup4

# Install Chromium (CDPBrowser will find it automatically)
pip install playwright && playwright install chromium
```

> **Note**: CDPBrowser uses Chrome/Chromium via CDP (Chrome DevTools Protocol). 
> It will automatically detect Playwright's cached Chromium at:
> - macOS: `~/Library/Caches/ms-playwright/chromium-*/`
> - Linux: `~/.cache/ms-playwright/chromium-*/`

### Full Setup (All browsers)
```bash
pip install requests beautifulsoup4 websockets playwright
playwright install chromium
```

---

## Choosing the Right Browser

| Browser | Use Case | JS | Speed | Deps |
|---------|----------|-----|-------|------|
| `BrowserSession` | Static HTML, APIs | ❌ | ⚡ Fastest | requests |
| **`CDPBrowser`** | **JS sites, SPAs** | ✅ | 🚀 Fast | websockets |
| `JsBrowserSession` | Complex automation | ✅ | 🐢 Slower | playwright |

**Prefer CDPBrowser** - it's our own implementation, lightweight, and powerful!

---

## Step 1: Choose Browser Based on Site

```python
from tascer.plugins.browser import (
    BrowserSession,      # Static sites
    CDPBrowser,          # JS sites (recommended!)
    JsBrowserSession,    # Complex automation
)

# For most JS-heavy sites, use CDPBrowser
async with CDPBrowser(headless=True) as browser:
    result = await browser.get("https://example.com")
```

---

## Step 2: Basic Scraping

### Static Sites (BrowserSession)
```python
from tascer.plugins.browser import BrowserSession

session = BrowserSession("mysite")
result = session.get("https://quotes.toscrape.com")

for quote in result.soup.select(".quote .text"):
    print(quote.get_text())
```

### JS-Heavy Sites (CDPBrowser)
```python
import asyncio
from tascer.plugins.browser import CDPBrowser

async def scrape():
    async with CDPBrowser() as browser:
        # Wait for JS to render
        result = await browser.get(
            "https://spa-app.com",
            wait_time_ms=3000,  # Wait 3s for JS
        )
        
        # Execute custom JS
        count = await browser.evaluate("document.querySelectorAll('.item').length")
        print(f"Found {count} items")

asyncio.run(scrape())
```

---

## Step 3: Infinite Scroll

```python
async with CDPBrowser() as browser:
    result = await browser.scroll_and_get(
        "https://quotes.toscrape.com/scroll",
        scroll_count=5,        # Scroll 5 times
        scroll_delay_ms=1500,  # Wait between scrolls
    )
    
    quotes = result.soup.select(".quote")
    print(f"Loaded {len(quotes)} quotes via infinite scroll!")
```

---

## Step 4: Form Interaction

```python
async with CDPBrowser() as browser:
    await browser.get("https://example.com/login")
    
    # Fill form
    await browser.fill("input[name='username']", "myuser")
    await browser.fill("input[name='password']", "mypass")
    
    # Click submit
    await browser.click("button[type='submit']")
    
    # Wait for navigation
    import asyncio
    await asyncio.sleep(2)
    
    # Check result
    html = await browser.evaluate("document.body.innerHTML")
```

---

## Step 5: Handling 2FA/Captcha

When automation hits a challenge, it pauses and requests human input:

```python
from tascer.plugins.browser import (
    CDPBrowser,
    request_human_input,
    wait_for_human_input,
    InputType,
)

async with CDPBrowser() as browser:
    result = await browser.get("https://dashboard.example.com")
    
    if "2fa" in result.text.lower():
        # Request human input
        req = request_human_input(
            input_type=InputType.TWO_FA_CODE,
            prompt="Enter 2FA code for Example",
            service_name="example",
        )
        print(f"Waiting for input... supe input respond {req.id} <code>")
        
        # Wait for human to provide code
        code = wait_for_human_input(req.id)
        
        # Submit code
        await browser.fill("input[name='otp']", code)
        await browser.click("button[type='submit']")
```

### CLI Commands for Human Input
```bash
supe input list                    # Show pending requests
supe input respond <id> <value>    # Provide input
```

---

## Step 6: Screenshots

```python
async with CDPBrowser() as browser:
    result = await browser.get(
        "https://example.com",
        take_screenshot=True,
    )
    print(f"Screenshot saved: {result.screenshot_path}")
    # → .tascer/screenshots/cdp_20231219_123456.png
```

---

## Step 7: Cookie Persistence

Cookies are automatically saved for `BrowserSession`:
```python
session = BrowserSession("mysite")
session.login(url, user, pass)  # Cookies saved automatically

# Later - same session restored
session = BrowserSession("mysite")  # Cookies loaded!
result = session.get("https://mysite.com/dashboard")  # Still logged in
```

For CDPBrowser, use `--user-data-dir`:
```python
CDPBrowser(user_data_dir=".tascer/chrome_profile")
```

---

## Troubleshooting

### Chrome Not Found
```python
# Check what path CDPBrowser detects
from tascer.plugins.browser import CDPBrowser
print(CDPBrowser.find_chrome())
```

If None:
1. Install Chromium via Playwright: `playwright install chromium`
2. Or install Chrome: https://www.google.com/chrome/

### Brotli Encoding Error
Already fixed! We use `Accept-Encoding: gzip, deflate` (no brotli).

### Timeout on JS Load
Increase wait time:
```python
await browser.get(url, wait_time_ms=5000)  # 5 seconds
```

---

## Example: Full Scraping Flow

```python
import asyncio
from tascer.plugins.browser import CDPBrowser

async def scrape_hn():
    """Scrape Hacker News top stories."""
    async with CDPBrowser() as browser:
        result = await browser.get(
            "https://news.ycombinator.com",
            wait_time_ms=2000,
            take_screenshot=True,
        )
        
        stories = []
        for row in result.soup.select(".athing"):
            title_el = row.select_one(".titleline > a")
            if title_el:
                stories.append({
                    "title": title_el.get_text(),
                    "url": title_el.get("href"),
                })
        
        print(f"Found {len(stories)} stories!")
        return stories

stories = asyncio.run(scrape_hn())
```
