# Development Task List

Status: living document; update as work progresses. Practice TDD for every change.

## Completed Highlights

### Core product
- [x] Fetch, sync, list, search, export-markdown/export-csv, configure, and `fetch-audio` placeholder commands.
- [x] Date-partitioned JSON persistence, index merge, incremental state (cursor + lastEndTime), and search/index services.
- [x] HTTP client with retries, Retry-After handling, friendly errors, and timezone validation on the CLI.
- [x] Default fetch behavior (markdown/headings) plus feature toggles, batch-size tuning, and combined per-date exports.

### Reliability & security
- [x] Structured JSON logging with log levels, centralized error handling, and consistent exit codes.
- [x] Security baseline: CodeQL, pip-audit, bandit, base-URL allowlist, log redaction, detect-secrets hook/baseline.
- [x] CI runs ruff, mypy, pytest, packaging build + twine check + smoke install; branch protection enabled on `main`.

### Tooling & packaging
- [x] Editable install + console script, mypy scoped to `limitless_tools`, tests organized by layer.
- [x] Packaging metadata (SPDX license, URLs, keywords, `py.typed`) and fresh-venv packaging validation.
- [x] Importlib metadata version helper (`limitless_tools._version`), dev/test extras (`pip install -e ".[dev]"`), and `scripts/release_check.sh` automation.

### Documentation & repo hygiene
- [x] README badges, quick start, macOS/Linux support note, and links to docs (`PRD`, `USAGE`, `AUDIO`).
- [x] CHANGELOG, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, RELEASING, LICENSE, issue/PR templates, CODEOWNERS.
- [x] Repository published publicly with secret scanning enabled; `.env`/data ignored; docs/TASKS kept in repo.

## Outstanding for v0.1.0
- [ ] Confirm the `limitless-tools` name is available on (Test)PyPI; pick an alternative if needed.
- [ ] Dry-run the TestPyPI upload flow (`python -m twine upload --repository testpypi dist/*`) using artifacts from `scripts/release_check.sh`.
- [ ] Optional polish before/after launch: architecture diagram for docs, README badges for PyPI once the package is live, and any Windows-specific notes once tested.

## Ongoing Maintenance
- [ ] Monitor CI/security signals (CodeQL, Dependabot, pip-audit, bandit) and remediate true findings promptly.
- [ ] Keep CHANGELOG/README/docs aligned with behavior changes; add PyPI badges/examples after the first public release.
- [ ] Track Windows support work (path separators, timezone database availability) for a future milestone.

## Operational Checklists

### Pre-release quality gate (rerun for every tag)
- [ ] Run `scripts/release_check.sh` (ruff → mypy → pytest → build → twine check → fresh-venv wheel smoke test).
- [ ] Ensure `python -m pytest -q`, `ruff check .`, and `mypy limitless_tools` also pass individually if you need targeted debugging.
- [ ] Keep deterministic tool versions in `requirements-dev.txt`; refresh the virtualenv if anything drifts.

### Security posture
- [ ] `pip-audit` and `bandit -r limitless_tools` run in CI; re-run locally after dependency bumps.
- [ ] Dependabot monitors pip requirements (`.github/dependabot.yml`); keep GitHub security alerts enabled.
- [ ] Maintain the detect-secrets baseline; confirm `.env` and local data directories stay untracked.

### Release execution
- [ ] Work from a clean `main` with CI green; bump `version` in `pyproject.toml` and update `CHANGELOG.md`.
- [ ] Run `scripts/release_check.sh`; inspect artifacts under `dist/` and fix any issues.
- [ ] Tag (`git tag vX.Y.Z`) and push (`git push origin vX.Y.Z`).
- [ ] Upload to TestPyPI (for RCs/first release) then PyPI via `python -m twine upload dist/*`.
- [ ] Smoke-test `pipx install limitless-tools` (macOS/Linux) after PyPI upload; document Windows status as experimental until verified.
- [ ] Optional: evaluate a Homebrew tap that wraps the PyPI wheel in a venv once the package is stable.

### Post-release follow-up
- [ ] Publish GitHub release notes linked to CHANGELOG entries.
- [ ] Open issues for roadmap/backlog items; label good-first-issue candidates.
- [ ] Continue monitoring CI/security dashboards and schedule dependency updates as needed.

## Backlog
- [ ] Additional exporters (e.g., JSONL) and richer export filters.
- [ ] Promote Pydantic to a required runtime dependency once Python 3.11+ is firmly required everywhere (remove fallback shim).
- [ ] Support lifelog-by-id and related endpoints when the API is documented.
- [ ] Audio downloads: implement `AudioService` + `fetch-audio` once the upstream API ships.
- [ ] CLI polish: consistent `--json` support for all commands that output lists.
- [ ] Dockerfile for reproducible execution (optional).
- [ ] Documentation enhancements: architecture overview diagram, visuals for sync/index pipelines.
