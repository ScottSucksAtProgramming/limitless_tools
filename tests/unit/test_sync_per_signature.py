"""
Per-signature sync: cursors kept separately for different filters.
Single assert per test.
"""


class CursorSession:
    def __init__(self, cursors):
        # cursors: list of nextCursor values per call
        self._cursors = list(cursors)
        self._i = 0
        self.params_history = []

    def get(self, url, headers, params):
        self.params_history.append(dict(params))
        if self._i >= len(self._cursors):
            next_cur = None
        else:
            next_cur = self._cursors[self._i]
        self._i += 1
        return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": next_cur}}})


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


def test_cursors_are_per_signature(tmp_path):
    from limitless_tools.services.lifelog_service import LifelogService
    from limitless_tools.http.client import LimitlessClient

    # First run: starred-only True writes STARCUR
    s1 = CursorSession(["STARCUR"])
    c1 = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s1)
    svc1 = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=c1)
    svc1.sync(is_starred=True)

    # Second run: starred-only False writes ALLCUR
    s2 = CursorSession(["ALLCUR"])
    c2 = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s2)
    svc2 = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=c2)
    svc2.sync(is_starred=False)

    # Third run: starred-only True should reuse STARCUR
    s3 = CursorSession([None])
    c3 = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s3)
    svc3 = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=c3)
    svc3.sync(is_starred=True)

    # Fourth run: starred-only False should reuse ALLCUR
    s4 = CursorSession([None])
    c4 = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s4)
    svc4 = LifelogService(api_key="K", api_url="https://api.limitless.ai", data_dir=str(tmp_path), client=c4)
    svc4.sync(is_starred=False)

    assert s3.params_history[0].get("cursor") == "STARCUR" and s4.params_history[0].get("cursor") == "ALLCUR"

