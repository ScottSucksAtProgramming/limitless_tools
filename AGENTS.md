# Repository Guidelines

## Project Structure & Module Organization
- `limitless_tools/cli/main.py` — CLI entrypoints (`fetch`, `sync`, `list`, `export-markdown`, `fetch-audio` placeholder). Console script: `limitless`.
- `limitless_tools/http/` — `LimitlessClient` for API calls, pagination, and retries/Retry‑After.
- `limitless_tools/services/` — orchestration/business logic (`LifelogService`, `AudioService` placeholder).
- `limitless_tools/storage/` — local JSON persistence (`json_repo`), index merge, and sync state (`state_repo`).
- `limitless_tools/config/` — path defaults (`paths`) and env/timezone helpers (`env`).
- `limitless_tools/models/` — typed models for `Lifelog`/`ContentNode` (pydantic with a fallback shim in tests).
- `tests/unit/` — unit tests by layer; see examples.
- `docs/` — PRD, usage, and audio notes (`docs/PRD.md`, `docs/USAGE.md`, `docs/AUDIO.md`).

## Build, Test, and Development Commands
- Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`
- Test: `pytest -q` (filter with `-k pattern`).
- Lint: `ruff check .` (configured in `pyproject.toml`).
- Types: `mypy .` (Python 3.11, strict for src; relaxed for tests).
- Run CLI via module: `python -m limitless_tools.cli.main fetch --limit 5`
- Editable install + console script: `pip install -e .` then run `limitless ...`

## Coding Style & Naming Conventions
- Python 3.11+. Use type hints; keep functions small and pure.
- Indentation: 4 spaces; line length guide: 100 (Ruff ignores E501 but keep within 100 when reasonable).
- Names: `snake_case` for modules/functions/vars, `PascalCase` for classes, `UPPER_CASE` for constants.
- Imports: sorted via Ruff/isort; group stdlib/third‑party/first‑party (`limitless_tools`).

## Testing Guidelines
- Practice strict TDD. Write tests before implementation.
- Framework: `pytest`. Place tests under `tests/unit/` named `test_*.py`.
- Style: prefer one clear assertion per test; add docstrings describing behavior.
- Keep tests fast and isolated (fake sessions, no network).
- Run `pytest -q`; keep `ruff` and `mypy` advisory‑clean.

## Commit & Pull Request Guidelines
- Follow Conventional Commits: `type(scope): summary` (e.g., `feat(sync): add incremental state`).
- Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
- PRs must include: what/why, linked issue (if any), CLI examples if behavior changed, and confirmation that tests/lint/type checks pass.

## Security & Configuration
- Never commit secrets. Use `.env` (template: `.env.example`).
- Required env: `LIMITLESS_API_KEY`. Optional: `LIMITLESS_API_URL`, `LIMITLESS_DATA_DIR`, `LIMITLESS_TZ`.
- Example: `export LIMITLESS_API_KEY=... && limitless fetch --limit 10`.
- Data directories are user‑configurable; defaults to `~/limitless_tools/data/lifelogs`. Avoid committing local data.
