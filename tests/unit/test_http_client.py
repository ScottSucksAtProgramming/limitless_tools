"""
Tests for LimitlessClient HTTP behavior: auth header, base URL formation, and pagination.
Single assert per test to pinpoint failures.
"""

import json
from typing import Any


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.ok = status_code == 200

    def json(self) -> dict[str, Any]:
        # Return a deep copy-like object to guard against mutation in code under test
        return json.loads(json.dumps(self._payload))


class FakeSession:
    def __init__(self, pages: list[dict[str, Any]]):
        self._pages = pages
        self._i = 0
        self.last_url: str | None = None
        self.last_headers: dict[str, str] | None = None
        self.last_params: dict[str, Any] | None = None

    def get(self, url: str, headers: dict[str, str], params: dict[str, Any]):
        self.last_url = url
        self.last_headers = headers
        self.last_params = params
        if self._i >= len(self._pages):
            return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None, "count": 0}}})
        page = self._pages[self._i]
        self._i += 1
        return FakeResponse(page)


def test_auth_header_and_base_url_importable():
    """Client should attach X-API-Key and build the correct lifelogs URL."""
    from limitless_tools.http.client import LimitlessClient

    page = {
        "data": {"lifelogs": []},
        "meta": {"lifelogs": {"nextCursor": None, "count": 0}},
    }
    session = FakeSession([page])
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)

    _ = client.get_lifelogs(limit=1)

    assert session.last_headers.get("X-API-Key") == "KEY"


def test_pagination_combines_pages_and_limit():
    """Client should paginate until nextCursor is None and honor limit slicing."""
    from limitless_tools.http.client import LimitlessClient

    page1 = {
        "data": {
            "lifelogs": [
                {
                    "id": "a",
                    "title": "t1",
                    "markdown": None,
                    "contents": [],
                    "startTime": "2025-01-01T01:00:00Z",
                    "endTime": "2025-01-01T02:00:00Z",
                    "isStarred": False,
                    "updatedAt": "2025-01-01T00:00:00Z",
                }
            ]
        },
        "meta": {"lifelogs": {"nextCursor": "CUR1", "count": 1}},
    }
    page2 = {
        "data": {
            "lifelogs": [
                {
                    "id": "b",
                    "title": "t2",
                    "markdown": None,
                    "contents": [],
                    "startTime": "2025-01-02T01:00:00Z",
                    "endTime": "2025-01-02T02:00:00Z",
                    "isStarred": False,
                    "updatedAt": "2025-01-02T00:00:00Z",
                }
            ]
        },
        "meta": {"lifelogs": {"nextCursor": None, "count": 1}},
    }

    session = FakeSession([page1, page2])
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)

    all_logs = client.get_lifelogs(limit=None)
    assert [x["id"] for x in all_logs] == ["a", "b"]

    # Use a fresh session/client for a new fetch with a limit of 1
    session2 = FakeSession([page1, page2])
    client2 = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session2)
    only_one = client2.get_lifelogs(limit=1)
    assert [x["id"] for x in only_one] == ["a"]
