# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
- README badge + installation guidance now point to the published PyPI package (pipx/venv instructions).

## [0.1.0] - 2025-11-14

### Added
- Initial CLI commands: `fetch`, `sync`, `list`, `search`, `export-markdown`, `export-csv`, `configure` (and `fetch-audio` placeholder)
- HTTP client with auth, retries/backoff, Retry‑After handling, and improved error messages
- Storage: date‑partitioned JSON persistence, index merge, and incremental sync state
- Services: lifelog pagination and orchestration
- Config: env/.env integration, TOML config with profiles and precedence, timezone helpers, JSON logging
- Local search over index (regex/fuzzy) and CSV/Markdown export features
- TDD unit tests across layers (client, services, storage, CLI)
- Pre‑release docs: CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, RELEASING
- GitHub issue and PR templates
- Package polish: importlib-based `__version__`, dev/test extras, automated `scripts/release_check.sh`, and docs noting macOS/Linux verification with Windows on the roadmap
