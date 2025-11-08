"""
Tests for LifelogService.fetch to ensure it pulls lifelogs via client and saves JSON files.
Single assert per test.
"""

from pathlib import Path
from typing import Any, Dict


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.ok = True

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


def _make_pages():
    page1 = {
        "data": {
            "lifelogs": [
                {
                    "id": "svcA",
                    "title": "t1",
                    "markdown": "m1",
                    "contents": [],
                    "startTime": "2025-03-04T01:02:03Z",
                    "endTime": "2025-03-04T02:02:03Z",
                    "isStarred": False,
                    "updatedAt": "2025-03-04T03:02:03Z",
                }
            ]
        },
        "meta": {"lifelogs": {"nextCursor": "CURX"}},
    }
    page2 = {
        "data": {
            "lifelogs": [
                {
                    "id": "svcB",
                    "title": "t2",
                    "markdown": "m2",
                    "contents": [],
                    "startTime": "2025-03-05T01:02:03Z",
                    "endTime": "2025-03-05T02:02:03Z",
                    "isStarred": True,
                    "updatedAt": "2025-03-05T03:02:03Z",
                }
            ]
        },
        "meta": {"lifelogs": {"nextCursor": None}},
    }
    return [page1, page2]


def test_service_fetch_saves_files(tmp_path: Path, monkeypatch):
    from limitless_tools.services.lifelog_service import LifelogService
    from limitless_tools.http.client import LimitlessClient

    # Build a client with fake session and inject into service
    session = FakeSession(_make_pages())
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)

    # Allow service to use our injected client
    service = LifelogService(api_key="KEY", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)

    files = service.fetch(limit=None, include_markdown=True, include_headings=True, direction="desc")

    saved = sorted([p.name for p in tmp_path.rglob("*.json")])
    assert saved == ["lifelog_svcA.json", "lifelog_svcB.json"]

