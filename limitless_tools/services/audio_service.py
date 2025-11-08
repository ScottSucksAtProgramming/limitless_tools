from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AudioService:
    api_key: str | None
    api_url: str | None

    def list_assets(self, lifelog_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError("Audio endpoints are not yet documented; see docs/AUDIO.md")

    def download(self, lifelog_id: str, target_dir: str, **opts: Any) -> list[str]:
        raise NotImplementedError("Audio endpoints are not yet documented; see docs/AUDIO.md")

