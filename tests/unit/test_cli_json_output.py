"""
CLI JSON output for fetch and sync.
Single assert per test.
"""

import json
from pathlib import Path


def _write_lifelog(p: Path, id_: str, title: str, start: str, end: str) -> None:
    p.write_text(
        json.dumps(
            {
                "id": id_,
                "title": title,
                "startTime": start,
                "endTime": end,
                "isStarred": False,
                "updatedAt": start,
                "markdown": "",
                "contents": [],
            }
        )
    )


def test_cli_fetch_json_outputs_items(monkeypatch, capsys, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    data_dir = tmp_path
    f1 = data_dir / "lifelog_a.json"
    f2 = data_dir / "lifelog_b.json"
    _write_lifelog(f1, "a", "A", "2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z")
    _write_lifelog(f2, "b", "B", "2025-01-02T00:00:00Z", "2025-01-02T01:00:00Z")

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def fetch(self, **kwargs):
            return [str(f1), str(f2)]

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    code = cli_main.main(["fetch", "--limit", "2", "--data-dir", str(data_dir), "--json"])
    out = capsys.readouterr().out
    items = json.loads(out)
    assert code == 0 and isinstance(items, list) and {x["id"] for x in items} == {"a", "b"}


def test_cli_sync_json_outputs_status_and_items(monkeypatch, capsys, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    # Use a data dir nested to allow state at parent/state
    data_dir = tmp_path / "lifelogs"
    data_dir.mkdir(parents=True, exist_ok=True)
    f1 = data_dir / "lifelog_c.json"
    f2 = data_dir / "lifelog_d.json"
    _write_lifelog(f1, "c", "C", "2025-02-01T00:00:00Z", "2025-02-01T01:00:00Z")
    _write_lifelog(f2, "d", "D", "2025-02-02T00:00:00Z", "2025-02-02T01:00:00Z")

    # Precreate state file that service would update
    state_dir = data_dir.parent / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "lifelogs_sync.json").write_text(json.dumps({"lastCursor": "CUR123", "lastEndTime": "2025-02-02T01:00:00Z"}))

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def sync(self, **kwargs):
            return [str(f1), str(f2)]

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    code = cli_main.main([
        "sync",
        "--start",
        "2025-02-01",
        "--end",
        "2025-02-03",
        "--data-dir",
        str(data_dir),
        "--json",
    ])
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert code == 0 and doc.get("saved_count") == 2 and {x["id"] for x in doc.get("items", [])} == {"c", "d"} and doc.get("lastCursor") == "CUR123"

