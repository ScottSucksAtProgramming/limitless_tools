from __future__ import annotations

from typing import Any, Dict, List, Optional

import os

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - requests should be present in dev
    requests = None  # type: ignore


class LimitlessClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        session: Optional[Any] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or os.getenv("LIMITLESS_API_URL") or "https://api.limitless.ai").rstrip("/")
        self.session = session or (requests.Session() if requests is not None else None)

    def _headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key}

    def get_lifelogs(
        self,
        *,
        limit: Optional[int] = None,
        direction: str = "desc",
        include_markdown: bool = True,
        include_headings: bool = True,
        date: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        timezone: Optional[str] = None,
        is_starred: Optional[bool] = None,
        batch_size: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Fetch lifelogs with automatic pagination. Returns a list of lifelog dicts.
        """

        if limit is not None:
            page_size = min(batch_size, max(1, int(limit)))
        else:
            page_size = batch_size

        collected: List[Dict[str, Any]] = []
        cursor: Optional[str] = None

        while True:
            params: Dict[str, Any] = {
                "limit": page_size,
                "direction": direction,
                "includeMarkdown": "true" if include_markdown else "false",
                "includeHeadings": "true" if include_headings else "false",
            }
            if date:
                params["date"] = date
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            if timezone:
                params["timezone"] = timezone
            if is_starred is not None:
                params["isStarred"] = "true" if is_starred else "false"
            if cursor:
                params["cursor"] = cursor

            url = f"{self.base_url}/v1/lifelogs"
            resp = self.session.get(url, headers=self._headers(), params=params)  # type: ignore[union-attr]
            if not getattr(resp, "ok", False):
                status = getattr(resp, "status_code", "?")
                raise RuntimeError(f"HTTP error fetching lifelogs (status {status})")

            body = resp.json()
            page_items: List[Dict[str, Any]] = body.get("data", {}).get("lifelogs", []) or []
            collected.extend(page_items)

            if limit is not None and len(collected) >= limit:
                return collected[:limit]

            cursor = body.get("meta", {}).get("lifelogs", {}).get("nextCursor")
            if not cursor:
                break

        return collected
