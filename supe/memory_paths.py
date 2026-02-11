"""Shared helpers for supe memory CLI path/project behavior."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def get_global_db_path() -> str:
    """Return the memory DB path with env-var override support.

    Priority:
    1. ``SUPE_DB``
    2. ``TASC_DB`` (legacy)
    3. ``~/.supe/memory.sqlite``
    """
    if db := os.environ.get("SUPE_DB"):
        return db
    if db := os.environ.get("TASC_DB"):
        return db

    default_path = os.path.expanduser("~/.supe/memory.sqlite")
    os.makedirs(os.path.dirname(default_path), exist_ok=True)
    return default_path


def get_current_project() -> str:
    """Get project identity from env var fallback to current directory name."""
    if project := os.environ.get("SUPE_PROJECT"):
        return project
    return os.path.basename(os.getcwd())


def filter_by_project(cards: Iterable[T], project: str | None) -> list[T]:
    """Filter card-like objects by project in ``owner_self`` field."""
    if not project:
        return list(cards)
    return [card for card in cards if getattr(card, "owner_self", None) and project in card.owner_self]
