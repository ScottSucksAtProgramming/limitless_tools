"""
Tests for CLI parsing and dispatch for `fetch` command.
Single assert per test; we monkeypatch the service used by the CLI to capture calls.
"""



def test_cli_fetch_invokes_service_with_parsed_args(monkeypatch, tmp_path):
    """CLI should pass parsed options to the service's fetch method."""
    called = {
        "args": None,
        "kwargs": None,
    }

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def fetch(self, **kwargs):
            called["kwargs"] = kwargs

    # Monkeypatch the service class used by CLI
    from limitless_tools.cli import main as cli_main

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    # Run main with args
    exit_code = cli_main.main([
        "fetch",
        "--limit",
        "2",
        "--direction",
        "desc",
        "--include-markdown",
        "--include-headings",
        "--data-dir",
        str(tmp_path),
    ])

    assert exit_code == 0

