"""
Security-related logging tests.
Single assert per test.
"""

import logging


def test_cli_configure_redacts_api_key_in_logs(monkeypatch, caplog, tmp_path):
    """When --verbose, logs should not contain the raw API key values."""

    from limitless_tools.cli import main as cli_main

    caplog.set_level(logging.DEBUG)
    cfg_path = tmp_path / "config.toml"
    code = cli_main.main([
        "--verbose",
        "--config", str(cfg_path),
        "configure",
        "--api-key", "SUPERSECRET",
        "--data-dir", str(tmp_path / "data"),
    ])
    assert code == 0 and "SUPERSECRET" not in caplog.text
