"""ScamShield FastAPI backend.

Detects scam phone calls from audio chunks: audio -> WAV -> speech-to-text
-> DistilBERT scam probability -> colour-coded status.

Heavy resources (the transformer model and the SQLite schema) are loaded in
the FastAPI lifespan handler rather than at import time, so importing this
module is cheap and unit tests can substitute fakes.
"""

from __future__ import annotations

import base64
import binascii
import logging
import sqlite3
import threading
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any

import filetype
import torch
import uvicorn
from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import config
import db
from predict import (
    PredictionError,
    TranscriptionError,
    convert_audio_to_wav,
    get_status_details,
    predict_scam,
    transcribe_audio,
)

logger = logging.getLogger(__name__)


class ScamDetectionRequest(BaseModel):
    call_id: str
    base64: str


# --- Model loading -----------------------------------------------------------


def load_model() -> tuple[Any, Any, str]:
    """Load the fine-tuned model, falling back to the pre-trained base model.

    Returns ``(tokenizer, model, model_version_name)``.
    """
    from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

    tokenizer = DistilBertTokenizer.from_pretrained(
        config.MODEL_NAME, cache_dir=str(config.CACHE_DIR)
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    try:
        model = DistilBertForSequenceClassification.from_pretrained(str(config.MODEL_DIR))
        model_version_name = str(config.MODEL_DIR)
        logger.info("Loaded fine-tuned model from %s", config.MODEL_DIR)
    except Exception as exc:
        logger.warning(
            "Could not load fine-tuned model (%s); falling back to pre-trained %s. "
            "Run src/train.py to produce real weights.",
            exc,
            config.MODEL_NAME,
        )
        model = DistilBertForSequenceClassification.from_pretrained(
            config.MODEL_NAME, num_labels=2, cache_dir=str(config.CACHE_DIR)
        )
        model_version_name = config.MODEL_NAME
    model.to(device)
    model.eval()
    return tokenizer, model, model_version_name


# --- Module-level resources (populated by lifespan, replaceable in tests) ----

tokenizer: Any | None = None
model: Any | None = None
model_version: str | None = None
device: torch.device | None = None

active_calls: dict[str, dict[str, Any]] = {}
_active_calls_lock = threading.Lock()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global tokenizer, model, model_version, device
    db.init_db()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer, model, model_version = load_model()
    yield


app = FastAPI(title="Scam Detection API", lifespan=lifespan)


def get_db() -> Any:
    database = db.connect()
    try:
        yield database
    finally:
        database.close()


DbConn = Annotated[Any, Depends(get_db)]


def update_context(call_id: str, new_text: str, tok: Any) -> str:
    """Append ``new_text`` to a call's rolling conversation context."""
    with _active_calls_lock:
        if call_id not in active_calls:
            active_calls[call_id] = {
                "context": "",
                "chunk_count": 0,
                "start_time": time.time(),
                "last_chunk_time": time.time(),
                "chunks": [],
            }

        call_state = active_calls[call_id]
        full_context = f"{call_state['context']} {new_text}".strip()
        tokens = tok.tokenize(full_context)
        if len(tokens) > config.MAX_CONTEXT_TOKENS:
            keep_from = len(tokens) - config.MAX_CONTEXT_TOKENS + config.CONTEXT_KEEP_TOKENS
            full_context = tok.convert_tokens_to_string(tokens[keep_from:])
        call_state["context"] = full_context
        call_state["chunk_count"] += 1
        call_state["last_chunk_time"] = time.time()
        call_state["chunks"].append(new_text)
        return full_context


# --- Endpoints ---------------------------------------------------------------


@app.post("/detect-scam/")
def detect_scam(request: ScamDetectionRequest) -> JSONResponse:
    """Detect scam probability for one audio chunk of an ongoing call."""
    if model is None or tokenizer is None or device is None:
        raise HTTPException(status_code=503, detail="Model is not loaded yet.")

    try:
        file_bytes = base64.b64decode(request.base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid base64 payload: {exc}") from exc

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload.")
    if len(file_bytes) > config.MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio payload exceeds the size limit.")

    kind = filetype.guess(file_bytes)
    if not kind:
        raise HTTPException(
            status_code=400, detail="Could not detect file type from provided data."
        )
    if kind.extension not in config.ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file format. Allowed formats: {', '.join(sorted(config.ALLOWED_AUDIO_FORMATS))}",
        )

    try:
        wav_file = convert_audio_to_wav(file_bytes, file_format=kind.extension)
        transcription = transcribe_audio(wav_file)
    except TranscriptionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    context = update_context(request.call_id, transcription, tokenizer)
    try:
        scam_prob = predict_scam(context, model, device)
    except PredictionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    status, _ = get_status_details(scam_prob)
    return JSONResponse(
        content={"scam_probability": scam_prob, "status": status, "transcription": transcription}
    )


@app.post("/save-call/")
def save_call(
    database: DbConn,
    call_id: Annotated[str, Body()],
    caller_number: Annotated[str | None, Body()] = None,
    user_feedback: Annotated[str | None, Body()] = None,
) -> JSONResponse:
    """Persist a finished call (with optional user feedback) to the database."""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call ID not found.")

    with _active_calls_lock:
        call_data = active_calls.pop(call_id)

    start_time = datetime.fromtimestamp(call_data["start_time"])
    end_time = datetime.now()
    duration = end_time.timestamp() - call_data["start_time"]

    final_status = "Unknown"
    if call_data["chunks"]:
        last_chunk_text = call_data["chunks"][-1]
        try:
            last_scam_prob = predict_scam(last_chunk_text, model, device)
            final_status, _ = get_status_details(last_scam_prob)
        except (PredictionError, TypeError) as exc:
            logger.warning("Could not score final chunk for call %s: %s", call_id, exc)

    cursor = database.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO call_records (
                call_id, start_time, end_time, duration, caller_number,
                full_transcription, user_feedback, final_status, model_version_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                call_id,
                start_time,
                end_time,
                duration,
                caller_number,
                call_data["context"],
                user_feedback,
                final_status,
                model_version,
            ),
        )
        database.commit()
        return JSONResponse(content={"message": "Call data saved successfully."})
    except sqlite3.Error as exc:
        database.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
    finally:
        cursor.close()


@app.get("/abandoned-calls/")
async def abandoned_calls() -> JSONResponse:
    """Drop call sessions that have not received a chunk recently."""
    now = time.time()
    with _active_calls_lock:
        abandoned_ids = [
            call_id
            for call_id, call_data in active_calls.items()
            if now - call_data["last_chunk_time"] > config.ABANDONED_CALL_TIMEOUT_SECONDS
        ]
        for call_id in abandoned_ids:
            del active_calls[call_id]
    if abandoned_ids:
        logger.info("Removed %d abandoned call(s)", len(abandoned_ids))
    return JSONResponse(content={"message": f"Removed {len(abandoned_ids)} abandoned calls."})


@app.get("/education/")
async def education_info() -> HTMLResponse:
    content = """
    <h2>Scam Detection Educational Module</h2>
    <p>This module explains the warning signs of scam calls:</p>
    <ul>
        <li>Urgency and pressure tactics</li>
        <li>Requests for confidential data</li>
        <li>Unsolicited contact and suspicious offers</li>
    </ul>
    <p>Always verify the identity of the caller and do not share sensitive information over the phone.</p>
    """
    return HTMLResponse(content=content)


@app.get("/health/")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "message": "Scam Detection API is running."}


@app.get("/model-info/")
def model_info(database: DbConn) -> JSONResponse:
    """Return the most recent training metadata recorded by train.py."""
    try:
        row = database.execute(
            "SELECT * FROM model_metadata ORDER BY model_id DESC LIMIT 1"
        ).fetchone()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    if row:
        info: dict[str, Any] = {
            "model_name": row["model_name"],
            "training_date": row["training_date"],
            "dataset_version": row["dataset_version"],
            "accuracy": row["accuracy"],
            "training_epochs": row["training_epochs"],
            "number_labels": row["number_labels"],
        }
    else:
        info = {
            "model_name": "No model metadata found",
            "training_date": None,
            "dataset_version": None,
            "accuracy": None,
            "training_epochs": None,
            "number_labels": None,
        }
    return JSONResponse(content=info)


def run_fastapi() -> None:
    uvicorn.run(app, host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_fastapi()
