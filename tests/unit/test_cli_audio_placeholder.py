"""
Placeholder test for `fetch-audio` CLI command.
Single assert per test.
"""


def test_cli_fetch_audio_placeholder(monkeypatch, capsys):
    from limitless_tools.cli import main as cli_main

    code = cli_main.main(["fetch-audio", "--lifelog-id", "abc123"])
    out = capsys.readouterr().out
    assert code == 2

