"""
CLI should pass --batch-size to the service for fetch and sync.
Single assert per test.
"""


def test_cli_fetch_passes_batch_size(monkeypatch, tmp_path):
    called = {"kwargs": None}

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def fetch(self, **kwargs):
            called["kwargs"] = kwargs

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main([
        "fetch",
        "--limit",
        "3",
        "--batch-size",
        "42",
        "--data-dir",
        str(tmp_path),
    ])

    assert code == 0 and called["kwargs"]["batch_size"] == 42


def test_cli_sync_passes_batch_size(monkeypatch, tmp_path):
    called = {"kwargs": None}

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def sync(self, **kwargs):
            called["kwargs"] = kwargs

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main([
        "sync",
        "--start",
        "2025-01-01",
        "--end",
        "2025-01-02",
        "--batch-size",
        "77",
        "--data-dir",
        str(tmp_path),
    ])

    assert code == 0 and called["kwargs"]["batch_size"] == 77

