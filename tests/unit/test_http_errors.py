"""
Improve error messages for non-retryable HTTP errors.
Single assert per test to keep failures crisp.
"""


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

    # Simulate an error payload the API might return
    payload = {"error": {"code": "INVALID_DATE", "message": "Bad request: invalid date"}}
    session = ErrorSession(400, payload)
    client = LimitlessClient(api_key="KEY", base_url="https://api.limitless.ai", session=session)

    try:
        client.get_lifelogs(limit=1)
        raised = False
    except RuntimeError as e:
        msg = str(e)
        raised = True

    assert raised and "400" in msg and "INVALID_DATE" in msg and "invalid date" in msg

