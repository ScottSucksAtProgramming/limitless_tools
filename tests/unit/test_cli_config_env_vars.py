"""
Env var overrides for config path and profile.
Single assert per test.
"""

from pathlib import Path


def test_env_LIMITLESS_CONFIG_selects_config_file(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    cfg = tmp_path / "mycfg.toml"
    cfg.write_text(
        """
        [default]
        data_dir = "./env_cfg_dir"
        batch_size = 21
        """.strip()
    )

    called = {"init_kwargs": None, "fetch_kwargs": None}

    class FakeService:
        def __init__(self, *_, **kwargs):
            called["init_kwargs"] = kwargs

        def fetch(self, **kwargs):
            called["fetch_kwargs"] = kwargs

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    # Avoid external .env pollution
    monkeypatch.setattr(cli_main, "load_env", lambda: None)
    # Point to our custom config path
    monkeypatch.setenv("LIMITLESS_CONFIG", str(cfg))
    monkeypatch.delenv("LIMITLESS_DATA_DIR", raising=False)

    code = cli_main.main(["fetch", "--limit", "1"])
    assert code == 0 and called["init_kwargs"]["data_dir"].endswith("env_cfg_dir") and called["fetch_kwargs"]["batch_size"] == 21


def test_env_LIMITLESS_PROFILE_selects_profile(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    cfg = tmp_path / "cfg.toml"
    cfg.write_text(
        """
        [default]
        data_dir = "./default_dir"
        [work]
        data_dir = "./work_dir"
        batch_size = 88
        """.strip()
    )

    called = {"init_kwargs": None, "sync_kwargs": None}

    class FakeService:
        def __init__(self, *_, **kwargs):
            called["init_kwargs"] = kwargs

        def sync(self, **kwargs):
            called["sync_kwargs"] = kwargs

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    monkeypatch.setattr(cli_main, "load_env", lambda: None)
    monkeypatch.setenv("LIMITLESS_CONFIG", str(cfg))
    monkeypatch.setenv("LIMITLESS_PROFILE", "work")

    code = cli_main.main(["sync", "--start", "2025-01-01", "--end", "2025-01-02"])
    assert code == 0 and called["init_kwargs"]["data_dir"].endswith("work_dir") and called["sync_kwargs"]["batch_size"] == 88

