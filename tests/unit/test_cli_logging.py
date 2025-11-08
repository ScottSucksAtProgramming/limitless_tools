"""
Tests for structured logging and --verbose flag.
Single assert per test.
"""

import logging


def test_cli_verbose_emits_debug_logs(monkeypatch, caplog, tmp_path):
    """--verbose should enable debug logs from the CLI."""
    called = {"kwargs": None}

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def fetch(self, **kwargs):
            called["kwargs"] = kwargs

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    caplog.set_level(logging.DEBUG)
    code = cli_main.main(["--verbose", "fetch", "--limit", "1", "--data-dir", str(tmp_path)])
    assert code == 0 and "parsed_args" in caplog.text


def test_cli_default_suppresses_debug_logs(monkeypatch, caplog, tmp_path):
    """Without --verbose, debug messages should not be emitted."""
    class FakeService:
        def __init__(self, *_, **__):
            pass

        def fetch(self, **kwargs):
            pass

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    caplog.set_level(logging.DEBUG)
    code = cli_main.main(["fetch", "--limit", "1", "--data-dir", str(tmp_path)])
    assert code == 0 and "parsed_args" not in caplog.text

