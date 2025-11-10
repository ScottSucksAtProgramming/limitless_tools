"""
CLI export-markdown frontmatter option.
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
                "isStarred": True,
                "updatedAt": start,
                "markdown": markdown,
                "contents": [],
            }
        )
    )


def test_cli_export_markdown_frontmatter_included(capsys, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    f = tmp_path / "lifelog_a.json"
    _write_lifelog(f, "a", "Title A", "2025-03-01T00:00:00Z", "2025-03-01T01:00:00Z", "content")
    code = cli_main.main(["export-markdown", "--limit", "1", "--data-dir", str(tmp_path), "--frontmatter"])
    out = capsys.readouterr().out
    assert code == 0 and out.splitlines()[0] == "---"

