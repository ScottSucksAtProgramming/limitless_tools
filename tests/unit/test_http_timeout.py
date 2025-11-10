"""
HTTP timeout behavior tests.
Single assert per test.
"""


class TimeoutSession:
    def __init__(self):
        self.last_timeout = None

    def get(self, url, headers, params, timeout=None):  # noqa: D401 - fake signature with timeout
        self.last_timeout = timeout
        return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})


class NoTimeoutSession:
    def __init__(self):
        self.calls = 0

    def get(self, url, headers, params):  # no timeout in signature
        self.calls += 1
        return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200, headers=None):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_timeout_default_applied(monkeypatch):
    from limitless_tools.http.client import LimitlessClient

    s = TimeoutSession()
    c = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s)
    _ = c.get_lifelogs(limit=1)
    assert abs(float(s.last_timeout) - 10.0) < 1e-6


def test_timeout_env_override(monkeypatch):
    from limitless_tools.http.client import LimitlessClient

    monkeypatch.setenv("LIMITLESS_HTTP_TIMEOUT", "2.5")
    s = TimeoutSession()
    c = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s)
    _ = c.get_lifelogs(limit=1)
    assert abs(float(s.last_timeout) - 2.5) < 1e-6


def test_no_timeout_param_signature_does_not_break():
    from limitless_tools.http.client import LimitlessClient

    s = NoTimeoutSession()
    c = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s)
    _ = c.get_lifelogs(limit=1)
    assert s.calls == 1

