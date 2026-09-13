"""Shared fixtures and fakes for the ScamShield test suite."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
import torch
from fastapi.testclient import TestClient

import backend
import config
import db


class FakeTokenizer:
    """Minimal stand-in for DistilBertTokenizer (word-level 'tokenization')."""

    def __call__(self, text: str, **_: Any) -> dict[str, torch.Tensor]:
        ids = [101, 2024, 5232, 102]
        return {
            "input_ids": torch.tensor([ids], dtype=torch.long),
            "attention_mask": torch.ones(1, len(ids), dtype=torch.long),
        }

    def tokenize(self, text: str) -> list[str]:
        return text.split()

    def convert_tokens_to_string(self, tokens: list[str]) -> str:
        return " ".join(tokens)


class FakeModel(torch.nn.Module):
    """Returns constant logits: [non-scam, scam] = [-logit, +logit]."""

    def __init__(self, scam_logit: float = 4.0, fail: bool = False) -> None:
        super().__init__()
        self.scam_logit = scam_logit
        self.fail = fail

    def forward(self, **_: Any) -> Any:
        if self.fail:
            raise RuntimeError("model exploded")
        logit = self.scam_logit
        logits = torch.tensor([[-logit, logit]])
        return SimpleNamespace(logits=logits)


@pytest.fixture()
def fake_tokenizer() -> FakeTokenizer:
    return FakeTokenizer()


@pytest.fixture()
def fake_model() -> FakeModel:
    return FakeModel()


@pytest.fixture()
def tmp_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> Any:
    """Redirect the application database into the test's tmp folder."""
    db_path = tmp_path / "test_calls.db"
    monkeypatch.setattr(config, "DATABASE_PATH", db_path)
    db.init_db()
    return db_path


@pytest.fixture()
def client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_db: Any,
    fake_model: FakeModel,
    fake_tokenizer: FakeTokenizer,
) -> Any:
    """TestClient with fake ML resources and a tmp database.

    Used as a context manager so the lifespan handler runs - but
    ``backend.load_model`` is stubbed so no real model is downloaded.
    """
    monkeypatch.setattr(backend, "model", fake_model)
    monkeypatch.setattr(backend, "tokenizer", fake_tokenizer)
    monkeypatch.setattr(backend, "device", torch.device("cpu"))
    monkeypatch.setattr(backend, "model_version", "test-scam-model")
    monkeypatch.setattr(
        backend,
        "load_model",
        lambda: (fake_tokenizer, fake_model, "test-scam-model"),
    )
    monkeypatch.setenv(config.CALLER_KEY_ENV_VAR, "test-caller-key")
    backend.active_calls.clear()
    with TestClient(backend.app) as test_client:
        yield test_client
    backend.active_calls.clear()


def make_wav_bytes(duration_ms: int = 200) -> bytes:
    """Generate a tiny valid WAV file in memory (no ffmpeg needed)."""
    import io

    from pydub import AudioSegment

    buf = io.BytesIO()
    AudioSegment.silent(duration=duration_ms).export(buf, format="wav")
    return buf.getvalue()
