"""CDP Browser Demo - No Playwright Required!

This demonstrates browser automation using CDPBrowser, which uses
Chrome DevTools Protocol directly - no Playwright needed!

Requirements:
- Chrome or Chromium installed
- websockets package: pip install websockets
- beautifulsoup4: pip install beautifulsoup4

No Playwright installation required!
"""

import asyncio
import sys
import os

# Add parent directory to path to import tascer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE
except ImportError as e:
    print(f"Error importing CDPBrowser: {e}")
    print("\nMake sure you're running from the project root directory.")
    sys.exit(1)


async def demo_basic_navigation():
    """Demo: Basic page navigation and content extraction."""
    print("\n" + "=" * 70)
    print("Demo 1: Basic Navigation")
    print("=" * 70)
    
    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser not available. Install websockets: pip install websockets")
        return
    
    async with CDPBrowser(headless=True) as browser:
        print("→ Navigating to example.com...")
        result = await browser.get("https://example.com", wait_time_ms=2000)
        
        if result.ok:
            print(f"✓ Successfully loaded page")
            print(f"  URL: {result.url}")
            print(f"  Status: {result.status_code}")
            print(f"  Title: {result.soup.title.string if result.soup.title else 'N/A'}")
            print(f"  Content length: {len(result.text)} characters")
            
            if result.screenshot_path:
                print(f"  Screenshot: {result.screenshot_path}")
        else:
            print(f"✗ Failed to load page: {result.status_code}")


async def demo_javascript_execution():
    """Demo: Execute JavaScript on the page."""
    print("\n" + "=" * 70)
    print("Demo 2: JavaScript Execution")
    print("=" * 70)
    
    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser not available")
        return
    
    async with CDPBrowser(headless=True) as browser:
        print("→ Navigating to example.com...")
        await browser.get("https://example.com", wait_time_ms=2000)
        
        print("→ Executing JavaScript to get page title...")
        title = await browser.evaluate("document.title")
        print(f"  JavaScript result: {title}")
        
        print("→ Getting window dimensions...")
        dimensions = await browser.evaluate("JSON.stringify({width: window.innerWidth, height: window.innerHeight})")
        print(f"  Window size: {dimensions}")
        
        print("→ Getting all links on the page...")
        links = await browser.evaluate("""
            Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.textContent.trim(),
                href: a.href
            }))
        """)
        print(f"  Found {len(links)} links")
        for link in links[:5]:  # Show first 5
            print(f"    - {link.get('text', '')[:50]}: {link.get('href', '')[:60]}")


async def demo_content_scraping():
    """Demo: Scrape content from a page."""
    print("\n" + "=" * 70)
    print("Demo 3: Content Scraping")
    print("=" * 70)
    
    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser not available")
        return
    
    async with CDPBrowser(headless=True) as browser:
        print("→ Navigating to quotes.toscrape.com...")
        result = await browser.get("http://quotes.toscrape.com/", wait_time_ms=3000)
        
        if result.ok and result.soup:
            print("✓ Page loaded successfully")
            
            # Extract quotes
            quotes = result.soup.select(".quote")
            print(f"\n  Found {len(quotes)} quotes:")
            
            for i, quote in enumerate(quotes[:3], 1):  # Show first 3
                text_elem = quote.select_one(".text")
                author_elem = quote.select_one(".author")
                
                if text_elem and author_elem:
                    text = text_elem.get_text().strip()
                    author = author_elem.get_text().strip()
                    print(f"\n  Quote {i}:")
                    print(f"    Text: {text[:80]}...")
                    print(f"    Author: {author}")


async def demo_screenshot_capture():
    """Demo: Take screenshots."""
    print("\n" + "=" * 70)
    print("Demo 4: Screenshot Capture")
    print("=" * 70)
    
    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser not available")
        return
    
    async with CDPBrowser(headless=True, screenshot_dir=".tascer/screenshots") as browser:
        print("→ Navigating to example.com...")
        result = await browser.get("https://example.com", wait_time_ms=2000, take_screenshot=True)
        
        if result.screenshot_path:
            print(f"✓ Screenshot saved: {result.screenshot_path}")
            print(f"  File size: {os.path.getsize(result.screenshot_path) / 1024:.2f} KB")
        else:
            print("✗ Screenshot not captured")


async def demo_scroll_and_load():
    """Demo: Scroll to load dynamic content."""
    print("\n" + "=" * 70)
    print("Demo 5: Scroll and Load Dynamic Content")
    print("=" * 70)
    
    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser not available")
        return
    
    async with CDPBrowser(headless=True) as browser:
        print("→ Navigating to quotes.toscrape.com/scroll...")
        result = await browser.scroll_and_get(
            "http://quotes.toscrape.com/scroll",
            scroll_count=3,
            wait_time_ms=2000
        )
        
        if result.ok and result.soup:
            quotes = result.soup.select(".quote")
            print(f"✓ Loaded page with {len(quotes)} quotes (after scrolling)")
        else:
            print(f"✗ Failed to load: {result.status_code}")


async def demo_form_interaction():
    """Demo: Interact with form elements."""
    print("\n" + "=" * 70)
    print("Demo 6: Form Interaction")
    print("=" * 70)
    
    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser not available")
        return
    
    async with CDPBrowser(headless=True) as browser:
        print("→ Navigating to httpbin.org/forms/post...")
        await browser.get("https://httpbin.org/forms/post", wait_time_ms=3000)
        
        print("→ Filling form fields...")
        # Fill customer name
        await browser.fill("input[name='custname']", "Test User")
        print("  ✓ Filled customer name")
        
        # Fill telephone
        await browser.fill("input[name='custtel']", "555-1234")
        print("  ✓ Filled telephone")
        
        print("→ Taking screenshot of filled form...")
        screenshot = await browser.screenshot("form_filled.png")
        if screenshot:
            print(f"  ✓ Screenshot: {screenshot}")


async def run_all_demos():
    """Run all CDP browser demos."""
    print("\n" + "=" * 70)
    print("CDP Browser Demo - No Playwright Required!")
    print("=" * 70)
    print("\nThis demo uses CDPBrowser which controls Chrome directly")
    print("via Chrome DevTools Protocol - no Playwright needed!\n")
    print("Requirements:")
    print("  - Chrome/Chromium installed")
    print("  - websockets: pip install websockets")
    print("  - beautifulsoup4: pip install beautifulsoup4")
    print()
    
    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser is not available!")
        print("\nTo enable it:")
        print("  1. Install websockets: pip install websockets")
        print("  2. Install beautifulsoup4: pip install beautifulsoup4")
        print("  3. Ensure Chrome/Chromium is installed")
        return
    
    demos = [
        ("Basic Navigation", demo_basic_navigation),
        ("JavaScript Execution", demo_javascript_execution),
        ("Content Scraping", demo_content_scraping),
        ("Screenshot Capture", demo_screenshot_capture),
        ("Scroll and Load", demo_scroll_and_load),
        ("Form Interaction", demo_form_interaction),
    ]
    
    results = {}
    for demo_name, demo_func in demos:
        try:
            await demo_func()
            results[demo_name] = "✓ Success"
        except Exception as e:
            print(f"\n✗ {demo_name} failed: {e}\n")
            results[demo_name] = f"✗ Error: {str(e)}"
    
    print("\n" + "=" * 70)
    print("Demo Summary")
    print("=" * 70)
    for demo_name, result in results.items():
        print(f"  {demo_name}: {result}")
    print("=" * 70)
    print("\n✓ All demos complete!")
    print("\nNote: CDPBrowser uses Chrome DevTools Protocol directly,")
    print("      so no Playwright installation is required!\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError running demos: {e}")
        import traceback
        traceback.print_exc()

