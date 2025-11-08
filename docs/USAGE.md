# Usage

This project provides a Python library and CLI to fetch and store Limitless lifelogs locally using TDD-built components.

## Prerequisites

- Python 3.11+
- A Limitless API key (set `LIMITLESS_API_KEY`)

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Optional: copy `.env.example` to `.env` and fill in variables, or export environment variables in your shell.

## Running tests

```
python -m pytest -q
```

Run linters/type checks:

```
ruff check .
mypy .
```

## CLI commands

All commands read `LIMITLESS_API_KEY` from the environment. Default data dir is `~/limitless_tools/data/lifelogs` (override with `--data-dir` or `LIMITLESS_DATA_DIR`).

- Fetch latest N lifelogs (saves JSON files):

```
python -m limitless_tools.cli.main fetch \
  --limit 10 \
  --direction desc \
  --include-markdown \
  --include-headings
```

- Sync by date or date range (writes `index.json` and updates incremental state):

```
python -m limitless_tools.cli.main sync \
  --start 2025-01-01 --end 2025-01-31 --timezone America/Los_Angeles

# or a single day
python -m limitless_tools.cli.main sync --date 2025-01-15
```

- List local lifelogs:

```
python -m limitless_tools.cli.main list --date 2025-01-15 --starred-only --json
```

- Export markdown from the latest N local lifelogs:

```
python -m limitless_tools.cli.main export-markdown --limit 5
```

## Notes

- The `sync` command maintains an incremental state file at `../state/lifelogs_sync.json` relative to your lifelogs data dir. On subsequent runs, if no `--start` is provided, it uses the last recorded end time as `start` to avoid re-fetching.
- To include markdown/headings for fetch(), pass `--include-markdown` and `--include-headings` (the `sync` command includes both by default).

