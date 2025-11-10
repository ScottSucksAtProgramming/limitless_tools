# Development Task List

Status: living document; update as work progresses. Use TDD for every task.

## Done
- Fetch lifelogs (pagination) and store JSON (date‑based folders)
- CLI commands: `fetch`, `sync`, `list`, `search`, `export-markdown`, `export-csv`, `configure` (and `fetch-audio` placeholder)
- Index generation and merge on sync
- Incremental state: lastEndTime resume; cursor resume; per‑signature state tracking
- HTTP retries/backoff with Retry‑After support
- Default fetch includes markdown/headings; `--no-include-*` toggles
- Editable install (`pip install -e .`) and console script `limitless`
- Usage docs (docs/USAGE.md) and audio plan (docs/AUDIO.md)
- TDD tests across client, services, storage, CLI
- Local search over index (title/markdown) + `search` CLI (regex/fuzzy)
- CSV export with optional markdown column
- Combined per‑date Markdown export (`export-markdown --date ... --write-dir ... --combine`)
- Env integration in CLI: auto‑load `.env` at startup
- Structured JSON logging and log levels (`--verbose`)
- Improved error messages for non‑retryable 4xx/5xx
- Timezone validation in CLI (IANA names) and documented behavior
- Performance: tuned defaults; added `--batch-size`
- User-scoped config file (TOML) with precedence: CLI flags > env > config; `--config`/`--profile`
- Security baseline:
  - CodeQL workflow
  - Dependency audit with `pip-audit` (CI)
  - Static analysis with `bandit` (CI)
  - Base URL allowlist to prevent unexpected egress
  - Log redaction of secret-like fields
  - detect-secrets pre-commit hook and baseline
- CI: ruff, mypy, pytest; packaging job builds wheels and runs twine check + smoke install
- Repo docs and templates: LICENSE (MIT), CHANGELOG, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, RELEASING, issue/PR templates, CODEOWNERS
- README badges added (CI, CodeQL, License) and Security section documented
- Packaging metadata modernized (SPDX license + license-files) and `py.typed` included
- Local packaging validation performed (build sdist/wheel, twine check, 3.11+ smoke install)
- Pre-commit configured (ruff, mypy, detect-secrets)
- Mypy scoped to src (`mypy limitless_tools`); tests remain relaxed

## In Progress / Next Up
- Release preparation on public GitHub (create repo, push code/history, enable branch protection & secret scanning)
- TestPyPI dry run then PyPI publish for v0.1.0
- Optional docs polish (architecture diagram, README badges for PyPI after publish)

## Pre‑Release Quality Gate (local)
 - Ruff clean: `ruff check .` (resolve all findings or add explicit ignores with rationale)
 - Mypy clean: `mypy limitless_tools` (focus on src)
- Tests green: `python -m pytest -q`
- Pre‑commit hooks: add `.pre-commit-config.yaml` to run ruff, mypy, and pytest on commit/push
- Pin deterministic local tooling versions where helpful (e.g., ruff/mypy in `requirements-dev.txt`)

## Security & Vulnerability (local + CI)
- Dependency audit: `pip-audit` runs in CI (and can be run locally)
- Static analysis: `bandit -r limitless_tools` runs in CI
- Dependabot for pip configured (`.github/dependabot.yml`); enable GH security alerts on repo
- Secrets: use detect-secrets pre-commit; verify no secrets or local data are committed; `.env`/data paths are gitignored

## Packaging & Distribution Prep (local)
Completed:
- Build/publish tools added to dev deps (`build`, `twine`)
- Metadata confirmed in `pyproject.toml` (license SPDX, classifiers, keywords, `project.urls`)
- License files included in sdist (via `project.license-files`)
- `py.typed` provided for type hints
- Artifacts built and checked (`python -m build`; `twine check dist/*`)
- Smoke install verified in a Python 3.11+ venv

Remaining:
- Verify project name availability on (Test)PyPI; adjust if needed
- Prepare TestPyPI publish flow: `twine upload --repository testpypi dist/*`

## Documentation & Files (completed)
- LICENSE (MIT)
- CHANGELOG.md (Keep a Changelog; version initialized `0.1.0`)
- CONTRIBUTING.md (env setup, commands, coding style, tests, TDD)
- CODE_OF_CONDUCT.md (Contributor Covenant)
- SECURITY.md (how to report vulnerabilities; supported versions)
- RELEASING.md (tagging, build, TestPyPI/PyPI, Homebrew notes)
- README: badges (CI, CodeQL, License), quick start, link to `docs/USAGE.md`, Security section
- Issue/PR templates and CODEOWNERS

## CI Workflow (prepared locally; activates after GitHub push)
- `.github/workflows/ci.yml`: Ubuntu, Python 3.11, `TZ=UTC`, pip cache, ruff, mypy, pytest
- Packaging job: build sdist/wheel, `twine check`, smoke install
- Security job: `pip-audit` and `bandit`
- Pin action versions; keep workflow minimal and fast

## Release Prep (public GitHub)
- Create a new public GitHub repository (manual) and push code/history
- Open initial PR (optional) to verify CI passes in GitHub environment
- Enable branch protection on `main` (require CI to pass before merge)
- Add README badges that reference the new repo URLs
- Adopt SemVer and Conventional Commits; document mapping in CONTRIBUTING/RELEASING
- Ensure CI green on main commit to be tagged; cut from a clean tree
- Bump version to `0.1.0`, update CHANGELOG, create tag `v0.1.0`; generate GitHub release notes

## Publish & Distribution
- PyPI: create account + API token; test publish to TestPyPI, then publish to PyPI
- Verify installation on a clean machine with `pipx install limitless-tools` (recommended for CLI)
- Homebrew (optional):
  - Evaluate packaging route: pipx recommendation vs. Homebrew formula
  - If Homebrew: create a tap with a `brew` formula using Python virtualenv and vendored resources; reference PyPI sdist and dependencies with SHA256; test on macOS

## Post‑Release
- Create GitHub release notes; link PRs/issues
- Open issues for backlog items and roadmap; label good‑first‑issue
- Monitor CI and vulnerability scans; schedule dependency updates

## Backlog
- Additional exporters (JSONL) and richer export filters
- Pydantic as a strong runtime dependency once Python 3.11+ baseline is ensured (remove fallback shim)
- Support lifelog‑by‑id and related endpoints when documented
- Audio downloads: implement `AudioService` + `fetch-audio` once API is published
- CLI polish: consistent `--json` for commands that produce listings
- Dockerfile for reproducible runs (optional)
- Documentation: architecture overview diagram
