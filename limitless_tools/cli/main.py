from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from zoneinfo import ZoneInfo

from limitless_tools.config.config import default_config_path, get_profile, load_config
from limitless_tools.config.env import load_env
from limitless_tools.config.logging import setup_logging
from limitless_tools.config.paths import default_data_dir, expand_path
from limitless_tools.errors import LimitlessError, ValidationError
from limitless_tools.services.lifelog_service import LifelogService, SaveReport


def _stderr_line(message: str) -> None:
    sys.stderr.write(f"{message}\n")
    sys.stderr.flush()


class ProgressReporter:
    def __init__(self, action: str):
        self.action = action
        self._start_ts: float | None = None
        self._callback: Callable[[int, int], None] | None = None

    def start(self) -> None:
        if self._start_ts is None:
            self._start_ts = time.perf_counter()
            _stderr_line(f"{self.action.title()} started...")

    def make_callback(self) -> Callable[[int, int], None]:
        if self._callback is None:
            def _cb(page: int, total: int) -> None:
                _stderr_line(
                    f"{self.action.title()} in progress: {total} lifelogs processed (page {page})"
                )

            self._callback = _cb
        return self._callback

    def finish(self, report: SaveReport | None) -> None:
        if self._start_ts is None:
            self.start()
        duration = (time.perf_counter() - self._start_ts) if self._start_ts is not None else None
        _stderr_line(_format_summary(self.action, report, duration))


def _format_summary(action: str, report: SaveReport | None, duration: float | None) -> str:
    title = action.title()
    duration_text = ""
    if duration is not None:
        duration_text = f" in {duration:.1f}s"
    if report is None:
        return f"{title} complete{duration_text}."
    if report.created or report.updated:
        parts: list[str] = []
        if report.created:
            parts.append(f"{report.created} new")
        if report.updated:
            parts.append(f"{report.updated} updated")
        if report.unchanged:
            parts.append(f"{report.unchanged} unchanged")
        return f"{title} complete{duration_text}: {', '.join(parts)}."
    if report.unchanged:
        return f"{title} complete{duration_text}: no changes (data already up to date)."
    return f"{title} complete{duration_text}: no lifelogs returned."


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

    srch = sub.add_parser("search", help="Search local lifelogs")
    srch.add_argument("--query", type=str, required=True)
    srch.add_argument("--date", type=str)
    srch.add_argument("--starred-only", action="store_true", default=False)
    srch.add_argument("--regex", "-rg", action="store_true", default=False)
    srch.add_argument("--fuzzy", action="store_true", default=False)
    srch.add_argument("--fuzzy-threshold", type=int, default=80)
    srch.add_argument("--json", action="store_true", default=False, dest="as_json")
    srch.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    exp = sub.add_parser("export-markdown", help="Export markdown from local lifelogs")
    exp.add_argument("--limit", type=int, default=1)
    exp.add_argument("--date", type=str, help="Export all lifelogs for this date (YYYY-MM-DD)")
    exp.add_argument("--write-dir", type=str, help="Write markdown files into this directory")
    exp.add_argument("--combine", action="store_true", default=False, help="Combine all matches into a single file (requires --date)")
    exp.add_argument("--frontmatter", action="store_true", default=False, help="Include YAML frontmatter per entry")
    exp.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    csvp = sub.add_parser("export-csv", help="Export lifelogs metadata as CSV")
    csvp.add_argument("--date", type=str)
    csvp.add_argument("--include-markdown", action="store_true", default=False)
    csvp.add_argument("--output", type=str)
    csvp.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    fa = sub.add_parser("fetch-audio", help="Download audio for a lifelog (placeholder)")
    fa.add_argument("--lifelog-id", required=True)
    fa.add_argument("--data-dir", type=str, default=os.getenv("LIMITLESS_DATA_DIR") or default_data_dir())

    cfgp = sub.add_parser("configure", help="Create or update user config (TOML)")
    cfgp.add_argument("--api-key", type=str)
    cfgp.add_argument("--api-url", type=str)
    cfgp.add_argument("--data-dir", type=str)
    cfgp.add_argument("--timezone", type=str)
    cfgp.add_argument("--batch-size", type=int)
    cfgp.add_argument("--http-timeout", type=float)
    cfgp.add_argument("--output-dir", type=str)

    return parser


def _normalize_data_dir(value: str | None, *, base_dir: str | None = None) -> str:
    """Return a data_dir resolved relative to an optional base directory."""
    normalized = expand_path(value, base_dir=base_dir)
    if normalized:
        return normalized
    return default_data_dir()


def _coerce_timeout_value(value: object, log: logging.Logger) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            log.debug("Invalid http_timeout config value: %s", value)
    return None


def _execute_command(
    *,
    args: argparse.Namespace,
    argv_list: list[str],
    prof: dict,
    config_base_dir: str,
    parser: argparse.ArgumentParser,
    log: logging.Logger,
    resolved_config_path: str,
    profile_name: str,
) -> int:
    def _provided(opt: str) -> bool:
        return opt in argv_list

    # data_dir precedence
    data_dir_from_config = False
    if not _provided("--data-dir") and not os.getenv("LIMITLESS_DATA_DIR"):
        if isinstance(prof.get("data_dir"), str):
            setattr(args, "data_dir", prof["data_dir"])
            data_dir_from_config = True

    # batch_size precedence for fetch/sync
    if not _provided("--batch-size") and isinstance(prof.get("batch_size"), (int, float)):
        # argparse stores parsed ints; coerce to int
        setattr(args, "batch_size", int(prof["batch_size"]))

    # timezone precedence for sync
    if getattr(args, "command", None) == "sync" and not _provided("--timezone") and not os.getenv("LIMITLESS_TZ"):
        if isinstance(prof.get("timezone"), str):
            setattr(args, "timezone", prof["timezone"])

    # Resolve API credentials
    resolved_api_key = os.getenv("LIMITLESS_API_KEY") or (prof.get("api_key") if isinstance(prof.get("api_key"), str) else None)
    resolved_api_url = os.getenv("LIMITLESS_API_URL") or (prof.get("api_url") if isinstance(prof.get("api_url"), str) else None)
    resolved_http_timeout: float | None = None
    if not os.getenv("LIMITLESS_HTTP_TIMEOUT"):
        resolved_http_timeout = _coerce_timeout_value(prof.get("http_timeout"), log)

    args.data_dir = _normalize_data_dir(
        getattr(args, "data_dir", None),
        base_dir=config_base_dir if data_dir_from_config else None,
    )

    if args.command == "fetch":
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
            http_timeout=resolved_http_timeout,
        )
        reporter = ProgressReporter("fetch")
        reporter.start()
        saved = service.fetch(
            limit=args.limit,
            direction=args.direction,
            include_markdown=args.include_markdown,
            include_headings=args.include_headings,
            batch_size=max(1, int(args.batch_size)),
            progress_callback=reporter.make_callback(),
        )
        if args.json:
            import json as _json
            docs = []
            for p in saved:
                try:
                    with open(p, encoding="utf-8") as _f:
                        obj = _json.loads(_f.read())
                    docs.append({
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "startTime": obj.get("startTime"),
                        "endTime": obj.get("endTime"),
                        "path": p,
                    })
                except (_json.JSONDecodeError, OSError) as exc:
                    log.debug("Skipping invalid saved lifelog %s: %s", p, exc)
                    continue
            print(_json.dumps(docs, ensure_ascii=False))
        reporter.finish(getattr(service, "last_report", None))
        return 0

    if args.command == "sync":
        # Validate timezone if provided
        if args.timezone:
            try:
                _ = ZoneInfo(args.timezone)
            except Exception as exc:
                raise ValidationError(
                    f"Invalid timezone: {args.timezone}. Use an IANA name like 'America/Los_Angeles' or 'UTC'.",
                    cause=exc,
                    context={"timezone": args.timezone},
                ) from exc
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
            http_timeout=resolved_http_timeout,
        )
        reporter = ProgressReporter("sync")
        reporter.start()
        saved = service.sync(
            date=args.date,
            start=args.start,
            end=args.end,
            timezone=args.timezone,
            is_starred=True if args.starred_only else None,
            batch_size=max(1, int(args.batch_size)),
            progress_callback=reporter.make_callback(),
        )
        if args.json:
            import json as _json
            from pathlib import Path as _Path
            # Build items JSON and read state for lastCursor/lastEndTime
            items = []
            for p in saved:
                try:
                    with open(p, encoding="utf-8") as _f:
                        obj = _json.loads(_f.read())
                    items.append({
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "startTime": obj.get("startTime"),
                        "endTime": obj.get("endTime"),
                        "path": p,
                    })
                except (_json.JSONDecodeError, OSError) as exc:
                    log.debug("Skipping invalid saved lifelog %s: %s", p, exc)
                    continue
            # State resides at ../state/lifelogs_sync.json
            try:
                state_path = _Path(args.data_dir).parent / "state" / "lifelogs_sync.json"
                if state_path.exists():
                    state = _json.loads(state_path.read_text())
                else:
                    state = {}
            except (_json.JSONDecodeError, OSError) as exc:
                log.debug("Unable to read sync state %s: %s", state_path, exc)
                state = {}
            result = {
                "saved_count": len(saved),
                "lastCursor": state.get("lastCursor"),
                "lastEndTime": state.get("lastEndTime"),
                "items": items,
            }
            print(_json.dumps(result, ensure_ascii=False))
        reporter.finish(getattr(service, "last_report", None))
        return 0

    if args.command == "list":
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
            http_timeout=resolved_http_timeout,
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
            http_timeout=resolved_http_timeout,
        )
        # Combined per-date export to a single file
        if args.combine:
            # Determine effective output directory: CLI --write-dir > config profile output_dir
            cfg_output_dir = (
                expand_path(prof.get("output_dir"), base_dir=config_base_dir)
                if isinstance(prof.get("output_dir"), str)
                else None
            )
            eff_write_dir = args.write_dir or cfg_output_dir
            if not args.date or not eff_write_dir:
                raise ValidationError(
                    "--combine requires --date and a write directory (provide --write-dir or set output_dir in config)",
                    context={"command": "export-markdown"},
                )
            text = service.export_markdown_by_date(date=args.date, frontmatter=args.frontmatter)
            from pathlib import Path as _Path
            outdir = _Path(eff_write_dir)
            outdir.mkdir(parents=True, exist_ok=True)
            outfile = outdir / f"{args.date}_lifelogs.md"
            outfile.write_text(text)
            return 0
        # Legacy behavior: print N latest entries to stdout
        text = service.export_markdown(limit=args.limit, frontmatter=bool(getattr(args, "frontmatter", False)))
        if text:
            print(text)
        return 0

    if args.command == "export-csv":
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
            http_timeout=resolved_http_timeout,
        )
        csv_text = service.export_csv(date=args.date, include_markdown=bool(getattr(args, "include_markdown", False)))
        # Determine effective output file: CLI --output > config profile output_dir + default filename; else stdout
        cfg_output_dir = (
            expand_path(prof.get("output_dir"), base_dir=config_base_dir)
            if isinstance(prof.get("output_dir"), str)
            else None
        )
        eff_output = getattr(args, "output", None)
        if not eff_output and cfg_output_dir:
            import os as _os
            base = f"lifelogs_{args.date}.csv" if getattr(args, "date", None) else "lifelogs.csv"
            eff_output = _os.path.join(cfg_output_dir, base)
        if eff_output:
            from pathlib import Path as _Path
            out_path = _Path(eff_output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(csv_text)
        else:
            print(csv_text)
        return 0

    if args.command == "search":
        service = LifelogService(
            api_key=resolved_api_key,
            api_url=resolved_api_url,
            data_dir=args.data_dir,
            http_timeout=resolved_http_timeout,
        )
        items = service.search_local(
            query=args.query,
            date=args.date,
            is_starred=True if args.starred_only else None,
            regex=bool(getattr(args, "regex", False)),
            fuzzy=bool(getattr(args, "fuzzy", False)),
            fuzzy_threshold=int(getattr(args, "fuzzy_threshold", 80)),
        )
        if args.as_json:
            import json
            print(json.dumps(items, ensure_ascii=False, indent=2))
        else:
            for it in items:
                print(f"{it.get('startTime')} {it.get('id')} {it.get('title')}")
        return 0

    if args.command == "fetch-audio":
        print("Audio endpoints are not yet documented; see docs/AUDIO.md")
        return 2

    if args.command == "configure":
        # Compute target config path and profile
        from limitless_tools.config.config import load_config as _load_cfg, save_config as _save_cfg
        target_path = resolved_config_path
        target_profile = profile_name
        # Load existing config
        current = _load_cfg(target_path)
        prof_dict = current.get(target_profile, {}) if current else {}
        # Apply updates from flags (ignore None values)
        updates = {}
        for k in ["api_key", "api_url", "data_dir", "timezone", "batch_size", "http_timeout", "output_dir"]:
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


def main(argv: list[str] | None = None) -> int:
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
    config_path_arg = args.config or os.getenv("LIMITLESS_CONFIG")
    resolved_config_path = expand_path(config_path_arg) or default_config_path()
    profile_name = args.profile or os.getenv("LIMITLESS_PROFILE") or "default"

    cfg = load_config(resolved_config_path)
    prof = get_profile(cfg, profile_name)
    config_base_dir = str(Path(resolved_config_path).expanduser().parent)

    argv_list = argv or []
    verbose = bool(getattr(args, "verbose", False))

    try:
        return _execute_command(
            args=args,
            argv_list=argv_list,
            prof=prof,
            config_base_dir=config_base_dir,
            parser=parser,
            log=log,
            resolved_config_path=resolved_config_path,
            profile_name=profile_name,
        )
    except ValidationError as exc:
        _stderr_line(f"Error: {exc}")
        return 2
    except LimitlessError as exc:
        log_args = {"context": getattr(exc, "context", {})}
        if verbose:
            log.exception("limitless_error", extra=log_args)
        else:
            log.error("limitless_error", extra={**log_args, "error": str(exc)})
        _stderr_line(f"Error: {exc}")
        return 1
    except KeyboardInterrupt:
        _stderr_line("Aborted by user.")
        return 130
    except Exception:  # pragma: no cover - final safeguard
        log.exception("unhandled_exception")
        _stderr_line("Unexpected error occurred. Re-run with --verbose for stack trace.")
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
