"""
Service search: regex and fuzzy matching.
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


def test_search_regex_matches(monkeypatch, tmp_path: Path):
    from limitless_tools.services.lifelog_service import LifelogService

    _write_sample(
        tmp_path,
        {
            "id": "R1",
            "title": "Weekly Meeting Notes",
            "markdown": "Roadmap and notes",
            "contents": [],
            "startTime": "2025-09-01T00:00:00Z",
            "endTime": "2025-09-01T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-09-01T02:00:00Z",
        },
    )

    svc = LifelogService(api_key=None, api_url=None, data_dir=str(tmp_path))
    results = svc.search_local(query="meet.*notes", regex=True)
    assert [x.get("id") for x in results] == ["R1"]


def test_search_fuzzy_matches_with_typo(tmp_path: Path):
    from limitless_tools.services.lifelog_service import LifelogService

    _write_sample(
        tmp_path,
        {
            "id": "F1",
            "title": "Wekly Meetng",  # typos
            "markdown": "",
            "contents": [],
            "startTime": "2025-10-01T00:00:00Z",
            "endTime": "2025-10-01T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-10-01T02:00:00Z",
        },
    )

    svc = LifelogService(api_key=None, api_url=None, data_dir=str(tmp_path))
    results = svc.search_local(query="Weekly Meeting", fuzzy=True, fuzzy_threshold=70)
    assert [x.get("id") for x in results] == ["F1"]

