"""
User-Agent header presence test.
Single assert per test.
"""


class UARecordingSession:
    def __init__(self):
        self.last_headers = None

    def get(self, url, headers, params, timeout=None):  # accept optional timeout
        self.last_headers = headers
        return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200, headers=None):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_user_agent_header_present():
    from limitless_tools.http.client import LimitlessClient

    s = UARecordingSession()
    c = LimitlessClient(api_key="K", base_url="https://api.limitless.ai", session=s)
    _ = c.get_lifelogs(limit=1)
    assert "User-Agent" in s.last_headers and "limitless-tools" in s.last_headers.get("User-Agent", "")

