"""
Tests for LifelogService.fetch to ensure it pulls lifelogs via client and saves JSON files.
Single assert per test.
"""

from pathlib import Path


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
    from limitless_tools.http.client import LimitlessClient
    from limitless_tools.services.lifelog_service import LifelogService

    # Build a client with fake session and inject into service
    session = FakeSession(_make_pages())
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)

    # Allow service to use our injected client
    service = LifelogService(api_key="KEY", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)

    _ = service.fetch(limit=None, include_markdown=True, include_headings=True, direction="desc")

    saved = sorted([p.name for p in tmp_path.rglob("*.json")])
    report = service.last_report
    assert saved == ["lifelog_svcA.json", "lifelog_svcB.json"] and report and report.created == 2 and report.updated == 0


def test_service_fetch_param_toggles_propagate(tmp_path: Path):
    """include_markdown/include_headings toggles should propagate to HTTP params."""
    from limitless_tools.http.client import LimitlessClient
    from limitless_tools.services.lifelog_service import LifelogService

    class RecordingSession:
        def __init__(self):
            self.last_params = None

        def get(self, url, headers, params):
            self.last_params = params
            return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})

    session = RecordingSession()
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)
    service = LifelogService(api_key="KEY", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)
    _ = service.fetch(limit=1, include_markdown=False, include_headings=False)
    assert session.last_params.get("includeMarkdown") == "false" and session.last_params.get("includeHeadings") == "false"


def test_service_passes_http_timeout_to_client(monkeypatch, tmp_path: Path):
    """Services constructed with http_timeout should pass it into LimitlessClient."""
    from limitless_tools.services import lifelog_service as svc_module

    captured = {"timeout": None}

    class FakeClient:
        def __init__(self, *_, **kwargs):
            captured["timeout"] = kwargs.get("timeout")

        def get_lifelogs(self, **_kwargs):
            return []

    monkeypatch.setattr(svc_module, "LimitlessClient", FakeClient)

    service = svc_module.LifelogService(
        api_key="KEY",
        api_url="https://api.limitless.ai",
        data_dir=str(tmp_path),
        http_timeout=22.0,
    )

    _ = service.fetch(limit=1)

    assert abs(float(captured["timeout"]) - 22.0) < 1e-6


def test_service_last_report_tracks_unchanged(tmp_path: Path, monkeypatch):
    """Fetching the same data twice should set last_report.unchanged."""
    from limitless_tools.http.client import LimitlessClient
    from limitless_tools.services import lifelog_service as svc_module

    session = FakeSession(_make_pages())
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)
    service = svc_module.LifelogService(api_key="KEY", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=client)

    _ = service.fetch(limit=None)
    # Re-run fetch with identical responses by resetting session iterator
    session2 = FakeSession(_make_pages())
    client2 = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session2)
    service.client = client2

    _ = service.fetch(limit=None)
    report = service.last_report
    assert report and report.unchanged == 2 and report.created == 0 and report.updated == 0
