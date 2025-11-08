"""
CLI tests for `search` command dispatch and JSON output.
Single assert per test.
"""

import json


def test_cli_search_invokes_service_with_parsed_args(monkeypatch, tmp_path):
    """CLI should pass query/date/starred to LifelogService.search_local."""
    called = {"kwargs": None}

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def search_local(self, **kwargs):
            called["kwargs"] = kwargs
            return []

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main(
        [
            "search",
            "--query",
            "roadmap",
            "--date",
            "2025-07-01",
            "--starred-only",
            "--data-dir",
            str(tmp_path),
        ]
    )

    assert code == 0 and called["kwargs"]["query"] == "roadmap" and called["kwargs"]["date"] == "2025-07-01" and called["kwargs"]["is_starred"] is True


def test_cli_search_json_outputs_items(monkeypatch, capsys, tmp_path):
    """With --json, CLI should print matching items as a JSON array."""

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def search_local(self, **kwargs):
            return [
                {"id": "X", "title": "Roadmap", "startTime": "2025-07-01T00:00:00Z", "endTime": "2025-07-01T01:00:00Z"},
                {"id": "Y", "title": "Meeting", "startTime": "2025-07-02T00:00:00Z", "endTime": "2025-07-02T01:00:00Z"},
            ]

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main([
        "search",
        "--query",
        "roadmap",
        "--data-dir",
        str(tmp_path),
        "--json",
    ])
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert code == 0 and {x["id"] for x in doc} == {"X", "Y"}

