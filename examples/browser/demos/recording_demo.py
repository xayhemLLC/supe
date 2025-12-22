"""CDP Browser Demo - Optimized for Recording

This demo is designed to be recorded with visible browser and clear output.
Perfect for creating video demos or GIFs.

Run with:
  python examples/cdp_browser_demo_recording.py
"""

import asyncio
import sys
import os
from time import sleep

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE
except ImportError as e:
    print(f"Error: {e}")
    sys.exit(1)


def print_step(step_num, description):
    """Print a clearly visible step."""
    print(f"\n{'='*70}")
    print(f"STEP {step_num}: {description}")
    print('='*70)


async def demo_for_recording():
    """Run a visual demo perfect for recording."""

    print("\n" + "="*70)
    print("CDP BROWSER DEMO - Chrome DevTools Protocol")
    print("No Playwright Required!")
    print("="*70)

    if not CDP_BROWSER_AVAILABLE:
        print("\nError: CDPBrowser not available")
        print("Install: pip install websockets beautifulsoup4")
        return

    # Use headless=False to see the browser in action
    async with CDPBrowser(headless=False, screenshot_dir=".tascer/screenshots") as browser:

        # Demo 1: Basic navigation
        print_step(1, "Navigate to example.com")
        result = await browser.get("https://example.com", wait_time_ms=3000)
        print(f"✓ Loaded: {result.url}")
        print(f"✓ Title: {result.soup.title.string if result.soup.title else 'N/A'}")
        await asyncio.sleep(2)  # Pause for recording

        # Demo 2: JavaScript execution
        print_step(2, "Execute JavaScript")
        title = await browser.evaluate("document.title")
        print(f"✓ JS Result: {title}")

        dimensions = await browser.evaluate(
            "JSON.stringify({width: window.innerWidth, height: window.innerHeight})"
        )
        print(f"✓ Window size: {dimensions}")
        await asyncio.sleep(2)

        # Demo 3: Screenshot
        print_step(3, "Take Screenshot")
        result = await browser.get("https://example.com", wait_time_ms=2000, take_screenshot=True)
        if result.screenshot_path:
            print(f"✓ Screenshot saved: {result.screenshot_path}")
            print(f"✓ Size: {os.path.getsize(result.screenshot_path) / 1024:.2f} KB")
        await asyncio.sleep(2)

        # Demo 4: Navigate to quotes site
        print_step(4, "Scrape Dynamic Content")
        print("→ Loading quotes.toscrape.com...")
        result = await browser.get("http://quotes.toscrape.com/", wait_time_ms=3000)

        if result.ok and result.soup:
            quotes = result.soup.select(".quote")
            print(f"✓ Found {len(quotes)} quotes")

            # Show first quote
            if quotes:
                first_quote = quotes[0]
                text = first_quote.select_one(".text").get_text().strip()
                author = first_quote.select_one(".author").get_text().strip()
                print(f"\n  First quote:")
                print(f"  {text}")
                print(f"  - {author}")
        await asyncio.sleep(3)

        # Demo 5: Scroll and load
        print_step(5, "Scroll to Load More Content")
        print("→ Loading infinite scroll page...")
        result = await browser.scroll_and_get(
            "http://quotes.toscrape.com/scroll",
            scroll_count=3,
            scroll_delay_ms=2000
        )

        if result.ok and result.soup:
            quotes = result.soup.select(".quote")
            print(f"✓ After scrolling: {len(quotes)} quotes loaded")
        await asyncio.sleep(3)

        # Demo 6: Form interaction
        print_step(6, "Fill Form Fields")
        print("→ Loading form...")
        await browser.get("https://httpbin.org/forms/post", wait_time_ms=3000)

        print("→ Filling customer name...")
        await browser.fill("input[name='custname']", "Demo User")
        await asyncio.sleep(1)

        print("→ Filling telephone...")
        await browser.fill("input[name='custtel']", "555-DEMO")
        await asyncio.sleep(1)

        print("✓ Form filled!")

        # Take screenshot of filled form (navigate again to capture state)
        result = await browser.get(browser._current_url, wait_time_ms=1000, take_screenshot=True)
        if result.screenshot_path:
            print(f"✓ Screenshot: {result.screenshot_path}")
        await asyncio.sleep(2)

    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Page navigation")
    print("  ✓ JavaScript execution")
    print("  ✓ Screenshot capture")
    print("  ✓ Content scraping")
    print("  ✓ Scroll and dynamic loading")
    print("  ✓ Form interaction")
    print("\nAll without Playwright! Pure Chrome DevTools Protocol.")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(demo_for_recording())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
