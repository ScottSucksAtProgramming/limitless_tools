"""
CLI should load .env before parsing so env-based defaults apply.
Single assert per test.
"""

import os
from pathlib import Path


def test_cli_honors_data_dir_from_env_dotenv(monkeypatch, tmp_path: Path):
    """When .env sets LIMITLESS_DATA_DIR, CLI should use it as default."""
    # Ensure the environment variable is not set beforehand
    monkeypatch.delenv("LIMITLESS_DATA_DIR", raising=False)

    # Create a .env file in a temporary CWD
    envfile = tmp_path / ".env"
    env_data_dir = tmp_path / "data_dir_from_env"
    envfile.write_text(f"LIMITLESS_DATA_DIR={env_data_dir}\n")

    # Switch CWD so CLI can load this .env
    monkeypatch.chdir(tmp_path)

    called = {"init_kwargs": None}

    class FakeService:
        def __init__(self, *_, **kwargs):
            called["init_kwargs"] = kwargs

        def fetch(self, **kwargs):
            # Not needed for this test
            pass

    from limitless_tools.cli import main as cli_main

    # Monkeypatch the service so we can capture the init kwargs
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    # Invoke CLI without explicitly passing --data-dir
    exit_code = cli_main.main(["fetch", "--limit", "1"])

    assert exit_code == 0
    # Verify that the service received the data_dir from .env
    assert called["init_kwargs"]["data_dir"] == str(env_data_dir)

