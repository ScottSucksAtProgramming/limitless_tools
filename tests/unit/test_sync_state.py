"""
Tests for incremental sync state: record last endTime and reuse it as start for next run.
Single assert per test.
"""

import json
from pathlib import Path


class RecordingSession:
    def __init__(self, pages):
        self._pages = pages
        self._i = 0
        self.params_history = []

    def get(self, url, headers, params):
        self.params_history.append(dict(params))
        if self._i >= len(self._pages):
            return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})
        page = self._pages[self._i]
        self._i += 1
        return FakeResponse(page)


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


def _pages():
    return [
        {
            "data": {
                "lifelogs": [
                    {
                        "id": "s1",
                        "title": "A",
                        "markdown": "m1",
                        "contents": [],
                        "startTime": "2025-06-01T00:00:00Z",
                        "endTime": "2025-06-01T01:00:00Z",
                        "isStarred": False,
                        "updatedAt": "2025-06-01T02:00:00Z",
                    },
                    {
                        "id": "s2",
                        "title": "B",
                        "markdown": "m2",
                        "contents": [],
                        "startTime": "2025-06-02T00:00:00Z",
                        "endTime": "2025-06-02T02:00:00Z",
                        "isStarred": True,
                        "updatedAt": "2025-06-02T03:00:00Z",
                    },
                ]
            },
            "meta": {"lifelogs": {"nextCursor": None}},
        }
    ]


def test_state_records_last_end_and_used_as_start(tmp_path: Path):
    from limitless_tools.services.lifelog_service import LifelogService
    from limitless_tools.http.client import LimitlessClient

    session = RecordingSession(_pages())
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)
    svc = LifelogService(api_key="KEY", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)

    svc.sync()

    # Check state file exists with last end time
    state_path = tmp_path.parent / "state" / "lifelogs_sync.json"
    state = json.loads(state_path.read_text())
    assert state.get("lastEndTime") == "2025-06-02T02:00:00Z"

    # Next run uses start parameter
    session2 = RecordingSession(_pages())
    client2 = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session2)
    svc2 = LifelogService(api_key="KEY", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client2)
    svc2.sync()

    # First call should include start equal to the lastEndTime
    first_params = session2.params_history[0]
    assert first_params.get("start") == "2025-06-02T02:00:00Z"

