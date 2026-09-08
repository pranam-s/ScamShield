"""Coverage for backend load_model branches, DB error paths, and run_fastapi."""

from __future__ import annotations

import sqlite3
import sys
import types
from typing import Any, ClassVar

import pytest
import torch
from conftest import make_wav_bytes

import backend


class FakeHFModel:
    saved_from: ClassVar[list[str]] = []

    @classmethod
    def from_pretrained(cls, path: str, **_: Any) -> FakeHFModel:
        cls.saved_from.append(path)
        instance = cls()
        instance.source = path
        return instance

    def to(self, device: Any) -> FakeHFModel:
        assert device.type in {"cpu", "cuda"}
        return self

    def eval(self) -> FakeHFModel:
        return self


class FakeHFTokenizer:
    @classmethod
    def from_pretrained(cls, name: str, **_: Any) -> FakeHFTokenizer:
        return cls()


def _stub_transformers(monkeypatch: pytest.MonkeyPatch, model_cls: Any) -> None:
    """Replace the transformers module in sys.modules.

    Patching attributes on the real module is unreliable because transformers
    5.x uses lazy-module machinery; stubbing sys.modules guarantees that
    `from transformers import ...` inside load_model resolves to our fakes.
    """
    stub = types.ModuleType("transformers")
    stub.DistilBertTokenizer = FakeHFTokenizer
    stub.DistilBertForSequenceClassification = model_cls
    monkeypatch.setitem(sys.modules, "transformers", stub)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)


def test_load_model_uses_fine_tuned_weights(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_transformers(monkeypatch, FakeHFModel)
    FakeHFModel.saved_from = []

    tokenizer, model, version = backend.load_model()
    assert isinstance(tokenizer, FakeHFTokenizer)
    assert isinstance(model, FakeHFModel)
    assert FakeHFModel.saved_from == [str(backend.config.MODEL_DIR)]
    assert version == str(backend.config.MODEL_DIR)


def test_load_model_falls_back_to_base(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    class MissingWeightsModel(FakeHFModel):
        @classmethod
        def from_pretrained(cls, path: str, **_: Any) -> Any:
            if "scam_detector" in str(path):
                raise OSError("no fine-tuned weights available")
            return super().from_pretrained(path, **_)

    _stub_transformers(monkeypatch, MissingWeightsModel)
    monkeypatch.setattr(backend.config, "MODEL_DIR", tmp_path / "scam_detector-missing")
    MissingWeightsModel.saved_from = []

    _tokenizer, model, version = backend.load_model()
    assert isinstance(model, MissingWeightsModel)
    assert model.source == backend.config.MODEL_NAME  # fell back to the base model id
    assert version == backend.config.MODEL_NAME


def test_save_call_duplicate_id_returns_500(client: Any, tmp_db: Any, fake_tokenizer: Any) -> None:
    backend.update_context("call-dup", "text", fake_tokenizer)
    with sqlite3.connect(tmp_db) as conn:
        conn.execute("INSERT INTO call_records (call_id) VALUES ('call-dup')")
    resp = client.post("/save-call/", json={"call_id": "call-dup"})
    assert resp.status_code == 500
    assert "Database error" in resp.json()["detail"]
    # the failed session was popped and the transaction rolled back
    assert "call-dup" not in backend.active_calls
    with sqlite3.connect(tmp_db) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM call_records WHERE call_id = 'call-dup'"
        ).fetchone()[0]
    assert count == 1  # rollback kept only the original row


def test_model_info_db_error_returns_500(client: Any, tmp_db: Any) -> None:
    with sqlite3.connect(tmp_db) as conn:
        conn.execute("DROP TABLE model_metadata")
    resp = client.get("/model-info/")
    assert resp.status_code == 500
    assert "Database error" in resp.json()["detail"]


def test_run_fastapi_uses_config_host_port(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_run(app: Any, host: str, port: int) -> None:
        seen["host"], seen["port"] = host, port

    monkeypatch.setattr(backend.uvicorn, "run", fake_run)
    backend.run_fastapi()
    assert seen == {"host": backend.config.HOST, "port": backend.config.PORT}


def test_detect_scam_real_wav_type_detection(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end type detection with a real WAV header (filetype.guess)."""
    monkeypatch.setattr(
        backend, "convert_audio_to_wav", lambda data, file_format=None: "fake-wav-stream"
    )
    monkeypatch.setattr(backend, "transcribe_audio", lambda wav, language=None: "hello")
    monkeypatch.setattr(backend, "predict_scam", lambda text, model, device: 0.1)
    resp = client.post(
        "/detect-scam/",
        json={
            "call_id": "wav-detect",
            "base64": __import__("base64").b64encode(make_wav_bytes()).decode(),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Safe"
