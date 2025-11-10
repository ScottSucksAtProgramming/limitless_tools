"""
CLI export-markdown default behavior prints to stdout.
Single assert per test.
"""

import json
from pathlib import Path


def _write_lifelog(p: Path, id_: str, title: str, start: str, end: str, markdown: str) -> None:
    p.write_text(
        json.dumps(
            {
                "id": id_,
                "title": title,
                "startTime": start,
                "endTime": end,
                "isStarred": False,
                "updatedAt": start,
                "markdown": markdown,
                "contents": [],
            }
        )
    )


def test_cli_export_markdown_default_stdout(capsys, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    # Arrange: two entries with different start times
    f1 = tmp_path / "lifelog_old.json"
    f2 = tmp_path / "lifelog_new.json"
    _write_lifelog(f1, "x", "X", "2025-01-01T00:00:00Z", "2025-01-01T01:00:00Z", "old md")
    _write_lifelog(f2, "y", "Y", "2025-02-01T00:00:00Z", "2025-02-01T01:00:00Z", "new md")

    code = cli_main.main(["export-markdown", "--limit", "2", "--data-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0 and out.strip() == "old md\n\nnew md"

