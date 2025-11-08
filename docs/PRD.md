# Project Requirements Document (PRD)

Project: limitless_tools

Version: 1.0 (Draft finalized)

Date: 2025-11-08

Owner: You (repo maintainer)

---

## 1. Summary

Build a Python 3.11+ library and CLI that syncs user lifelogs from the Limitless Developer API to the local filesystem in JSON format. The system will prioritize Test-Driven Development (TDD), clean OOP design, and extensibility for future endpoints (e.g., audio assets). Data will be written as individual JSON files organized by date, with a configurable root data directory defaulting to `~/limitless_tools/data/lifelogs`.

Key capabilities v1:
- Authenticate with API key via header `X-API-Key`.
- Fetch lifelogs using `GET https://api.limitless.ai/v1/lifelogs` with pagination.
- Store each lifelog as canonical JSON (exact API fields) under date-based folders.
- Provide a CLI and a Python library interface.
- TDD-first implementation with extensive unit tests and user-story-driven tests.

Future-oriented:
- Optional downloads for additional artifacts (e.g., audio files) if/when API exposes endpoints.
- Extensible service architecture to add more API domains without breaking existing code.

Non-goals (initial):
- Cloud database or hosted backend.
- Web UI.

---

## 2. Constraints and Principles

- Language/runtime: Python 3.11+
- Mode: Library + CLI
- Architecture: OOP; clean, modular layers; typed models
- Development process: Strict TDD (write tests first), single-assert-per-test, well-documented tests
- Env management: `venv`; local git repository; `.env` template committed; `.env` ignored
- Defaults: Data directory `~/limitless_tools/data/lifelogs` (user-overridable)
- Performance: Respect API limits (expect ~10 lifelogs per page); efficient pagination and sensible defaults
- Security: Do not log secrets; API key from env/.env; no secrets committed

---

## 3. User Stories

- As a user, I can configure my API key and default timezone and fetch lifelogs.
- As a user, I can fetch lifelogs for a date or date range, with automatic pagination.
- As a user, I can choose which fields/artifacts to download (markdown, headings, raw content, and—when available—audio files), with everything available by default.
- As a user, I can run incremental syncs (date range initially; cursor/time-window support planned) to avoid re-fetching unchanged data.
- As a user, I can store lifelogs as individual JSON files under date-based directories for easy navigation.
- As a user, I can list locally stored lifelogs and filter by date/starred.
- As a user, I can export lifelog markdown from my local store.

---

## 4. API Overview (from official examples + OpenAPI)

- Base URL: `https://api.limitless.ai/`
- Auth: Header `X-API-Key: <YOUR_API_KEY>`
- Endpoint (v1): `GET /v1/lifelogs`
  - Parameters (query):
    - `timezone` (string, IANA) – default to local if missing
    - `date` (YYYY-MM-DD) – all entries beginning on the date in the timezone
    - `start`, `end` (ISO-like) – start/end datetimes; offsets ignored
    - `cursor` (string) – pagination cursor
    - `direction` (asc|desc) – default desc
    - `includeMarkdown` (bool) – default true
    - `includeHeadings` (bool) – default true
    - `limit` (int) – page size; API currently limits around 10
    - `isStarred` (bool) – filter starred
- Pagination: `meta.lifelogs.nextCursor` when more results are available

Notes
- The public examples and OpenAPI focus on lifelogs. Other endpoints (e.g., audio assets) are not in the provided spec and will be researched as part of expansion.

---

## 5. Data Schema (canonical, per OpenAPI)

Lifelog (object):
- `id` (string): unique identifier
- `title` (string): title, equals first heading1 node
- `markdown` (string|null): raw markdown content
- `contents` (ContentNode[]): list of structured nodes
- `startTime` (ISO-8601 string)
- `endTime` (ISO-8601 string)
- `isStarred` (boolean)
- `updatedAt` (ISO-8601 string)

ContentNode (object):
- `type` (string): e.g., heading1, heading2, heading3, blockquote, paragraph (extensible)
- `content` (string)
- `startTime` (ISO-8601 string)
- `endTime` (ISO-8601 string)
- `startOffsetMs` (integer)
- `endOffsetMs` (integer)
- `children` (ContentNode[])
- `speakerName` (string|null)
- `speakerIdentifier` ("user"|null)

Response shape:
- `data.lifelogs` (Lifelog[])
- `meta.lifelogs.count` (int)
- `meta.lifelogs.nextCursor` (string|null)

Storage augmentations (local-only, optional):
- `fetchedAt` (ISO-8601 string): when we fetched it
- `sourceVersion` (string): internal client version

---

## 6. Local File Layout

- Root data dir (default): `~/limitless_tools/data/lifelogs` (configurable)
- Per-lifelog JSON file under date folders:
  - `~/limitless_tools/data/lifelogs/YYYY/MM/DD/lifelog_{id}.json`
  - Contents: exact API JSON (canonical), plus optional `fetchedAt` and `sourceVersion` meta
- Optional local index: `~/limitless_tools/data/lifelogs/index.json`
  - Array of `{ id, startTime, endTime, title, isStarred, updatedAt, path }`
- Optional sync state: `~/limitless_tools/data/state/lifelogs_sync.json`
  - Tracks last cursors/time windows keyed by query signature

Idempotency & updates
- If a lifelog with same `id` exists and `updatedAt` differs, overwrite the file.

---

## 7. Architecture

Layers (packages):
- `limitless_tools.config` – load env/.env and CLI overrides; resolve paths
- `limitless_tools.http` – `LimitlessClient` (requests session, headers, retry/backoff)
- `limitless_tools.models` – `Lifelog`, `ContentNode` (pydantic), typed responses
- `limitless_tools.services` – `LifelogService` (pagination, query assembly)
- `limitless_tools.storage` – `JsonFileRepository`, `IndexRepository`, `StateRepository`
- `limitless_tools.sync` – `LifelogSynchronizer` (orchestrates fetch→dedupe→persist→index)
- `limitless_tools.cli` – CLI entrypoints (argparse or Typer) wired to services
- `limitless_tools.utils` – logging, time, paths

Extensibility
- Add new domains (e.g., audio assets) with new `services/models` and storage handlers.
- `LimitlessClient` exposes `get(path, params)` used across services.

---

## 8. Functional Requirements

Authentication
- Read API key from env `LIMITLESS_API_KEY` or `.env`.
- Optional `LIMITLESS_API_URL` override (default `https://api.limitless.ai`).

Fetch lifelogs
- Support: `date`, `start`, `end`, `timezone`, `direction`, `includeMarkdown`, `includeHeadings`, `limit`, `isStarred`.
- Paginate until exhausted; respect API page size (~10).
- Sensible defaults: local timezone via `tzlocal`; `direction=desc`; `includeMarkdown=true`; `includeHeadings=true`.

Storage
- Persist one JSON per lifelog; date-based directory structure.
- Deduplicate by `id`; update on `updatedAt` change.
- Optional index/state files.

Incremental sync
- v1: Date-range sync (`--start`/`--end` or `--date`).
- Planned: Cursor-based resume and last-time-window resume, saved in state file.

Config
- CLI flags override env values; `.env` supported via `python-dotenv`.
- Data directory configurable; default `~/limitless_tools/data/lifelogs`.

CLI (initial)
- `limitless fetch` – fetch latest N lifelogs; flags: `--limit`, `--direction`, `--include-markdown`, `--include-headings`, `--starred-only`.
- `limitless sync` – sync by date/date-range: flags: `--date` | `--start` `--end`, `--timezone`.
- `limitless list` – list local lifelogs; flags: `--date`, `--starred-only`, `--json`.
- `limitless export-markdown` – print markdown for latest N from local or directly from API.
- Global: `--api-key`, `--api-url`, `--data-dir`, `--quiet`, `--verbose`.

Downloads & coverage selection
- Everything available by default (`markdown`, `contents`).
- Add flags/toggles to select artifacts at fetch time.
- Audio files: research and add when API endpoints are known (see TODOs).

Error handling (initial)
- Clear exceptions for 4xx (except 429) and 5xx with retry logic.
- Avoid logging secrets; structured logs where useful.

---

## 9. Non-Functional Requirements

Reliability
- Retry/backoff on 429/5xx; respect `Retry-After` when present.

Performance
- Batch/page size configurable; defaults to API limit.
- Avoid unnecessary re-writes.

Security
- API key via env/.env; never logged; `.env` ignored by git; `.env.example` committed.

Portability
- macOS/Linux; Python 3.11+.

Observability
- Log levels; `--verbose` for debug.

---

## 10. TDD Strategy and Test Plan

Principles
- Write tests first; small, incremental cycles.
- Single assert per test to pinpoint failures.
- Tests must be well-documented: docstring describing scenario and expectation.

Structure
- `tests/unit/` – modules by layer (`test_http_client.py`, `test_lifelog_service.py`, `test_storage.py`, etc.)
- `tests/story/` – user-story scenarios (e.g., fetch latest N, sync date range, list local, export markdown).
- Fixtures – static JSON responses for lifelogs (with pagination, edge cases, error codes).

Coverage (initial)
- HTTP client: headers, auth, retries, error paths.
- Service: param assembly, pagination (cursor), limits.
- Storage: path resolution, write/update idempotency, index/state handling.
- CLI: argument parsing, wiring to services, basic output.

Tooling
- `pytest` for tests; `pytest-cov` optional.
- Type checking via `mypy`.
- Linting via `ruff`.

---

## 11. Development Plan

Prototype
1) Minimal `LimitlessClient.get_lifelogs()` with pagination; store latest N to JSON under date folders.
2) CLI `limitless fetch --limit N` using env API key.
3) TDD: unit tests for client pagination; storage write; CLI parses/dispatches.

MVP
1) `sync` command for date/date-range with timezone; local index/state files.
2) `list` and `export-markdown` commands.
3) Config/flags (`--data-dir`, `--include-markdown`, `--include-headings`, `--starred-only`).
4) Retries/backoff; robust error handling.
5) Extensive unit tests plus story tests reflecting user stories.

Expansion
1) Add incremental resume strategies: cursor-based and last-time-window state.
2) Research and add audio file downloads if API supports it; generalize “artifact downloaders”.
3) Optional: search across local index; Dockerfile and CI when packaging.
4) Add additional API resources as they are documented.

Acceptance criteria
- Prototype: Can fetch and store N lifelogs to dated JSON files; tests passing.
- MVP: Supports date-range sync, listing, markdown export, and index/state; tests passing.
- Expansion: Audio/artifact downloaders (if API available) and advanced resume; tests passing.

---

## 12. Risks and Mitigations

- API evolution: Wrap responses in models; store canonical raw JSON; version client.
- Rate limits: Exponential backoff, jitter, respect Retry-After, allow tuning page size.
- Timezones: Default from system via `tzlocal`; allow override; document behavior.
- Large volumes: Date-partitioned storage; avoid re-writes; index file for faster scans.

---

## 13. Configuration

Environment variables
- `LIMITLESS_API_KEY` (required)
- `LIMITLESS_API_URL` (optional; default `https://api.limitless.ai`)
- `LIMITLESS_TZ` (optional; default local tz if absent)

Files
- `.env.example` committed with placeholders.
- `.env` ignored by git.

---

## 14. TODOs (Research / Follow-ups)

- Audio assets
  - Investigate whether lifelogs expose audio URLs or separate endpoints for audio retrieval (not in provided OpenAPI).
  - If available: design `AudioService` + downloader with configurable storage (e.g., `~/limitless_tools/data/audio/YYYY/MM/DD/{lifelogId}_{segmentId}.ogg`).
  - Add CLI flag `--include-audio` and/or a dedicated `limitless fetch-audio`.
- Additional endpoints
  - Identify future API resources (lifelog-by-id, attachments, highlights, webhooks) and plan services/models accordingly.
- Packaging & CI
  - Add packaging (pyproject), Dockerfile, and CI once core functionality stabilizes.

---

## 15. CLI Naming Note

The project is named `limitless_tools`. The CLI will be exposed as `limitless` for brevity. If conflicts arise, we can also provide an alias `limitless-tools` during packaging.

