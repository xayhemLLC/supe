"""
Ingest Discord Developer Docs into AB Memory, then learn via INGEST mode.

Why this exists:
- INGEST mode currently pulls evidence from AB Memory (awareness track).
- So we first seed the memory with real Discord docs content (URL/title/text/html).
- Then we run a curated "expert curriculum" of questions using supe.learn(..., mode="ingest").

Usage (recommended):
  source .venv/bin/activate
  python drivers/ingest_discord_docs.py --db discord_memory.sqlite --max-pages 18 --learn

Notes:
- Uses ONLY the Python standard library for fetching and HTML-to-text.
- Adds a polite User-Agent and a small delay between requests.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional

from ab.models import Buffer
from supe import Supe


DISCORD_API_DOCS_RAW_BASE = "https://raw.githubusercontent.com/discord/discord-api-docs/main/"

# Prefer ingesting the source markdown/mdx from the official repo instead of
# discord.com/developers/docs (which is JS-only and won't render via plain HTTP fetch).
DEFAULT_SEED_PATHS = [
    "README.md",
    # Quick start / architecture
    "docs/quick-start/getting-started.mdx",
    "docs/quick-start/overview-of-apps.mdx",
    # Core topics
    "docs/topics/oauth2.mdx",
    "docs/topics/rate-limits.md",
    "docs/topics/opcodes-and-status-codes.md",
    "docs/topics/permissions.md",
    # Gateway
    "docs/events/gateway.mdx",
    "docs/events/gateway-events.mdx",
    # Interactions
    "docs/interactions/overview.mdx",
    "docs/interactions/receiving-and-responding.mdx",
    "docs/interactions/application-commands.mdx",
    # Key resources
    "docs/resources/user.mdx",
    "docs/resources/channel.mdx",
    "docs/resources/guild.mdx",
    "docs/resources/webhook.mdx",
]


EXPERT_CURRICULUM_QUESTIONS = [
    # Architecture / mental model
    "Explain Discord's API architecture: REST vs Gateway vs Interactions, and when to use each.",
    "What are Discord rate limits (per-route vs global)? How should a client handle them correctly?",
    "What are opcodes and status codes in Discord, and what are common failure modes?",
    # Auth
    "How does Discord OAuth2 work end-to-end for bots and for user authorization? What are scopes and redirect URIs?",
    "What are access tokens vs refresh tokens in Discord OAuth2? How do you refresh safely?",
    # Gateway
    "How does the Discord Gateway connection lifecycle work (identify, resume, heartbeats, reconnect)?",
    "What are Gateway Intents, why do they exist, and how do privileged intents change implementation?",
    "How do you handle events reliably from the Gateway (ordering, missed events, caching strategy)?",
    # REST resources
    "How do Discord channels differ by type and what are key channel fields a client must understand?",
    "How do guilds work (roles, permissions, members) at a high level?",
    "How do webhooks work and what are best practices and limitations?",
    # Interactions / commands
    "Describe the full lifecycle of an Interaction (acknowledgements, follow-ups, timeouts).",
    "How do Application Commands work (global vs guild, registration, permissions, autocomplete)?",
    "How do Message Components work (buttons/selects) and what state must the developer manage?",
    "How do Modals work and how do you validate user input safely?",
]


def _infer_title_from_markdown(text: str) -> str:
    """Heuristic title: first '# ' heading, else fallback."""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return "Discord API Docs"


@dataclass
class FetchedPage:
    url: str
    title: str
    text: str
    raw: str


def _fetch_url(url: str, timeout_s: int = 25) -> FetchedPage:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "supe-ingester/0.1 (+https://github.com/xayhemLLC/supe) Python-urllib",
            "Accept": "text/plain,text/markdown,text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="ignore")

    title = _infer_title_from_markdown(raw)
    text = raw

    return FetchedPage(url=url, title=title, text=text, raw=raw)


def _store_page(supe: Supe, page: FetchedPage, *, max_raw_chars: int = 400_000, max_text_chars: int = 200_000) -> int:
    """Store a page into AB Memory (awareness track) for INGEST mode to retrieve later."""
    raw = page.raw[:max_raw_chars]
    text = page.text[:max_text_chars]
    title = page.title[:300]

    # Put searchable material into master_output so ABMemory LIKE queries can hit.
    master_output = f"{title}\n\n{text[:3000]}"

    buffers = [
        Buffer(name="url", headers={"type": "url"}, payload=page.url.encode("utf-8")),
        Buffer(name="title", headers={"type": "title"}, payload=title.encode("utf-8")),
        Buffer(name="text", headers={"type": "text", "length": len(text)}, payload=text.encode("utf-8")),
        Buffer(name="raw", headers={"type": "source", "length": len(raw)}, payload=raw.encode("utf-8")),
        Buffer(name="scraped_at", headers={"type": "timestamp"}, payload=datetime.now().isoformat().encode("utf-8")),
    ]

    card = supe.memory.store_card(
        label="discord_docs",
        buffers=buffers,
        master_input=page.url,
        master_output=master_output,
        track="awareness",
    )
    return card.id


async def _learn_curriculum(supe: Supe, questions: Iterable[str]) -> List[dict]:
    results: List[dict] = []
    for q in questions:
        r = await supe.learn(q, mode="ingest")
        results.append(r)
    return results


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="discord_memory.sqlite", help="SQLite DB path for AB Memory")
    ap.add_argument("--max-pages", type=int, default=18, help="Max pages to fetch/store")
    ap.add_argument("--sleep-ms", type=int, default=400, help="Delay between requests (polite throttling)")
    ap.add_argument("--learn", action="store_true", help="Run expert curriculum via supe.learn(mode='ingest')")
    args = ap.parse_args()

    supe = Supe(db_path=args.db, auto_load_plugins=False)

    paths = DEFAULT_SEED_PATHS[: max(1, min(args.max_pages, len(DEFAULT_SEED_PATHS)))]
    urls = [DISCORD_API_DOCS_RAW_BASE + p for p in paths]

    print(f"Ingesting {len(urls)} Discord docs pages into {args.db!r} ...")
    stored_ids: List[int] = []

    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] Fetch {url}")
        try:
            page = _fetch_url(url)
            cid = _store_page(supe, page)
            stored_ids.append(cid)
            print(f"  stored card_id={cid} title={page.title[:80]!r}")
        except urllib.error.HTTPError as e:
            print(f"  HTTPError: {e.code} {e.reason}")
        except Exception as e:
            print(f"  ERROR: {e}")

        time.sleep(max(0.0, args.sleep_ms / 1000.0))

    print(f"Done. Stored {len(stored_ids)} pages.")

    if args.learn:
        print("\nRunning expert curriculum (INGEST mode)...")
        results = await _learn_curriculum(supe, EXPERT_CURRICULUM_QUESTIONS)

        # Store a session summary card for quick recall later.
        lines = [
            "Discord Docs INGEST Summary",
            f"- pages_ingested: {len(stored_ids)}",
            f"- questions: {len(EXPERT_CURRICULUM_QUESTIONS)}",
            "",
        ]
        for r in results:
            lines.append(f"Q: {r['question']}")
            lines.append(f"  beliefs: {r['beliefs_count']}  evidence: {r['evidence_count']}  gaps: {r['gaps_count']}  conf: {r['confidence']:.2f}")
            lines.append("")

        summary_text = "\n".join(lines)
        supe.memory.store_card(
            label="discord_ingest_summary",
            buffers=[Buffer(name="text", headers={"type": "text"}, payload=summary_text.encode("utf-8"))],
            master_input="discord_ingest_summary",
            master_output=summary_text[:4000],
            track="awareness",
        )

        print("Curriculum complete. Stored 'discord_ingest_summary' in memory.")


if __name__ == "__main__":
    asyncio.run(main())


