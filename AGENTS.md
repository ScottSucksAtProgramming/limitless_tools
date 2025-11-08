# Repository Guidelines

## Project Structure & Module Organization
- `limitless_tools/cli/main.py` — CLI entrypoints (`fetch`, `sync`, `list`, `export-markdown`, `configure`, `fetch-audio` placeholder). Console script: `limitless`.
- `limitless_tools/http/` — `LimitlessClient` for API calls, pagination, retries/Retry‑After, and error messages.
- `limitless_tools/services/` — orchestration/business logic (`LifelogService`, `AudioService` placeholder).
- `limitless_tools/storage/` — local JSON persistence (`json_repo`), index merge, and sync state (`state_repo`).
- `limitless_tools/config/` — `paths.py` (defaults), `env.py` (.env + timezone helpers), `config.py` (TOML config + profiles), `logging.py` (JSON logging setup).
- `limitless_tools/models/` — typed models for `Lifelog`/`ContentNode` (pydantic with a fallback shim in tests).
- `tests/unit/` — unit tests by layer; see examples.
- `docs/` — PRD, usage, and audio notes (`docs/PRD.md`, `docs/USAGE.md`, `docs/AUDIO.md`).

## Build, Test, and Development Commands
- Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`
- Test: `python -m pytest -q` (filter with `-k pattern`). Using `python -m` ensures the venv’s Python runs pytest.
- Lint: `ruff check .` (configured in `pyproject.toml`).
- Types: `mypy .` (Python 3.11, strict for src; relaxed for tests).
- Run CLI via module:
  - Fetch: `python -m limitless_tools.cli.main fetch --limit 5 [--json] [--batch-size 50]`
  - Sync: `python -m limitless_tools.cli.main sync --start 2025-01-01 --end 2025-01-31 --timezone UTC [--json]`
  - List: `python -m limitless_tools.cli.main list --date 2025-01-15 --json`
  - Configure: `python -m limitless_tools.cli.main configure --api-key KEY --data-dir /path`
  - Pass `--profile work` or env `LIMITLESS_PROFILE=work` to select a config profile
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
- Never commit secrets. Use `.env` (template: `.env.example`). CLI auto-loads `.env` from CWD/parents at startup.
- Required env: `LIMITLESS_API_KEY`. Optional: `LIMITLESS_API_URL`, `LIMITLESS_DATA_DIR`, `LIMITLESS_TZ`.
- Config default path: `~/limitless_tools/config/config.toml` with profiles as sections `[default]`, `[work]`, etc.
- Override config path/profile via flags `--config`/`--profile` or env `LIMITLESS_CONFIG`/`LIMITLESS_PROFILE`.
- Precedence: CLI flags > environment variables > config file > built‑in defaults.
- Example: `export LIMITLESS_API_KEY=... && limitless fetch --limit 10`.
- Data directories are user‑configurable; default `~/limitless_tools/data/lifelogs`. Avoid committing local data.
- Timezone validation for `sync`: must be a valid IANA name; invalid values exit with code 2.
- Logging: use `--verbose` for JSON debug logs to stderr.
