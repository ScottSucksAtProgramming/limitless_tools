from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from limitless_tools.errors import LimitlessError, StorageError


@dataclass
class SaveResult:
    path: str
    status: Literal["created", "updated", "unchanged"]


class JsonFileRepository:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir).expanduser()

    def path_for_lifelog(self, lifelog: dict[str, Any]) -> str:
        start_time = str(lifelog.get("startTime") or "0000-00-00T00:00:00Z")
        try:
            yyyy, mm, dd = start_time[:10].split("-")
        except ValueError as exc:
            raise StorageError(
                "Invalid startTime format for lifelog path.",
                cause=exc,
                context={"startTime": start_time, "lifelog_id": lifelog.get("id")},
            ) from exc
        dir_path = self.base_dir / yyyy / mm / dd
        file_path = dir_path / f"lifelog_{lifelog.get('id')}.json"
        return str(file_path)

    def save_lifelog(self, lifelog: dict[str, Any]) -> SaveResult:
        try:
            path = Path(self.path_for_lifelog(lifelog))
        except LimitlessError:
            raise
        except Exception as exc:  # pragma: no cover - defensive guard
            raise StorageError(
                "Failed to build lifelog path.", cause=exc, context={"lifelog_id": lifelog.get("id")}
            ) from exc
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                "Unable to create lifelog directory.", cause=exc, context={"path": str(path.parent)}
            ) from exc
        serialized = json.dumps(lifelog, ensure_ascii=False, indent=2)
        status: Literal["created", "updated", "unchanged"]
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except json.JSONDecodeError:
                existing = None
            except OSError as exc:
                raise StorageError(
                    "Unable to read existing lifelog file.", cause=exc, context={"path": str(path)}
                ) from exc
            if existing == lifelog:
                status = "unchanged"
            else:
                status = "updated"
        else:
            status = "created"
        if status != "unchanged":
            try:
                path.write_text(serialized)
            except OSError as exc:
                raise StorageError("Unable to write lifelog file.", cause=exc, context={"path": str(path)}) from exc
        return SaveResult(str(path), status)
