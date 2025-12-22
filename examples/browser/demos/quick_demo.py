"""CDP Browser - 30 Second Demo
Quick demonstration of browser automation without Playwright!
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE


def print_action(action):
    """Print action clearly."""
    print(f"\n→ {action}")


async def quick_demo():
    """30-second demo of CDP browser capabilities."""

    print("\n" + "="*60)
    print("CDP BROWSER - 30 Second Demo")
    print("Browser Automation WITHOUT Playwright!")
    print("="*60)

    if not CDP_BROWSER_AVAILABLE:
        print("\n❌ Error: Install websockets and beautifulsoup4")
        return

    async with CDPBrowser(headless=False, screenshot_dir=".tascer/screenshots") as browser:

        # 1. Navigate
        print_action("Navigate to example.com")
        result = await browser.get("https://example.com", wait_time_ms=1500)
        print(f"   ✓ Loaded: {result.soup.title.string}")

        # 2. Execute JavaScript
        print_action("Execute JavaScript")
        title = await browser.evaluate("document.title")
        print(f"   ✓ Title: {title}")
        await asyncio.sleep(1)

        # 3. Scrape content
        print_action("Scrape quotes.toscrape.com")
        result = await browser.get("http://quotes.toscrape.com/", wait_time_ms=1500)
        quotes = result.soup.select(".quote")
        print(f"   ✓ Found {len(quotes)} quotes")
        await asyncio.sleep(1)

        # 4. Scroll and load
        print_action("Scroll infinite scroll page")
        result = await browser.scroll_and_get(
            "http://quotes.toscrape.com/scroll",
            scroll_count=2,
            scroll_delay_ms=800
        )
        quotes = result.soup.select(".quote")
        print(f"   ✓ Loaded {len(quotes)} quotes after scrolling")
        await asyncio.sleep(1)

        # 5. Fill form
        print_action("Fill form on httpbin.org")
        await browser.get("https://httpbin.org/forms/post", wait_time_ms=1500)
        await browser.fill("input[name='custname']", "CDP Demo User")
        await browser.fill("input[name='custtel']", "555-0123")
        print("   ✓ Form filled!")
        await asyncio.sleep(1)

        # 6. Screenshot
        print_action("Take screenshot")
        result = await browser.get(browser._current_url, wait_time_ms=500, take_screenshot=True)
        if result.screenshot_path:
            print(f"   ✓ Saved: {result.screenshot_path}")

    print("\n" + "="*60)
    print("✓ DEMO COMPLETE - All without Playwright!")
    print("="*60)
    print("\nFeatures shown:")
    print("  • Page navigation")
    print("  • JavaScript execution")
    print("  • Content scraping")
    print("  • Infinite scroll handling")
    print("  • Form interaction")
    print("  • Screenshot capture")
    print("\nPure Chrome DevTools Protocol - No Playwright needed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(quick_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
