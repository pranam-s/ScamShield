# ScamShield Codebase Audit — 2026-09-09

Full review of the Python backend (`src/`), repository hygiene, packaging and
docs. Each finding lists severity, status, and the action taken. "Fixed"
items are covered by tests in `tests/`; "Open" items are deliberate,
documented deferrals with a recommended owner action.

| # | Severity | Finding | Status | Action |
|---|----------|---------|--------|--------|
| 1 | Critical | `backend.detect_scam` referenced an undefined `call_id` variable → `NameError`, every detection request returned HTTP 500 | Fixed | Uses `request.call_id`; regression-tested |
| 2 | Critical | `train.py` loaded the dataset from a CWD-relative `dataset.csv` → crashed when run from the repo root (`python src/train.py`) | Fixed | All paths anchored to repo root in `src/config.py` |
| 3 | Critical | `TrainingArguments(evaluation_strategy=...)` was removed in transformers 5.x → training crashed at startup with the locked (current) dependency versions | Fixed | Renamed to `eval_strategy` |
| 4 | Critical | `recognize_google(audio, language="auto")` — `"auto"` is not a valid BCP-47 code for the Google Speech API → every transcription failed at request time | Fixed | Configurable language, default `en-IN` (`config.TRANSCRIPTION_LANGUAGE`) |
| 5 | High | A full virtualenv was committed: `Scripts/` (34 MB on disk, incl. a 31 MB `ruff.exe`), `share/`, `pyvenv.cfg`, `CACHEDIR.TAG` | Fixed | Removed from git and disk; `.gitignore` hardened so it cannot recur |
| 6 | High | Model, tokenizer and DB schema were loaded at import time → importing `backend` downloaded model weights, `gradio_interface` could trigger a full training run on import; unit testing impossible | Fixed | FastAPI lifespan handler + lazy `get_tokenizer()` singleton |
| 7 | High | 500 responses returned raw exception text (`detail=f"Internal server error: {e}"`) → internal-detail disclosure | Fixed | Generic client-facing detail; full detail goes to the log |
| 8 | High | No size limit on base64 audio payloads → trivial DoS (unbounded memory + decode work) | Fixed | 10 MB cap → HTTP 413 (`config.MAX_AUDIO_BYTES`) |
| 9 | High | Inference + network STT ran inside `async def` handlers → blocked the event loop during every request | Fixed | Handlers are `def` (FastAPI threadpool); `active_calls` guarded by a lock |
| 10 | Medium | Invalid base64 produced HTTP 500 instead of 400 | Fixed | `binascii.Error` mapped to 400 |
| 11 | Medium | `init_db()`/schema SQL duplicated in `backend.py` and `train.py`; model constants duplicated in 4 files | Fixed | `src/db.py` + `src/config.py` single sources of truth |
| 12 | Medium | `/save-call` crashed (500) if final-chunk scoring raised | Fixed | Falls back to `final_status="Unknown"`, call still saved |
| 13 | Medium | Gradio format detection via `mimetypes` was fragile (unbound variables when MIME unknown) | Fixed | Pure function with explicit mapping table + default |
| 14 | Medium | **README published live Expo credentials** (username + password) | Fixed (redacted) | Credentials removed from README; owner must still rotate them in Expo |
| 15 | Medium | Dead code: `temp_file_path` never assigned; unused imports (`io`, `random`, `mimetypes`, `uuid`, `File`, `UploadFile`, `Form`) | Fixed | Removed; ruff enforces going forward |
| 16 | Medium | `get_db` dependency opened an unused DB connection per detection request | Fixed | Dependency removed from `detect_scam` |
| 17 | Medium | Scheduler step count used floor division → under-counted optimizer steps by one per epoch | Fixed | `math.ceil` |
| 18 | Medium | `accuracy` metric re-downloaded on every `compute_metrics` call | Fixed | Cached via `lru_cache` |
| 19 | Medium | Frontend hardcodes a dead ngrok tunnel URL (`frontend/app/recordscam.tsx:120`) → app cannot reach any locally-hosted backend | Open | Move base URL to env config (`EXPO_PUBLIC_API_URL`) — frontend is outside this pass |
| 20 | Medium | No authentication on any endpoint (anyone can submit audio / read model info) | Open | Acceptable for hackathon demo; add API key before any public deployment |
| 21 | Medium | `caller_number` (PII) stored in plaintext SQLite with no retention policy | Fixed (2026-09-14) | `caller_number` is now stored only as a keyed HMAC-SHA256 hash (`db.hash_caller_number`); the key comes from the `SCAMSHIELD_CALLER_KEY` environment variable and a missing/blank key is a hard HTTP 503 with the call session kept for retry — never a silent plaintext fallback. Keyed (not merely salted) hashing was chosen over encryption because no feature reads the number back, so reversibility serves nothing; the deterministic hash still allows exact-match lookups. Retention: `db.purge_expired_calls()` deletes records older than `config.CALL_RECORD_RETENTION_DAYS` (30) at every backend startup. Migration: `init_db` scrubs any pre-hash (legacy plaintext) value to NULL. Covered by tests (plaintext absent from raw DB bytes, 503 path, scrub, purge). |
| 22 | Medium | `active_calls` is in-memory only: lost on restart, breaks with `--workers > 1` | Open | Documented; move to Redis for horizontal scaling |
| 23 | Low | Fallback to the untrained base model silently produced meaningless probabilities | Improved | Loud warning logged directing to run `src/train.py`; recommend HTTP 503 instead |
| 24 | Low | `demo.launch(share=True)` exposes a public Gradio tunnel by default | Documented | Comment added; set `False` unless demoing |
| 25 | Low | `ABANDONED_CALL_TIMEOUT=30s` drops calls with >30s silence (hold music, long pauses) | Documented | Configurable in `config.py` |
| 26 | Low | pydub requires system ffmpeg for anything non-WAV (undocumented) | Documented | README prerequisites section |
| 27 | Low | pydub 0.25.1 emits `SyntaxWarning` on Python 3.13 (upstream regex strings) | Open (upstream) | Cosmetic; no action |
| 28 | Low | `requirements.txt` was fully unpinned | Superseded | Deleted; `pyproject.toml` + `uv.lock` provide reproducible, current pins |
| 29 | Low | `form 1.jpg` filename contains a space | Fixed (2026-09-16) | Renamed to `docs/survey-charts.jpg` / `docs/survey-responses.jpg`; references updated in README and PRD |
| 30 | High | No tests, no CI, no packaging | Fixed | 61 offline tests (100% line coverage on `predict`, `backend`, `dataset_setup`, `db`, `config`), GitHub Actions workflow (uv + ruff + mypy + pytest with ≥90 % core coverage gate), `pyproject.toml` + `uv.lock` |

## Testing notes

- 2026-09-14 remediation (#21): the suite grew from 61 to 74 tests; the
  caller-number hashing, legacy-plaintext scrub and retention purge are all
  covered, including a byte-level check that the plaintext number is absent
  from the SQLite file itself. Core modules remain at 100 % line coverage.
- Tests never touch the network: the Hugging Face loader is stubbed via
  `sys.modules` (transformers 5.x lazy modules defeat plain attribute
  monkeypatching — see `tests/test_backend_advanced.py`), and speech
  recognition / audio conversion are stubbed at the module boundary.
- `train.py` sits at 35 % line coverage by design: `train_model()` and
  `get_tokenizer_and_model()` require a real model download and a full
  training run (GPU-scale). These functions are excluded from the CI
  coverage gate with this written justification. The CI gate
  (`coverage report --fail-under=90`) covers `predict`, `backend`,
  `dataset_setup`, `db`, `config` — currently at 100 %.
- The test suite caught a real regression during this pass (missing
  `config.DATABASE_PATH`), validating the investment.
