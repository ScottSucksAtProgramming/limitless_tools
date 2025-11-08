# limitless_tools

A Python 3.11+ library and CLI to fetch and store Limitless lifelogs locally as JSON. Built with TDD and clean, extensible architecture.

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

## Notes

- Uses pagination with sensible defaults. See docs/PRD.md for detailed requirements and roadmap.
- TDD-first: tests are single-assert and documented for clarity.

## Code quality

- Ruff: a fast Python linter that aggregates many checks (pycodestyle/pyflakes/isort/pyupgrade) in one tool. It keeps the codebase consistent and catches common issues early.
- mypy: static type checker for Python. It enforces type hints to reduce runtime errors and improve maintainability.

Run locally:

```
ruff check .
mypy .
```

