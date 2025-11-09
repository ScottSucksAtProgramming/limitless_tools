from __future__ import annotations

import os
from typing import Any

try:
    import requests
except Exception:  # pragma: no cover - requests should be present in dev
    requests = None


class LimitlessClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        session: Any | None = None,
        *,
        max_retries: int = 0,
        backoff_factor: float = 0.5,
        retry_statuses: tuple[int, ...] = (429, 502, 503, 504),
        sleep_fn: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or os.getenv("LIMITLESS_API_URL") or "https://api.limitless.ai").rstrip("/")
        self._enforce_base_url_allowlist()
        self.session = session or (requests.Session() if requests is not None else None)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_statuses = retry_statuses
        # default sleep uses time.sleep, but lazily import to avoid overhead in tests
        if sleep_fn is None:
            import time as _time
            self.sleep_fn = _time.sleep
        else:
            self.sleep_fn = sleep_fn

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key}

    def _enforce_base_url_allowlist(self) -> None:
        """Prevent accidental egress by restricting base_url host to an allowlist.

        Allowed by default: api.limitless.ai, localhost, 127.0.0.1
        Extend via env `LIMITLESS_URL_ALLOWLIST` (comma-separated), or bypass with
        `LIMITLESS_ALLOW_UNSAFE_URLS=1`.
        """
        if os.getenv("LIMITLESS_ALLOW_UNSAFE_URLS"):
            return
        try:
            from urllib.parse import urlparse

            host = urlparse(self.base_url).hostname or ""
        except Exception:
            host = ""
        default_allowed = {"api.limitless.ai", "localhost", "127.0.0.1"}
        extra = os.getenv("LIMITLESS_URL_ALLOWLIST", "")
        extra_hosts = {h.strip() for h in extra.split(",") if h.strip()}
        allowed = default_allowed | extra_hosts
        if host not in allowed:
            raise ValueError(f"Base URL host not allowed: {host}")

    def get_lifelogs(
        self,
        *,
        limit: int | None = None,
        direction: str = "desc",
        include_markdown: bool = True,
        include_headings: bool = True,
        date: str | None = None,
        start: str | None = None,
        end: str | None = None,
        timezone: str | None = None,
        is_starred: bool | None = None,
        batch_size: int = 50,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch lifelogs with automatic pagination. Returns a list of lifelog dicts.
        """

        if limit is not None:
            page_size = min(batch_size, max(1, int(limit)))
        else:
            page_size = batch_size

        collected: list[dict[str, Any]] = []
        # seed initial cursor if provided
        current_cursor: str | None = cursor
        self.last_next_cursor: str | None = None

        while True:
            params: dict[str, Any] = {
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
            if current_cursor:
                params["cursor"] = current_cursor

            url = f"{self.base_url}/v1/lifelogs"
            # perform request with retry loop
            attempt = 0
            while True:
                resp = self.session.get(url, headers=self._headers(), params=params)  # type: ignore[union-attr]
                if getattr(resp, "ok", False):
                    break
                status = getattr(resp, "status_code", None)
                if status in self.retry_statuses and attempt < self.max_retries:
                    attempt += 1
                    # Use Retry-After header if provided; otherwise exponential backoff
                    headers = getattr(resp, "headers", {}) or {}
                    ra = headers.get("Retry-After") if isinstance(headers, dict) else None
                    try:
                        delay = float(ra) if ra is not None else self.backoff_factor * (2 ** (attempt - 1))
                    except Exception:
                        delay = self.backoff_factor * (2 ** (attempt - 1))
                    self.sleep_fn(delay)
                    continue
                # Build informative error message for non-retryable errors
                detail = self._error_detail(resp)
                raise RuntimeError(f"HTTP {status} error fetching lifelogs: {detail}")

            body = resp.json()
            page_items: list[dict[str, Any]] = body.get("data", {}).get("lifelogs", []) or []
            collected.extend(page_items)

            if limit is not None and len(collected) >= limit:
                return collected[:limit]

            current_cursor = body.get("meta", {}).get("lifelogs", {}).get("nextCursor")
            if current_cursor:
                self.last_next_cursor = current_cursor
            if not current_cursor:
                break

        return collected

    def _error_detail(self, resp: Any) -> str:
        """Extract an informative error message from a failed HTTP response."""
        # Try JSON body first
        try:
            body = resp.json()
        except Exception:  # pragma: no cover - exercised implicitly when non-JSON
            body = None
        # Common shapes: {"error": {"code": "X", "message": "..."}} or {"message": "..."}
        if isinstance(body, dict):
            if isinstance(body.get("error"), dict):
                err = body["error"]
                code = err.get("code")
                msg = err.get("message") or err.get("detail")
                if code and msg:
                    return f"{code}: {msg}"
                if code:
                    return str(code)
                if msg:
                    return str(msg)
            # Fallbacks
            if isinstance(body.get("message"), str):
                return body["message"]
            if isinstance(body.get("detail"), str):
                return body["detail"]
        # Fallback to text if available
        text = getattr(resp, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()
        return "Unknown error"
