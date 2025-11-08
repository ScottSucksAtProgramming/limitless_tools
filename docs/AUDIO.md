# Audio Downloads (Research TODO)

Current status: The public OpenAPI in the official examples does not document audio download endpoints for lifelogs. The examples and docs we reviewed expose `GET /v1/lifelogs` with transcript-like content but no audio asset URLs.

Planned design:
- `limitless_tools.services.audio_service.AudioService`
  - `list_assets(lifelog_id: str) -> list[dict]`: enumerate downloadable audio segments for a lifelog.
  - `download(lifelog_id: str, target_dir: str, **opts) -> list[str]`: download audio files to a local directory.
- CLI: `limitless fetch-audio --lifelog-id <id> [--data-dir ...]` to download audio for a specific lifelog.

Open questions:
- Endpoint(s) for audio listing and download, content types (mp3/ogg/wav), and auth headers.
- Rate limits and range requests (partial downloads by time window?)
- Mapping between lifelog content nodes and audio segments.

Next steps:
- Monitor official docs and examples for audio endpoints.
- Once available, implement `AudioService` and wire the CLI.

