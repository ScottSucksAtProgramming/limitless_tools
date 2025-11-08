from __future__ import annotations

import argparse
import os
from typing import List, Optional

from limitless_tools.services.lifelog_service import LifelogService
from limitless_tools.config.paths import default_data_dir
from limitless_tools.config.env import load_env
from limitless_tools.config.logging import setup_logging
from limitless_tools.config.config import load_config, get_profile, default_config_path
import logging
import sys
from zoneinfo import ZoneInfo


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="limitless", description="Limitless Tools CLI")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", type=str, help=f"Path to config TOML (default: {default_config_path()})")
    parser.add_argument("--profile", type=str, default=None, help="Config profile/section to use (default)")
    sub = parser.add_subparsers(dest="command")

    fetch = sub.add_parser("fetch", help="Fetch lifelogs")
    fetch.add_argument("--limit", type=int, default=10)
    fetch.add_argument("--direction", type=str, default="desc", choices=["asc", "desc"])
    # Defaults: include markdown/headings by default; allow disabling via --no-*
    fetch.add_argument("--include-markdown", dest="include_markdown", action="store_true")
    fetch.add_argument("--no-include-markdown", dest="include_markdown", action="store_false")
    fetch.set_defaults(include_markdown=True)
    fetch.add_argument("--include-headings", dest="include_headings", action="store_true")
    fetch.add_argument("--no-include-headings", dest="include_headings", action="store_false")
    fetch.set_defaults(include_headings=True)
    fetch.add_argument("--batch-size", type=int, default=50, help="Page size to use when fetching (default: 50)")
    fetch.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())
    fetch.add_argument("--json", action="store_true", default=False, help="Output JSON summary of saved items")

    sync = sub.add_parser("sync", help="Sync lifelogs for a date or range")
    sync.add_argument("--date", type=str)
    sync.add_argument("--start", type=str)
    sync.add_argument("--end", type=str)
    sync.add_argument(
        "--timezone",
        type=str,
        help="IANA timezone name (e.g., 'America/Los_Angeles', 'UTC')."
    )
    sync.add_argument("--starred-only", action="store_true", default=False)
    sync.add_argument("--batch-size", type=int, default=50, help="Page size to use when syncing (default: 50)")
    sync.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())
    sync.add_argument("--json", action="store_true", default=False, help="Output JSON summary of results")

    lst = sub.add_parser("list", help="List local lifelogs")
    lst.add_argument("--date", type=str)
    lst.add_argument("--starred-only", action="store_true", default=False)
    lst.add_argument("--json", action="store_true", default=False, dest="as_json")
    lst.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    exp = sub.add_parser("export-markdown", help="Export markdown from local lifelogs")
    exp.add_argument("--limit", type=int, default=1)
    exp.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    fa = sub.add_parser("fetch-audio", help="Download audio for a lifelog (placeholder)")
    fa.add_argument("--lifelog-id", required=True)
    fa.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    cfgp = sub.add_parser("configure", help="Create or update user config (TOML)")
    cfgp.add_argument("--api-key", type=str)
    cfgp.add_argument("--api-url", type=str)
    cfgp.add_argument("--data-dir", type=str)
    cfgp.add_argument("--timezone", type=str)
    cfgp.add_argument("--batch-size", type=int)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    # Ensure .env and related environment variables are loaded before parsing
    load_env()
    parser = _build_parser()
    args = parser.parse_args(args=argv)
    setup_logging(verbose=bool(getattr(args, "verbose", False)))

    log = logging.getLogger("limitless_tools.cli")
    log.info("cli_start", extra={"event": "cli_start", "command": args.command})
    if getattr(args, "verbose", False):
        # Emit a debug message for tests/diagnostics (avoid reserved LogRecord keys)
        log.debug("parsed_args", extra={"cli_args": vars(args)})

    # Load config and resolve profile
    # Allow env var overrides for config path and profile
    config_path = args.config or os.getenv("LIMITLESS_CONFIG")
    profile_name = args.profile or os.getenv("LIMITLESS_PROFILE") or "default"

    cfg = load_config(config_path)
    prof = get_profile(cfg, profile_name)

    # Precedence: CLI flags > environment variables > config > defaults
    argv_list = argv or []

    def _provided(opt: str) -> bool:
        return opt in argv_list

    # data_dir precedence
    if not _provided("--data-dir") and not os.getenv("LIMITLESS_DATA_DIR"):
        if isinstance(prof.get("data_dir"), str):
            setattr(args, "data_dir", prof["data_dir"])  # type: ignore[index]

    # batch_size precedence for fetch/sync
    if not _provided("--batch-size") and isinstance(prof.get("batch_size"), (int, float)):
        # argparse stores parsed ints; coerce to int
        setattr(args, "batch_size", int(prof["batch_size"]))  # type: ignore[index]

    # timezone precedence for sync
    if getattr(args, "command", None) == "sync" and not _provided("--timezone") and not os.getenv("LIMITLESS_TZ"):
        if isinstance(prof.get("timezone"), str):
            setattr(args, "timezone", prof["timezone"])  # type: ignore[index]

    # Resolve API credentials
    resolved_api_key = os.getenv("LIMITLESS_API_KEY") or (prof.get("api_key") if isinstance(prof.get("api_key"), str) else None)
    resolved_api_url = os.getenv("LIMITLESS_API_URL") or (prof.get("api_url") if isinstance(prof.get("api_url"), str) else None)

    if args.command == "fetch":
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
        )
        saved = service.fetch(
            limit=args.limit,
            direction=args.direction,
            include_markdown=args.include_markdown,
            include_headings=args.include_headings,
            batch_size=max(1, int(args.batch_size)),
        )
        if args.json:
            import json as _json
            docs = []
            for p in saved:
                try:
                    with open(p, "r", encoding="utf-8") as _f:
                        obj = _json.loads(_f.read())
                    docs.append({
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "startTime": obj.get("startTime"),
                        "endTime": obj.get("endTime"),
                        "path": p,
                    })
                except Exception:
                    continue
            print(_json.dumps(docs, ensure_ascii=False))
        return 0

    if args.command == "sync":
        # Validate timezone if provided
        if args.timezone:
            try:
                _ = ZoneInfo(args.timezone)
            except Exception:
                sys.stderr.write(
                    f"Invalid timezone: {args.timezone}. Use an IANA name like 'America/Los_Angeles' or 'UTC'.\n"
                )
                return 2
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
        )
        saved = service.sync(
            date=args.date,
            start=args.start,
            end=args.end,
            timezone=args.timezone,
            is_starred=True if args.starred_only else None,
            batch_size=max(1, int(args.batch_size)),
        )
        if args.json:
            import json as _json
            from pathlib import Path as _Path
            # Build items JSON and read state for lastCursor/lastEndTime
            items = []
            for p in saved:
                try:
                    with open(p, "r", encoding="utf-8") as _f:
                        obj = _json.loads(_f.read())
                    items.append({
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "startTime": obj.get("startTime"),
                        "endTime": obj.get("endTime"),
                        "path": p,
                    })
                except Exception:
                    continue
            # State resides at ../state/lifelogs_sync.json
            try:
                state_path = _Path(args.data_dir).parent / "state" / "lifelogs_sync.json"
                state = _json.loads(state_path.read_text()) if state_path.exists() else {}
            except Exception:
                state = {}
            result = {
                "saved_count": len(saved),
                "lastCursor": state.get("lastCursor"),
                "lastEndTime": state.get("lastEndTime"),
                "items": items,
            }
            print(_json.dumps(result, ensure_ascii=False))
        return 0

    if args.command == "list":
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
        )
        items = service.list_local(date=args.date, is_starred=True if args.starred_only else None)
        if args.as_json:
            import json
            print(json.dumps(items, ensure_ascii=False, indent=2))
        else:
            for it in items:
                print(f"{it.get('startTime')} {it.get('id')} {it.get('title')}")
        return 0

    if args.command == "export-markdown":
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
        )
        text = service.export_markdown(limit=args.limit)
        if text:
            print(text)
        return 0

    if args.command == "fetch-audio":
        print("Audio endpoints are not yet documented; see docs/AUDIO.md")
        return 2

    if args.command == "configure":
        # Compute target config path and profile
        from limitless_tools.config.config import load_config as _load_cfg, save_config as _save_cfg
        target_path = config_path or default_config_path()
        target_profile = profile_name
        # Load existing config
        current = _load_cfg(target_path)
        prof_dict = current.get(target_profile, {}) if current else {}
        # Apply updates from flags (ignore None values)
        updates = {}
        for k in ["api_key", "api_url", "data_dir", "timezone", "batch_size"]:
            v = getattr(args, k, None)
            if v is not None:
                updates[k] = v
        prof_dict.update(updates)
        if not current:
            current = {target_profile: prof_dict}
        else:
            current[target_profile] = prof_dict
        _save_cfg(target_path, current)
        print(f"Wrote config to {target_path}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
