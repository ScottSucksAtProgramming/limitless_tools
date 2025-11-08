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

Optional: copy `.env.example` to `.env` and fill in variables. The CLI automatically loads `.env` from the current directory (or parents) on startup, so environment-based defaults like `LIMITLESS_DATA_DIR` and `LIMITLESS_API_KEY` are honored without extra flags. You can also export environment variables in your shell.

## Editable install (optional)

Install the package locally to get a `limitless` CLI command:

```
pip install -e .

# Now you can run the CLI as a command
limitless fetch --limit 5
```

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

All commands read `LIMITLESS_API_KEY` from the environment. Default data dir is `~/limitless_tools/data/lifelogs` (override with `--data-dir` or `LIMITLESS_DATA_DIR`). Default batch size is `50` (override with `--batch-size`).

- Fetch latest N lifelogs (saves JSON files): defaults include markdown and headings. Use `--json` to print a JSON array of saved item summaries to stdout.

```
python -m limitless_tools.cli.main fetch \
  --limit 10 \
  --direction desc \
  --batch-size 50

# To disable markdown or headings explicitly:
#   --no-include-markdown
#   --no-include-headings

# If you installed with `pip install -e .`, you can also run:
# limitless fetch --limit 10 --direction desc
```

- Search local lifelogs by keyword (matches title and markdown). Supports regex and fuzzy search.

```
python -m limitless_tools.cli.main search \
  --query meeting \
  --date 2025-07-01 \
  --starred-only \
  --data-dir /path/to/lifelogs \
  --json

# Without --json, prints lines like:
# 2025-07-01T00:00:00Z S1 Weekly Meeting Notes

# Regex and fuzzy examples
python -m limitless_tools.cli.main search --query "meet.*notes" -rg --data-dir /path
python -m limitless_tools.cli.main search --query "Weekly Meeting" --fuzzy --fuzzy-threshold 80 --json
```

### Configuration file (MVP)

You can store defaults in a user config TOML and select profiles via `--profile`:

- Default path: `~/limitless_tools/config/config.toml`
- Override path with `--config` or `LIMITLESS_CONFIG` env var.
- Select a profile with `--profile` or `LIMITLESS_PROFILE` env var (default: `default`).
- Precedence: CLI flags > environment variables > config file > built-in defaults.

Example `config.toml`:

```
[default]
api_key = "YOUR_API_KEY"
data_dir = "/path/to/lifelogs"
timezone = "UTC"
batch_size = 50

[work]
api_key = "WORK_API_KEY"
data_dir = "/work/data/lifelogs"
timezone = "America/Los_Angeles"
batch_size = 100
```

Use a profile:

```
python -m limitless_tools.cli.main --profile work fetch --limit 5
```

## Configure via CLI

You can write or update your config file non-interactively:

```
# Write to default path (~/limitless_tools/config/config.toml), default profile
python -m limitless_tools.cli.main configure \
  --api-key YOUR_API_KEY \
  --data-dir /path/to/lifelogs \
  --timezone UTC \
  --batch-size 50

# Write to a custom file and profile
python -m limitless_tools.cli.main --config /tmp/cfg.toml --profile work configure \
  --api-key WORK_API_KEY --data-dir /work/lifelogs --batch-size 100
```

## JSON Output Examples

```
# Fetch with JSON output
python -m limitless_tools.cli.main fetch --limit 2 --json
[
  {"id": "a", "title": "...", "startTime": "...", "endTime": "...", "path": "/.../lifelog_a.json"},
  {"id": "b", "title": "...", "startTime": "...", "endTime": "...", "path": "/.../lifelog_b.json"}
]

# Sync with JSON output
python -m limitless_tools.cli.main sync --start 2025-01-01 --end 2025-01-02 --json
{
  "saved_count": 2,
  "lastCursor": "CUR123",
  "lastEndTime": "2025-01-02T01:00:00Z",
  "items": [
    {"id": "a", "title": "...", "startTime": "...", "endTime": "...", "path": "/.../lifelog_a.json"},
    {"id": "b", "title": "...", "startTime": "...", "endTime": "...", "path": "/.../lifelog_b.json"}
  ]
}
```

- Sync by date or date range (writes `index.json` and updates incremental state). Use `--json` to print a status object to stdout including `saved_count`, `lastCursor`, `lastEndTime`, and `items`.

```
python -m limitless_tools.cli.main sync \
  --start 2025-01-01 --end 2025-01-31 --timezone America/Los_Angeles \
  --batch-size 100

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

- Export combined markdown for a specific date to a single file (good for Obsidian):

```
python -m limitless_tools.cli.main export-markdown \
  --date 2025-11-01 \
  --data-dir /path/to/lifelogs \
  --write-dir /path/to/obsidian/vault \
  --combine
```

- Export CSV metadata (optionally include markdown):

```
python -m limitless_tools.cli.main export-csv \
  --date 2025-12-01 \
  --data-dir /path/to/lifelogs \
  --include-markdown \
  --output /tmp/lifelogs_2025-12-01.csv
```

## Bulk export script

For exporting many days at once (e.g., to an Obsidian vault), use the helper script:

```
python scripts/export_markdown_range.py \
  --start 2025-01-01 \
  --end 2025-12-31 \
  --data-dir /path/to/lifelogs \
  --out-dir /path/to/obsidian/vault \
  --frontmatter       # optional

# Writes files like: /path/to/obsidian/vault/2025-01-01_lifelogs.md
```

## Notes

- The `sync` command maintains an incremental state file at `../state/lifelogs_sync.json` relative to your lifelogs data dir. On subsequent runs, if no `--start` is provided, it uses the last recorded end time as `start` to avoid re-fetching.
- To include markdown/headings for fetch(), pass `--include-markdown` and `--include-headings` (the `sync` command includes both by default).
- The `search` command reads a lightweight index when present to filter by date/starred quickly, and opens files as needed to match against markdown. Regex uses case-insensitive `re`, fuzzy uses `rapidfuzz` when available (falls back to `difflib`).
- The `sync` command tracks resume info per‑signature of parameters (date/start/end/timezone/is_starred), preventing different sync modes from clobbering each other.
