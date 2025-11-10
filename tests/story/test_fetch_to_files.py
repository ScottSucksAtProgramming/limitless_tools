"""
Story: fetch latest N writes N lifelogs to dated JSON files.
Single assert per test.
"""

from pathlib import Path


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.ok = True

    def json(self):
        return self._payload


class Pages:
    def __init__(self, items):
        self.items = items

    def to_pages(self):
        page = {"data": {"lifelogs": self.items}, "meta": {"lifelogs": {"nextCursor": None}}}
        return [page]


class Session:
    def __init__(self, pages):
        self.pages = pages
        self.i = 0

    def get(self, url, headers, params):
        if self.i >= len(self.pages):
            return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})
        p = self.pages[self.i]
        self.i += 1
        return FakeResponse(p)


def test_fetch_writes_json_files(tmp_path: Path):
    from limitless_tools.http.client import LimitlessClient
    from limitless_tools.services.lifelog_service import LifelogService

    items = [
        {
            "id": "S1",
            "title": "T1",
            "markdown": "M1",
            "contents": [],
            "startTime": "2025-01-10T00:00:00Z",
            "endTime": "2025-01-10T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-01-10T02:00:00Z",
        },
        {
            "id": "S2",
            "title": "T2",
            "markdown": "M2",
            "contents": [],
            "startTime": "2025-01-11T00:00:00Z",
            "endTime": "2025-01-11T01:00:00Z",
            "isStarred": True,
            "updatedAt": "2025-01-11T02:00:00Z",
        },
    ]
    pages = Pages(items).to_pages()
    session = Session(pages)
    client = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=session)
    svc = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)
    saved = svc.fetch(limit=None)
    assert len(saved) == 2

