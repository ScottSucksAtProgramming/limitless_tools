from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from limitless_tools.errors import ApiError, ConfigurationError

try:
    import requests
except ImportError:  # pragma: no cover - requests should be present in dev
    requests = None

log = logging.getLogger(__name__)


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
        timeout: float | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = (base_url or os.getenv("LIMITLESS_API_URL") or "https://api.limitless.ai").rstrip("/")
        self._enforce_base_url_allowlist()
        self.session = session or (requests.Session() if requests is not None else None)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_statuses = retry_statuses
        # Default request timeout (seconds)
        if timeout is None:
            env_to = os.getenv("LIMITLESS_HTTP_TIMEOUT")
            try:
                self.timeout = float(env_to) if env_to else 30.0
            except (ValueError, TypeError) as exc:
                log.debug("Invalid LIMITLESS_HTTP_TIMEOUT (%s): %s", env_to, exc)
                self.timeout = 30.0
        else:
            self.timeout = timeout
        # default sleep uses time.sleep, but lazily import to avoid overhead in tests
        if sleep_fn is None:
            import time as _time
            self.sleep_fn = _time.sleep
        else:
            self.sleep_fn = sleep_fn

    def _headers(self) -> dict[str, str]:
        # Add a simple User-Agent with package version when available
        ua = "limitless-tools"
        try:
            from importlib.metadata import version

            ua = f"limitless-tools/{version('limitless-tools')}"
        except (ImportError, ModuleNotFoundError) as exc:
            log.debug("Failed to read package metadata: %s", exc)
        return {"X-API-Key": self.api_key, "User-Agent": ua}

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
        except (ImportError, ValueError, AttributeError) as exc:
            log.debug("Failed to parse base URL host %s: %s", self.base_url, exc)
            host = ""
        default_allowed = {"api.limitless.ai", "localhost", "127.0.0.1"}
        extra = os.getenv("LIMITLESS_URL_ALLOWLIST", "")
        extra_hosts = {h.strip() for h in extra.split(",") if h.strip()}
        allowed = default_allowed | extra_hosts
        if host not in allowed:
            raise ConfigurationError(f"Base URL host not allowed: {host}")

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
        progress_callback: Callable[[int, int], None] | None = None,
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

        page_number = 0
        while True:
            page_number += 1
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
                # Pass timeout only if the session.get signature accepts it (keeps tests' fakes working)
                req_kwargs: dict[str, Any] = {}
                try:
                    import inspect as _inspect

                    sig = _inspect.signature(self.session.get)  # type: ignore[union-attr]
                    if "timeout" in sig.parameters or any(
                        p.kind == p.VAR_KEYWORD for p in sig.parameters.values()
                    ):
                        req_kwargs["timeout"] = self.timeout
                except (AttributeError, ValueError, TypeError) as exc:
                    log.debug("Session.get signature missing timeout: %s", exc)
                try:
                    resp = self.session.get(  # type: ignore[union-attr]
                        url,
                        headers=self._headers(),
                        params=params,
                        **req_kwargs,
                    )
                except Exception as exc:
                    if attempt < self.max_retries:
                        attempt += 1
                        delay = self.backoff_factor * (2 ** (attempt - 1))
                        self.sleep_fn(delay)
                        continue
                    msg = self._network_error_message(exc)
                    raise ApiError(
                        msg,
                        cause=exc,
                        context={
                            "url": url,
                            "params": {k: params.get(k) for k in ("cursor", "limit", "date") if params.get(k)},
                        },
                    ) from exc
                if getattr(resp, "ok", False):
                    break
                status = getattr(resp, "status_code", None)
                if status in self.retry_statuses and attempt < self.max_retries:
                    attempt += 1
                    # Use Retry-After header if provided; otherwise exponential backoff
                    headers = getattr(resp, "headers", {}) or {}
                    ra = headers.get("Retry-After") if isinstance(headers, dict) else None
                    delay = None
                    if ra is not None:
                        # Retry-After can be seconds or HTTP-date per RFC 7231
                        try:
                            delay = float(ra)
                        except Exception:
                            try:
                                from datetime import datetime, timezone as _tz
                                from email.utils import parsedate_to_datetime as _pdt

                                dt = _pdt(str(ra))
                                if dt is not None:
                                    now = datetime.now(_tz.utc)  # noqa: UP017
                                    if dt.tzinfo is None:
                                        dt = dt.replace(tzinfo=_tz.utc)  # noqa: UP017
                                    delay = max(0.0, (dt - now).total_seconds())
                            except Exception:
                                delay = None
                    if delay is None:
                        delay = self.backoff_factor * (2 ** (attempt - 1))
                    self.sleep_fn(delay)
                    continue
                # Build informative error message for non-retryable errors
                detail = self._error_detail(resp)
                raise ApiError(
                    f"HTTP {status} error fetching lifelogs: {detail}",
                    status_code=status,
                    context={"url": url, "params": {"cursor": params.get("cursor")}},
                )

            body = resp.json()
            page_items: list[dict[str, Any]] = body.get("data", {}).get("lifelogs", []) or []
            collected.extend(page_items)
            if progress_callback is not None:
                try:
                    progress_callback(page_number, len(collected))
                except Exception:
                    log.debug("Progress callback failed", exc_info=True)

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

    def _network_error_message(self, exc: Exception) -> str:
        text = str(exc).strip().lower()
        if self._looks_like_timeout(exc, text):
            return "Request timed out while fetching lifelogs."
        return "Network error while fetching lifelogs."

    @staticmethod
    def _looks_like_timeout(exc: Exception, text: str) -> bool:
        if isinstance(exc, TimeoutError):  # noqa: F821 - built-in in >=3.10
            return True
        if "timeout" in text:
            return True
        timeout_cls = getattr(requests, "Timeout", None) if requests is not None else None
        return timeout_cls is not None and isinstance(exc, timeout_cls)
