"""
Tests for listing local lifelogs and exporting markdown.
Single assert per test.
"""

import json
from pathlib import Path


def _write_sample(dirpath: Path, obj: dict) -> Path:
    y, m, d = obj["startTime"][0:10].split("-")
    folder = dirpath / y / m / d
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / f"lifelog_{obj['id']}.json"
    p.write_text(json.dumps(obj))
    return p


def test_list_local_filters_by_date_and_starred(tmp_path: Path):
    from limitless_tools.services.lifelog_service import LifelogService

    a = {
        "id": "L1",
        "title": "A",
        "markdown": "ma",
        "contents": [],
        "startTime": "2025-05-01T00:00:00Z",
        "endTime": "2025-05-01T01:00:00Z",
        "isStarred": False,
        "updatedAt": "2025-05-01T02:00:00Z",
    }
    b = {
        "id": "L2",
        "title": "B",
        "markdown": "mb",
        "contents": [],
        "startTime": "2025-05-02T00:00:00Z",
        "endTime": "2025-05-02T01:00:00Z",
        "isStarred": True,
        "updatedAt": "2025-05-02T02:00:00Z",
    }
    _write_sample(tmp_path, a)
    _write_sample(tmp_path, b)

    svc = LifelogService(api_key=None, api_url=None, data_dir=str(tmp_path))
    items = svc.list_local(date="2025-05-02", is_starred=True)
    ids = [x["id"] for x in items]
    assert ids == ["L2"]


def test_export_markdown_returns_latest_n(tmp_path: Path):
    from limitless_tools.services.lifelog_service import LifelogService

    # Older
    _write_sample(
        tmp_path,
        {
            "id": "E1",
            "title": "Older",
            "markdown": "older markdown",
            "contents": [],
            "startTime": "2025-01-01T00:00:00Z",
            "endTime": "2025-01-01T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-01-01T02:00:00Z",
        },
    )

    # Newer
    _write_sample(
        tmp_path,
        {
            "id": "E2",
            "title": "Newer",
            "markdown": "newer markdown",
            "contents": [],
            "startTime": "2025-02-01T00:00:00Z",
            "endTime": "2025-02-01T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-02-01T02:00:00Z",
        },
    )

    svc = LifelogService(api_key=None, api_url=None, data_dir=str(tmp_path))
    text = svc.export_markdown(limit=1)
    assert text.strip() == "newer markdown"

