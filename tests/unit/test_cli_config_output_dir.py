"""
Config-driven default output directory for export commands.
Single assert per test.
"""

import json
from pathlib import Path


def _write_cfg(path: Path, text: str) -> None:
    path.write_text(text)


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


def test_export_markdown_combine_uses_config_output_dir(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    # Prepare data
    lifelogs = tmp_path / "lifelogs"
    lifelogs.mkdir(parents=True, exist_ok=True)
    _write_lifelog(lifelogs / "lifelog_a.json", "a", "A", "2025-11-01T00:00:00Z", "2025-11-01T01:00:00Z", "md1")
    _write_lifelog(lifelogs / "lifelog_b.json", "b", "B", "2025-11-01T02:00:00Z", "2025-11-01T03:00:00Z", "md2")

    # Config with output_dir
    cfg = tmp_path / "cfg.toml"
    out_dir = tmp_path / "vault"
    _write_cfg(
        cfg,
        f"""
[default]
output_dir = "{out_dir}"
""".strip(),
    )

    code = cli_main.main([
        "--config",
        str(cfg),
        "export-markdown",
        "--date",
        "2025-11-01",
        "--data-dir",
        str(lifelogs),
        "--combine",
    ])

    out_file = out_dir / "2025-11-01_lifelogs.md"
    assert code == 0 and out_file.exists() and out_file.read_text().strip() == "md1\n\nmd2"


def test_export_csv_uses_config_output_dir_when_no_output(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    # Prepare data
    lifelogs = tmp_path / "lifelogs"
    lifelogs.mkdir(parents=True, exist_ok=True)
    _write_lifelog(lifelogs / "lifelog_c.json", "c", "C", "2025-12-02T00:00:00Z", "2025-12-02T01:00:00Z", "md")

    # Config with output_dir
    cfg = tmp_path / "cfg.toml"
    out_dir = tmp_path / "out"
    _write_cfg(
        cfg,
        f"""
[default]
output_dir = "{out_dir}"
""".strip(),
    )

    code = cli_main.main([
        "--config",
        str(cfg),
        "export-csv",
        "--data-dir",
        str(lifelogs),
        "--date",
        "2025-12-02",
    ])

    # Expect lifelogs_YYYY-MM-DD.csv in output_dir
    outfile = out_dir / "lifelogs_2025-12-02.csv"
    assert code == 0 and outfile.exists() and outfile.read_text().splitlines()[0].startswith("id,startTime,endTime,title,isStarred,updatedAt,path")


def test_configure_writes_output_dir(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main
    from limitless_tools.config.config import load_config

    cfg = tmp_path / "cfg.toml"
    out_dir = tmp_path / "vault"

    code = cli_main.main([
        "--config",
        str(cfg),
        "configure",
        "--output-dir",
        str(out_dir),
    ])

    merged = load_config(str(cfg))
    assert code == 0 and str(merged["default"]["output_dir"]).endswith("vault")

