"""End-to-end tests for CLI error presentation."""

from limitless_tools.errors import ServiceError


def test_cli_fetch_reports_service_error_without_traceback(monkeypatch, tmp_path, capsys):
    class FakeService:
        def __init__(self, *_, **__):
            pass

        def fetch(self, **kwargs):  # noqa: D401 - simple stub
            raise ServiceError("Failed to fetch lifelogs: request timed out.", context={"operation": "fetch"})

    from limitless_tools.cli import main as cli_main

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main([
        "fetch",
        "--limit",
        "1",
        "--data-dir",
        str(tmp_path),
    ])

    captured = capsys.readouterr()
    assert code == 1 and "Error: Failed to fetch lifelogs" in captured.err and captured.out == ""
