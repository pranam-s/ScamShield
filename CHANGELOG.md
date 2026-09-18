# Changelog

All notable changes to ScamShield, newest first. Dates come from the
commit history; the prototype was built 2025-02 and hardened 2026-09.

## 2026-09-18 (SDK 57 upgrade and hardening)

### Added

- **Expo SDK 52 → 57** (docs/adr/0001): expo 57.0.24, React Native 0.86.3,
  React 19.2.3, jest-expo 57.0.5, aligned via `expo install --fix`;
  `expo-asset` and `react-native-worklets` peers installed;
  `expo-doctor` 21/21. Clears the dependency tree the 34 remaining
  Dependabot alerts were gated on (re-scan happens post-push).
- Recording migrated from expo-av to **expo-audio** (`useAudioRecorder`,
  `AudioModule` permissions); chunk reading moved to expo-file-system's
  `File.arrayBuffer()` + a Hermes `btoa` encoder (the legacy
  `readAsStringAsync` now throws at runtime in the SDK 57 root export).
- Frontend CI job (npm ci → tsc → jest → knip) alongside the Python
  matrix; all commands executed locally and green. Actions stay
  disabled on GitHub (zero-spend policy).
- docs/design.md (HLD + LLD), docs/BUILD_LOG.md,
  docs/style-guides/typescript-react-native.md, docs/STATUS.md, ADR-0001,
  and real screenshots from the SDK 57 web export in docs/screenshots/.

### Fixed

- The 12 sqlite3 "default datetime adapter is deprecated" warnings:
  timestamps now cross the boundary as `YYYY-MM-DD HH:MM:SS` strings via
  `db.to_sqlite_timestamp`, shared with the retention purge. Suite went
  from 15 warnings to 2 (both upstream-internal, documented in
  docs/STATUS.md); the dev `httpx` dependency became `httpx2` per
  starlette's testclient migration.
- Accessibility: call status is conveyed by text as well as colour,
  dial-pad keys expose `keyboardkey` role with labels, icon-only buttons
  and settings switches carry labels, colour-only emoji bullets removed
  from the education screen.
- Call screen's action image rendered unstyled at full intrinsic size;
  style applied and verified in a browser run.
- Frontend dead code: 7 unused template components deleted; 9 unused
  dependencies removed (@react-navigation/*, axios, expo-linear-gradient,
  expo-status-bar, expo-symbols, expo-web-browser, expo-system-ui);
  Knip configured (`frontend/knip.json`) and clean. Backend: deptry +
  vulture adopted, and the directly-imported pydantic/numpy are now
  declared instead of riding transitively.
- `app.json` renamed from the template placeholder ("expo@latest" failed
  SDK 57's slug schema) to ScamShield; `newArchEnabled` removed
  (New Architecture is the only mode in SDK 57).
- The frontend detection endpoint no longer points at a dead ngrok URL
  (AUDIT #19): backend address lives in `frontend/constants/Api.ts`.

## Unreleased (2026-09-16)

### Security

- Dependabot triage (docs/AUDIT.md): 164 open alerts enumerated live (all
  npm, `frontend/package-lock.json`). 130 are stale: no locked version is
  inside the vulnerable range, Dependabot's scan predates the current lock;
  they should auto-close on its next scan. The 34 real ones (tar ×12,
  @xmldom/xmldom ×15, postcss ×4, uuid ×1, image-size ×2 no-fix) all sit in
  Expo 52 / RN 0.76 build-tooling paths whose fix is the Expo SDK 57 /
  React Native 0.87 upgrade, recorded as planned work. Safe set applied:
  `npm update` (expo 52.0.49 tree, ~2.7k lock lines refreshed; axios
  1.7.9 → 1.20.0, uuid 11.0.5 → 11.1.1) and non-breaking `npm audit fix`
  (expo-router 4.0.17 → 4.0.20, @expo/plist 0.2.1 → 0.2.2);
  `npm audit` findings 60 → 26 (26 re-verified on a clean `npm ci`).
  Gates: backend pytest 74/74 + ruff clean, frontend jest 1/1. Numbers
  independently re-verified 2026-09-17 (docs/AUDIT.md).

### Changed

- Survey screenshots moved under `docs/` with clean names:
  `docs/survey-charts.jpg` and `docs/survey-responses.jpg` (the space in
  the old `form 1.jpg` filename kept breaking tooling). README, PRD and
  AUDIT references updated.
- README prose rewritten in plainer language; no claim changed.
- Added this changelog.
- GitHub Actions disabled on this repository (no paid
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
- README no longer publishes live Expo credentials (AUDIT #14; rotation
  on the Expo side is still outstanding).

### Removed

- A committed virtualenv (`Scripts/`, `share/`, `pyvenv.cfg`,
  `CACHEDIR.TAG`) and the unpinned `requirements.txt`, superseded by
  `pyproject.toml` + `uv.lock`.

## 2025-02-03 to 2025-02-08

- Initial prototype: FastAPI backend, DistilBERT training pipeline on a
  1,245-record dataset, Gradio interface, Expo frontend scaffold.
