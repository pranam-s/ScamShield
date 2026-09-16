# Changelog

All notable changes to ScamShield, newest first. Dates come from the
commit history; the prototype was built 2025-02 and hardened 2026-09.

## Unreleased (2026-09-16)

### Security

- Dependabot triage (docs/AUDIT.md): 164 open alerts enumerated live (all
  npm, `frontend/package-lock.json`). 130 are stale — no locked version is
  inside the vulnerable range, Dependabot's scan predates the current lock;
  they should auto-close on its next scan. The 34 real ones (tar ×12,
  @xmldom/xmldom ×15, postcss ×4, uuid ×1, image-size ×2 no-fix) all sit in
  Expo 52 / RN 0.76 build-tooling paths whose fix is the Expo SDK 57 /
  React Native 0.87 upgrade — recorded as planned work. Safe set applied:
  `npm update` (expo 52.0.49 tree, ~2.7k lock lines refreshed) and
  non-breaking `npm audit fix` (expo-router 4.0.20, @expo/plist 0.2.2);
  `npm audit` findings 27 → 26. Gates: backend pytest 74/74 + ruff clean,
  frontend jest 1/1.

### Changed

- Survey screenshots moved under `docs/` with clean names:
  `docs/survey-charts.jpg` and `docs/survey-responses.jpg` (the space in
  the old `form 1.jpg` filename kept breaking tooling). README, PRD and
  AUDIT references updated.
- README prose rewritten in plainer language; no claim changed.
- Added this changelog.
- GitHub Actions disabled on this repository by owner decision (no paid
  Actions); the quality gates run locally, and a CI note in the README
  records how to re-enable with a self-hosted runner.

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
