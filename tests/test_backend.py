"""API tests for src/backend.py using TestClient with fake ML resources."""

from __future__ import annotations

import base64
import sqlite3
import time
from typing import Any

import pytest
from conftest import make_wav_bytes

import backend
import config
from predict import PredictionError, TranscriptionError


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


@pytest.fixture()
def patched_pipeline(monkeypatch: pytest.MonkeyPatch):
    """Stub audio conversion/transcription/prediction inside backend."""
    monkeypatch.setattr(
        backend, "convert_audio_to_wav", lambda data, file_format=None: "fake-wav-stream"
    )

    def fake_transcribe(wav_file: Any, language: str | None = None) -> str:
        return "please share your otp immediately"

    monkeypatch.setattr(backend, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(backend, "predict_scam", lambda text, model, device: 0.93)


# --- infrastructure endpoints ------------------------------------------------


def test_health(client: Any) -> None:
    resp = client.get("/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_education(client: Any) -> None:
    resp = client.get("/education/")
    assert resp.status_code == 200
    assert "Educational Module" in resp.text


def test_model_info_empty(client: Any) -> None:
    resp = client.get("/model-info/")
    assert resp.status_code == 200
    assert resp.json()["model_name"] == "No model metadata found"


def test_model_info_after_training_row(client: Any, tmp_db: Any) -> None:
    with sqlite3.connect(tmp_db) as conn:
        conn.execute(
            "INSERT INTO model_metadata (model_name, dataset_version, training_epochs, number_labels, accuracy) "
            "VALUES ('distilbert-base-uncased', '1.0', 3, 2, 0.91)"
        )
    resp = client.get("/model-info/")
    body = resp.json()
    assert resp.status_code == 200
    assert body["accuracy"] == 0.91
    assert body["training_epochs"] == 3


def test_lifespan_loads_resources(client: Any) -> None:
    # The client fixture enters the lifespan handler with stubbed load_model.
    assert backend.model is not None
    assert backend.tokenizer is not None
    assert backend.model_version == "test-scam-model"


# --- POST /detect-scam -------------------------------------------------------


def test_detect_scam_success(client: Any, patched_pipeline: None) -> None:
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": b64(make_wav_bytes())})
    assert resp.status_code == 200
    body = resp.json()
    assert body["scam_probability"] == 0.93
    assert body["status"] == "Scam"
    assert body["transcription"] == "please share your otp immediately"
    # session bookkeeping happened
    assert "c1" in backend.active_calls
    assert backend.active_calls["c1"]["chunk_count"] == 1


def test_detect_scam_503_when_model_missing(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backend, "model", None)
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": b64(b"x")})
    assert resp.status_code == 503


def test_detect_scam_invalid_base64(client: Any, patched_pipeline: None) -> None:
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": "!!!not-base64!!!"})
    assert resp.status_code == 400
    assert "base64" in resp.json()["detail"]


def test_detect_scam_empty_payload(client: Any, patched_pipeline: None) -> None:
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": ""})
    assert resp.status_code == 400
    assert "Empty" in resp.json()["detail"]


def test_detect_scam_oversized_payload(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "MAX_AUDIO_BYTES", 8)
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": b64(b"1234567890")})
    assert resp.status_code == 413


def test_detect_scam_unknown_file_type(client: Any, patched_pipeline: None) -> None:
    resp = client.post(
        "/detect-scam/", json={"call_id": "c1", "base64": b64(b"\x00\x01\x02\x03junk")}
    )
    assert resp.status_code == 400
    assert "Could not detect" in resp.json()["detail"]


def test_detect_scam_disallowed_format(client: Any, patched_pipeline: None) -> None:
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # valid PNG signature
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": b64(png)})
    assert resp.status_code == 415
    assert "Invalid file format" in resp.json()["detail"]


def test_detect_scam_transcription_failure(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        backend, "convert_audio_to_wav", lambda data, file_format=None: "fake-wav-stream"
    )

    def boom(wav_file: Any, language: str | None = None) -> str:
        raise TranscriptionError("unintelligible")

    monkeypatch.setattr(backend, "transcribe_audio", boom)
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": b64(make_wav_bytes())})
    assert resp.status_code == 422
    assert "unintelligible" in resp.json()["detail"]


def test_detect_scam_prediction_failure(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        backend, "convert_audio_to_wav", lambda data, file_format=None: "fake-wav-stream"
    )
    monkeypatch.setattr(backend, "transcribe_audio", lambda wav, language=None: "text")
    monkeypatch.setattr(
        backend,
        "predict_scam",
        lambda text, model, device: (_ for _ in ()).throw(PredictionError("gpu on fire")),
    )
    resp = client.post("/detect-scam/", json={"call_id": "c1", "base64": b64(make_wav_bytes())})
    assert resp.status_code == 502


# --- context management ------------------------------------------------------


def test_update_context_accumulates_and_truncates(
    client: Any, monkeypatch: pytest.MonkeyPatch, fake_tokenizer: Any
) -> None:
    monkeypatch.setattr(config, "MAX_CONTEXT_TOKENS", 5)
    monkeypatch.setattr(config, "CONTEXT_KEEP_TOKENS", 1)

    ctx1 = backend.update_context("call-x", "one two three", fake_tokenizer)
    assert ctx1 == "one two three"

    ctx2 = backend.update_context("call-x", "four five six seven eight nine ten", fake_tokenizer)
    words = ctx2.split()
    assert len(words) <= config.MAX_CONTEXT_TOKENS
    assert "one" not in words  # oldest content dropped

    state = backend.active_calls["call-x"]
    assert state["chunk_count"] == 2
    assert state["chunks"][-1] == "four five six seven eight nine ten"
    assert state["start_time"] > 0


# --- POST /save-call ---------------------------------------------------------


def test_save_call_unknown_id(client: Any) -> None:
    resp = client.post("/save-call/", json={"call_id": "missing"})
    assert resp.status_code == 404


def test_save_call_success(client: Any, patched_pipeline: None, tmp_db: Any) -> None:
    backend.update_context("call-9", "a scammy sentence", backend.tokenizer)
    resp = client.post(
        "/save-call/",
        json={"call_id": "call-9", "caller_number": "+91-000", "user_feedback": "correct"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Call data saved successfully."
    assert "call-9" not in backend.active_calls  # session removed

    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT caller_number, user_feedback, final_status, model_version_used "
            "FROM call_records WHERE call_id = 'call-9'"
        ).fetchone()
    assert row == ("+91-000", "correct", "Scam", "test-scam-model")


def test_save_call_survives_scoring_failure(
    client: Any, monkeypatch: pytest.MonkeyPatch, tmp_db: Any
) -> None:
    backend.update_context("call-err", "text", backend.tokenizer)
    monkeypatch.setattr(
        backend,
        "predict_scam",
        lambda text, model, device: (_ for _ in ()).throw(PredictionError("down")),
    )
    resp = client.post("/save-call/", json={"call_id": "call-err"})
    assert resp.status_code == 200
    with sqlite3.connect(tmp_db) as conn:
        final_status = conn.execute(
            "SELECT final_status FROM call_records WHERE call_id = 'call-err'"
        ).fetchone()[0]
    assert final_status == "Unknown"


def test_save_call_with_empty_session(client: Any, tmp_db: Any) -> None:
    backend.active_calls["empty-call"] = {
        "context": "",
        "chunk_count": 0,
        "start_time": time.time(),
        "last_chunk_time": time.time(),
        "chunks": [],
    }
    resp = client.post("/save-call/", json={"call_id": "empty-call"})
    assert resp.status_code == 200
    with sqlite3.connect(tmp_db) as conn:
        final_status = conn.execute(
            "SELECT final_status FROM call_records WHERE call_id = 'empty-call'"
        ).fetchone()[0]
    assert final_status == "Unknown"


# --- GET /abandoned-calls ----------------------------------------------------


def test_abandoned_calls_removed(client: Any) -> None:
    backend.active_calls["old"] = {
        "context": "",
        "chunk_count": 1,
        "start_time": time.time() - 999,
        "last_chunk_time": time.time() - config.ABANDONED_CALL_TIMEOUT_SECONDS - 5,
        "chunks": ["x"],
    }
    backend.active_calls["fresh"] = {
        "context": "",
        "chunk_count": 1,
        "start_time": time.time(),
        "last_chunk_time": time.time(),
        "chunks": ["y"],
    }
    resp = client.get("/abandoned-calls/")
    body = resp.json()
    assert resp.status_code == 200
    assert body["message"] == "Removed 1 abandoned calls."
    assert "old" not in backend.active_calls
    assert "fresh" in backend.active_calls
