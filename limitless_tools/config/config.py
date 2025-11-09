from __future__ import annotations

import os
from typing import Any


def default_config_path() -> str:
    """Return default user config path within ~/limitless_tools/.

    New default: ~/limitless_tools/config/config.toml
    """
    home = os.path.expanduser("~")
    base = os.path.join(home, "limitless_tools", "config")
    return os.path.join(base, "config.toml")


def _parse_toml_minimal(text: str) -> dict[str, dict[str, Any]]:
    """Very small TOML parser supporting [sections] and key=value.

    Supports strings (".." or '..'), ints, floats, booleans.
    Not a full TOML parser; sufficient for our tests and simple config.
    """
    data: dict[str, dict[str, Any]] = {}
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


def load_config(path: str | None = None) -> dict[str, dict[str, Any]]:
    """Load a TOML config file into a nested dict keyed by profile/section.

    Returns an empty dict if no file exists or parsing fails.
    """
    cfg_path = path or default_config_path()
    try:
        if not os.path.exists(cfg_path):
            return {}
        text = open(cfg_path, encoding="utf-8").read()
        # Try tomllib if available (Python 3.11+)
        try:
            import tomllib

            return tomllib.loads(text)
        except Exception:
            return _parse_toml_minimal(text)
    except Exception:
        return {}


def get_profile(config: dict[str, dict[str, Any]], profile: str | None) -> dict[str, Any]:
    """Return the selected profile dictionary (default section if absent)."""
    if not config:
        return {}
    if profile and profile in config:
        return config.get(profile, {}) or {}
    # If TOML parser returns top-level keys under other shape, fallback
    return config.get("default", {}) or {}


def save_config(path: str, config: dict[str, dict[str, Any]]) -> None:
    """Write the config dict to TOML at path, creating parent directories.

    Minimal TOML writer supporting strings, ints, floats, and booleans.
    """
    from pathlib import Path as _Path

    def _format(v: Any) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        # default to string; escape double quotes
        s = str(v).replace("\"", "\\\"")
        return f'"{s}"'

    p = _Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for section in sorted(config.keys()):
        lines.append(f"[{section}]")
        for key, value in config[section].items():
            lines.append(f"{key} = {_format(value)}")
        lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    p.write_text(text, encoding="utf-8")
