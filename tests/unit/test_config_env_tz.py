"""
Config should load .env and resolve timezone default from system when not provided.
Single assert per test.
"""

import os
from pathlib import Path


def test_env_loader_reads_dotenv(tmp_path: Path, monkeypatch):
    from limitless_tools.config.env import load_env

    envfile = tmp_path / ".env"
    envfile.write_text("LIMITLESS_API_KEY=FROM_ENV_FILE\n")

    monkeypatch.chdir(tmp_path)
    load_env()  # should load .env in CWD
    assert os.getenv("LIMITLESS_API_KEY") == "FROM_ENV_FILE"


def test_resolve_timezone_uses_system_when_none(monkeypatch):
    from limitless_tools.config import env as env_mod

    class FakeTzModule:
        @staticmethod
        def get_localzone_name():
            return "America/TestZone"

    import sys
    monkeypatch.setitem(sys.modules, 'tzlocal', FakeTzModule)

    tz = env_mod.resolve_timezone(None)
    assert tz == "America/TestZone"
