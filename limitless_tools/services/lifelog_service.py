from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from limitless_tools.config.env import resolve_timezone
from limitless_tools.errors import LimitlessError, ServiceError
from limitless_tools.http.client import LimitlessClient
from limitless_tools.storage.json_repo import JsonFileRepository
from limitless_tools.storage.state_repo import StateRepository

log = logging.getLogger(__name__)


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        log.debug("Failed to read JSON from %s: %s", path, exc)
        return None

@dataclass
class SaveReport:
    created: int = 0
    updated: int = 0
    unchanged: int = 0

    def record(self, status: str) -> None:
        if status == "created":
            self.created += 1
        elif status == "updated":
            self.updated += 1
        else:
            self.unchanged += 1

    @property
    def total(self) -> int:
        return self.created + self.updated + self.unchanged


@dataclass
class LifelogService:
    api_key: str | None
    api_url: str | None
    data_dir: str | None
    client: LimitlessClient | None = None
    repo: JsonFileRepository | None = None
    http_timeout: float | None = None
    last_report: SaveReport | None = None

    def fetch(
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
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[str]:
        """Fetch lifelogs from API and save them to JSON files. Returns saved file paths."""

        client = self.client or LimitlessClient(
            api_key=self.api_key or "",
            base_url=self.api_url or None,
            timeout=self.http_timeout,
        )
        repo = self.repo or JsonFileRepository(base_dir=self.data_dir or "")

        try:
            lifelogs = client.get_lifelogs(
                limit=limit,
                direction=direction,
                include_markdown=include_markdown,
                include_headings=include_headings,
                date=date,
                start=start,
                end=end,
                timezone=timezone,
                is_starred=is_starred,
                batch_size=batch_size,
                progress_callback=progress_callback,
            )
        except LimitlessError as exc:
            raise ServiceError(f"Failed to fetch lifelogs: {exc}", cause=exc, context={"operation": "fetch"}) from exc
        except Exception as exc:  # pragma: no cover - best-effort guard
            raise ServiceError("Unexpected error while fetching lifelogs.", cause=exc, context={"operation": "fetch"}) from exc

        report = SaveReport()
        saved_paths: list[str] = []
        for item in lifelogs:
            try:
                save_result = repo.save_lifelog(item)
            except LimitlessError as exc:
                lifelog_id = item.get("id")
                raise ServiceError(
                    f"Failed to save lifelog {lifelog_id}: {exc}",
                    cause=exc,
                    context={"operation": "fetch", "lifelog_id": lifelog_id},
                ) from exc
            except Exception as exc:  # pragma: no cover - best-effort guard
                lifelog_id = item.get("id")
                raise ServiceError(
                    f"Unexpected failure while saving lifelog {lifelog_id}.",
                    cause=exc,
                    context={"operation": "fetch", "lifelog_id": lifelog_id},
                ) from exc
            saved_paths.append(save_result.path)
            report.record(save_result.status)

        self.last_report = report
        return saved_paths

    def sync(
        self,
        *,
        date: str | None = None,
        start: str | None = None,
        end: str | None = None,
        timezone: str | None = None,
        is_starred: bool | None = None,
        batch_size: int = 50,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[str]:
        client = self.client or LimitlessClient(
            api_key=self.api_key or "",
            base_url=self.api_url or None,
            timeout=self.http_timeout,
        )
        repo = self.repo or JsonFileRepository(base_dir=self.data_dir or "")
        state_repo = StateRepository(base_lifelogs_dir=self.data_dir or "")

        # Load previous state and derive default start if none provided
        try:
            st = state_repo.load()
        except LimitlessError as exc:
            raise ServiceError("Failed to load sync state.", cause=exc, context={"operation": "sync"}) from exc
        except Exception as exc:  # pragma: no cover - best-effort guard
            raise ServiceError("Unexpected error loading sync state.", cause=exc, context={"operation": "sync"}) from exc
        # Compute a signature for the current sync parameters
        sig_dict = {
            "date": date,
            "start": start,
            "end": end,
            "timezone": timezone,
            "is_starred": is_starred,
            "direction": "desc",
        }
        sig_json = json.dumps(sig_dict, sort_keys=True, ensure_ascii=False)
        sig = hashlib.sha256(sig_json.encode("utf-8")).hexdigest()
        signatures = st.get("signatures", {}) if isinstance(st.get("signatures"), dict) else {}
        sig_state = signatures.get(sig, {})
        eff_start = start or sig_state.get("lastEndTime") or st.get("lastEndTime")

        eff_tz = resolve_timezone(timezone)
        try:
            lifelogs = client.get_lifelogs(
                limit=None,
                direction="desc",
                include_markdown=True,
                include_headings=True,
                date=date,
                start=eff_start,
                end=end,
                timezone=eff_tz,
                is_starred=is_starred,
                batch_size=batch_size,
                cursor=(sig_state.get("lastCursor") or st.get("lastCursor")) if not any([date, start, end]) else None,
                progress_callback=progress_callback,
            )
        except LimitlessError as exc:
            raise ServiceError(f"Failed to sync lifelogs: {exc}", cause=exc, context={"operation": "sync"}) from exc
        except Exception as exc:  # pragma: no cover - best-effort guard
            raise ServiceError("Unexpected error while syncing lifelogs.", cause=exc, context={"operation": "sync"}) from exc

        report = SaveReport()
        saved_paths: list[str] = []
        index_rows: list[dict[str, str | bool | None]] = []
        for ll in lifelogs:
            try:
                save_result = repo.save_lifelog(ll)
            except LimitlessError as exc:
                raise ServiceError(
                    f"Failed to save lifelog {ll.get('id')}: {exc}",
                    cause=exc,
                    context={"operation": "sync", "lifelog_id": ll.get("id")},
                ) from exc
            except Exception as exc:  # pragma: no cover - best-effort guard
                raise ServiceError(
                    f"Unexpected failure while saving lifelog {ll.get('id')}.",
                    cause=exc,
                    context={"operation": "sync", "lifelog_id": ll.get("id")},
                ) from exc
            saved_paths.append(save_result.path)
            report.record(save_result.status)
            index_rows.append(
                {
                    "id": ll.get("id"),
                    "title": ll.get("title"),
                    "startTime": ll.get("startTime"),
                    "endTime": ll.get("endTime"),
                    "isStarred": ll.get("isStarred"),
                    "updatedAt": ll.get("updatedAt"),
                    "path": save_result.path,
                }
            )

        # write index.json at base dir
        base = Path(self.data_dir or "")
        base.mkdir(parents=True, exist_ok=True)
        # merge/update index if exists
        idx_path = base / "index.json"
        existing: list[dict] = []
        if idx_path.exists():
            existing_obj = _load_json(idx_path)
            if isinstance(existing_obj, list):
                existing = existing_obj
        merged: dict[str, dict] = {str(it.get("id")): it for it in existing}
        for row in index_rows:
            merged[str(row.get("id"))] = row
        # sort by startTime ascending for stability
        merged_list = sorted(merged.values(), key=lambda x: str(x.get("startTime") or ""))
        idx_path.write_text(json.dumps(merged_list, ensure_ascii=False, indent=2))

        # update state with latest end time observed
        if lifelogs:
            try:
                last_end = max([str(x.get("endTime") or "") for x in lifelogs])
            except (TypeError, ValueError):
                last_end = None
            if last_end:
                st["lastEndTime"] = last_end  # top-level for compatibility
                # per-signature
                signatures.setdefault(sig, {})["lastEndTime"] = last_end
        # update lastCursor from client if available
        if getattr(client, "last_next_cursor", None):
            st["lastCursor"] = client.last_next_cursor  # top-level for compatibility
            signatures.setdefault(sig, {})["lastCursor"] = client.last_next_cursor
        if signatures:
            st["signatures"] = signatures
        try:
            state_repo.save(st)
        except LimitlessError as exc:
            raise ServiceError("Failed to persist sync state.", cause=exc, context={"operation": "sync"}) from exc
        except Exception as exc:  # pragma: no cover - best-effort guard
            raise ServiceError("Unexpected error while saving sync state.", cause=exc, context={"operation": "sync"}) from exc

        self.last_report = report
        return saved_paths

    def list_local(
        self,
        *,
        date: str | None = None,
        is_starred: bool | None = None,
    ) -> list[dict[str, object]]:
        """List locally stored lifelogs, optionally filtered by date (YYYY-MM-DD) and starred."""
        base = Path(self.data_dir or "")
        results: list[dict[str, object]] = []

        # If we have an index, prefer it; else scan files
        idx_path = base / "index.json"
        items: list[dict[str, object]] = []
        if idx_path.exists():
            idx_items = _load_json(idx_path)
            if isinstance(idx_items, list):
                items = idx_items
        else:
            for p in base.rglob("lifelog_*.json"):
                obj = _load_json(p)
                if not isinstance(obj, dict):
                    continue
                items.append(
                    {
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "startTime": obj.get("startTime"),
                        "endTime": obj.get("endTime"),
                        "isStarred": obj.get("isStarred"),
                        "updatedAt": obj.get("updatedAt"),
                        "path": str(p),
                    }
                )

        for it in items:
            if date and (str(it.get("startTime")) or "")[:10] != date:
                continue
            if is_starred is not None and bool(it.get("isStarred")) != is_starred:
                continue
            results.append(it)

        return results

    def export_markdown(self, *, limit: int = 1, frontmatter: bool = False) -> str:
        """Return concatenated markdown from the latest N local lifelogs (by startTime).

        If frontmatter is True, prepend YAML blocks per entry similar to export_markdown_by_date.
        """
        base = Path(self.data_dir or "")
        entries: list[dict[str, object]] = []
        for p in base.rglob("lifelog_*.json"):
            obj = _load_json(p)
            if not isinstance(obj, dict):
                continue
            entries.append(obj)

        entries.sort(key=lambda x: str(x.get("startTime") or ""))
        entries = entries[-limit:] if limit is not None else entries

        parts: list[str] = []
        for e in entries:
            md = e.get("markdown")
            if isinstance(md, str) and md:
                if frontmatter:
                    fm_lines = [
                        "---",
                        f"id: {e.get('id')}",
                        f"title: {e.get('title')}",
                        f"startTime: {e.get('startTime')}",
                        f"endTime: {e.get('endTime')}",
                        f"isStarred: {e.get('isStarred')}",
                        f"updatedAt: {e.get('updatedAt')}",
                        "---",
                    ]
                    parts.append("\n".join(fm_lines) + "\n" + md)
                else:
                    parts.append(md)

        return "\n\n".join(parts)

    def search_local(
        self,
        *,
        query: str,
        date: str | None = None,
        is_starred: bool | None = None,
        regex: bool = False,
        fuzzy: bool = False,
        fuzzy_threshold: int = 80,
    ) -> list[dict[str, object]]:
        """Search local lifelogs by case-insensitive substring in title or markdown.

        Returns a list of summary dicts similar to list_local.
        """
        import re

        q = (query or "").strip()
        if not q:
            return []
        ql = q.lower()
        pattern = None
        if regex:
            try:
                pattern = re.compile(q, flags=re.IGNORECASE)
            except re.error:
                pattern = None
        # optional fuzzy scorer
        rf_scorer = None
        try:
            from rapidfuzz import fuzz as _rf

            def _rf_score(a: str, b: str) -> int:
                # partial_ratio is a good default for substring-like fuzziness
                return int(_rf.partial_ratio(a, b))

            rf_scorer = _rf_score
        except ImportError:
            rf_scorer = None
        import difflib as _difflib

        base = Path(self.data_dir or "")
        results: list[dict[str, object]] = []

        # Prefer index for quick pass; we will open files as needed to check markdown
        idx_items: list[dict[str, object]] = []
        idx_path = base / "index.json"
        if idx_path.exists():
            idx_json = _load_json(idx_path)
            if isinstance(idx_json, list):
                idx_items = idx_json
        else:
            # Build items by scanning files
            for p in base.rglob("lifelog_*.json"):
                obj = _load_json(p)
                if not isinstance(obj, dict):
                    continue
                idx_items.append(
                    {
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "startTime": obj.get("startTime"),
                        "endTime": obj.get("endTime"),
                        "isStarred": obj.get("isStarred"),
                        "updatedAt": obj.get("updatedAt"),
                        "path": str(p),
                    }
                )

        for it in idx_items:
            st = str(it.get("startTime") or "")
            if date and st[:10] != date:
                continue
            if is_starred is not None and bool(it.get("isStarred")) != is_starred:
                continue

            title = str(it.get("title") or "")
            match = False
            if regex and pattern is not None:
                match = bool(pattern.search(title))
            elif fuzzy:
                # fuzzy against title first
                if rf_scorer is not None:
                    match = rf_scorer(ql, title.lower()) >= max(0, int(fuzzy_threshold))
                else:
                    ratio = _difflib.SequenceMatcher(None, ql, title.lower()).ratio() * 100.0
                    match = ratio >= max(0, float(fuzzy_threshold))
            else:
                match = ql in title.lower()
            if not match:
                path_str = it.get("path")
                if isinstance(path_str, str) and path_str:
                    obj = _load_json(Path(path_str))
                    if isinstance(obj, dict):
                        md = obj.get("markdown")
                        if isinstance(md, str) and md:
                            if regex and pattern is not None:
                                match = bool(pattern.search(md))
                            elif fuzzy:
                                if rf_scorer is not None:
                                    match = rf_scorer(ql, md.lower()) >= max(0, int(fuzzy_threshold))
                                else:
                                    ratio = _difflib.SequenceMatcher(None, ql, md.lower()).ratio() * 100.0
                                    match = ratio >= max(0, float(fuzzy_threshold))
                            else:
                                match = ql in md.lower()
            if match:
                results.append(it)

        return results

    def export_markdown_by_date(self, *, date: str, frontmatter: bool = False) -> str:
        """Return concatenated markdown for all lifelogs on a specific date."""
        base = Path(self.data_dir or "")
        entries: list[dict[str, object]] = []
        for p in base.rglob("lifelog_*.json"):
            obj = _load_json(p)
            if not isinstance(obj, dict):
                continue
            st = str(obj.get("startTime") or "")
            if st[:10] != date:
                continue
            entries.append(obj)

        # sort by startTime ascending
        entries.sort(key=lambda x: str(x.get("startTime") or ""))

        parts: list[str] = []
        for e in entries:
            md = e.get("markdown")
            if isinstance(md, str) and md:
                if frontmatter:
                    fm_lines = [
                        "---",
                        f"id: {e.get('id')}",
                        f"title: {e.get('title')}",
                        f"startTime: {e.get('startTime')}",
                        f"endTime: {e.get('endTime')}",
                        f"isStarred: {e.get('isStarred')}",
                        f"updatedAt: {e.get('updatedAt')}",
                        "---",
                    ]
                    parts.append("\n".join(fm_lines) + "\n" + md)
                else:
                    parts.append(md)

        return "\n\n".join(parts)

    def export_csv(self, *, date: str | None = None, include_markdown: bool = False) -> str:
        """Return CSV for lifelogs with optional markdown column."""
        import csv
        from io import StringIO


        base = Path(self.data_dir or "")
        # Prefer index for listing paths
        idx_items: list[dict[str, object]] = []
        idx_path = base / "index.json"
        if idx_path.exists():
            idx_json = _load_json(idx_path)
            if isinstance(idx_json, list):
                idx_items = idx_json
        else:
            for p in base.rglob("lifelog_*.json"):
                obj = _load_json(p)
                if not isinstance(obj, dict):
                    continue
                idx_items.append(
                    {
                        "id": obj.get("id"),
                        "title": obj.get("title"),
                        "startTime": obj.get("startTime"),
                        "endTime": obj.get("endTime"),
                        "isStarred": obj.get("isStarred"),
                        "updatedAt": obj.get("updatedAt"),
                        "path": str(p),
                    }
                )

        # Filter and sort
        items: list[dict[str, object]] = []
        for it in idx_items:
            st = str(it.get("startTime") or "")
            if date and st[:10] != date:
                continue
            items.append(it)
        items.sort(key=lambda x: str(x.get("startTime") or ""))

        # Build CSV
        buf = StringIO()
        fieldnames = ["id", "startTime", "endTime", "title", "isStarred", "updatedAt", "path"]
        if include_markdown:
            fieldnames.append("markdown")
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for it in items:
            row = {k: it.get(k) for k in fieldnames if k != "markdown"}
            if include_markdown:
                md = ""
                path_str = it.get("path")
                if isinstance(path_str, str) and path_str:
                    obj = _load_json(Path(path_str))
                    if isinstance(obj, dict):
                        mdt = obj.get("markdown")
                        if isinstance(mdt, str):
                            md = mdt
                row["markdown"] = md
            writer.writerow(row)
        return buf.getvalue()
