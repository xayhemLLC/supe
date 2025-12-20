#!/usr/bin/env python3
"""Supe Feature Demo - Comprehensive showcase of all capabilities.

This demo showcases:
1. TascPlan creation and validation
2. Agent session tracking
3. CDPBrowser for JS scraping
4. Human-in-the-loop input
5. Tasc citations
6. All using LEGAL public data sources

Data sources used (all public/legal):
- quotes.toscrape.com (scraping practice site)
- books.toscrape.com (scraping practice site)  
- httpbin.org (HTTP testing service)
- Hacker News (public API)
"""

import asyncio
import json
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tascer import (
    # TascPlan
    create_plan,
    execute_plan,
    validate_tasc,
    ProofType,
    # Session tracking
    start_session,
    log_step,
    complete_session,
    get_session_summary,
    # Citations
    cite_tasc,
    TascCitation,
    # Metrics
    calculate_plan_metrics,
    PlanMetrics,
)

from tascer.plugins.browser import (
    BrowserSession,
    CDPBrowser,
    CDP_BROWSER_AVAILABLE,
)


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()


async def demo_cdp_scraping():
    """Demo 1: CDPBrowser - our own JS browser implementation."""
    print_header("📦 Demo 1: CDPBrowser - JS Scraping Without Playwright!")
    
    if not CDP_BROWSER_AVAILABLE:
        print("⚠️  CDPBrowser not available (install websockets)")
        return None
    
    chrome_path = CDPBrowser.find_chrome()
    print(f"Chrome found: {chrome_path[:60] if chrome_path else 'NOT FOUND'}...")
    
    if not chrome_path:
        print("⚠️  Chrome not found. Run: playwright install chromium")
        return None
    
    results = {}
    
    async with CDPBrowser(headless=True) as browser:
        # Test 1: Static page
        print("📋 Scraping quotes.toscrape.com...")
        result = await browser.get("https://quotes.toscrape.com", wait_time_ms=2000)
        quotes = [q.get_text() for q in result.soup.select(".quote .text")][:5]
        results["static_quotes"] = quotes
        print(f"   ✅ Found {len(quotes)} quotes (first 5)")
        
        # Test 2: Infinite scroll
        print("📋 Testing infinite scroll...")
        result = await browser.scroll_and_get(
            "https://quotes.toscrape.com/scroll",
            scroll_count=3,
            scroll_delay_ms=1500,
        )
        scroll_quotes = result.soup.select(".quote .text")
        results["scroll_count"] = len(scroll_quotes)
        print(f"   ✅ Loaded {len(scroll_quotes)} quotes via scroll!")
        
        # Test 3: Screenshot
        print("📋 Taking screenshot of Hacker News...")
        result = await browser.get(
            "https://news.ycombinator.com",
            wait_time_ms=2000,
            take_screenshot=True,
        )
        results["screenshot"] = result.screenshot_path
        stories = [a.get_text() for a in result.soup.select(".titleline > a")][:5]
        results["hn_stories"] = stories
        print(f"   ✅ Screenshot: {result.screenshot_path}")
        print(f"   ✅ Found {len(stories)} HN stories (first 5)")
        
        # Test 4: Custom JS execution
        print("📋 Executing custom JavaScript...")
        title = await browser.evaluate("document.title")
        url = await browser.evaluate("window.location.href")
        results["js_eval"] = {"title": title, "url": url}
        print(f"   ✅ document.title = {title}")
    
    return results


def demo_tasc_plan():
    """Demo 2: TascPlan creation and validation."""
    print_header("📋 Demo 2: TascPlan - Proof-of-Work Task Validation")
    
    # Create a plan with testable tasks
    plan = create_plan(
        title="Scrape Public Data Demo",
        tascs=[
            {
                "id": "check_deps",
                "title": "Verify dependencies installed",
                "testing_instructions": "python -c 'import bs4, requests; print(\"OK\")'",
                "desired_outcome": "BeautifulSoup and requests are installed",
            },
            {
                "id": "check_browser",
                "title": "Verify browser available",
                "testing_instructions": "python -c 'from tascer.plugins.browser import CDPBrowser; print(\"OK\" if CDPBrowser.find_chrome() else \"FAIL\")'",
                "dependencies": ["check_deps"],
            },
            {
                "id": "test_scrape",
                "title": "Test basic scraping",
                "testing_instructions": "python -c 'from tascer.plugins.browser import BrowserSession; s=BrowserSession(\"test\"); r=s.get(\"https://httpbin.org/get\"); print(\"OK\" if r.ok else \"FAIL\")'",
                "dependencies": ["check_deps"],
            },
        ],
    )
    
    print(f"✅ Created plan: {plan.title}")
    print(f"   ID: {plan.id}")
    print(f"   Tascs: {len(plan.tascs)}")
    
    for tasc in plan.tascs:
        deps = f" (deps: {tasc.dependencies})" if tasc.dependencies else ""
        print(f"   - {tasc.id}: {tasc.title}{deps}")
    
    return plan


def demo_session_tracking(scrape_results: dict):
    """Demo 3: Agent session tracking."""
    print_header("📝 Demo 3: Agent Session Tracking")
    
    # Start a session
    session = start_session(
        tasc_id="demo_scraping",
        goal="Demonstrate supe's browser scraping capabilities",
        model="cdp_browser",
        agent_name="supe_demo",
        constraints=["Only use public/legal data sources"],
    )
    
    print(f"✅ Session started: {session.id}")
    
    # Log steps
    log_step(
        session,
        mode="plan",
        thought="Setting up CDPBrowser for JS-heavy site scraping",
        planned_actions=[{"type": "START_BROWSER", "headless": True}],
    )
    
    log_step(
        session,
        mode="execute",
        thought="Scraping quotes from toscrape.com",
        executed_actions=[{"type": "GET", "url": "quotes.toscrape.com"}],
        results=[{"quotes_found": len(scrape_results.get("static_quotes", []))}] if scrape_results else [],
    )
    
    log_step(
        session,
        mode="execute", 
        thought="Testing infinite scroll capability",
        executed_actions=[{"type": "SCROLL_AND_GET", "scroll_count": 3}],
        results=[{"scroll_quotes": scrape_results.get("scroll_count", 0)}] if scrape_results else [],
        critic_verdict="accept",
    )
    
    # Complete session
    complete_session(
        session,
        success=True,
        summary="Successfully demonstrated CDPBrowser scraping capabilities",
        risks=["None - all data sources are public test sites"],
        follow_ups=["Try with more complex SPA applications"],
    )
    
    print(f"✅ Session completed!")
    print()
    print(get_session_summary(session))
    
    return session


def demo_citations():
    """Demo 4: Tasc citations - referencing prior work."""
    print_header("🔗 Demo 4: Tasc Citations")
    
    # Create a citation chain
    citation1 = cite_tasc(
        source_tasc_id="scrape_v2",
        cited_tasc_id="scrape_v1",
        citation_type="supersedes",
        description="Improved version using CDPBrowser instead of Selenium",
    )
    print(f"✅ Citation 1: {citation1.source_tasc_id} supersedes {citation1.cited_tasc_id}")
    
    citation2 = cite_tasc(
        source_tasc_id="full_demo",
        cited_tasc_id="scrape_v2",
        citation_type="derived_from",
        description="Demo built on scraping implementation",
    )
    print(f"✅ Citation 2: {citation2.source_tasc_id} derived_from {citation2.cited_tasc_id}")
    
    return [citation1, citation2]


def demo_browser_session():
    """Demo 5: BrowserSession for fast static scraping."""
    print_header("⚡ Demo 5: BrowserSession - Fast Static Scraping")
    
    session = BrowserSession("demo")
    
    # Scrape books
    print("📋 Scraping books.toscrape.com...")
    result = session.get("https://books.toscrape.com")
    books = []
    for book in result.soup.select(".product_pod")[:5]:
        title = book.select_one("h3 a")
        price = book.select_one(".price_color")
        if title and price:
            books.append({
                "title": title.get("title", title.get_text()),
                "price": price.get_text(),
            })
    
    print(f"   ✅ Found {len(books)} books:")
    for book in books:
        print(f"      - {book['title'][:40]}: {book['price']}")
    
    # Test login flow with CSRF
    print()
    print("📋 Testing login with CSRF extraction...")
    result = session.login(
        login_url="https://quotes.toscrape.com/login",
        username="testuser",
        password="testpass",
    )
    logged_in = "Logout" in result.text
    print(f"   ✅ Login {'successful' if logged_in else 'form submitted'}!")
    
    return {"books": books, "logged_in": logged_in}


def save_results(results: dict, path: str = ".tascer/demo_results.json"):
    """Save demo results to file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✅ Results saved to: {path}")


async def main():
    """Run all demos."""
    print()
    print("=" * 70)
    print("     SUPE - Comprehensive Feature Demo")
    print("     All data sources are public and legal!")
    print("=" * 70)
    
    results = {}
    
    # Demo 1: CDPBrowser
    scrape_results = await demo_cdp_scraping()
    if scrape_results:
        results["cdp_scraping"] = scrape_results
    
    # Demo 2: TascPlan
    plan = demo_tasc_plan()
    results["tasc_plan"] = {
        "id": plan.id,
        "title": plan.title,
        "tasc_count": len(plan.tascs),
    }
    
    # Demo 3: Session tracking
    session = demo_session_tracking(scrape_results or {})
    results["session"] = {
        "id": session.id,
        "steps": session.total_steps,
        "status": session.status,
    }
    
    # Demo 4: Citations
    citations = demo_citations()
    results["citations"] = [c.to_dict() for c in citations]
    
    # Demo 5: BrowserSession
    browser_results = demo_browser_session()
    results["browser_session"] = browser_results
    
    # Save results
    save_results(results)
    
    print_header("🎉 Demo Complete!")
    print("Features demonstrated:")
    print("  ✅ CDPBrowser - Our own JS browser (no Playwright needed!)")
    print("  ✅ TascPlan - Proof-of-work task validation")
    print("  ✅ Session Tracking - Step-by-step logging")
    print("  ✅ Citations - Reference prior work with proof hashes")
    print("  ✅ BrowserSession - Fast static scraping")
    print("  ✅ Login with CSRF - Automatic token extraction")
    print("  ✅ Infinite scroll - Dynamic content loading")
    print("  ✅ Screenshots - Visual evidence capture")
    print()
    print("All data sourced from public test sites:")
    print("  - quotes.toscrape.com")
    print("  - books.toscrape.com")
    print("  - httpbin.org")
    print("  - news.ycombinator.com")
    print()


if __name__ == "__main__":
    asyncio.run(main())
