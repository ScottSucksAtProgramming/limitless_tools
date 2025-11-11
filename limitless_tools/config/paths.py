from __future__ import annotations

import os
from pathlib import Path


def default_data_dir() -> str:
    """Return the default data directory path for lifelogs."""
    return str(Path(os.path.expanduser("~")) / "limitless_tools" / "data" / "lifelogs")


def expand_path(path: str | None, *, base_dir: str | None = None) -> str | None:
    """Return the provided path expanded, optionally relative to a base directory."""
    if not path:
        return None
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = _restore_missing_root(candidate)
    if not candidate.is_absolute() and base_dir:
        base = Path(base_dir).expanduser()
        candidate = base / candidate
    return str(candidate)


def _restore_missing_root(candidate: Path) -> Path:
    """If the user omitted the leading '/', detect home-relative roots."""
    parts = candidate.parts
    if not parts:
        return candidate
    home = Path.home()
    home_parts = home.parts
    rel_home = home_parts[1:]
    if rel_home and len(parts) >= len(rel_home) and tuple(parts[: len(rel_home)]) == tuple(rel_home):
        root = home_parts[0] if home_parts else os.sep
        return Path(root).joinpath(*parts)
    return candidate
