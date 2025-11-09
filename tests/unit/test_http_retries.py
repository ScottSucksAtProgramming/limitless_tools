"""
HTTP client should retry on 429 and then succeed, using injected sleep to avoid delays.
Single assert per test.
"""


class FakeResponse:
    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


class FlakySession:
    def __init__(self, failures: int):
        self.failures = failures
        self.calls = 0

    def get(self, url, headers, params):
        self.calls += 1
        if self.calls <= self.failures:
            return FakeResponse({}, ok=False, status_code=429)
        return FakeResponse({"data": {"lifelogs": []}, "meta": {"lifelogs": {"nextCursor": None}}})


def test_retries_on_429_then_succeeds():
    from limitless_tools.http.client import LimitlessClient

    sleeps: list[float] = []

    def fake_sleep(seconds: float):
        sleeps.append(seconds)

    session = FlakySession(failures=2)
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session, max_retries=3, backoff_factor=0.1, sleep_fn=fake_sleep)

    # Should succeed after 2 retries, with at least two sleeps recorded
    _ = client.get_lifelogs(limit=1)
    assert len(sleeps) == 2
