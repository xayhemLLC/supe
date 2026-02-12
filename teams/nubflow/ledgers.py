"""Ledger contracts and adapters for FoT v0.0.0."""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .types import LedgerCursor, LedgerQueryResult, LedgerSummaryResult, new_sid


def _get_env(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return ""


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _json_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float = 8.0,
) -> tuple[dict[str, Any] | list[Any], int, str | None]:
    body = None
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")

    request = Request(url, data=body, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="ignore")
            status = int(getattr(response, "status", 200))
            parsed = json.loads(raw) if raw else {}
            if isinstance(parsed, dict):
                return parsed, status, None
            if isinstance(parsed, list):
                return parsed, status, None
            return {"value": parsed}, status, None
    except HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8", errors="ignore")
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {"error": str(exc)}
        return parsed if isinstance(parsed, dict) else {"error": str(exc)}, exc.code, str(exc)
    except (URLError, TimeoutError, ValueError, OSError) as exc:
        return {"error": str(exc)}, 0, str(exc)


@dataclass
class BaseLedgerAdapter:
    """Default adapter implementation used for v0.0.0 stubs."""

    kind: str
    sid: str = field(default_factory=new_sid)
    seeded_items: list[dict[str, Any]] = field(default_factory=list)

    def query(
        self,
        query_plan: dict[str, Any],
        cursor: LedgerCursor,
        budget: int,
    ) -> LedgerQueryResult:
        limit = max(0, min(_to_int(query_plan.get("limit"), 10), budget))
        items = list(self.seeded_items[:limit])
        next_cursor = None
        if self.seeded_items and limit < len(self.seeded_items):
            next_cursor = str(limit)
        evidence = {
            "ledger_kind": self.kind,
            "count": len(items),
            "query_plan": query_plan,
        }
        return LedgerQueryResult(items=items, next_cursor=next_cursor, evidence_pack=evidence)

    def summarize(
        self,
        items: list[dict[str, Any]],
        goal: str,
        budget: int,
    ) -> LedgerSummaryResult:
        sample = items[: max(0, min(len(items), budget, 3))]
        summary = {
            "goal": goal,
            "ledger_kind": self.kind,
            "item_count": len(items),
            "sample": sample,
        }
        pointers = [f"{self.kind}:{idx}" for idx, _ in enumerate(sample)]
        return LedgerSummaryResult(summary_artifact=summary, pointers=pointers)


class GitLedgerAdapter(BaseLedgerAdapter):
    def __init__(self) -> None:
        super().__init__(kind="GitLedger")

    def query(
        self,
        query_plan: dict[str, Any],
        cursor: LedgerCursor,
        budget: int,
    ) -> LedgerQueryResult:
        repo_path = str(query_plan.get("repo_path") or query_plan.get("cwd") or ".")
        limit = max(1, min(_to_int(query_plan.get("limit"), 10), budget))
        include_diff = bool(query_plan.get("include_diff", False))

        def _run(args: list[str]) -> str:
            result = subprocess.run(
                args,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return ""
            return result.stdout.strip()

        branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"
        commit = _run(["git", "rev-parse", "HEAD"])[:12]
        status = _run(["git", "status", "--short"])
        log = _run(["git", "log", "--oneline", f"-n{limit}"])
        diff = _run(["git", "diff", "--stat"]) if include_diff else ""

        changed_files = []
        for line in status.splitlines():
            line = line.strip()
            if not line:
                continue
            path = line.split()[-1]
            changed_files.append(path)

        items: list[dict[str, Any]] = []
        for idx, line in enumerate(log.splitlines()):
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            sha = parts[0]
            message = parts[1] if len(parts) > 1 else ""
            component = changed_files[idx] if idx < len(changed_files) else "repo"
            items.append(
                {
                    "commit": sha,
                    "message": message,
                    "component": component.split("/")[0],
                    "interface": "git",
                }
            )

        if not items:
            items.append(
                {
                    "commit": commit,
                    "message": "working tree snapshot",
                    "component": "repo",
                    "interface": "git",
                }
            )

        evidence = {
            "ledger_kind": self.kind,
            "repo_path": repo_path,
            "branch": branch,
            "commit": commit,
            "status_lines": len(status.splitlines()) if status else 0,
            "diff_stat": diff,
        }
        next_cursor = None
        return LedgerQueryResult(items=items[:limit], next_cursor=next_cursor, evidence_pack=evidence)


class JiraLedgerAdapter(BaseLedgerAdapter):
    def __init__(self) -> None:
        super().__init__(kind="JiraLedger")

    def query(
        self,
        query_plan: dict[str, Any],
        cursor: LedgerCursor,
        budget: int,
    ) -> LedgerQueryResult:
        limit = max(1, min(_to_int(query_plan.get("limit"), 10), budget))
        seeded = list(query_plan.get("items") or self.seeded_items)

        base_url = str(query_plan.get("base_url") or _get_env("JIRA_BASE_URL", "ATLASSIAN_BASE_URL")).rstrip("/")
        email = str(query_plan.get("email") or _get_env("JIRA_EMAIL", "ATLASSIAN_EMAIL"))
        token = str(query_plan.get("token") or _get_env("JIRA_API_TOKEN", "JIRA_TOKEN", "ATLASSIAN_API_TOKEN"))

        if not (base_url and token):
            items = [item for item in seeded[:limit] if isinstance(item, dict)]
            evidence = {
                "ledger_kind": self.kind,
                "mode": "seeded",
                "reason": "missing_jira_credentials",
                "count": len(items),
            }
            return LedgerQueryResult(items=items, next_cursor=None, evidence_pack=evidence)

        jql = str(query_plan.get("jql") or "ORDER BY updated DESC")
        fields = query_plan.get("fields") or ["summary", "status", "assignee", "updated", "project"]
        if not isinstance(fields, list):
            fields = ["summary", "status", "assignee", "updated", "project"]

        start_at = _to_int(query_plan.get("start_at") or cursor.paging_cursor, 0)
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": limit,
            "fields": ",".join(str(f) for f in fields),
        }
        url = f"{base_url}/rest/api/3/search?{urlencode(params)}"

        if email:
            encoded = base64.b64encode(f"{email}:{token}".encode()).decode("utf-8")
            auth_header = f"Basic {encoded}"
            auth_mode = "basic"
        else:
            auth_header = token if token.lower().startswith("bearer ") else f"Bearer {token}"
            auth_mode = "bearer"

        payload, status_code, error = _json_request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": auth_header,
            },
        )

        issues = payload.get("issues", []) if isinstance(payload, dict) else []
        items: list[dict[str, Any]] = []
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            fields_obj = issue.get("fields") if isinstance(issue.get("fields"), dict) else {}
            project = fields_obj.get("project") if isinstance(fields_obj.get("project"), dict) else {}
            status_obj = fields_obj.get("status") if isinstance(fields_obj.get("status"), dict) else {}
            assignee = fields_obj.get("assignee") if isinstance(fields_obj.get("assignee"), dict) else {}
            items.append(
                {
                    "key": issue.get("key"),
                    "summary": fields_obj.get("summary", ""),
                    "status": status_obj.get("name", ""),
                    "assignee": assignee.get("displayName", ""),
                    "updated": fields_obj.get("updated", ""),
                    "component": project.get("key", "jira"),
                    "interface": "jira",
                }
            )

        next_cursor = None
        total = _to_int(payload.get("total") if isinstance(payload, dict) else 0, 0)
        if start_at + len(items) < total:
            next_cursor = str(start_at + len(items))

        evidence = {
            "ledger_kind": self.kind,
            "mode": "api",
            "status_code": status_code,
            "count": len(items),
            "auth_mode": auth_mode,
            "error": error,
        }

        if not items and seeded:
            items = [item for item in seeded[:limit] if isinstance(item, dict)]
            evidence["mode"] = "seeded_fallback"

        return LedgerQueryResult(items=items, next_cursor=next_cursor, evidence_pack=evidence)


class NotionLedgerAdapter(BaseLedgerAdapter):
    def __init__(self) -> None:
        super().__init__(kind="NotionLedger")

    def query(
        self,
        query_plan: dict[str, Any],
        cursor: LedgerCursor,
        budget: int,
    ) -> LedgerQueryResult:
        limit = max(1, min(_to_int(query_plan.get("limit"), 10), budget))
        seeded = list(query_plan.get("pages") or query_plan.get("items") or self.seeded_items)

        token = str(query_plan.get("token") or _get_env("NOTION_API_KEY", "NOTION_TOKEN"))
        notion_version = str(query_plan.get("notion_version") or "2022-06-28")

        if not token:
            items = [item for item in seeded[:limit] if isinstance(item, dict)]
            evidence = {
                "ledger_kind": self.kind,
                "mode": "seeded",
                "reason": "missing_notion_token",
                "count": len(items),
            }
            return LedgerQueryResult(items=items, next_cursor=None, evidence_pack=evidence)

        query = str(query_plan.get("query") or "")
        body: dict[str, Any] = {"page_size": limit}
        if query:
            body["query"] = query
        if cursor.paging_cursor:
            body["start_cursor"] = cursor.paging_cursor

        data, status_code, error = _json_request(
            "https://api.notion.com/v1/search",
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": notion_version,
                "Accept": "application/json",
            },
            payload=body,
        )

        results = data.get("results", []) if isinstance(data, dict) else []
        items: list[dict[str, Any]] = []
        for node in results:
            if not isinstance(node, dict):
                continue
            entry_type = str(node.get("object", "page"))
            url = str(node.get("url", ""))
            title = self._extract_notion_title(node)
            items.append(
                {
                    "id": node.get("id"),
                    "title": title,
                    "url": url,
                    "type": entry_type,
                    "component": "notion",
                    "interface": "notion",
                }
            )

        next_cursor = None
        if isinstance(data, dict) and data.get("has_more") and data.get("next_cursor"):
            next_cursor = str(data.get("next_cursor"))

        evidence = {
            "ledger_kind": self.kind,
            "mode": "api",
            "status_code": status_code,
            "count": len(items),
            "error": error,
        }

        if not items and seeded:
            items = [item for item in seeded[:limit] if isinstance(item, dict)]
            evidence["mode"] = "seeded_fallback"

        return LedgerQueryResult(items=items, next_cursor=next_cursor, evidence_pack=evidence)

    @staticmethod
    def _extract_notion_title(item: dict[str, Any]) -> str:
        properties = item.get("properties") if isinstance(item.get("properties"), dict) else {}
        for value in properties.values():
            if not isinstance(value, dict):
                continue
            if value.get("type") == "title" and isinstance(value.get("title"), list):
                parts = [str(chunk.get("plain_text", "")) for chunk in value["title"] if isinstance(chunk, dict)]
                title = "".join(parts).strip()
                if title:
                    return title

        if isinstance(item.get("title"), list):
            parts = [str(chunk.get("plain_text", "")) for chunk in item["title"] if isinstance(chunk, dict)]
            title = "".join(parts).strip()
            if title:
                return title

        return ""


class DiscordLedgerAdapter(BaseLedgerAdapter):
    def __init__(self) -> None:
        super().__init__(kind="DiscordLedger")

    def query(
        self,
        query_plan: dict[str, Any],
        cursor: LedgerCursor,
        budget: int,
    ) -> LedgerQueryResult:
        limit = max(1, min(_to_int(query_plan.get("limit"), 10), budget))
        seeded = list(query_plan.get("messages") or query_plan.get("items") or self.seeded_items)

        token = str(query_plan.get("token") or _get_env("DISCORD_BOT_TOKEN", "DISCORD_TOKEN"))
        if token and not token.lower().startswith(("bot ", "bearer ")):
            token = f"Bot {token}"

        channel_ids = query_plan.get("channel_ids")
        if not isinstance(channel_ids, list):
            single = query_plan.get("channel_id") or _get_env("DISCORD_CHANNEL_ID")
            channel_ids = [single] if single else []

        if not (token and channel_ids):
            items = [item for item in seeded[:limit] if isinstance(item, dict)]
            evidence = {
                "ledger_kind": self.kind,
                "mode": "seeded",
                "reason": "missing_discord_token_or_channel",
                "count": len(items),
            }
            return LedgerQueryResult(items=items, next_cursor=None, evidence_pack=evidence)

        per_channel = max(1, limit // max(1, len(channel_ids)))
        before = str(query_plan.get("before") or cursor.paging_cursor or "")

        collected: list[dict[str, Any]] = []
        last_id = None
        for channel_id in channel_ids:
            params = {"limit": per_channel}
            if before:
                params["before"] = before
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages?{urlencode(params)}"
            data, _status_code, _error = _json_request(
                url,
                headers={
                    "Authorization": token,
                    "Accept": "application/json",
                },
            )
            rows = data if isinstance(data, list) else []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                author = row.get("author") if isinstance(row.get("author"), dict) else {}
                message_id = str(row.get("id", ""))
                if message_id:
                    last_id = message_id
                collected.append(
                    {
                        "id": message_id,
                        "channel_id": str(channel_id),
                        "author": author.get("username", ""),
                        "content": str(row.get("content", ""))[:500],
                        "timestamp": row.get("timestamp", ""),
                        "component": str(channel_id),
                        "interface": "discord",
                    }
                )

        items = collected[:limit]
        evidence = {
            "ledger_kind": self.kind,
            "mode": "api",
            "count": len(items),
            "channels": [str(channel) for channel in channel_ids],
        }
        next_cursor = last_id if len(items) >= limit else None

        if not items and seeded:
            items = [item for item in seeded[:limit] if isinstance(item, dict)]
            evidence["mode"] = "seeded_fallback"

        return LedgerQueryResult(items=items, next_cursor=next_cursor, evidence_pack=evidence)


class WebLedgerAdapter(BaseLedgerAdapter):
    def __init__(self) -> None:
        super().__init__(kind="WebLedger")

    def query(
        self,
        query_plan: dict[str, Any],
        cursor: LedgerCursor,
        budget: int,
    ) -> LedgerQueryResult:
        urls = list(query_plan.get("urls") or [])
        limit = max(0, min(_to_int(query_plan.get("limit"), len(urls) or 5), budget))
        collected: list[dict[str, Any]] = []

        for url in urls[:limit]:
            item = self._fetch_url(str(url))
            collected.append(item)

        if not collected:
            collected = list(self.seeded_items[:limit])

        next_cursor = None
        if len(urls) > limit:
            next_cursor = str(limit)

        evidence = {
            "ledger_kind": self.kind,
            "fetched_count": len(collected),
            "requested_count": len(urls),
        }
        return LedgerQueryResult(items=collected, next_cursor=next_cursor, evidence_pack=evidence)

    @staticmethod
    def _fetch_url(url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        host = parsed.netloc or "unknown"
        req = Request(url, headers={"User-Agent": "supe-fot/0.0.0"})
        try:
            with urlopen(req, timeout=6) as response:
                body = response.read(12000).decode("utf-8", errors="ignore")
                status_code = getattr(response, "status", 200)
            title = ""
            match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
            if match:
                title = re.sub(r"\s+", " ", match.group(1)).strip()[:200]
            snippet = re.sub(r"\s+", " ", body).strip()[:300]
            return {
                "url": url,
                "status_code": status_code,
                "title": title,
                "snippet": snippet,
                "component": host,
                "interface": "http",
            }
        except (URLError, TimeoutError, ValueError) as exc:
            return {
                "url": url,
                "status_code": 0,
                "title": "",
                "snippet": str(exc),
                "component": host,
                "interface": "http",
                "error": str(exc),
            }


class CustomLedgerAdapter(BaseLedgerAdapter):
    def __init__(self, kind: str = "CustomLedger") -> None:
        super().__init__(kind=kind)


class LedgerRegistry:
    """Name-indexed registry of ledger adapters."""

    def __init__(self) -> None:
        self._items: dict[str, BaseLedgerAdapter] = {}

    @classmethod
    def with_defaults(cls) -> LedgerRegistry:
        registry = cls()
        for adapter in (
            GitLedgerAdapter(),
            JiraLedgerAdapter(),
            NotionLedgerAdapter(),
            DiscordLedgerAdapter(),
            WebLedgerAdapter(),
        ):
            registry.register(adapter)
        return registry

    def register(self, adapter: BaseLedgerAdapter) -> None:
        self._items[adapter.kind] = adapter

    def get(self, kind: str) -> BaseLedgerAdapter | None:
        return self._items.get(kind)

    def all(self) -> dict[str, BaseLedgerAdapter]:
        return dict(self._items)

    def by_buffer_name(self, buffer_name: str) -> BaseLedgerAdapter | None:
        mapping = {
            "git_ledger": "GitLedger",
            "jira_ledger": "JiraLedger",
            "notion_ledger": "NotionLedger",
            "discord_ledger": "DiscordLedger",
            "web_ledger": "WebLedger",
        }
        return self.get(mapping.get(buffer_name, ""))
