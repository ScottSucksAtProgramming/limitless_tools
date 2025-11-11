from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_config_path(tmp_path_factory, monkeypatch) -> None:
    """Prevent pytest from loading the user config by pointing it to a temp path."""
    cfg_dir = tmp_path_factory.mktemp("config")
    cfg_path = cfg_dir / "config.toml"
    monkeypatch.setenv("LIMITLESS_CONFIG", str(cfg_path))
