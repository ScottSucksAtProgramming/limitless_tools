"""
Timezone CLI arg is passed through to service.
Single assert per test.
"""

import json
from pathlib import Path


def test_cli_sync_passes_timezone_argument(monkeypatch, tmp_path: Path):
    from limitless_tools.cli import main as cli_main

    # Minimal config file (not used for timezone in this test)
    cfg = tmp_path / "cfg.toml"
    cfg.write_text("[default]\n")

    # Stub out service to capture timezone passed
    captured = {"tz": None}

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def sync(self, **kwargs):
            captured["tz"] = kwargs.get("timezone")
            return []

    monkeypatch.delenv("LIMITLESS_TZ", raising=False)
    monkeypatch.setenv("LIMITLESS_API_KEY", "X")
    monkeypatch.setenv("LIMITLESS_CONFIG", str(cfg))
    monkeypatch.setenv("LIMITLESS_PROFILE", "default")
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main(["--config", str(cfg), "--profile", "default", "sync", "--start", "2025-01-01", "--end", "2025-01-02", "--timezone", "UTC", "--data-dir", str(tmp_path)])
    assert code == 0 and captured["tz"] == "UTC"
