# Evaluation: model, system, and test quality

**Last updated:** 2026-09-18 (see
docs/STATUS.md for the current gate numbers and the real-run evidence).
This document reports only numbers that were actually produced on this
repository. Nothing here is estimated or projected.

## 1. Model evaluation protocol

* **Task:** binary text classification (1 = scam, 0 = normal) on call
  transcripts.
* **Model:** `distilbert-base-uncased`, fine-tuned with HF `Trainer`
  (`src/train.py`): 3 epochs, batch 16, LR 2e-5 (linear decay, no warmup),
  weight decay 0.01.
* **Data:** `src/dataset.csv`: 1,245 labelled records (before feedback
  augmentation), split 90/10 train/eval with `seed=42` for reproducibility.
* **Metric:** accuracy via the `evaluate` library, computed on the held-out
  eval split at each epoch (`compute_metrics`).
* **Where results live:** after training, accuracy + dataset version +
  epoch count are written to the SQLite `model_metadata` table and served by
  `GET /model-info/`. This is the single source of truth: the API serves
  whatever the last real training run produced.

### Current status (honest)

**No trained weights are present in the repository** (`model/scam_detector/`
is gitignored, by design; model binaries don't belong in git). Consequently
**no accuracy number is claimed in any documentation**: run
`uv run python src/train.py` to produce a model and metrics, then check
`uv run python -c "import db; print(db.load_feedback_data())"` or
`GET /model-info/` after a backend start. The `/model-info/` endpoint
returns `"No model metadata found"` until a training run has completed,
which is itself a useful integration check.

Until a training run is done, the backend falls back to the *untrained*
base model and logs a warning. Detection results from the fallback are not
meaningful and must not be demoed.

## 2. System-level evaluation (verified locally, 2026-09-14)

These numbers come from the actual test run of this repository
(Python 3.13.15, torch 2.14.0+cpu, transformers 5.16.1, last verified
2026-09-14):

| Check | Result |
|---|---|
| Test suite | **74 passed**, offline (no model downloads, no network) |
| Line coverage, `predict.py` | **100 %** (70/70 stmts) |
| Line coverage, `backend.py` | **100 %** (163/163 stmts) |
| Line coverage, `dataset_setup.py` | **100 %** (27/27) |
| Line coverage, `db.py` | **100 %** (57/57) |
| Line coverage, `config.py` | **100 %** (20/20) |
| Line coverage, `train.py` | 35 %; see exclusion note |
| Total coverage | 89 % |
| Coverage gate (core modules, ≥90 % required) | **passes at 100 %** |
| ruff check / ruff format | clean |
| mypy | clean (7 source files) |

**train.py exclusion justification:** the uncovered functions
(`train_model`, `get_tokenizer_and_model`) require downloading the base
DistilBERT weights and executing a full 3-epoch training run (hundreds of
CPU-minutes), which is out of scope for unit CI. The testable pure logic
(`compute_metrics`, split fraction) *is* tested; the rest is exercised
manually per the README training step. If this project moves past
prototype stage, the right fix is a tiny (e.g. 2-sample) dummy-model
training integration test, not a gate exemption.

## 3. Known limitations

1. **Dataset scale and provenance.** 1,245 short synthetic-style records
   is small for production NLP; expect weak generalisation to real
   conversational audio, dialects, and code-switching.
2. **English-only.** `TRANSCRIPTION_LANGUAGE` is configurable (default
   `en-IN`) but the classifier is English-only today.
3. **Classifier sees text, not audio.** Detection quality is capped by STT
   quality; accents, VoIP artifacts and background noise degrade the chain
   before the model ever sees the words.
4. **Latency.** Each chunk does STT (network) + one transformer pass. Fine
   for demo; real-time budgets need profiling (explicitly not measured here).
5. **Single-process state.** `active_calls` is in-memory; restarting the
   backend or running multiple workers loses or fragments call sessions.
6. **Privacy.** Saved-call transcripts are still stored in plaintext SQLite
   so the feedback-driven retraining loop can read them; encrypting them at
   rest is future work. Caller numbers, however, are no longer plaintext
   (AUDIT #21, fixed 2026-09-14): they are stored as keyed HMAC-SHA256
   hashes (`SCAMSHIELD_CALLER_KEY` environment variable; missing key → HTTP
   503, never a silent fallback), legacy plaintext values are scrubbed to
   NULL by `init_db`, and call records are purged after
   `config.CALL_RECORD_RETENTION_DAYS` (30 days) at backend startup.
7. **No authentication.** All endpoints are open; do not expose the API to
   the public internet as-is.
8. **Feedback-label conflicts.** When feedback contradicts the base dataset
   for the same text, retraining keeps the feedback label (feedback is
   concatenated last and duplicates are dropped, keeping the last
   occurrence).
9. **Accuracy metric only.** Accuracy is computed on a balanced-ish small
   split; precision/recall per class should be added before making claims
   about real-world protection.

## 4. How to reproduce

```bash
uv sync
uv run pytest --cov=src --cov-report=term-missing   # tables in section 2
uv run coverage report --include='src/predict.py,src/backend.py,src/dataset_setup.py,src/db.py,src/config.py' --fail-under=90
uv run python src/train.py                          # produce real model + metrics
uv run python src/backend.py                        # then GET /model-info/
```
