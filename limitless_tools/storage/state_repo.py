from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from limitless_tools.errors import StateError


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
        except json.JSONDecodeError as exc:
            raise StateError("Sync state file is corrupted.", cause=exc, context={"path": str(p)}) from exc
        except OSError as exc:
            raise StateError("Unable to read sync state file.", cause=exc, context={"path": str(p)}) from exc

    def save(self, state: dict[str, Any]) -> None:
        p = self._state_path
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StateError("Unable to create sync state directory.", cause=exc, context={"path": str(p.parent)}) from exc
        try:
            p.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        except OSError as exc:
            raise StateError("Unable to write sync state file.", cause=exc, context={"path": str(p)}) from exc
