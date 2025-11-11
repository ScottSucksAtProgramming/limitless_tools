from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class StateRepository:
    base_lifelogs_dir: str

    @property
    def _state_path(self) -> Path:
        lifelogs_dir = Path(self.base_lifelogs_dir).expanduser()
        return lifelogs_dir.parent / "state" / "lifelogs_sync.json"

    def load(self) -> dict[str, Any]:
        p = self._state_path
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}

    def save(self, state: dict[str, Any]) -> None:
        p = self._state_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2))
