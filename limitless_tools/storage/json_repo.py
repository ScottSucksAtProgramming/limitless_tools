from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass
class SaveResult:
    path: str
    status: Literal["created", "updated", "unchanged"]


class JsonFileRepository:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir).expanduser()

    def path_for_lifelog(self, lifelog: dict[str, Any]) -> str:
        start_time = lifelog.get("startTime", "0000-00-00T00:00:00Z")
        yyyy, mm, dd = start_time[:10].split("-")
        dir_path = self.base_dir / yyyy / mm / dd
        file_path = dir_path / f"lifelog_{lifelog.get('id')}.json"
        return str(file_path)

    def save_lifelog(self, lifelog: dict[str, Any]) -> SaveResult:
        path = Path(self.path_for_lifelog(lifelog))
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(lifelog, ensure_ascii=False, indent=2)
        status: Literal["created", "updated", "unchanged"]
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                existing = None
            if existing == lifelog:
                status = "unchanged"
            else:
                status = "updated"
        else:
            status = "created"
        if status != "unchanged":
            path.write_text(serialized)
        return SaveResult(str(path), status)
