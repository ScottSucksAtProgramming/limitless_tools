# limitless_tools

A Python 3.11+ library and CLI to fetch and store Limitless lifelogs locally as JSON. Built with TDD and clean, extensible architecture.

[![CI](https://github.com/ScottSucksAtProgramming/limitless_tools/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ScottSucksAtProgramming/limitless_tools/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ScottSucksAtProgramming/limitless_tools/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/ScottSucksAtProgramming/limitless_tools/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

- PRD: docs/PRD.md
- Default data dir: `~/limitless_tools/data/lifelogs` (configurable)

## Quick start

1) Create a virtual environment and install dev dependencies:

```
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

2) Configure environment (copy `.env.example` to `.env` and fill in values or export env vars):

```
export LIMITLESS_API_KEY=your_api_key
# export LIMITLESS_API_URL=https://api.limitless.ai
# export LIMITLESS_DATA_DIR=~/limitless_tools/data/lifelogs
```

3) Run tests:

```
python3 -m pytest -q
```

4) Fetch lifelogs (saves JSON files under the data dir):

```
python3 -m limitless_tools.cli.main fetch \
  --limit 10 \
  --direction desc \
  --include-markdown \
    --include-headings
```

## Installation

Once published, install the CLI with:

```
pip install limitless-tools
# or install it into an isolated environment:
pipx install limitless-tools
```

For local development you can keep an editable install around and run the console script directly:

```
pip install -e .
limitless --help
```

## Configuration

- Example config file: `config.toml.example` in this repo.
  - Default user path: `~/limitless_tools/config/config.toml`
  - Copy and edit: `mkdir -p ~/limitless_tools/config && cp config.toml.example ~/limitless_tools/config/config.toml`
  - Or pass a custom file with `--config /path/to/config.toml`.
- You can also write/update the config via CLI:

```
python -m limitless_tools.cli.main configure \
  --api-key YOUR_API_KEY \
  --data-dir ~/limitless_tools/data/lifelogs \
  --output-dir ~/limitless_tools/exports \
  --timezone UTC \
  --batch-size 50
```

Notes: You can define multiple profiles (e.g., `[default]`, `[work]`) and select with `--profile work`. Precedence: CLI flags > environment variables > config file > built‑in defaults.

## Notes

- Uses pagination with sensible defaults. See docs/PRD.md for detailed requirements and roadmap.
- TDD-first: tests are single-assert and documented for clarity.

## CLI at a glance

- `limitless fetch --limit 10 --direction desc` — fetch the latest entries with markdown/headings by default.
- `limitless sync --date 2025-11-01 --timezone UTC` — incremental sync that updates `index.json` and sync state.
- `limitless list --date 2025-11-01 --json` — list indexed lifelogs filtered by date and starred status.
- `limitless search --query "meeting notes" --regex` — search titles and markdown with regex or fuzzy matching.
- `limitless export-markdown --limit 5` / `--date YYYY-MM-DD --combine` — print or write markdown exports.
- `limitless export-csv --date 2025-11-01 --output /tmp/lifelogs.csv` — dump metadata (add `--include-markdown` to include body content).

## Documentation

- Usage guide: docs/USAGE.md
- PRD & roadmap: docs/PRD.md
- Audio research: docs/AUDIO.md
- Task tracker: docs/TASKS.md

## Links

- Changelog: CHANGELOG.md
- Contributing & workflow: CONTRIBUTING.md
- Security policy: SECURITY.md

## Code quality

- Ruff: a fast Python linter that aggregates many checks (pycodestyle/pyflakes/isort/pyupgrade) in one tool. It keeps the codebase consistent and catches common issues early.
- mypy: static type checker for Python. It enforces type hints to reduce runtime errors and improve maintainability.

Run locally:

```
ruff check .
mypy limitless_tools
```

## Security & Privacy

- No unexpected egress: the HTTP client enforces a base URL allowlist (default: `api.limitless.ai`, `localhost`, `127.0.0.1`).
  - Extend with `LIMITLESS_URL_ALLOWLIST="host1,host2"` or bypass with `LIMITLESS_ALLOW_UNSAFE_URLS=1` if you explicitly need it.
- Log redaction: secret‑like fields (e.g., `api_key`, `X-API-Key`, `authorization`, `token`, `password`, `secret`) are redacted as `[REDACTED]` in structured logs.
- Secret scanning: a `detect-secrets` pre‑commit hook and baseline are included.
  - Install hooks: `pre-commit install`
  - Run locally: `pre-commit run --all-files`
