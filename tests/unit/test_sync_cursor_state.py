"""
Tests cursor-based resume: store lastCursor and use it on next run when no date/time is provided.
Single assert per test.
"""


class CursorSession:
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


def _page_with_cursor(next_cursor):
    return {
        "data": {"lifelogs": []},
        "meta": {"lifelogs": {"nextCursor": next_cursor}},
    }


def test_cursor_saved_and_used(tmp_path):
    from limitless_tools.services.lifelog_service import LifelogService
    from limitless_tools.http.client import LimitlessClient

    s1 = CursorSession([_page_with_cursor("ABC")])
    c1 = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s1)
    svc1 = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=c1)
    svc1.sync()  # no date/time provided, should store cursor

    s2 = CursorSession([_page_with_cursor(None)])
    c2 = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s2)
    svc2 = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=c2)
    svc2.sync()  # should pass 'cursor' on first call
    assert s2.params_history[0].get("cursor") == "ABC"

