#!/usr/bin/env python3
"""Automatic Screen Recording for CDP Browser Demo

This script:
1. Starts screen recording with ffmpeg
2. Runs the CDP browser demo
3. Stops recording and saves MP4
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check ffmpeg
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    print("❌ Error: ffmpeg not installed")
    print("Install with: brew install ffmpeg")
    sys.exit(1)


def get_screen_size():
    """Get screen resolution on macOS."""
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True,
            text=True
        )
        # Parse resolution from output
        for line in result.stdout.split('\n'):
            if 'Resolution' in line:
                parts = line.split()
                if len(parts) >= 4:
                    width = parts[1]
                    height = parts[3]
                    return f"{width}x{height}"
    except Exception as e:
        print(f"Warning: Could not detect screen size: {e}")

    # Default to common resolution
    return "1920x1080"


async def run_demo():
    """Run the CDP browser demo."""
    from tascer.plugins.browser import CDPBrowser, CDP_BROWSER_AVAILABLE

    if not CDP_BROWSER_AVAILABLE:
        print("❌ CDPBrowser not available")
        return

    print("\n" + "="*60)
    print("CDP BROWSER - 30 Second Demo")
    print("Browser Automation WITHOUT Playwright!")
    print("="*60)

    async with CDPBrowser(headless=False, screenshot_dir=".tascer/screenshots") as browser:
        # Demo sequence
        print("\n→ Navigate to example.com")
        result = await browser.get("https://example.com", wait_time_ms=1500)
        print(f"   ✓ Loaded: {result.soup.title.string}")

        print("\n→ Execute JavaScript")
        title = await browser.evaluate("document.title")
        print(f"   ✓ Title: {title}")
        await asyncio.sleep(1)

        print("\n→ Scrape quotes.toscrape.com")
        result = await browser.get("http://quotes.toscrape.com/", wait_time_ms=1500)
        quotes = result.soup.select(".quote")
        print(f"   ✓ Found {len(quotes)} quotes")
        await asyncio.sleep(1)

        print("\n→ Scroll infinite scroll page")
        result = await browser.scroll_and_get(
            "http://quotes.toscrape.com/scroll",
            scroll_count=2,
            scroll_delay_ms=800
        )
        quotes = result.soup.select(".quote")
        print(f"   ✓ Loaded {len(quotes)} quotes after scrolling")
        await asyncio.sleep(1)

        print("\n→ Fill form on httpbin.org")
        await browser.get("https://httpbin.org/forms/post", wait_time_ms=1500)
        await browser.fill("input[name='custname']", "CDP Demo User")
        await browser.fill("input[name='custtel']", "555-0123")
        print("   ✓ Form filled!")
        await asyncio.sleep(1)

        print("\n→ Take screenshot")
        result = await browser.get(browser._current_url, wait_time_ms=500, take_screenshot=True)
        if result.screenshot_path:
            print(f"   ✓ Saved: {result.screenshot_path}")

    print("\n" + "="*60)
    print("✓ DEMO COMPLETE - All without Playwright!")
    print("="*60 + "\n")


def main():
    """Main recording function."""
    # Setup
    output_dir = Path.home() / "Desktop"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"cdp_browser_demo_{timestamp}.mp4"

    print("="*60)
    print("CDP Browser Demo - Automatic Recording")
    print("="*60)
    print(f"\nOutput file: {output_file}")
    print("\nStarting in 3 seconds...")
    print("  (Position your windows now!)")
    time.sleep(3)

    # Get screen size
    screen_size = get_screen_size()
    print(f"\nRecording screen: {screen_size}\n")

    # Start ffmpeg recording
    print("→ Starting screen recording...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "avfoundation",
        "-capture_cursor", "1",
        "-capture_mouse_clicks", "1",
        "-framerate", "30",
        "-i", "1:none",  # Display 1, no audio
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-y",
        str(output_file)
    ]

    ffmpeg_process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print(f"  Recording started (PID: {ffmpeg_process.pid})")
    time.sleep(2)  # Let ffmpeg initialize

    # Run the demo
    print("\n→ Running CDP Browser demo...\n")
    try:
        asyncio.run(run_demo())
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

    # Stop recording
    time.sleep(1)
    print("\n→ Stopping recording...")
    ffmpeg_process.send_signal(signal.SIGINT)
    ffmpeg_process.wait(timeout=10)

    # Check result
    time.sleep(1)
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print("\n" + "="*60)
        print("✓ Recording Complete!")
        print("="*60)
        print(f"\nVideo saved to:")
        print(f"  {output_file}")
        print(f"\nFile size: {size_mb:.1f} MB")
        print("\nTo play:")
        print(f'  open "{output_file}"')
        print("="*60 + "\n")

        # Ask to open
        try:
            response = input("Open video now? (y/N): ").strip().lower()
            if response == 'y':
                subprocess.run(["open", str(output_file)])
        except KeyboardInterrupt:
            print("\n")
    else:
        print("\n❌ Error: Video file not created")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nRecording cancelled.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
