"""Tests for authenticated ledger adapters with safe fallbacks."""

from __future__ import annotations

from teams.nubflow.ledgers import DiscordLedgerAdapter, JiraLedgerAdapter, NotionLedgerAdapter
from teams.nubflow.types import LedgerCursor


def test_jira_adapter_seeded_fallback_without_credentials(monkeypatch) -> None:
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    adapter = JiraLedgerAdapter()

    result = adapter.query(
        query_plan={"items": [{"key": "PROJ-1"}], "limit": 1},
        cursor=LedgerCursor(ledger_sid=adapter.sid),
        budget=5,
    )

    assert result.items and result.items[0]["key"] == "PROJ-1"
    assert result.evidence_pack["mode"] == "seeded"


def test_jira_adapter_parses_api_response(monkeypatch) -> None:
    adapter = JiraLedgerAdapter()

    def fake_json_request(*_args, **_kwargs):
        return (
            {
                "total": 1,
                "issues": [
                    {
                        "key": "PLAT-42",
                        "fields": {
                            "summary": "Implement auth",
                            "status": {"name": "In Progress"},
                            "assignee": {"displayName": "Chris"},
                            "updated": "2026-02-12T10:00:00Z",
                            "project": {"key": "PLAT"},
                        },
                    }
                ],
            },
            200,
            None,
        )

    monkeypatch.setattr("teams.nubflow.ledgers._json_request", fake_json_request)

    result = adapter.query(
        query_plan={
            "base_url": "https://jira.example.com",
            "email": "x@example.com",
            "token": "secret",
            "jql": "project=PLAT",
            "limit": 5,
        },
        cursor=LedgerCursor(ledger_sid=adapter.sid),
        budget=5,
    )

    assert result.items and result.items[0]["key"] == "PLAT-42"
    assert result.evidence_pack["mode"] == "api"


def test_notion_adapter_seeded_fallback_without_token(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    adapter = NotionLedgerAdapter()

    result = adapter.query(
        query_plan={"pages": [{"id": "abc", "title": "Doc"}], "limit": 1},
        cursor=LedgerCursor(ledger_sid=adapter.sid),
        budget=3,
    )

    assert result.items and result.items[0]["title"] == "Doc"
    assert result.evidence_pack["mode"] == "seeded"


def test_notion_adapter_parses_api_response(monkeypatch) -> None:
    adapter = NotionLedgerAdapter()

    def fake_json_request(*_args, **_kwargs):
        return (
            {
                "results": [
                    {
                        "id": "page-1",
                        "object": "page",
                        "url": "https://www.notion.so/page-1",
                        "properties": {
                            "Name": {
                                "type": "title",
                                "title": [{"plain_text": "Backend Plan"}],
                            }
                        },
                    }
                ],
                "has_more": False,
            },
            200,
            None,
        )

    monkeypatch.setattr("teams.nubflow.ledgers._json_request", fake_json_request)

    result = adapter.query(
        query_plan={"token": "secret", "query": "backend", "limit": 2},
        cursor=LedgerCursor(ledger_sid=adapter.sid),
        budget=2,
    )

    assert result.items and result.items[0]["title"] == "Backend Plan"
    assert result.evidence_pack["mode"] == "api"


def test_discord_adapter_seeded_fallback_without_token(monkeypatch) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    adapter = DiscordLedgerAdapter()

    result = adapter.query(
        query_plan={"messages": [{"id": "1", "content": "hello"}], "limit": 1},
        cursor=LedgerCursor(ledger_sid=adapter.sid),
        budget=2,
    )

    assert result.items and result.items[0]["content"] == "hello"
    assert result.evidence_pack["mode"] == "seeded"


def test_discord_adapter_parses_api_response(monkeypatch) -> None:
    adapter = DiscordLedgerAdapter()

    def fake_json_request(*_args, **_kwargs):
        return (
            [
                {
                    "id": "99",
                    "content": "ship it",
                    "timestamp": "2026-02-12T10:00:00Z",
                    "author": {"username": "bot"},
                }
            ],
            200,
            None,
        )

    monkeypatch.setattr("teams.nubflow.ledgers._json_request", fake_json_request)

    result = adapter.query(
        query_plan={"token": "secret", "channel_ids": ["123"], "limit": 1},
        cursor=LedgerCursor(ledger_sid=adapter.sid),
        budget=2,
    )

    assert result.items and result.items[0]["id"] == "99"
    assert result.items[0]["channel_id"] == "123"
    assert result.evidence_pack["mode"] == "api"
