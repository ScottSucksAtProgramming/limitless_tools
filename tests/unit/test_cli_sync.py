"""
Tests for CLI parsing and dispatch for `sync` command.
Single assert per test.
"""


def test_cli_sync_invokes_service_with_parsed_args(monkeypatch, tmp_path):
    called = {"kwargs": None}

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def sync(self, **kwargs):
            called["kwargs"] = kwargs

    from limitless_tools.cli import main as cli_main

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    exit_code = cli_main.main([
        "sync",
        "--start",
        "2025-01-01",
        "--end",
        "2025-01-31",
        "--timezone",
        "America/Los_Angeles",
        "--starred-only",
        "--data-dir",
        str(tmp_path),
    ])

    assert exit_code == 0

