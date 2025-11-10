"""
Structured JSON logs shape on --verbose.
Single assert per test.
"""

import json


def test_verbose_logs_are_json_lines(monkeypatch, capsys, tmp_path):
    from limitless_tools.cli import main as cli_main

    class FakeService:
        def __init__(self, *_, **__):
            pass

        def fetch(self, **kwargs):
            return []

    monkeypatch.setattr(cli_main, "LifelogService", FakeService)

    code = cli_main.main(["--verbose", "fetch", "--limit", "1", "--data-dir", str(tmp_path)])
    err = capsys.readouterr().err
    first_line = err.strip().splitlines()[0]
    doc = json.loads(first_line)
    assert code == 0 and all(k in doc for k in ("time", "level", "name", "message"))

