"""
CLI progress reporter tests ensure user-visible output occurs during long operations.
Single assert per test using capsys.
"""

from pathlib import Path


def test_fetch_command_emits_progress_and_summary(monkeypatch, tmp_path: Path, capsys):
    from limitless_tools.cli import main as cli_main
    from limitless_tools.services.lifelog_service import SaveReport

    class FakeService:
        def __init__(self, *_, **__):
            self.last_report = SaveReport(created=1, updated=1, unchanged=0)

        def fetch(self, **kwargs):
            progress_callback = kwargs.get("progress_callback")
            if callable(progress_callback):
                progress_callback(1, 1)
                progress_callback(2, 2)
            return [str(tmp_path / "lifelog_a.json"), str(tmp_path / "lifelog_b.json")]

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    monkeypatch.setattr(cli_main, "load_env", lambda: None)
    monkeypatch.delenv("LIMITLESS_DATA_DIR", raising=False)

    code = cli_main.main([
        "fetch",
        "--limit",
        "2",
        "--data-dir",
        str(tmp_path),
    ])
    stderr = capsys.readouterr().err
    assert code == 0 and "Fetch started" in stderr and "Fetch complete" in stderr


def test_sync_reports_no_changes(monkeypatch, tmp_path: Path, capsys):
    from limitless_tools.cli import main as cli_main
    from limitless_tools.services.lifelog_service import SaveReport

    class FakeService:
        def __init__(self, *_, **__):
            self.last_report = SaveReport(created=0, updated=0, unchanged=3)

        def sync(self, **kwargs):
            progress_callback = kwargs.get("progress_callback")
            if callable(progress_callback):
                progress_callback(1, 0)
            return []

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)
    monkeypatch.setattr(cli_main, "load_env", lambda: None)
    monkeypatch.delenv("LIMITLESS_DATA_DIR", raising=False)

    code = cli_main.main([
        "sync",
        "--start",
        "2025-01-01",
        "--end",
        "2025-01-02",
        "--data-dir",
        str(tmp_path),
    ])
    stderr = capsys.readouterr().err
    assert code == 0 and "no changes" in stderr
