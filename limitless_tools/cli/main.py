from __future__ import annotations

import argparse
import os
from typing import List, Optional

from limitless_tools.services.lifelog_service import LifelogService
from limitless_tools.config.paths import default_data_dir


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="limitless", description="Limitless Tools CLI")
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
    fetch.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    sync = sub.add_parser("sync", help="Sync lifelogs for a date or range")
    sync.add_argument("--date", type=str)
    sync.add_argument("--start", type=str)
    sync.add_argument("--end", type=str)
    sync.add_argument("--timezone", type=str)
    sync.add_argument("--starred-only", action="store_true", default=False)
    sync.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

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

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(args=argv)

    if args.command == "fetch":
        service = LifelogService(
            api_key=os.getenv("LIMITLESS_API_KEY"),
            api_url=os.getenv("LIMITLESS_API_URL"),
            data_dir=args.data_dir,
        )
        service.fetch(
            limit=args.limit,
            direction=args.direction,
            include_markdown=args.include_markdown,
            include_headings=args.include_headings,
        )
        return 0

    if args.command == "sync":
        service = LifelogService(
            api_key=os.getenv("LIMITLESS_API_KEY"),
            api_url=os.getenv("LIMITLESS_API_URL"),
            data_dir=args.data_dir,
        )
        service.sync(
            date=args.date,
            start=args.start,
            end=args.end,
            timezone=args.timezone,
            is_starred=True if args.starred_only else None,
        )
        return 0

    if args.command == "list":
        service = LifelogService(
            api_key=os.getenv("LIMITLESS_API_KEY"),
            api_url=os.getenv("LIMITLESS_API_URL"),
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
            api_key=os.getenv("LIMITLESS_API_KEY"),
            api_url=os.getenv("LIMITLESS_API_URL"),
            data_dir=args.data_dir,
        )
        text = service.export_markdown(limit=args.limit)
        if text:
            print(text)
        return 0

    if args.command == "fetch-audio":
        print("Audio endpoints are not yet documented; see docs/AUDIO.md")
        return 2

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
