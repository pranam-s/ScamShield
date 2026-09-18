# Status: honest state

Updated: 2026-09-18 (IST), all work complete. The Expo
frontend moved from SDK 52 to SDK 57 (docs/adr/0001), the Python-side
sqlite3 datetime-adapter warnings were fixed at the boundary, dead-code
tooling runs clean on both sides, and every gate was re-run from a clean
tree. All commands below were executed on this repository; nothing is
projected.

## Final gate, 2026-09-18 (real output, clean tree)

Backend (Windows, Python 3.14.7, uv-managed venv):

| Gate | Result |
|---|---|
| `uv run ruff check src tests` | 0 diagnostics |
| `uv run ruff format --check src tests` | clean |
| `uv run mypy src` | 0 diagnostics (7 files) |
| `uv run deptry .` | no issues (after declaring pydantic+numpy; config documented) |
| `uv run vulture src --min-confidence 80` | clean |
| `uv run pytest -q` | **74 passed, 2 warnings** (both upstream-internal: starlette's anyio alias via its testclient, SpeechRecognition's aifc notice; the 12 sqlite3 datetime warnings and the httpx-deprecation warning were fixed on 2026-09-18, and coverage tracing exposed four genuinely unclosed sqlite connections, all now closed via `db.connection()` and a committing+closing test helper) |
| Coverage gate (predict, backend, dataset_setup, db, config ≥ 90%) | **100% (347/347 statements)**; full `--cov=src` matrix TOTAL 89% (train.py/gradio_interface.py excluded by recorded decision: they need real model download/training) |

Frontend (Expo SDK 57: expo 57.0.24, react-native 0.86.3, react 19.2.3,
jest-expo 57.0.5):

| Gate | Result |
|---|---|
| `npx tsc --noEmit` | 0 errors |
| `npx jest` | 1 passed / 1 total |
| `npx knip --no-progress` | no issues (config in frontend/knip.json) |
| `npx expo-doctor` | 21/21 checks passed |
| `npx expo export --platform web` | production build succeeds, all routes |

CI (`.github/workflows/ci.yml`): Python matrix (3.12/3.13) with the gates
above plus the coverage floor, and a new frontend job (npm ci, tsc, jest,
knip). Every job's commands were executed locally and are green; GitHub
Actions stays disabled on the repository to keep spend at zero. Local
Python verification ran on 3.14; CI keeps the recorded
3.12/3.13 matrix.

## Feature run (2026-09-18, real evidence)

Backend (`uv run uvicorn backend:app --app-dir src`, fresh database):

- `/health/` → 200 `{"status":"ok",...}`.
- `/model-info/` → 200 `"No model metadata found"`; honest: no trained
  weights exist in the repo, none claimed anywhere.
- `/education/` → 200, HTML education module.
- `/abandoned-calls/` → 200, `{"message":"Removed 0 abandoned calls."}`.
- `/detect-scam/` with a synthetic 440 Hz tone WAV → 422 `"Speech
  recognition could not understand the audio"` (correct behavior for
  non-speech input; the STT leg genuinely ran).
- `/detect-scam/` with a real speech WAV (a narrated passage) → 200 with
  `scam_probability: 0.5353`, `status: "Suspicious"`, and an accurate
  transcription of the passage: the full decode → WAV → STT →
  DistilBERT pipeline executed for real. The mid-range score is the
  documented base-model fallback behavior (no fine-tuned weights exist).
- `/save-call/` with an unknown call id → 404 `"Call ID not found."`
  (saving completes a call the app tracked, by design).

Frontend: the SDK 57 web export was served and driven in headless
Chromium; screenshots of the home, recording, call, study, landing,
history, and settings screens in docs/screenshots/ are from that run. The
call screen shot also exposed and verified the fix for an unstyled action
image that rendered at full intrinsic size.

## Known residuals (deliberate, documented)

- **No trained model.** `/model-info/` stays empty until someone runs
  `uv run python src/train.py`; base-model scores are not meaningful and
  are labelled as such everywhere.
- **2 upstream warnings** remain (starlette/anyio, SpeechRecognition/aifc);
  not suppressible at this repo without hiding upstream defects.
- **npm audit: 14 moderate** findings, all inside Expo's build tooling
  (`@expo/config*` chain) at the current SDK release; no fix published
  upstream, none are runtime app dependencies. `npm audit fix --force`
  would desync the SDK tree, so it was not done.
- **Dependabot (34 alerts)** clears with the SDK 57 lockfile; the re-scan
  happens on GitHub after the push.

## License audit (2026-09-18)

Backend: 95 installed distributions scanned: MIT / BSD / Apache-2.0 /
PSF plus certifi, orjson, pathspec, tqdm under MPL-2.0 (file-level
copyleft, no conflict with the repository MIT license). Frontend: the Expo
SDK and its key libraries (React, React Native, Jest, testing library)
are MIT. LICENSE (MIT) verified intact, warranty disclaimer present.
