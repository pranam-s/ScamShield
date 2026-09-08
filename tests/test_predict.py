"""Tests for src/predict.py (conversion, transcription, classification)."""

from __future__ import annotations

import io
from typing import Any

import pytest
import speech_recognition as sr
import torch
from conftest import FakeModel, FakeTokenizer

import predict

# --- get_status_details ------------------------------------------------------


@pytest.mark.parametrize(
    ("prob", "expected"),
    [
        (0.95, ("Scam", "red")),
        (0.8, ("Scam", "red")),  # boundary: >= 0.8 is Scam
        (0.79, ("Suspicious", "yellow")),
        (0.4, ("Suspicious", "yellow")),  # boundary: >= 0.4 is Suspicious
        (0.39, ("Safe", "green")),
        (0.0, ("Safe", "green")),
    ],
)
def test_get_status_details_boundaries(prob: float, expected: tuple[str, str]) -> None:
    assert predict.get_status_details(prob) == expected


def test_get_status_details_custom_thresholds() -> None:
    assert predict.get_status_details(0.5, scam_threshold=0.9, suspicious_threshold=0.6) == (
        "Safe",
        "green",
    )
    assert predict.get_status_details(0.65, scam_threshold=0.9, suspicious_threshold=0.6) == (
        "Suspicious",
        "yellow",
    )


# --- convert_audio_to_wav ----------------------------------------------------


def _wav_bytes(duration_ms: int = 300) -> bytes:
    from pydub import AudioSegment

    buf = io.BytesIO()
    AudioSegment.silent(duration=duration_ms).export(buf, format="wav")
    return buf.getvalue()


def test_convert_bytes_without_format_raises() -> None:
    with pytest.raises(ValueError, match="file_format must be provided"):
        predict.convert_audio_to_wav(_wav_bytes())


def test_convert_wav_bytes_to_wav_stream() -> None:
    from pydub import AudioSegment

    stream = predict.convert_audio_to_wav(_wav_bytes(500), file_format="wav")
    audio = AudioSegment.from_file(stream, format="wav")
    assert len(audio) == 500  # milliseconds


def test_convert_from_path(tmp_path: Any) -> None:
    from pydub import AudioSegment

    src = tmp_path / "clip.wav"
    src.write_bytes(_wav_bytes(250))

    stream = predict.convert_audio_to_wav(str(src))
    assert len(AudioSegment.from_file(stream, format="wav")) == 250


def test_convert_from_path_with_explicit_format(tmp_path: Any) -> None:
    src = tmp_path / "mystery_no_extension"
    src.write_bytes(_wav_bytes(150))
    stream = predict.convert_audio_to_wav(str(src), file_format="WAV")  # case-insensitive
    assert stream.read(4) == b"RIFF"


def test_convert_path_without_extension_raises(tmp_path: Any) -> None:
    src = tmp_path / "noext"
    src.write_bytes(b"not audio")
    with pytest.raises(ValueError, match="Cannot determine audio format"):
        predict.convert_audio_to_wav(str(src))


# --- transcribe_audio --------------------------------------------------------


class FakeRecognizer:
    def __init__(self, text: str | None, raise_unknown: bool = False, raise_request: bool = False):
        self.text = text
        self.raise_unknown = raise_unknown
        self.raise_request = raise_request
        self.recorded_language: str | None = None

    def record(self, source: Any) -> str:
        return "fake-audio-data"

    def recognize_google(self, audio_data: Any, language: str = "en-US") -> str:
        self.recorded_language = language
        if self.raise_unknown:
            raise sr.UnknownValueError()
        if self.raise_request:
            raise sr.RequestError("service down")
        return self.text  # type: ignore[return-value]


@pytest.fixture()
def patch_recognizer(monkeypatch: pytest.MonkeyPatch):
    def _patch(rec: FakeRecognizer) -> list[str]:
        entered: list[str] = []

        class FakeAudioFile:
            def __init__(self, wav_file: Any) -> None:
                entered.append("init")

            def __enter__(self) -> Any:
                entered.append("enter")
                return object()

            def __exit__(self, *args: Any) -> None:
                entered.append("exit")

        monkeypatch.setattr(sr, "AudioFile", FakeAudioFile)
        monkeypatch.setattr(sr, "Recognizer", lambda: rec)
        return entered

    return _patch


def test_transcribe_success(monkeypatch: pytest.MonkeyPatch, patch_recognizer: Any) -> None:
    rec = FakeRecognizer("hello there")
    patch_recognizer(rec)
    assert predict.transcribe_audio(io.BytesIO(b"wav")) == "hello there"
    assert rec.recorded_language == predict.config.TRANSCRIPTION_LANGUAGE


def test_transcribe_custom_language(monkeypatch: pytest.MonkeyPatch, patch_recognizer: Any) -> None:
    rec = FakeRecognizer("namaste")
    patch_recognizer(rec)
    assert predict.transcribe_audio(io.BytesIO(b"wav"), language="hi-IN") == "namaste"
    assert rec.recorded_language == "hi-IN"


def test_transcribe_unintelligible(monkeypatch: pytest.MonkeyPatch, patch_recognizer: Any) -> None:
    patch_recognizer(FakeRecognizer(None, raise_unknown=True))
    with pytest.raises(predict.TranscriptionError, match="could not understand"):
        predict.transcribe_audio(io.BytesIO(b"wav"))


def test_transcribe_service_error(monkeypatch: pytest.MonkeyPatch, patch_recognizer: Any) -> None:
    patch_recognizer(FakeRecognizer(None, raise_request=True))
    with pytest.raises(predict.TranscriptionError, match="speech recognition service"):
        predict.transcribe_audio(io.BytesIO(b"wav"))


def test_transcribe_unreadable_file(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenAudioFile:
        def __init__(self, wav_file: Any) -> None:
            raise ValueError("bad file")

    monkeypatch.setattr(sr, "AudioFile", BrokenAudioFile)
    with pytest.raises(predict.TranscriptionError, match="Could not read audio file"):
        predict.transcribe_audio(io.BytesIO(b"junk"))


# --- predict_scam ------------------------------------------------------------


def test_predict_scam_returns_probability(
    fake_model: FakeModel, fake_tokenizer: FakeTokenizer
) -> None:
    prob = predict.predict_scam(
        "send me the otp", fake_model, torch.device("cpu"), tokenizer=fake_tokenizer
    )
    # logits [-4, +4] -> softmax -> [0.00033, 0.99966]
    assert prob == pytest.approx(0.9996646, abs=1e-5)


def test_predict_scam_uses_lazy_tokenizer(
    monkeypatch: pytest.MonkeyPatch, fake_model: FakeModel
) -> None:
    sentinel = FakeTokenizer()
    monkeypatch.setattr(predict, "_tokenizer", sentinel)
    prob = predict.predict_scam("text", fake_model, torch.device("cpu"))
    assert 0.0 <= prob <= 1.0
    assert predict._tokenizer is sentinel  # cached instance reused


def test_predict_scam_wraps_model_errors(
    fake_tokenizer: FakeTokenizer, monkeypatch: pytest.MonkeyPatch
) -> None:
    failing = FakeModel(fail=True)
    with pytest.raises(predict.PredictionError, match="Error during model prediction"):
        predict.predict_scam("text", failing, torch.device("cpu"), tokenizer=fake_tokenizer)


def test_get_tokenizer_loads_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeHFTokenizer:
        @classmethod
        def from_pretrained(cls, name: str, cache_dir: Any = None) -> FakeHFTokenizer:
            calls.append(name)
            return cls()

    import transformers

    monkeypatch.setattr(predict, "_tokenizer", None)
    monkeypatch.setattr(transformers, "DistilBertTokenizer", FakeHFTokenizer)
    first = predict.get_tokenizer()
    second = predict.get_tokenizer()
    assert first is second
    assert calls == [predict.config.MODEL_NAME]
    monkeypatch.setattr(predict, "_tokenizer", None)  # don't leak fake into other tests
