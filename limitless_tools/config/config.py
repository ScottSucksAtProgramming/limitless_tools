from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional


def default_config_path() -> str:
    """Return default user config path (platform-specific).

    Fallback if `platformdirs` is unavailable:
      - macOS: ~/Library/Application Support/limitless-tools/config.toml
      - Linux/Unix: ~/.config/limitless-tools/config.toml
      - Windows: %APPDATA%/limitless-tools/config.toml
    """
    try:
        from platformdirs import PlatformDirs  # type: ignore

        d = PlatformDirs("limitless-tools", "")
        cfg_dir = d.user_config_dir
        return os.path.join(cfg_dir, "config.toml")
    except Exception:
        home = os.path.expanduser("~")
        if sys.platform.startswith("darwin"):
            base = os.path.join(home, "Library", "Application Support", "limitless-tools")
        elif os.name == "nt":
            base = os.path.join(os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming")), "limitless-tools")
        else:
            base = os.path.join(home, ".config", "limitless-tools")
        return os.path.join(base, "config.toml")


def _parse_toml_minimal(text: str) -> Dict[str, Dict[str, Any]]:
    """Very small TOML parser supporting [sections] and key=value.

    Supports strings (".." or '..'), ints, floats, booleans.
    Not a full TOML parser; sufficient for our tests and simple config.
    """
    data: Dict[str, Dict[str, Any]] = {}
    section = "default"
    data[section] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line.strip("[]").strip()
            data.setdefault(section, {})
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        key = k.strip()
        val = v.strip()
        if val.startswith("#"):
            continue
        # strip inline comments
        if " #" in val:
            val = val.split(" #", 1)[0].strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            parsed: Any = val[1:-1]
        elif val.lower() in ("true", "false"):
            parsed = val.lower() == "true"
        else:
            try:
                if "." in val:
                    parsed = float(val)
                else:
                    parsed = int(val)
            except Exception:
                parsed = val
        data[section][key] = parsed
    return data


def load_config(path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Load a TOML config file into a nested dict keyed by profile/section.

    Returns an empty dict if no file exists or parsing fails.
    """
    cfg_path = path or default_config_path()
    try:
        if not os.path.exists(cfg_path):
            return {}
        text = open(cfg_path, "r", encoding="utf-8").read()
        # Try tomllib if available (Python 3.11+)
        try:
            import tomllib  # type: ignore

            return tomllib.loads(text)  # type: ignore[no-any-return]
        except Exception:
            return _parse_toml_minimal(text)
    except Exception:
        return {}


def get_profile(config: Dict[str, Dict[str, Any]], profile: Optional[str]) -> Dict[str, Any]:
    """Return the selected profile dictionary (default section if absent)."""
    if not config:
        return {}
    if profile and profile in config:
        return config.get(profile, {}) or {}
    # If TOML parser returns top-level keys under other shape, fallback
    return config.get("default", {}) or {}

