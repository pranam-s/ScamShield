"""Tests for src/dataset_setup.py and src/db.py."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any

import pytest
from datasets import Dataset

import config
import db
from dataset_setup import load_and_prepare_dataset, tokenize_dataset

# --- load_and_prepare_dataset ------------------------------------------------


def test_missing_file_raises(tmp_path: Any) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_and_prepare_dataset(tmp_path / "nope.csv")


def test_empty_csv_raises(tmp_path: Any) -> None:
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("text,label\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        load_and_prepare_dataset(csv_path)


def test_wrong_columns_raise(tmp_path: Any) -> None:
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("sentence,target\nhello,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain 'text' and 'label'"):
        load_and_prepare_dataset(csv_path)


def test_valid_csv_loads(tmp_path: Any) -> None:
    csv_path = tmp_path / "good.csv"
    csv_path.write_text(
        "text,label\nShare your OTP,1\nhello friend,0\n",
        encoding="utf-8",
    )
    dataset = load_and_prepare_dataset(csv_path)
    assert isinstance(dataset, Dataset)
    assert dataset.num_rows == 2
    assert set(dataset.column_names) == {"text", "label"}


def test_default_path_points_at_repo_dataset() -> None:
    assert config.DATASET_PATH.name == "dataset.csv"
    assert config.DATASET_PATH.is_file()  # repo ships the training data


# --- tokenize_dataset --------------------------------------------------------


class BatchFakeTokenizer:
    def __call__(self, texts: list[str], **_: Any) -> dict[str, list[list[int]]]:
        return {
            "input_ids": [[101, 102] for _ in texts],
            "attention_mask": [[1, 1] for _ in texts],
        }


def test_tokenize_dataset_removes_text_column() -> None:
    dataset = Dataset.from_dict({"text": ["a", "b"], "label": [0, 1]})
    tokenized = tokenize_dataset(dataset, tokenizer=BatchFakeTokenizer())
    assert "text" not in tokenized.column_names
    assert "input_ids" in tokenized.column_names
    assert tokenized[0]["input_ids"] == [101, 102]


# --- caller-number hashing (AUDIT #21) ---------------------------------------


def test_hash_caller_number_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(config.CALLER_KEY_ENV_VAR, "secret-1")
    assert db.hash_caller_number("+91-000") == db.hash_caller_number("+91-000")


def test_hash_caller_number_differs_per_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(config.CALLER_KEY_ENV_VAR, "secret-1")
    first = db.hash_caller_number("+91-000")
    monkeypatch.setenv(config.CALLER_KEY_ENV_VAR, "secret-2")
    assert db.hash_caller_number("+91-000") != first


def test_hash_caller_number_format_conceals_number(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(config.CALLER_KEY_ENV_VAR, "secret-1")
    hashed = db.hash_caller_number("+91-000")
    assert hashed.startswith(db.CALLER_HASH_PREFIX)
    assert "+91-000" not in hashed


def test_hash_caller_number_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(config.CALLER_KEY_ENV_VAR, raising=False)
    with pytest.raises(db.CallerKeyMissingError, match="SCAMSHIELD_CALLER_KEY"):
        db.hash_caller_number("+91-000")


def test_hash_caller_number_blank_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(config.CALLER_KEY_ENV_VAR, "   ")
    with pytest.raises(db.CallerKeyMissingError, match="SCAMSHIELD_CALLER_KEY"):
        db.hash_caller_number("+91-000")


# --- retention purge (AUDIT #21) ---------------------------------------------


def _insert_call_with_end(db_path: Any, call_id: str, end_time: str | None) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO call_records (call_id, end_time) VALUES (?, ?)", (call_id, end_time)
        )


def test_purge_expired_calls_deletes_only_stale_rows(tmp_db: Any) -> None:
    stale = (datetime.now() - timedelta(days=config.CALL_RECORD_RETENTION_DAYS + 1)).isoformat(
        sep=" "
    )
    fresh = datetime.now().isoformat(sep=" ")
    _insert_call_with_end(tmp_db, "stale", stale)
    _insert_call_with_end(tmp_db, "fresh", fresh)
    _insert_call_with_end(tmp_db, "no-end", None)  # cannot be aged -> kept

    assert db.purge_expired_calls() == 1

    with sqlite3.connect(tmp_db) as conn:
        remaining = {row[0] for row in conn.execute("SELECT call_id FROM call_records")}
    assert remaining == {"fresh", "no-end"}


def test_purge_empty_database_deletes_nothing(tmp_db: Any) -> None:
    assert db.purge_expired_calls() == 0


def test_purge_honours_retention_constant(monkeypatch: pytest.MonkeyPatch, tmp_db: Any) -> None:
    monkeypatch.setattr(config, "CALL_RECORD_RETENTION_DAYS", 7)
    _insert_call_with_end(
        tmp_db, "ten-days-old", (datetime.now() - timedelta(days=10)).isoformat(sep=" ")
    )
    assert db.purge_expired_calls() == 1


def test_purge_cutoff_comes_from_injected_now(tmp_db: Any) -> None:
    five_days_ago = datetime.now() - timedelta(days=5)
    _insert_call_with_end(tmp_db, "recent", five_days_ago.isoformat(sep=" "))

    assert db.purge_expired_calls(now=datetime.now()) == 0
    assert db.purge_expired_calls(now=datetime.now() + timedelta(days=30)) == 1


# --- db helpers --------------------------------------------------------------


def _insert_call(db_path: Any, text: str, feedback: str | None, status: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO call_records (call_id, full_transcription, user_feedback, final_status) "
            "VALUES (?, ?, ?, ?)",
            (f"id-{text}-{feedback}-{status}", text, feedback, status),
        )


def test_init_db_creates_tables(tmp_path: Any) -> None:
    db_path = tmp_path / "fresh.db"
    db.init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"call_records", "model_metadata"} <= tables


def test_init_db_idempotent(tmp_path: Any) -> None:
    db_path = tmp_path / "again.db"
    db.init_db(db_path)
    db.init_db(db_path)  # must not raise


def test_load_feedback_empty_returns_none(tmp_db: Any) -> None:
    assert db.load_feedback_data() is None


def test_load_feedback_label_mapping(tmp_db: Any) -> None:
    _insert_call(tmp_db, "a", "correct", "Scam")  # -> 1
    _insert_call(tmp_db, "b", "correct", "Safe")  # -> 0
    _insert_call(tmp_db, "c", "incorrect", "Scam")  # -> 0
    _insert_call(tmp_db, "d", "incorrect", "Suspicious")  # -> 1
    _insert_call(tmp_db, "e", "maybe", "Scam")  # ignored: unknown feedback
    _insert_call(tmp_db, "f", None, "Scam")  # ignored: NULL feedback

    data = db.load_feedback_data()
    assert data is not None
    assert len(data) == 4
    assert {d["text"]: d["label"] for d in data} == {"a": 1, "b": 0, "c": 0, "d": 1}


def test_load_feedback_db_error_returns_none(tmp_path: Any) -> None:
    bad = tmp_path / "not-a-db.sqlite"
    bad.write_text("this is not a database", encoding="utf-8")
    assert db.load_feedback_data(str(bad)) is None


def test_init_db_scrubs_legacy_plaintext_caller_numbers(
    monkeypatch: pytest.MonkeyPatch, tmp_db: Any
) -> None:
    monkeypatch.setenv(config.CALLER_KEY_ENV_VAR, "secret-1")
    hashed = db.hash_caller_number("+91-000")
    with sqlite3.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO call_records (call_id, caller_number) VALUES ('legacy', '+91-1234567890')"
        )
        conn.execute(
            "INSERT INTO call_records (call_id, caller_number) VALUES ('hashed', ?)", (hashed,)
        )
    db.init_db()  # second init over existing rows
    with sqlite3.connect(tmp_db) as conn:
        rows = dict(conn.execute("SELECT call_id, caller_number FROM call_records").fetchall())
    assert rows["legacy"] is None  # plaintext dropped, not trusted
    assert rows["hashed"] == hashed  # hash-format value untouched


def test_connect_uses_config_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    redirected = tmp_path / "redirected.db"
    monkeypatch.setattr(config, "DATABASE_PATH", redirected)
    db.init_db()  # no explicit path -> must land at the config path
    assert redirected.is_file()
