from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)


def load_env() -> None:
    """Load a .env file from the current directory or parent tree (if available)."""
    load_dotenv = None
    find_dotenv = None
    try:
        from dotenv import find_dotenv as _fd, load_dotenv as _ld
        load_dotenv = _ld
        find_dotenv = _fd
    except ImportError as exc:
        log.debug("dotenv loaders unavailable: %s", exc)
    if find_dotenv and load_dotenv:
        env_path = find_dotenv(usecwd=True)
        if env_path:
            # Override existing process env so tests and CLI defaults honor .env
            load_dotenv(env_path, override=True)
            return
    # fallback: simple parser for .env in CWD
    try:
        path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    except OSError as exc:
        log.debug("Failed to parse local .env (%s) fallback: %s", path, exc)
        return


def resolve_timezone(tz: str | None) -> str | None:
    """Return tz if provided, else system local timezone name."""
    if tz:
        return tz
    try:
        import tzlocal

        return tzlocal.get_localzone_name()
    except (ImportError, OSError) as exc:
        log.debug("Unable to resolve timezone via tzlocal: %s", exc)
        return None
