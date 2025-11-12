"""Service-level error handling to guard API and storage failures."""

import pytest

from limitless_tools.errors import ApiError, ServiceError, StorageError


class FailingClient:
    def get_lifelogs(self, **_):  # noqa: D401 - simple stub
        raise ApiError("request failed", status_code=500)


class StubRepo:
    def __init__(self, *_, **__):
        pass

    def save_lifelog(self, lifelog):  # noqa: D401 - simple stub
        return lifelog


def test_fetch_wraps_api_error(tmp_path):
    from limitless_tools.services.lifelog_service import LifelogService

    service = LifelogService(api_key="k", api_url=None, data_dir=str(tmp_path), client=FailingClient(), repo=StubRepo())

    with pytest.raises(ServiceError) as excinfo:
        service.fetch(limit=1)

    assert "Failed to fetch lifelogs" in str(excinfo.value) and isinstance(excinfo.value.cause, ApiError)


class SuccessfulClient:
    def get_lifelogs(self, **_):  # noqa: D401 - simple stub returning one lifelog
        return [{"id": "1", "startTime": "2024-01-01T00:00:00Z", "endTime": "2024-01-01T01:00:00Z"}]


class FailingRepo:
    def save_lifelog(self, lifelog):
        raise StorageError("cannot write", context={"path": "/tmp/lifelog"})


def test_fetch_wraps_storage_error(tmp_path):
    from limitless_tools.services.lifelog_service import LifelogService

    service = LifelogService(api_key="k", api_url=None, data_dir=str(tmp_path), client=SuccessfulClient(), repo=FailingRepo())

    with pytest.raises(ServiceError) as excinfo:
        service.fetch(limit=1)

    assert "Failed to save lifelog" in str(excinfo.value) and isinstance(excinfo.value.cause, StorageError)

