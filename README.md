# 🛡️ ScamShield: Real-Time Scam Call Detection

**Stop phone scams before they start.** ScamShield is an AI-powered mobile
application that provides real-time protection against scam calls, designed
especially for vulnerable users and speakers of Indian languages.

## The Problem

Phone scams are a pervasive and devastating problem, and traditional
spam filters offer no defence against live, conversational fraud. Scammers
are sophisticated social engineers: they manufacture urgency, impersonate
banks and government agencies, and demand OTPs and remote access. Our user
survey (see `form 1.jpg` / `form2.jpg`) showed overwhelming concern among
family members of elderly and non-tech-savvy users — the people most
frequently targeted. See [PRD.md](PRD.md) for the full problem statement.

## What ScamShield Does

* **Instant scam detection** — a fine-tuned DistilBERT model analyses the
  live conversation transcript for scam indicators (OTP requests, urgency
  and pressure tactics, remote-access demands, suspicious offers).
* **Proactive, colour-coded alerts** — Green (Safe) / Yellow (Suspicious) /
  Red (Scam), with suggested actions so the user can hang up and stay safe.
* **Privacy-first design** — audio chunks are processed per call and
  transcription data is only stored with user consent.
* **Adaptive learning** — user feedback ("correct" / "incorrect") is stored
  and folded back into retraining (`src/train.py --retrain` path).
* **Built-in education module** — teaches users the warning signs of scam
  calls (in the Gradio UI and the mobile app).

## Architecture

```
Phone call audio (Expo/React Native app or Gradio demo)
        │  base64 audio chunk
        ▼
FastAPI backend (src/backend.py)  ──►  SQLite (src/db.py, scam_calls.db)
        │                              - call records + user feedback
        ▼                              - model training metadata
pydub (ffmpeg) → WAV
        ▼
SpeechRecognition (Google STT) → transcript
        ▼
DistilBERT scam classifier (src/predict.py, trained by src/train.py)
        ▼
{scam_probability, status, transcription}
```

**Tech stack:** Python 3.12+, FastAPI, Transformers (DistilBERT),
SpeechRecognition, pydub, Gradio, SQLite · uv for dependency management ·
React Native / Expo frontend (`frontend/`).

## Getting Started

### Prerequisites

* [uv](https://docs.astral.sh/uv/) (Python + dependency manager)
* **ffmpeg** on your system PATH (pydub needs it to decode MP3/3GP/M4A/OGG
  audio; WAV works without it)
* A Google Speech Recognition–reachable internet connection (transcription
  is cloud-based)

### Install

```bash
uv sync              # creates .venv and installs the locked dependencies
uv run pytest        # optional: run the test suite (offline, no model needed)
```

### Train the model (required before first run)

No trained weights are committed to the repository. The first backend start
would otherwise fall back to the *untrained* base model (it logs a loud
warning). Produce real weights with:

```bash
uv run python src/train.py            # trains on src/dataset.csv (~2k labelled utterances)
```

Training records accuracy and metadata in SQLite (`model_metadata` table)
and saves the model to `model/scam_detector/`. To fold in user feedback
later: `uv run python -c "from train import train_model; train_model(retrain=True)"`.

### Run the backend API

```bash
uv run python src/backend.py          # http://0.0.0.0:8000
```

Key endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health/` | GET | Liveness check |
| `/detect-scam/` | POST | `{call_id, base64}` audio chunk → `{scam_probability, status, transcription}` |
| `/save-call/` | POST | Persist a finished call (+ optional user feedback) |
| `/abandoned-calls/` | GET | Drop stale call sessions |
| `/model-info/` | GET | Latest training metadata |
| `/education/` | GET | Scam-education HTML module |

### Run the Gradio demo (no mobile app needed)

```bash
uv run python src/gradio_interface.py
```

Upload an audio file, get the transcript, scam probability and colour-coded
verdict. (`share=True` opens a public tunnel — edit the source if you don't
want that.)

### Run the Expo frontend

```bash
cd frontend
npm install
npx expo start
```

> **Note:** the frontend currently hardcodes an ngrok URL
> (`frontend/app/recordscam.tsx`); point it at your backend host before use.

## Development

```bash
uv run ruff check src tests        # lint
uv run ruff format src tests       # format
uv run mypy src                    # type-check
uv run pytest --cov=src            # tests + coverage
```

CI (`.github/workflows/ci.yml`) runs all of the above on Python 3.12/3.13
and enforces **≥90 % line coverage on the core modules**.

See [docs/AUDIT.md](docs/AUDIT.md) for the codebase audit,
[EVALUATION.md](EVALUATION.md) for model evaluation and limitations,
[PRD.md](PRD.md) for the product requirements, and
[docs/style-guides/](docs/style-guides/) for the coding conventions.

## Roadmap

* **Full on-device AI** — local processing for maximum privacy.
* **Adaptive-learning toggle** — user control over data contribution.
* **More languages** — the STT language is already configurable; add
  multilingual training data.
* **Advanced alerting** — emergency contacts and in-app reporting.
* **Frontend config** — replace the hardcoded backend URL with env config.

## Team TechnoTitans

We are TechnoTitans, driven by a passion to use technology to build a safer
world. ScamShield is our commitment to protecting vulnerable individuals
from the growing threat of phone scams.

## License

See [LICENSE](LICENSE).
