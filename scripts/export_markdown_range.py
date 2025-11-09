from __future__ import annotations

import argparse
from collections.abc import Iterator
from datetime import datetime, timedelta
from pathlib import Path

from limitless_tools.config.paths import default_data_dir
from limitless_tools.services.lifelog_service import LifelogService


def _iter_dates(start_date: str, end_date: str) -> Iterator[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    if end < start:
        raise SystemExit("end date must be >= start date")
    d = start
    while d <= end:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


def _resolve_lifelogs_dir(path: str | None) -> str:
    """Return a directory that contains lifelog_*.json files.

    Accept either the lifelogs directory itself (~/.../data/lifelogs) or its parent (~/.../data).
    If a 'lifelogs' subdirectory exists under the provided path, prefer it.
    """
    if not path:
        return default_data_dir()
    p = Path(path).expanduser()
    # If they passed the lifelogs dir already, use it
    if p.name == "lifelogs":
        return str(p)
    # If a lifelogs subdir exists, use it
    lifelogs_sub = p / "lifelogs"
    if lifelogs_sub.exists() and lifelogs_sub.is_dir():
        return str(lifelogs_sub)
    # Otherwise, use provided path (rglob will still find nested matches)
    return str(p)


def export_range(
    *,
    start: str,
    end: str,
    data_dir: str | None,
    out_dir: str,
    frontmatter: bool = False,
    skip_empty: bool = True,
) -> int:
    lifelogs_dir = _resolve_lifelogs_dir(data_dir)
    service = LifelogService(api_key=None, api_url=None, data_dir=lifelogs_dir)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    wrote = 0
    for day in _iter_dates(start, end):
        text = service.export_markdown_by_date(date=day, frontmatter=frontmatter)
        if skip_empty and not text.strip():
            continue
        (out_path / f"{day}_lifelogs.md").write_text(text, encoding="utf-8")
        wrote += 1
        print(f"wrote: {day}_lifelogs.md")
    print(f"done: wrote {wrote} file(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Export combined markdown for a date range")
    p.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    p.add_argument("--end", required=True, help="End date YYYY-MM-DD (inclusive)")
    p.add_argument("--data-dir", default=None, help="Path to lifelogs data dir (defaults to user dir)")
    p.add_argument("--out-dir", required=True, help="Directory to write combined markdown files")
    p.add_argument("--frontmatter", action="store_true", default=False, help="Include YAML frontmatter")
    p.add_argument("--include-empty", action="store_true", default=False, help="Write files even if no markdown found for the date")
    args = p.parse_args(argv)

    return export_range(
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
        out_dir=args.out_dir,
        frontmatter=bool(args.frontmatter),
        skip_empty=not bool(args.include_empty),
    )


if __name__ == "__main__":
    raise SystemExit(main())
