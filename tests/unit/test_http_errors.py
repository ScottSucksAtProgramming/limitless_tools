"""
Improve error handling ergonomics for HTTP failures and network timeouts.
Single assert per test to keep failures crisp.
"""

import pytest

from limitless_tools.errors import ApiError


class FakeResponse:
    def __init__(self, payload, ok=False, status_code=400, headers=None):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload


class ErrorSession:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self.payload = payload

    def get(self, url, headers, params):
        return FakeResponse(self.payload, ok=False, status_code=self.status_code)


def test_client_raises_informative_message_on_400():
    from limitless_tools.http.client import LimitlessClient

    payload = {"error": {"code": "INVALID_DATE", "message": "Bad request: invalid date"}}
    session = ErrorSession(400, payload)
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)

    with pytest.raises(ApiError) as excinfo:
        client.get_lifelogs(limit=1)

    msg = str(excinfo.value)
    assert excinfo.value.status_code == 400 and "INVALID_DATE" in msg and "invalid date" in msg


def test_error_detail_falls_back_to_text():
    """When JSON parsing fails, error detail should fall back to response.text."""
    from limitless_tools.http.client import LimitlessClient

    class TextResponse:
        def __init__(self):
            self.ok = False
            self.status_code = 500
            self.text = "Internal server error"

        def json(self):
            raise ValueError("not json")

    class TextSession:
        def get(self, url, headers, params):
            return TextResponse()

    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=TextSession())

    with pytest.raises(ApiError) as excinfo:
        client.get_lifelogs(limit=1)

    assert excinfo.value.status_code == 500 and "Internal server error" in str(excinfo.value)


def test_timeout_is_wrapped_in_api_error():
    from limitless_tools.http.client import LimitlessClient

    class RaisingSession:
        def get(self, url, headers, params):  # noqa: ARG002 - signature required
            raise TimeoutError("simulated timeout")

    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=RaisingSession())

    with pytest.raises(ApiError) as excinfo:
        client.get_lifelogs(limit=1)

    msg = str(excinfo.value).lower()
    assert "timeout" in msg or "timed out" in msg
