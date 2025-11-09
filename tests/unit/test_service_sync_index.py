"""
Service sync writes index.json summarizing local lifelogs.
Single assert per test.
"""

import json
from pathlib import Path


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, pages):
        self._pages = pages
        self._i = 0

    def get(self, url, headers, params):
        if self._i >= len(self._pages):
            return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})
        page = self._pages[self._i]
        self._i += 1
        return FakeResponse(page)


def _pages():
    return [
        {
            "data": {
                "lifelogs": [
                    {
                        "id": "i1",
                        "title": "One",
                        "markdown": "m1",
                        "contents": [],
                        "startTime": "2025-04-01T01:00:00Z",
                        "endTime": "2025-04-01T02:00:00Z",
                        "isStarred": False,
                        "updatedAt": "2025-04-01T03:00:00Z",
                    },
                    {
                        "id": "i2",
                        "title": "Two",
                        "markdown": "m2",
                        "contents": [],
                        "startTime": "2025-04-02T01:00:00Z",
                        "endTime": "2025-04-02T02:00:00Z",
                        "isStarred": True,
                        "updatedAt": "2025-04-02T03:00:00Z",
                    },
                ]
            },
            "meta": {"lifelogs": {"nextCursor": None}},
        }
    ]


def test_sync_writes_index(tmp_path: Path):
    from limitless_tools.http.client import LimitlessClient
    from limitless_tools.services.lifelog_service import LifelogService

    session = FakeSession(_pages())
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)

    service = LifelogService(api_key="KEY", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)

    service.sync(start="2025-04-01", end="2025-04-05", timezone="UTC")

    idx = json.loads((tmp_path / "index.json").read_text())
    ids = [x["id"] for x in idx]
    assert ids == ["i1", "i2"]

