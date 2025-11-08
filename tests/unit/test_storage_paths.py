"""
Tests for file path computation and roundtrip save/load behavior in the JSON repository.
Single assert per test.
"""

import json
from pathlib import Path


def test_path_for_lifelog_uses_date_folders(tmp_path: Path):
    """Path should include YYYY/MM/DD and filename lifelog_{id}.json."""
    from limitless_tools.storage.json_repo import JsonFileRepository

    repo = JsonFileRepository(base_dir=str(tmp_path))
    lifelog = {
        "id": "ABC123",
        "title": "t",
        "markdown": None,
        "contents": [],
        "startTime": "2025-02-03T04:05:06Z",
        "endTime": "2025-02-03T05:05:06Z",
        "isStarred": False,
        "updatedAt": "2025-02-03T06:05:06Z",
    }
    p = repo.path_for_lifelog(lifelog)
    # Normalize to POSIX-like separators for assertion simplicity
    parts = Path(p).parts[-4:]
    assert parts[-1] == "lifelog_ABC123.json" and parts[0] == "2025" and parts[1] == "02" and parts[2] == "03"


def test_save_and_load_roundtrip(tmp_path: Path):
    """Saved lifelog should be readable back with same id."""
    from limitless_tools.storage.json_repo import JsonFileRepository

    repo = JsonFileRepository(base_dir=str(tmp_path))
    lifelog = {
        "id": "XYZ789",
        "title": "t",
        "markdown": "md",
        "contents": [],
        "startTime": "2025-01-01T00:00:00Z",
        "endTime": "2025-01-01T01:00:00Z",
        "isStarred": True,
        "updatedAt": "2025-01-01T02:00:00Z",
    }

    path = repo.save_lifelog(lifelog)
    data = json.loads(Path(path).read_text())
    assert data["id"] == "XYZ789"

