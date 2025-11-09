# Contributing to limitless_tools

Thanks for your interest in contributing! This project aims for clean, well‑tested, and maintainable code with a strong TDD workflow.

Please read and follow this guide. By participating, you agree to abide by our Code of Conduct (see CODE_OF_CONDUCT.md).

## Getting Started
- Python: 3.11+
- Create a virtual environment and install dev tools:

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

- Environment:
  - Required: `LIMITLESS_API_KEY`
  - Optional: `LIMITLESS_API_URL`, `LIMITLESS_DATA_DIR`, `LIMITLESS_TZ`
  - You may copy `.env.example` to `.env` (loaded automatically by the CLI)

## Development Workflow (TDD)
- Write tests first; keep them fast and isolated. One clear assertion per test.
- Place tests under `tests/unit/` and name files `test_*.py`.
- Run frequently:

```
python -m pytest -q
ruff check .
mypy .
```

## Linting & Types
- Lint: `ruff check .` (see `pyproject.toml` for rules)
- Types: `mypy .` (strict for `limitless_tools`, relaxed for tests via `mypy.ini`)
- Code style: 4‑space indent, type hints everywhere, keep lines ~100 chars when reasonable

## Running the CLI Locally
Examples (module entry):

```
python -m limitless_tools.cli.main fetch --limit 5 --json
python -m limitless_tools.cli.main sync --start 2025-01-01 --end 2025-01-31 --timezone UTC --json
python -m limitless_tools.cli.main list --date 2025-01-15 --json
python -m limitless_tools.cli.main search --query "text" --json
```

You can also do an editable install:

```
pip install -e .
limitless --help
```

## Commit Messages
- Follow Conventional Commits:
  - `feat(scope): add X`
  - `fix(scope): correct Y`
  - `docs(scope): update Z`
  - `refactor(scope): …`, `test(scope): …`, `chore(scope): …`
- Keep commits focused and small; explain the why in the body when helpful

## Pull Requests
- Ensure locally:
  - `ruff check .` passes
  - `mypy .` passes
  - `python -m pytest -q` is green
- Update `README.md`, `docs/`, and `CHANGELOG.md` when behavior changes
- Provide CLI examples if user‑facing behavior changed
- Link issues (if any) and describe what/why

## Code of Conduct
Please see `CODE_OF_CONDUCT.md`. Report unacceptable behavior per the Enforcement section.

## Questions / Help
Open a GitHub issue with context (environment, version, steps) or start a discussion thread if enabled.

