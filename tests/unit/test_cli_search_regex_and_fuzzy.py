"""
CLI should support --regex/-rg and --fuzzy with threshold.
Single assert per test.
"""


def test_cli_search_parses_regex_and_fuzzy(monkeypatch, tmp_path):
    called = {"kwargs": None}

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def search_local(self, **kwargs):
            called["kwargs"] = kwargs
            return []

    from limitless_tools.cli import main as cli_main
    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main([
        "search",
        "--query",
        "meet.*notes",
        "-rg",
        "--fuzzy",
        "--fuzzy-threshold",
        "78",
        "--data-dir",
        str(tmp_path),
    ])

    assert code == 0 and called["kwargs"]["regex"] is True and called["kwargs"]["fuzzy"] is True and called["kwargs"]["fuzzy_threshold"] == 78

