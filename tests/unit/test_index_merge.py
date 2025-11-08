"""
Index merge should update/append entries instead of rewriting blindly.
Single assert per test.
"""

import json
from pathlib import Path


def test_index_merged_without_losing_entries(tmp_path: Path):
    from limitless_tools.services.lifelog_service import LifelogService
    from limitless_tools.http.client import LimitlessClient

    # Pre-existing index with iOld
    (tmp_path / "index.json").write_text(json.dumps([
        {"id": "iOld", "title": "Old", "startTime": "2025-01-01T00:00:00Z", "endTime": "2025-01-01T01:00:00Z", "isStarred": False, "updatedAt": "2025-01-01T02:00:00Z", "path": "p"}
    ]))

    class Session:
        def get(self, url, headers, params):
            return Resp({
                "data": {"lifelogs": [
                    {"id": "iNew", "title": "New", "markdown": None, "contents": [], "startTime": "2025-02-01T00:00:00Z", "endTime": "2025-02-01T01:00:00Z", "isStarred": False, "updatedAt": "2025-02-01T02:00:00Z"}
                ]},
                "meta": {"lifelogs": {"nextCursor": None}}
            })

    class Resp:
        def __init__(self, p):
            self.ok = True
            self._p = p
        def json(self):
            return self._p

    client = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=Session())
    svc = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)
    svc.sync()

    idx = json.loads((tmp_path / "index.json").read_text())
    ids = sorted([x["id"] for x in idx])
    assert ids == ["iNew", "iOld"]

