"""
Client should use Retry-After header seconds before backoff when present.
Single assert per test.
"""


class RetryAfterSession:
    def __init__(self):
        self.calls = 0

    def get(self, url, headers, params):
        self.calls += 1
        if self.calls == 1:
            return FakeResponse({}, ok=False, status_code=429, headers={"Retry-After": "1.5"})
        return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200, headers=None):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_uses_retry_after_before_backoff():
    from limitless_tools.http.client import LimitlessClient

    sleeps = []

    def fake_sleep(s):
        sleeps.append(s)

    session = RetryAfterSession()
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session, max_retries=2, backoff_factor=0.1, sleep_fn=fake_sleep)
    client.get_lifelogs(limit=1)
    assert abs(sleeps[0] - 1.5) < 1e-6

