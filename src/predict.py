"""Audio conversion, transcription, and scam-probability prediction helpers.

The Hugging Face tokenizer is loaded lazily (first call to
:func:`get_tokenizer`) instead of at import time so that importing this
module never touches the network or the filesystem - that keeps unit
tests fast and offline-safe.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

import speech_recognition as sr
import torch
from pydub import AudioSegment

import config

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when audio could not be transcribed (unintelligible or service down)."""


class PredictionError(Exception):
    """Raised when the model failed to produce a prediction."""


_tokenizer: Any | None = None


def get_tokenizer() -> Any:
    """Return the shared DistilBERT tokenizer, loading it on first use."""
    global _tokenizer
    if _tokenizer is None:
        from transformers import DistilBertTokenizer

        _tokenizer = DistilBertTokenizer.from_pretrained(
            config.MODEL_NAME, cache_dir=str(config.CACHE_DIR)
        )
        logger.info("Loaded tokenizer %s", config.MODEL_NAME)
    return _tokenizer


def get_status_details(
    scam_prob: float,
    scam_threshold: float | None = None,
    suspicious_threshold: float | None = None,
) -> tuple[str, str]:
    """Map a scam probability to a (status, color) pair.

    Thresholds default to ``config`` values so callers and tests can override
    them without touching global state.
    """
    scam_threshold = config.SCAM_THRESHOLD if scam_threshold is None else scam_threshold
    suspicious_threshold = (
        config.SUSPICIOUS_THRESHOLD if suspicious_threshold is None else suspicious_threshold
    )
    if scam_prob >= scam_threshold:
        return "Scam", "red"
    if scam_prob >= suspicious_threshold:
        return "Suspicious", "yellow"
    return "Safe", "green"


def convert_audio_to_wav(input_data: bytes | str, file_format: str | None = None) -> io.BytesIO:
    """Convert audio bytes (or a file path) to a WAV stream via pydub.

    Note: non-WAV formats require ffmpeg to be installed on the system.
    """
    if isinstance(input_data, bytes):
        if not file_format:
            raise ValueError("file_format must be provided when converting from bytes.")
        audio = AudioSegment.from_file(io.BytesIO(input_data), format=file_format)
    else:
        suffix = file_format or Path(input_data).suffix.lstrip(".")
        if not suffix:
            raise ValueError(f"Cannot determine audio format for path {input_data!r}.")
        audio = AudioSegment.from_file(input_data, format=suffix.lower())

    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)
    return wav_io


def transcribe_audio(wav_file: Any, language: str | None = None) -> str:
    """Transcribe WAV audio to text using Google Speech Recognition."""
    language = language or config.TRANSCRIPTION_LANGUAGE
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
    except Exception as exc:
        raise TranscriptionError(f"Could not read audio file: {exc}") from exc

    try:
        text = recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError as exc:
        raise TranscriptionError("Speech recognition could not understand the audio") from exc
    except sr.RequestError as exc:
        raise TranscriptionError(
            f"Could not request results from the speech recognition service; {exc}"
        ) from exc

    logger.info("Transcription successful: %s...", text[:50])
    return text


def predict_scam(
    text: str, model: Any, device: torch.device, tokenizer: Any | None = None
) -> float:
    """Return the model's probability (0..1) that ``text`` is a scam.

    ``model`` must be an nn.Module in eval mode that returns logits over two
    classes; index 1 is the "scam" class.
    """
    tok = tokenizer if tokenizer is not None else get_tokenizer()
    inputs = tok(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    try:
        with torch.no_grad():
            outputs = model(**inputs)
    except Exception as exc:
        raise PredictionError(f"Error during model prediction: {exc}") from exc

    logits = outputs.logits
    probabilities = torch.nn.functional.softmax(logits, dim=-1)
    scam_prob = probabilities[0][1].item()
    logger.debug("Scam probability: %.4f", scam_prob)
    return scam_prob
