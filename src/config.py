"""Shared configuration for ScamShield.

All paths are anchored to the project root so the app behaves the same no
matter which working directory it is launched from (the previous
CWD-relative paths broke `python src/train.py` run from the repo root).
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Model ---
MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = PROJECT_ROOT / "hf_models"  # Hugging Face download cache
MODEL_DIR = PROJECT_ROOT / "model" / "scam_detector"  # fine-tuned weights output
DATASET_PATH = PROJECT_ROOT / "src" / "dataset.csv"
DATASET_VERSION = "1.0"
DATABASE_PATH = PROJECT_ROOT / "scam_calls.db"  # runtime SQLite database

# --- Conversation context window ---
MAX_CONTEXT_TOKENS = 512
CONTEXT_KEEP_TOKENS = 100  # headroom kept under the limit when truncating

# --- Classification thresholds (must match frontend colour coding) ---
SCAM_THRESHOLD = 0.8  # >= -> "Scam" (red)
SUSPICIOUS_THRESHOLD = 0.4  # >= -> "Suspicious" (yellow), else "Safe" (green)

# --- Audio upload limits ---
MAX_AUDIO_BYTES = 10 * 1024 * 1024  # reject decoded payloads above 10 MB (DoS guard)
ALLOWED_AUDIO_FORMATS = frozenset({"mp3", "wav", "3gp", "mpeg", "m4a", "ogg", "flac"})

# --- Call session handling ---
ABANDONED_CALL_TIMEOUT_SECONDS = 30  # no chunk for this long -> call considered gone

# --- Privacy: caller numbers are never stored in plaintext (AUDIT #21) ---
# The HMAC key comes from the environment at call time; without it the app
# refuses to persist caller numbers (no silent plaintext fallback).
CALLER_KEY_ENV_VAR = "SCAMSHIELD_CALLER_KEY"

# --- Transcription ---
# Google Speech Recognition needs a BCP-47 code; "auto" (the old default) is
# not accepted by the API and fails at request time.
TRANSCRIPTION_LANGUAGE = "en-IN"

# --- Server ---
HOST = "0.0.0.0"
PORT = 8000
