from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


class JsonFileRepository:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)

    def path_for_lifelog(self, lifelog: Dict[str, Any]) -> str:
        start_time = lifelog.get("startTime", "0000-00-00T00:00:00Z")
        yyyy, mm, dd = start_time[:10].split("-")
        dir_path = self.base_dir / yyyy / mm / dd
        file_path = dir_path / f"lifelog_{lifelog.get('id')}.json"
        return str(file_path)

    def save_lifelog(self, lifelog: Dict[str, Any]) -> str:
        path = Path(self.path_for_lifelog(lifelog))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(lifelog, ensure_ascii=False, indent=2))
        return str(path)

