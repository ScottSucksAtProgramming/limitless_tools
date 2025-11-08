"""
Timezone validation: CLI should accept valid IANA names and reject invalid ones.
Single assert per test.
"""


def test_cli_sync_valid_timezone(monkeypatch, tmp_path):
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
        "--timezone",
        "UTC",
        "--data-dir",
        str(tmp_path),
    ])

    assert code == 0


def test_cli_sync_invalid_timezone(monkeypatch, capsys, tmp_path):
    class FakeService:
        def __init__(self, *_, **__):
            pass

        def sync(self, **kwargs):
            pass

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main([
        "sync",
        "--start",
        "2025-01-01",
        "--end",
        "2025-01-02",
        "--timezone",
        "Not/AZone",
        "--data-dir",
        str(tmp_path),
    ])
    err = capsys.readouterr().err
    assert code == 2 and "Invalid timezone" in err

