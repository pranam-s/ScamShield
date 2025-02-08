import io
import os
import sqlite3
import time
import uuid
import base64
import filetype  
import torch
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi import Body
from pydantic import BaseModel
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
from datetime import datetime
from predict import convert_audio_to_wav, transcribe_audio, predict_scam, get_status_details
import mimetypes
import random

# --- Configuration ---
MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"
MODEL_DIR = "model/scam_detector"
DATABASE_PATH = "scam_calls.db"
MAX_CONTEXT_TOKENS = 512
CONTEXT_TRUNCATION = 100
ABANDONED_CALL_TIMEOUT = 30
DATASET_VERSION = "1.0"
ALLOWED_AUDIO_FORMATS = ["mp3", "wav", "3gp", "mpeg", "m4a", "ogg", "flac"]

class ScamDetectionRequest(BaseModel):
    call_id: str
    base64: str

# --- Database Setup ---
def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield db
    finally:
        db.close()

def init_db():
    with sqlite3.connect(DATABASE_PATH) as db:
        cursor = db.cursor()
        cursor.execute("""
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
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metadata (
                model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                training_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                dataset_version TEXT,
                accuracy REAL,
                training_epochs INTEGER,
                number_labels INTEGER
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_id ON call_records (call_id)")
        db.commit()

init_db()

# --- Model Loading ---
def load_model():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
    try:
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
        print("Loaded fine-tuned model from:", MODEL_DIR)
        model_version_name = MODEL_DIR
    except Exception as e:
        print(f"Could not load fine-tuned model: {e}. Loading pre-trained model.")
        model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2, cache_dir=CACHE_DIR)
        model_version_name = MODEL_NAME
    model.to(device)
    model.eval()
    return tokenizer, model, model_version_name

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer, model, model_version = load_model() 

# --- In-Memory Call Context Storage ---
active_calls = {}  # {call_id: {context: "", chunk_count: 0, start_time: 0.0, last_chunk_time: 0.0}}

def update_context(call_id: str, new_text: str, tokenizer) -> str:
    """Updates the conversation context for a given call_id."""
    if call_id not in active_calls:
        active_calls[call_id] = {
            "context": "",
            "chunk_count": 0,
            "start_time": time.time(),
            "last_chunk_time": time.time(),
            "chunks": []
        }

    full_context = active_calls[call_id]["context"] + " " + new_text
    tokens = tokenizer.tokenize(full_context)
    if len(tokens) > MAX_CONTEXT_TOKENS:
        truncated_tokens = tokens[len(tokens) - MAX_CONTEXT_TOKENS + CONTEXT_TRUNCATION:]
        full_context = tokenizer.convert_tokens_to_string(truncated_tokens)
    active_calls[call_id]["context"] = full_context
    active_calls[call_id]["chunk_count"] += 1
    active_calls[call_id]["last_chunk_time"] = time.time()
    active_calls[call_id]["chunks"].append(new_text)
    return full_context

# --- FastAPI App ---
app = FastAPI(title="Scam Detection API")

@app.post("/detect-scam/")
async def detect_scam(
    request: ScamDetectionRequest,
    db: sqlite3.Connection = Depends(get_db)
):
    """Detects scam probability in an audio chunk."""
    temp_file_path = None
    try:
        file_bytes = base64.b64decode(request.base64)
        kind = filetype.guess(file_bytes)
        if not kind:
            raise HTTPException(status_code=400, detail="Could not detect file type from provided data.")
        file_extension = kind.extension
        if file_extension not in ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_AUDIO_FORMATS)}"
            )

        wav_file = convert_audio_to_wav(file_bytes, file_format=file_extension)
        transcription = transcribe_audio(wav_file)
        context = update_context(call_id, transcription, tokenizer)
        scam_prob = predict_scam(context, model, device)
        status, _ = get_status_details(scam_prob)
        return JSONResponse(content={"scam_probability": scam_prob, "status": status, "transcription": transcription})
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error in detect_scam: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.post("/save-call/")
async def save_call(
    call_id: str = Body(...),
    caller_number: str = Body(None),
    user_feedback: str = Body(None),
    db: sqlite3.Connection = Depends(get_db)
):
    """Saves call data to the database after the call ends (with user consent)."""
    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call ID not found.")
    call_data = active_calls.pop(call_id)
    start_time = datetime.fromtimestamp(call_data['start_time'])
    end_time = datetime.now()
    duration = end_time.timestamp() - call_data['start_time']

    if call_data['chunks']:
        last_chunk_text = call_data['chunks'][-1]
        last_scam_prob = predict_scam(last_chunk_text, model, device)
        final_status, _ = get_status_details(last_scam_prob)
    else:
        final_status = "Unknown"

    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO call_records (
                call_id, start_time, end_time, duration, caller_number,
                full_transcription, user_feedback, final_status, model_version_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            start_time,
            end_time,
            duration,
            caller_number,
            call_data['context'],
            user_feedback,
            final_status,
            model_version
        ))
        db.commit()
        return JSONResponse(content={"message": "Call data saved successfully."})
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        cursor.close()

@app.get("/abandoned-calls/")
async def abandoned_calls():
    """Removes abandoned calls from the active_calls dictionary."""
    now = time.time()
    abandoned_ids = [call_id for call_id, call_data in active_calls.items() if now - call_data['last_chunk_time'] > ABANDONED_CALL_TIMEOUT]
    for call_id in abandoned_ids:
        active_calls.pop(call_id)
        print("Abandoned Removed")
    return JSONResponse(content={"message": f"Removed {len(abandoned_ids)} abandoned calls."})

@app.get("/education/")
async def education_info():
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
async def health_check():
    return {"status": "ok", "message": "Scam Detection API is running."}

@app.get("/model-info/")
async def model_info():
    try:
        with sqlite3.connect(DATABASE_PATH) as db:
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute("SELECT * FROM model_metadata ORDER BY model_id DESC LIMIT 1")
            model_data = cursor.fetchone()
            if model_data:
                info = {
                    "model_name": model_data["model_name"],
                    "training_date": model_data["training_date"],
                    "dataset_version": model_data["dataset_version"],
                    "accuracy": model_data["accuracy"],
                    "training_epochs": model_data["training_epochs"],
                    "number_labels": model_data["number_labels"]
                }
            else:
                info = {
                    "model_name": "No model metadata found",
                    "training_date": None,
                    "dataset_version": None,
                    "accuracy": None,
                    "training_epochs": None,
                    "number_labels": None
                }
            return JSONResponse(content=info)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_fastapi()
