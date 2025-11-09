from __future__ import annotations

import json
import logging
import sys
from typing import Any

REDACTED = "[REDACTED]"


def _redact_value(key: str, value: Any) -> Any:
    """Redact sensitive values based on key name (case-insensitive)."""
    sensitive = {"api_key", "x-api-key", "authorization", "token", "password", "secret"}
    if key.lower() in sensitive:
        return REDACTED
    return value


def _redact_mapping(obj: Any) -> Any:
    """Return a redacted shallow copy for dict-like extras; recurse into dicts/lists."""
    if isinstance(obj, dict):
        red: dict[str, Any] = {}
        for k, v in obj.items():
            red[k] = _redact_mapping(_redact_value(k, v))
        return red
    if isinstance(obj, list):
        return [_redact_mapping(v) for v in obj]
    return obj


class JSONFormatter(logging.Formatter):
    """A minimal JSON formatter for structured logs.

    Fields: time, level, name, message, and any extra keys passed via `extra`.
    """

    # Keys commonly present on LogRecord that we don't want to echo as extras
    _reserved = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        base: dict[str, Any] = {
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # Include extras (attributes added via `extra=`) and redact sensitive keys
        extras: dict[str, Any] = {}
        for k, v in record.__dict__.items():
            if k not in self._reserved and not k.startswith("_") and k not in base:
                extras[k] = v
        if extras:
            extras = _redact_mapping(extras)
            base.update(extras)
        return json.dumps(base, ensure_ascii=False)


def setup_logging(verbose: bool = False) -> None:
    """Configure root logger with JSON formatter to stderr.

    Idempotent across multiple invocations; it replaces any prior handler added
    by this function.
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Remove prior handler(s) we added
    to_remove = []
    for h in root.handlers:
        if getattr(h, "_limitless_handler", False):
            to_remove.append(h)
    for h in to_remove:
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler._limitless_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(JSONFormatter())
    handler.setLevel(logging.DEBUG)
    root.addHandler(handler)
