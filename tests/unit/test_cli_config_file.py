"""
MVP config file support: TOML with profiles and precedence.
Single assert per test.
"""

from pathlib import Path


def _write_config(path: Path, text: str) -> None:
    path.write_text(text)


def test_cli_uses_config_defaults_when_not_provided(monkeypatch, tmp_path: Path):
    """CLI should read data_dir from config when no CLI/env overrides provided."""
    from limitless_tools.cli import main as cli_main

    cfg = tmp_path / "config.toml"
    _write_config(
        cfg,
        """
        [default]
        data_dir = "./from_config"
        batch_size = 33
        api_key = "KEY_FROM_CONFIG"
        """.strip(),
    )

    called = {"init_kwargs": None, "method_kwargs": None}

    class FakeService:
        def __init__(self, *_, **kwargs):
            called["init_kwargs"] = kwargs

        def fetch(self, **kwargs):
            called["method_kwargs"] = kwargs

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    # Prevent load_env from re-populating env from external .env files
    monkeypatch.setattr(cli_main, "load_env", lambda: None)

    # Clear env so config can supply values
    monkeypatch.delenv("LIMITLESS_DATA_DIR", raising=False)
    monkeypatch.delenv("LIMITLESS_API_KEY", raising=False)

    code = cli_main.main(["--config", str(cfg), "fetch", "--limit", "1"])

    assert (
        code == 0
        and called["init_kwargs"]["data_dir"].endswith("from_config")
        and called["init_kwargs"]["api_key"] == "KEY_FROM_CONFIG"
        and called["method_kwargs"]["batch_size"] == 33
    )


def test_cli_config_profile_selection(monkeypatch, tmp_path: Path):
    """--profile should choose a named section from the config file."""
    from limitless_tools.cli import main as cli_main

    cfg = tmp_path / "config.toml"
    _write_config(
        cfg,
        """
        [default]
        data_dir = "./default_dir"
        [work]
        data_dir = "./work_dir"
        timezone = "UTC"
        batch_size = 99
        """.strip(),
    )

    called = {"init_kwargs": None, "sync_kwargs": None}

    class FakeService:
        def __init__(self, *_, **kwargs):
            called["init_kwargs"] = kwargs

        def sync(self, **kwargs):
            called["sync_kwargs"] = kwargs

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    monkeypatch.delenv("LIMITLESS_DATA_DIR", raising=False)

    code = cli_main.main([
        "--config",
        str(cfg),
        "--profile",
        "work",
        "sync",
        "--start",
        "2025-01-01",
        "--end",
        "2025-01-02",
    ])

    assert (
        code == 0
        and called["init_kwargs"]["data_dir"].endswith("work_dir")
        and called["sync_kwargs"]["batch_size"] == 99
    )


def test_cli_env_overrides_config_for_data_dir(monkeypatch, tmp_path: Path):
    """Environment variable should win over config when CLI flag is absent."""
    from limitless_tools.cli import main as cli_main

    cfg = tmp_path / "config.toml"
    _write_config(
        cfg,
        """
        [default]
        data_dir = "./from_config"
        """.strip(),
    )

    called = {"init_kwargs": None}

    class FakeService:
        def __init__(self, *_, **kwargs):
            called["init_kwargs"] = kwargs

        def fetch(self, **kwargs):
            pass

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    monkeypatch.setenv("LIMITLESS_DATA_DIR", str(tmp_path / "from_env"))

    code = cli_main.main(["--config", str(cfg), "fetch", "--limit", "1"])
    assert code == 0 and called["init_kwargs"]["data_dir"].endswith("from_env")
