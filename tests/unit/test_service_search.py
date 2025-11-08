"""
Tests for local search over lifelogs by title/markdown with optional filters.
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


def test_search_matches_title_and_markdown(tmp_path: Path):
    """Search should match case-insensitive substrings in title or markdown."""
    from limitless_tools.services.lifelog_service import LifelogService

    _write_sample(
        tmp_path,
        {
            "id": "S1",
            "title": "Weekly Meeting Notes",
            "markdown": "Discussed roadmap and milestones",
            "contents": [],
            "startTime": "2025-07-01T00:00:00Z",
            "endTime": "2025-07-01T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-07-01T02:00:00Z",
        },
    )
    _write_sample(
        tmp_path,
        {
            "id": "S2",
            "title": "Random",
            "markdown": "shopping list: apples, bananas",
            "contents": [],
            "startTime": "2025-07-02T00:00:00Z",
            "endTime": "2025-07-02T01:00:00Z",
            "isStarred": True,
            "updatedAt": "2025-07-02T02:00:00Z",
        },
    )

    svc = LifelogService(api_key=None, api_url=None, data_dir=str(tmp_path))
    results = svc.search_local(query="meeting")
    ids = [x.get("id") for x in results]
    assert ids == ["S1"]


def test_search_filters_by_date_and_starred(tmp_path: Path):
    """Search should respect --date and --starred-only filters."""
    from limitless_tools.services.lifelog_service import LifelogService

    _write_sample(
        tmp_path,
        {
            "id": "D1",
            "title": "Alpha",
            "markdown": "alpha text",
            "contents": [],
            "startTime": "2025-08-01T00:00:00Z",
            "endTime": "2025-08-01T01:00:00Z",
            "isStarred": True,
            "updatedAt": "2025-08-01T02:00:00Z",
        },
    )
    _write_sample(
        tmp_path,
        {
            "id": "D2",
            "title": "Beta",
            "markdown": "beta text",
            "contents": [],
            "startTime": "2025-08-02T00:00:00Z",
            "endTime": "2025-08-02T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-08-02T02:00:00Z",
        },
    )

    svc = LifelogService(api_key=None, api_url=None, data_dir=str(tmp_path))
    results = svc.search_local(query="a", date="2025-08-01", is_starred=True)
    assert [x.get("id") for x in results] == ["D1"]

