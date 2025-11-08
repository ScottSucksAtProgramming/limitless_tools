from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from limitless_tools.http.client import LimitlessClient
from limitless_tools.storage.json_repo import JsonFileRepository


@dataclass
class LifelogService:
    api_key: Optional[str]
    api_url: Optional[str]
    data_dir: Optional[str]
    client: Optional[LimitlessClient] = None
    repo: Optional[JsonFileRepository] = None

    def fetch(
        self,
        *,
        limit: Optional[int] = None,
        direction: str = "desc",
        include_markdown: bool = True,
        include_headings: bool = True,
        date: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        timezone: Optional[str] = None,
        is_starred: Optional[bool] = None,
        batch_size: int = 10,
    ) -> List[str]:
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

        saved_paths: List[str] = []
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
        batch_size: int = 10,
    ) -> list[str]:
        client = self.client or LimitlessClient(api_key=self.api_key or "", base_url=self.api_url or None)
        repo = self.repo or JsonFileRepository(base_dir=self.data_dir or "")

        lifelogs = client.get_lifelogs(
            limit=None,
            direction="desc",
            include_markdown=True,
            include_headings=True,
            date=date,
            start=start,
            end=end,
            timezone=timezone,
            is_starred=is_starred,
            batch_size=batch_size,
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
        from pathlib import Path
        import json

        base = Path(self.data_dir or "")
        base.mkdir(parents=True, exist_ok=True)
        (base / "index.json").write_text(json.dumps(index_rows, ensure_ascii=False, indent=2))
        return saved_paths

    def list_local(
        self,
        *,
        date: str | None = None,
        is_starred: bool | None = None,
    ) -> list[dict[str, object]]:
        """List locally stored lifelogs, optionally filtered by date (YYYY-MM-DD) and starred."""
        from pathlib import Path
        import json

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

    def export_markdown(self, *, limit: int = 1) -> str:
        """Return concatenated markdown from the latest N local lifelogs (by startTime)."""
        from pathlib import Path
        import json

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
                parts.append(md)

        return "\n\n".join(parts)
