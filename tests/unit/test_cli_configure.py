"""
Tests for `limitless configure` command writing TOML config.
Single assert per test.
"""

from pathlib import Path


def test_configure_writes_profile_with_values(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main
    cfg = tmp_path / "cfg.toml"

    # No interactive input; we pass flags
    code = cli_main.main([
        "--config",
        str(cfg),
        "--profile",
        "work",
        "configure",
        "--api-key",
        "KEY123",
        "--data-dir",
        str(tmp_path / "data_dir"),
        "--timezone",
        "UTC",
        "--batch-size",
        "77",
        "--http-timeout",
        "55.5",
    ])

    assert (
        code == 0
        and cfg.exists()
        and "[work]" in cfg.read_text()
        and "batch_size = 77" in cfg.read_text()
        and "http_timeout = 55.5" in cfg.read_text()
    )


def test_configure_merges_existing_profile(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main
    from limitless_tools.config.config import load_config

    cfg = tmp_path / "cfg.toml"
    cfg.write_text("""
[default]
batch_size = 50
""".strip())

    code = cli_main.main([
        "--config",
        str(cfg),
        "configure",
        "--data-dir",
        str(tmp_path / "dir2"),
    ])

    merged = load_config(str(cfg))
    assert code == 0 and merged["default"]["batch_size"] == 50 and str(merged["default"]["data_dir"]).endswith("dir2")
