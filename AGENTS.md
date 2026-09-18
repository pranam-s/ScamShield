# AGENTS.md — guidance for AI agents and contributors working on ScamShield

## Repo map

```
src/
  backend.py           FastAPI app: /detect-scam, /save-call, /abandoned-calls,
                       /model-info, /education, /health. Model + DB load in the
                       lifespan handler, NOT at import time.
  predict.py           Audio→WAV (pydub), STT (SpeechRecognition), scam
                       probability (DistilBERT). Lazy tokenizer singleton.
  train.py             Fine-tuning + feedback-driven retraining (HF Trainer).
  dataset_setup.py     CSV → HF Dataset → tokenization.
  config.py            ALL shared constants & paths (anchored to repo root).
  db.py                SQLite schema + helpers (call_records, model_metadata,
                       load_feedback_data).
  gradio_interface.py  Demo UI. Model loads lazily on first detection.
  dataset.csv          1,245 labelled records (text,label).
tests/                 Offline pytest suite (see tests/conftest.py for fakes).
frontend/              Expo SDK 57 / React Native 0.86 app (own toolchain:
                       tsc, jest via jest-expo, knip, expo-doctor — see
                       docs/style-guides/typescript-react-native.md).
docs/                  AUDIT.md, design.md, BUILD_LOG.md, STATUS.md, ADRs,
                       style-guides/, screenshots/.
PRD.md / EVALUATION.md / README.md
```

## Environment & commands

* Use **uv** for everything Python. `uv sync` (locked install), then
  `uv run <cmd>`. Never install system-wide Python; never commit `.venv`,
  `Scripts/`, `pyvenv.cfg` (gitignored — they were once committed, see
  docs/AUDIT.md #5).
* Quality gate (must pass before committing):
  ```bash
undefined```
* CI (GitHub Actions) runs the same on Python 3.12/3.13 and enforces
  ≥90 % line coverage on `predict`, `backend`, `dataset_setup`, `db`,
  `config` via `coverage report --fail-under=90`. Actions is currently
  DISABLED on this repository by owner decision (no paid Actions); the
  gates must therefore pass on local execution before every push.

## House rules

1. **Keep tests offline.** Unit tests must never download model weights or
   call external services. Stub ML boundaries (see `tests/conftest.py`;
   note transformers 5.x lazy modules require a `sys.modules` stub, not
   attribute monkeypatching — see `tests/test_backend_advanced.py`).
2. **No import-time side effects** in `src/` — no model loads, no DB files,
   no network. `backend.app`'s lifespan is the only place that loads
   heavyweight resources.
3. **Constants live in `config.py`**, DB access in `db.py`. Don't
   re-duplicate (this codebase did; we cleaned it up).
4. **No fabricated numbers.** Metrics in docs must come from actual runs;
   `EVALUATION.md` records the real test/coverage numbers and the honest
   "no trained model committed" status.
5. **Conventional commits** (`fix:`, `feat:`, `test:`, `ci:`, `docs:`,
   `chore:`), one logical change per commit, repo always committable.
6. **Error handling:** user-input problems → 4xx; upstream/dependency
   failures → 502/503; never leak exception text in responses (log it).
7. **Paths:** always via `config.PROJECT_ROOT` anchoring — CWD-relative
   paths broke `python src/train.py` once already (AUDIT #2).
8. When changing thresholds (`SCAM_THRESHOLD`, `SUSPICIOUS_THRESHOLD`) or
   status colours, keep backend, Gradio UI and frontend in sync — the
   colour coding is part of the product contract.
9. `model/`, `hf_models/`, `*.db`, `results/`, `logs/` are runtime
   artifacts — gitignored, never commit them.
10. Frontend (`frontend/`) is Expo SDK 57 / React Native — not covered by
    the Python toolchain; don't "fix" it with Python tooling. Frontend
    gates: `npx tsc --noEmit`, `npx jest`, `npx knip --no-progress`,
    `npx expo-doctor` (all from `frontend/`; versions come from Expo's
    bundled dependency table via `npx expo install`, never hand-pinned).
    The backend address lives in `frontend/constants/Api.ts` — no
    endpoint URLs in screens.

## Known sharp edges

* pydub needs **ffmpeg** for non-WAV audio (WAV-only paths work without).
* The base-model fallback in `backend.load_model()` produces *untrained*
  predictions — run `uv run python src/train.py` first; the warning log is
  deliberate.
* Timestamps cross the sqlite3 boundary as strings via
  `db.to_sqlite_timestamp` (the default datetime adapters are deprecated
  since Python 3.12). Keep using it for new columns/queries; its
  `YYYY-MM-DD HH:MM:SS` form sorts correctly as text, which the retention
  purge depends on.
