"""
CLI list command plain text output.
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


def test_cli_list_plain_prints_lines(capsys, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    # No index.json present; code will scan files
    f = tmp_path / "lifelog_a.json"
    _write_lifelog(f, "a", "A", "2025-04-01T00:00:00Z", "2025-04-01T01:00:00Z")
    code = cli_main.main(["list", "--data-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0 and "2025-04-01T00:00:00Z a A" in out

