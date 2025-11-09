"""
CSV export with optional markdown column.
Single assert per test.
"""

import json
from pathlib import Path


def _write(dirpath: Path, obj: dict) -> None:
    p = dirpath / f"lifelog_{obj['id']}.json"
    p.write_text(json.dumps(obj))


def test_cli_export_csv_basic(monkeypatch, capsys, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    data_dir = tmp_path / "lifelogs"
    data_dir.mkdir(parents=True, exist_ok=True)
    _write(
        data_dir,
        {
            "id": "c1",
            "title": "T1",
            "markdown": "M1",
            "contents": [],
            "startTime": "2025-12-01T00:00:00Z",
            "endTime": "2025-12-01T01:00:00Z",
            "isStarred": False,
            "updatedAt": "2025-12-01T02:00:00Z",
        },
    )

    code = cli_main.main([
        "export-csv",
        "--data-dir",
        str(data_dir),
    ])
    out = capsys.readouterr().out
    # no markdown column by default
    assert code == 0 and out.splitlines()[0].startswith("id,startTime,endTime,title,isStarred,updatedAt,path")


def test_cli_export_csv_include_markdown(monkeypatch, capsys, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    data_dir = tmp_path / "lifelogs"
    data_dir.mkdir(parents=True, exist_ok=True)
    _write(
        data_dir,
        {
            "id": "c2",
            "title": "T2",
            "markdown": "M2",
            "contents": [],
            "startTime": "2025-12-02T00:00:00Z",
            "endTime": "2025-12-02T01:00:00Z",
            "isStarred": True,
            "updatedAt": "2025-12-02T02:00:00Z",
        },
    )

    code = cli_main.main([
        "export-csv",
        "--data-dir",
        str(data_dir),
        "--include-markdown",
    ])
    out = capsys.readouterr().out
    # markdown column present
    assert code == 0 and out.splitlines()[0].startswith("id,startTime,endTime,title,isStarred,updatedAt,path,markdown")

