# Changelog

All notable changes to ScamShield, newest first. Dates come from the
commit history; the prototype was built 2025-02 and hardened 2026-09.

## Unreleased (2026-09-16)

### Changed

- Survey screenshots moved under `docs/` with clean names:
  `docs/survey-charts.jpg` and `docs/survey-responses.jpg` (the space in
  the old `form 1.jpg` filename kept breaking tooling). README, PRD and
  AUDIT references updated.
- README prose rewritten in plainer language; no claim changed.
- Added this changelog.

## 2026-09-14

### Added

- Caller-number privacy (AUDIT #21): `caller_number` is stored only as a
  keyed HMAC-SHA256 hash, keyed by the `SCAMSHIELD_CALLER_KEY` environment
  variable. A missing or blank key fails the save with HTTP 503 and keeps
  the call session for retry; there is no plaintext fallback.
- Legacy plaintext caller numbers are scrubbed to NULL when the schema
  initializes.
- Retention: call records older than `CALL_RECORD_RETENTION_DAYS` (30
  days) are purged at every backend startup.

### Changed

- Test suite grew from 61 to 74 offline tests; core modules remain at
  100 % line coverage.

## 2026-09-09

### Added

- Offline pytest suite (61 tests, 100 % line coverage on `predict`,
  `backend`, `dataset_setup`, `db`, `config`) and a GitHub Actions
  workflow (uv, ruff, mypy, pytest with a >=90 % core-coverage gate).
- Project documentation: README rewrite, PRD, EVALUATION, AUDIT, AGENTS
  and a Python style guide.

### Fixed

- Prototype-blocking runtime bugs: undefined `call_id` in `detect_scam`,
  CWD-relative dataset paths, `evaluation_strategy` renamed to
  `eval_strategy` for transformers 5.x, invalid `language="auto"` STT
  call, import-time model loads, raw exception text in 500 responses,
  unbounded audio payloads (now capped at 10 MB), event-loop-blocking
  handlers, Gradio 6 CSS migration.
- README no longer publishes live Expo credentials (AUDIT #14; the owner
  still needs to rotate them on the Expo side).

### Removed

- A committed virtualenv (`Scripts/`, `share/`, `pyvenv.cfg`,
  `CACHEDIR.TAG`) and the unpinned `requirements.txt`, superseded by
  `pyproject.toml` + `uv.lock`.

## 2025-02-03 to 2025-02-08

- Initial prototype: FastAPI backend, DistilBERT training pipeline on a
  1,245-record dataset, Gradio interface, Expo frontend scaffold.
