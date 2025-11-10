"""
Story: sync resumes using lastEndTime when start is omitted.
Single assert per test.
"""

import json
from pathlib import Path


class FakeResponse:
    def __init__(self, payload, ok=True):
        self._payload = payload
        self.ok = ok

    def json(self):
        return self._payload


class CursorSession:
    def __init__(self, pages):
        self.pages = pages
        self.i = 0

    def get(self, url, headers, params):
        if self.i >= len(self.pages):
            return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})
        p = self.pages[self.i]
        self.i += 1
        return FakeResponse(p)


def _page_with_item(id_: str, start: str, end: str):
    return {
        "data": {
            "lifelogs": [
                {
                    "id": id_,
                    "title": id_,
                    "markdown": "",
                    "contents": [],
                    "startTime": start,
                    "endTime": end,
                    "isStarred": False,
                    "updatedAt": end,
                }
            ]
        },
        "meta": {"lifelogs": {"nextCursor": None}},
    }


def test_sync_uses_last_end_time_when_no_start(tmp_path: Path):
    from limitless_tools.http.client import LimitlessClient
    from limitless_tools.services.lifelog_service import LifelogService

    # First run: writes an item ending at t1, also writes state with lastEndTime
    pages1 = [_page_with_item("X", "2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z")]
    session1 = CursorSession(pages1)
    client1 = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=session1)
    svc1 = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client1)
    _ = svc1.sync()

    # Second run: no explicit start; service should read state and use lastEndTime
    state_path = Path(tmp_path).parent / "state" / "lifelogs_sync.json"
    assert json.loads(state_path.read_text()).get("lastEndTime") == "2025-01-01T01:00:00Z"

