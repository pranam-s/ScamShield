"""SQLite access helpers shared by the backend and the training script."""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3

import config

CALLER_HASH_PREFIX = "hmac-sha256:"


class CallerKeyMissingError(RuntimeError):
    """Raised when the caller-number hashing key is not configured."""


def hash_caller_number(caller_number: str) -> str:
    """Return the keyed-hash (HMAC-SHA256) form of a caller number.

    Caller numbers are PII (AUDIT #21) and are never stored in plaintext.
    The HMAC key is read from the environment at call time; a missing or
    blank key is an error, never a silent fallback to plaintext. Because the
    hash is deterministic under one key, exact-match lookups on the number
    remain possible without making the number recoverable.
    """
    secret = os.environ.get(config.CALLER_KEY_ENV_VAR, "").strip()
    if not secret:
        raise CallerKeyMissingError(
            f"Environment variable {config.CALLER_KEY_ENV_VAR} must hold a "
            "non-empty secret before caller numbers can be stored."
        )
    digest = hmac.new(secret.encode("utf-8"), caller_number.encode("utf-8"), hashlib.sha256)
    return f"{CALLER_HASH_PREFIX}{digest.hexdigest()}"


def connect(db_path: str | None = None) -> sqlite3.Connection:
    """Open a connection with row access by column name.

    Reads ``config.DATABASE_PATH`` at call time so tests can redirect the
    database by monkeypatching the config value.
    """
    conn = sqlite3.connect(db_path or config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    """Create the schema if it does not exist yet."""
    with sqlite3.connect(db_path or config.DATABASE_PATH) as db:
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS call_records (
                call_id TEXT PRIMARY KEY,
                start_time DATETIME,
                end_time DATETIME,
                duration REAL,
                caller_number TEXT,
                full_transcription TEXT,
                user_feedback TEXT,
                final_status TEXT,
                model_version_used TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS model_metadata (
                model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                training_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                dataset_version TEXT,
                accuracy REAL,
                training_epochs INTEGER,
                number_labels INTEGER
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_id ON call_records (call_id)")
        db.commit()


def load_feedback_data(db_path: str | None = None) -> list[dict[str, object]] | None:
    """Return human-feedback rows as labelled examples for retraining.

    Feedback semantics:
      * "correct"   -> keep the model's verdict as the label
      * "incorrect" -> flip the model's verdict
      * anything else / NULL -> ignored

    Returns ``None`` when there is nothing usable or the database fails.
    """
    try:
        with connect(db_path) as db:
            rows = db.execute(
                """
                SELECT full_transcription AS text, user_feedback, final_status
                FROM call_records
                WHERE user_feedback IS NOT NULL
                """
            ).fetchall()
    except sqlite3.Error as exc:
        print(f"Database error while loading feedback: {exc}")
        return None

    data: list[dict[str, object]] = []
    for row in rows:
        feedback, final_status = row["user_feedback"], row["final_status"]
        if feedback == "correct":
            label = 1 if final_status == "Scam" else 0
        elif feedback == "incorrect":
            label = 0 if final_status == "Scam" else 1
        else:
            continue
        data.append({"text": row["text"], "label": label})
    return data or None
