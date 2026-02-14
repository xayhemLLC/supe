"""Vault: Markdown view layer + index for AB Memory.

Renders Cards as markdown files with YAML frontmatter, organized by label.
Provides a fast vault index for first-pass retrieval.

Two layers:
  1. Pure rendering functions (no filesystem, fully testable)
  2. Filesystem export functions (write .md files + binary assets)
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import Buffer, Card, CardStats


# ---------------------------------------------------------------------------
# VaultIndexEntry
# ---------------------------------------------------------------------------

@dataclass
class VaultIndexEntry:
    """Lightweight summary of a card for vault index scanning."""

    card_id: int
    label: str
    track: str
    summary: str
    strength: float
    recall_count: int
    created_at: str
    buffer_count: int


# ---------------------------------------------------------------------------
# Pure rendering functions
# ---------------------------------------------------------------------------

def slugify(text: str, max_len: int = 50) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len].rstrip("-")


def _card_summary(card: Card) -> str:
    """Extract a short summary from a card for display and filenames."""
    if card.master_input:
        return card.master_input[:80]
    for buf in card.buffers:
        ct = buf.headers.get("content_type", "text/plain")
        if ct.startswith("text/") or ct == "application/json":
            payload = buf.payload
            if isinstance(payload, bytes):
                try:
                    payload = payload.decode("utf-8", errors="replace")
                except Exception:
                    continue
            if payload:
                return str(payload)[:80]
    return f"{card.label}-{card.id}"


def _is_text_buffer(buf: Buffer) -> bool:
    """Check if a buffer contains text content."""
    ct = buf.headers.get("content_type", "text/plain")
    return ct.startswith("text/") or ct in ("application/json",)


def _ext_from_content_type(content_type: str) -> str:
    """Derive file extension from content_type header."""
    ext = mimetypes.guess_extension(content_type)
    if ext:
        return ext
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "application/pdf": ".pdf",
        "application/octet-stream": ".bin",
    }
    return mapping.get(content_type, ".bin")


def _decode_payload(buf: Buffer) -> str:
    """Decode a buffer payload to string."""
    payload = buf.payload
    if isinstance(payload, bytes):
        return payload.decode("utf-8", errors="replace")
    return str(payload) if payload else ""


def card_to_frontmatter(card: Card, stats: CardStats | None = None) -> dict:
    """Card metadata as a YAML frontmatter dict."""
    tags = []
    if hasattr(card, "tags") and card.tags:  # pragma: no branch
        try:
            tags = json.loads(card.tags) if isinstance(card.tags, str) else card.tags
        except (json.JSONDecodeError, TypeError):
            tags = []

    fm: dict = {
        "id": card.id,
        "label": card.label,
        "track": card.track,
        "owner": card.owner_self,
        "created_at": card.created_at,
        "moment_id": card.moment_id,
    }

    if stats:
        fm["strength"] = round(stats.strength, 4)
        fm["recall_count"] = stats.recall_count
    else:
        fm["strength"] = None
        fm["recall_count"] = 0

    fm["tags"] = tags
    return fm


def _render_frontmatter(fm: dict) -> str:
    """Render frontmatter dict as YAML block."""
    lines = ["---"]
    for key, value in fm.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, list):
            lines.append(f"{key}: {json.dumps(value)}")
        elif isinstance(value, str) and ("\n" in value or ":" in value or '"' in value):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def card_to_markdown(
    card: Card,
    stats: CardStats | None = None,
    assets_rel: str = "../assets",
) -> str:
    """Render a single Card as markdown with YAML frontmatter.

    Args:
        card: The card to render.
        stats: Optional card stats for strength/recall info.
        assets_rel: Relative path to assets directory from the card's .md file.

    Returns:
        Complete markdown string.
    """
    fm = card_to_frontmatter(card, stats)
    parts = [_render_frontmatter(fm), ""]

    # Title
    parts.append(f"# {card.label} #{card.id}")
    parts.append("")

    # Master input/output
    if card.master_input:
        parts.append(f"**Input:** {card.master_input}")
        parts.append("")
    if card.master_output:
        parts.append(f"**Output:** {card.master_output}")
        parts.append("")

    # Buffers
    for buf in card.buffers:
        if _is_text_buffer(buf):
            parts.append(f"## {buf.name}")
            parts.append("")
            parts.append(_decode_payload(buf))
            parts.append("")
        else:
            ct = buf.headers.get("content_type", "application/octet-stream")
            ext = _ext_from_content_type(ct)
            asset_filename = f"{card.id}-{buf.name}{ext}"
            parts.append(f"## {buf.name}")
            parts.append("")
            parts.append(f"![{buf.name}]({assets_rel}/{asset_filename})")
            parts.append("")

    return "\n".join(parts)


def generate_index(entries: list[VaultIndexEntry]) -> str:
    """Render vault index as a markdown table.

    Args:
        entries: List of VaultIndexEntry objects to render.

    Returns:
        Markdown string with table.
    """
    lines = [
        "# Vault Index",
        "",
        f"Total cards: {len(entries)}",
        "",
        "| ID | Label | Track | Summary | Strength | Recalls | Buffers |",
        "|----|-------|-------|---------|----------|---------|---------|",
    ]

    for e in entries:
        summary = e.summary[:60].replace("|", "/").replace("\n", " ")
        strength = f"{e.strength:.2f}" if e.strength is not None else "-"
        lines.append(
            f"| {e.card_id} | {e.label} | {e.track} | {summary} | "
            f"{strength} | {e.recall_count} | {e.buffer_count} |"
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Filesystem export functions
# ---------------------------------------------------------------------------

def export_card(
    card: Card,
    stats: CardStats | None,
    vault_dir: Path,
) -> Path:
    """Write card markdown + binary assets to vault directory.

    Args:
        card: Card to export.
        stats: Optional card stats.
        vault_dir: Root vault directory.

    Returns:
        Path to the written .md file.
    """
    # Determine folder (by label)
    folder = card.label or "uncategorized"
    card_dir = vault_dir / folder
    card_dir.mkdir(parents=True, exist_ok=True)

    # Assets directory at vault root
    assets_dir = vault_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Write binary buffers as assets
    for buf in card.buffers:
        if not _is_text_buffer(buf):
            ct = buf.headers.get("content_type", "application/octet-stream")
            ext = _ext_from_content_type(ct)
            asset_filename = f"{card.id}-{buf.name}{ext}"
            asset_path = assets_dir / asset_filename
            asset_path.write_bytes(buf.payload if isinstance(buf.payload, bytes) else b"")

    # Write markdown
    summary = _card_summary(card)
    slug = slugify(summary)
    filename = f"{card.id}-{slug}.md" if slug else f"{card.id}.md"
    md_path = card_dir / filename
    md_content = card_to_markdown(card, stats)
    md_path.write_text(md_content, encoding="utf-8")

    return md_path


def export_vault(
    memory,
    vault_dir: Path,
    project: str | None = None,
) -> dict:
    """Export all cards to vault directory.

    Args:
        memory: ABMemory instance.
        vault_dir: Target directory for vault export.
        project: Optional project filter (owner_self).

    Returns:
        Summary dict with counts.
    """
    vault_dir = Path(vault_dir)
    vault_dir.mkdir(parents=True, exist_ok=True)

    # Get all non-forgotten cards via vault_index
    entries = memory.vault_index(project=project, limit=10000)

    exported = 0
    labels: set[str] = set()

    for entry in entries:
        try:
            card = memory.get_card(entry.card_id)
        except KeyError:
            continue

        stats = None
        try:
            stats = memory.get_card_stats(entry.card_id)
        except Exception:
            pass

        export_card(card, stats, vault_dir)
        labels.add(card.label)
        exported += 1

    # Write index
    index_md = generate_index(entries)
    index_path = vault_dir / "_index.md"
    index_path.write_text(index_md, encoding="utf-8")

    return {
        "exported": exported,
        "labels": sorted(labels),
        "index_path": str(index_path),
        "vault_dir": str(vault_dir),
    }
