# Development Task List

Status: living document; update as work progresses. Use TDD for every task.

## Done
- Fetch lifelogs (pagination) and store JSON (date‑based folders)
- CLI commands: `fetch`, `sync`, `list`, `export-markdown`
- Index generation and merge on sync
- Incremental state: lastEndTime resume; cursor resume
- HTTP retries/backoff with Retry‑After support
- Default fetch includes markdown/headings; `--no-include-*` toggles
- Editable install (`pip install -e .`) and console script `limitless`
- Usage docs (docs/USAGE.md) and audio plan (docs/AUDIO.md)
- TDD tests across client, services, storage, CLI
- Env integration in CLI: call `load_env()` at startup so `.env` is always honored
 - Structured logging and log levels (`--verbose`)
 - Improve error messages for non‑retryable 4xx/5xx

## In Progress / Next Up
- Document/guard timezone behavior in CLI help; validate IANA names
- Performance: tune batch size defaults; add `--batch-size`
- User-scoped config file (TOML via platformdirs) with precedence: CLI flags > env > config; support `--config`/`--profile` (MVP)

## Backlog
- Local search over index (by title/date/star/keywords)
- Additional exporters (JSONL, CSV) and richer export filters
- Pydantic as a strong runtime dependency once Python 3.11+ baseline is ensured (remove fallback shim)
- Per‑signature state tracking (separate cursors/lastEndTime by parameter set)
- Support lifelog‑by‑id and related endpoints when documented
- Audio downloads: implement `AudioService` + `fetch-audio` once API is published
- CLI polish: consistent `--json` for commands that produce listings
- Packaging & CI: GitHub Actions (tests + ruff + mypy), Dockerfile (optional) post‑MVP
- Documentation: architecture overview diagram, contribution guide
