"""
Export all lifelogs from a specific date into one markdown file.
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


def test_cli_export_markdown_combine_date_to_file(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    # Arrange: create two lifelogs for same date under nested structure
    lifelogs_dir = tmp_path / "lifelogs"
    lifelogs_dir.mkdir(parents=True, exist_ok=True)
    f1 = lifelogs_dir / "lifelog_a.json"
    f2 = lifelogs_dir / "lifelog_b.json"
    _write_lifelog(f1, "a", "A", "2025-11-01T00:00:00Z", "2025-11-01T01:00:00Z", "md1")
    _write_lifelog(f2, "b", "B", "2025-11-01T02:00:00Z", "2025-11-01T03:00:00Z", "md2")

    out_dir = tmp_path / "vault"
    out_dir.mkdir(parents=True, exist_ok=True)

    code = cli_main.main([
        "export-markdown",
        "--date",
        "2025-11-01",
        "--data-dir",
        str(lifelogs_dir),
        "--write-dir",
        str(out_dir),
        "--combine",
    ])

    out_file = out_dir / "2025-11-01_lifelogs.md"
    assert code == 0 and out_file.exists() and out_file.read_text().strip() == "md1\n\nmd2"

