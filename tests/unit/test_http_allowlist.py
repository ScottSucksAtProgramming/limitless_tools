"""
Tests for HTTP client base URL allowlisting.
Single assert per test.
"""

import pytest


def test_disallow_unknown_base_url(monkeypatch):
    """Client should reject non-allowlisted base URLs by default."""
    from limitless_tools.http.client import LimitlessClient

    with pytest.raises(ValueError):
        _ = LimitlessClient(api_key="K", base_url="https://example.com")


def test_allow_default_public_api_url():
    """Default public API host is allowlisted."""
    from limitless_tools.http.client import LimitlessClient

    c = LimitlessClient(api_key="K", base_url="https://api.limitless.ai")
    assert c.base_url.endswith("api.limitless.ai")

