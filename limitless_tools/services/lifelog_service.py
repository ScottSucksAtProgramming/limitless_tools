from __future__ import annotations

from dataclasses import dataclass

from limitless_tools.config.env import resolve_timezone
from limitless_tools.http.client import LimitlessClient
from limitless_tools.storage.json_repo import JsonFileRepository
from limitless_tools.storage.state_repo import StateRepository


@dataclass
class LifelogService:
    api_key: str | None
    api_url: str | None
    data_dir: str | None
    client: LimitlessClient | None = None
    repo: JsonFileRepository | None = None

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
    ) -> list[str]:
        """Fetch lifelogs from API and save them to JSON files. Returns saved file paths."""

        client = self.client or LimitlessClient(api_key=self.api_key or "", base_url=self.api_url or None)
        repo = self.repo or JsonFileRepository(base_dir=self.data_dir or "")

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
        )

        saved_paths: list[str] = []
        for item in lifelogs:
            saved_paths.append(repo.save_lifelog(item))

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
    ) -> list[str]:
        client = self.client or LimitlessClient(api_key=self.api_key or "", base_url=self.api_url or None)
        repo = self.repo or JsonFileRepository(base_dir=self.data_dir or "")
        state_repo = StateRepository(base_lifelogs_dir=self.data_dir or "")

        # Load previous state and derive default start if none provided
        st = state_repo.load()
        # Compute a signature for the current sync parameters
        import hashlib
        import json as _json
        sig_dict = {
            "date": date,
            "start": start,
            "end": end,
            "timezone": timezone,
            "is_starred": is_starred,
            "direction": "desc",
        }
        sig_json = _json.dumps(sig_dict, sort_keys=True, ensure_ascii=False)
        sig = hashlib.sha1(sig_json.encode("utf-8")).hexdigest()
        signatures = st.get("signatures", {}) if isinstance(st.get("signatures"), dict) else {}
        sig_state = signatures.get(sig, {})
        eff_start = start or sig_state.get("lastEndTime") or st.get("lastEndTime")

        eff_tz = resolve_timezone(timezone)
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
        )

        saved_paths: list[str] = []
        index_rows: list[dict[str, str | bool | None]] = []
        for ll in lifelogs:
            p = repo.save_lifelog(ll)
            saved_paths.append(p)
            index_rows.append(
                {
                    "id": ll.get("id"),
                    "title": ll.get("title"),
                    "startTime": ll.get("startTime"),
                    "endTime": ll.get("endTime"),
                    "isStarred": ll.get("isStarred"),
                    "updatedAt": ll.get("updatedAt"),
                    "path": p,
                }
            )

        # write index.json at base dir
        import json
        from pathlib import Path

        base = Path(self.data_dir or "")
        base.mkdir(parents=True, exist_ok=True)
        # merge/update index if exists
        idx_path = base / "index.json"
        existing: list[dict] = []
        if idx_path.exists():
            try:
                existing = json.loads(idx_path.read_text())
            except Exception:
                existing = []
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
            except Exception:
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
        state_repo.save(st)

        return saved_paths

    def list_local(
        self,
        *,
        date: str | None = None,
        is_starred: bool | None = None,
    ) -> list[dict[str, object]]:
        """List locally stored lifelogs, optionally filtered by date (YYYY-MM-DD) and starred."""
        import json
        from pathlib import Path

        base = Path(self.data_dir or "")
        results: list[dict[str, object]] = []

        # If we have an index, prefer it; else scan files
        idx_path = base / "index.json"
        items: list[dict[str, object]] = []
        if idx_path.exists():
            try:
                items = json.loads(idx_path.read_text())
            except Exception:
                items = []
        else:
            for p in base.rglob("lifelog_*.json"):
                try:
                    obj = json.loads(p.read_text())
                except Exception:
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
        import json
        from pathlib import Path

        base = Path(self.data_dir or "")
        entries: list[dict[str, object]] = []
        for p in base.rglob("lifelog_*.json"):
            try:
                obj = json.loads(p.read_text())
            except Exception:
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
        import json
        import re
        from pathlib import Path

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
        except Exception:
            rf_scorer = None
        import difflib as _difflib

        base = Path(self.data_dir or "")
        results: list[dict[str, object]] = []

        # Prefer index for quick pass; we will open files as needed to check markdown
        idx_items: list[dict[str, object]] = []
        idx_path = base / "index.json"
        if idx_path.exists():
            try:
                idx_items = json.loads(idx_path.read_text())
            except Exception:
                idx_items = []
        else:
            # Build items by scanning files
            for p in base.rglob("lifelog_*.json"):
                try:
                    obj = json.loads(p.read_text())
                except Exception:
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
                # try markdown by opening file
                path_str = it.get("path")
                try:
                    if isinstance(path_str, str) and path_str:
                        obj = json.loads(Path(path_str).read_text())
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
                except Exception:
                    match = False
            if match:
                results.append(it)

        return results

    def export_markdown_by_date(self, *, date: str, frontmatter: bool = False) -> str:
        """Return concatenated markdown for all lifelogs on a specific date."""
        import json
        from pathlib import Path

        base = Path(self.data_dir or "")
        entries: list[dict[str, object]] = []
        for p in base.rglob("lifelog_*.json"):
            try:
                obj = json.loads(p.read_text())
            except Exception:
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
        import json
        from io import StringIO
        from pathlib import Path

        base = Path(self.data_dir or "")
        # Prefer index for listing paths
        idx_items: list[dict[str, object]] = []
        idx_path = base / "index.json"
        if idx_path.exists():
            try:
                idx_items = json.loads(idx_path.read_text())
            except Exception:
                idx_items = []
        else:
            for p in base.rglob("lifelog_*.json"):
                try:
                    obj = json.loads(p.read_text())
                except Exception:
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
                try:
                    if isinstance(path_str, str) and path_str:
                        obj = json.loads(Path(path_str).read_text())
                        mdt = obj.get("markdown")
                        if isinstance(mdt, str):
                            md = mdt
                except Exception:
                    md = ""
                row["markdown"] = md
            writer.writerow(row)
        return buf.getvalue()
