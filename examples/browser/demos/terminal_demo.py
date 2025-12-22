"""CDP Browser Terminal Demo - Visually Appealing Terminal Output

Perfect for recording with asciinema or terminal recording tools.
Shows progress, colors, and clear output.
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE


# ANSI color codes for beautiful terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'


def print_header(text):
    """Print a bold header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 70}{Colors.ENDC}\n")


def print_step(num, text):
    """Print a step number and description."""
    print(f"{Colors.BOLD}{Colors.YELLOW}[STEP {num}]{Colors.ENDC} {Colors.BOLD}{text}{Colors.ENDC}")


def print_action(text):
    """Print an action being taken."""
    print(f"  {Colors.CYAN}→{Colors.ENDC} {text}")


def print_success(text):
    """Print a success message."""
    print(f"  {Colors.GREEN}✓{Colors.ENDC} {text}")


def print_info(label, value):
    """Print info with label and value."""
    print(f"  {Colors.DIM}{label}:{Colors.ENDC} {Colors.BOLD}{value}{Colors.ENDC}")


def print_quote(text, author):
    """Print a quote nicely formatted."""
    print(f"  {Colors.DIM}❝{Colors.ENDC} {Colors.CYAN}{text}{Colors.ENDC}")
    print(f"    {Colors.DIM}— {author}{Colors.ENDC}")


async def terminal_demo():
    """Run a terminal-optimized demo with beautiful output."""

    # Title
    print_header("CDP BROWSER DEMO")
    print(f"{Colors.DIM}Browser Automation Without Playwright{Colors.ENDC}".center(70))
    print(f"{Colors.DIM}Using Chrome DevTools Protocol{Colors.ENDC}".center(70))
    print()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.DIM}Started: {timestamp}{Colors.ENDC}".center(70))
    print()

    if not CDP_BROWSER_AVAILABLE:
        print(f"{Colors.RED}✗ CDPBrowser not available{Colors.ENDC}")
        print(f"{Colors.DIM}Install: pip install websockets beautifulsoup4{Colors.ENDC}")
        return

    # Progress bar simulation
    print(f"{Colors.DIM}Initializing browser...{Colors.ENDC}")
    for i in range(20):
        print(f"\r  [{'█' * i}{'░' * (19-i)}] {i*5}%", end='', flush=True)
        await asyncio.sleep(0.05)
    print(f"\r  [{'█' * 20}] 100%")
    print()

    async with CDPBrowser(headless=True, screenshot_dir=".tascer/screenshots") as browser:

        # Step 1: Basic Navigation
        print_step(1, "Navigate & Extract Content")
        print_action("Loading example.com...")
        result = await browser.get("https://example.com", wait_time_ms=1500)
        await asyncio.sleep(0.3)

        if result.ok:
            print_success("Page loaded successfully")
            print_info("URL", result.url)
            print_info("Title", result.soup.title.string if result.soup.title else "N/A")
            print_info("Content", f"{len(result.text):,} characters")
        print()

        # Step 2: JavaScript Execution
        print_step(2, "Execute JavaScript")
        print_action("Running document.title...")
        title = await browser.evaluate("document.title")
        await asyncio.sleep(0.3)
        print_success(f"Result: {title}")

        print_action("Getting window dimensions...")
        dimensions = await browser.evaluate(
            "JSON.stringify({width: window.innerWidth, height: window.innerHeight})"
        )
        await asyncio.sleep(0.3)
        print_success(f"Window: {dimensions}")
        print()

        # Step 3: Content Scraping
        print_step(3, "Scrape Dynamic Content")
        print_action("Loading quotes.toscrape.com...")
        result = await browser.get("http://quotes.toscrape.com/", wait_time_ms=1500)
        await asyncio.sleep(0.3)

        if result.ok and result.soup:
            quotes = result.soup.select(".quote")
            print_success(f"Found {len(quotes)} quotes")

            if quotes:
                print()
                print(f"  {Colors.DIM}First Quote:{Colors.ENDC}")
                first = quotes[0]
                text = first.select_one(".text").get_text().strip()
                author = first.select_one(".author").get_text().strip()
                print_quote(text[:80] + "...", author)
        print()

        # Step 4: Scroll and Load
        print_step(4, "Infinite Scroll Handling")
        print_action("Loading infinite scroll page...")
        await asyncio.sleep(0.3)

        # Show scroll progress
        print(f"  {Colors.DIM}Scrolling:{Colors.ENDC}")
        for i in range(3):
            print(f"    {Colors.CYAN}↓{Colors.ENDC} Scroll {i+1}/3...")
            await asyncio.sleep(0.5)

        result = await browser.scroll_and_get(
            "http://quotes.toscrape.com/scroll",
            scroll_count=3,
            scroll_delay_ms=500
        )

        if result.ok and result.soup:
            quotes = result.soup.select(".quote")
            print_success(f"Loaded {len(quotes)} quotes after scrolling")
        print()

        # Step 5: Form Interaction
        print_step(5, "Form Interaction")
        print_action("Loading httpbin.org form...")
        await browser.get("https://httpbin.org/forms/post", wait_time_ms=1500)
        await asyncio.sleep(0.3)

        print_action("Filling customer name field...")
        await browser.fill("input[name='custname']", "CDP Demo User")
        await asyncio.sleep(0.3)
        print_success("Name: CDP Demo User")

        print_action("Filling telephone field...")
        await browser.fill("input[name='custtel']", "555-DEMO")
        await asyncio.sleep(0.3)
        print_success("Phone: 555-DEMO")
        print()

        # Step 6: Screenshot
        print_step(6, "Capture Screenshot")
        print_action("Taking screenshot...")
        result = await browser.get(browser._current_url, wait_time_ms=500, take_screenshot=True)
        await asyncio.sleep(0.3)

        if result.screenshot_path:
            size_kb = os.path.getsize(result.screenshot_path) / 1024
            print_success("Screenshot captured")
            print_info("Path", result.screenshot_path)
            print_info("Size", f"{size_kb:.1f} KB")
        print()

    # Summary
    print_header("DEMO COMPLETE")

    features = [
        "Page Navigation & Content Extraction",
        "JavaScript Execution",
        "Dynamic Content Scraping",
        "Infinite Scroll Handling",
        "Form Field Interaction",
        "Screenshot Capture"
    ]

    print(f"{Colors.BOLD}Features Demonstrated:{Colors.ENDC}\n")
    for feature in features:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} {feature}")

    print()
    print(f"{Colors.DIM}{'─' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}All without Playwright - Pure Chrome DevTools Protocol!{Colors.ENDC}")
    print(f"{Colors.DIM}{'─' * 70}{Colors.ENDC}\n")

    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Colors.DIM}Completed: {end_time}{Colors.ENDC}".center(70))
    print()


if __name__ == "__main__":
    try:
        asyncio.run(terminal_demo())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted by user.{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n\n{Colors.RED}Error: {e}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
