import io
import os
import sqlite3
import time
import uuid
import torch
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from pydub import AudioSegment
import speech_recognition as sr
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
from datetime import datetime, timedelta

# --- Configuration ---
MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"
MODEL_DIR = "model/scam_detector"
DATABASE_PATH = "scam_calls.db"
MAX_CONTEXT_TOKENS = 512
CONTEXT_TRUNCATION = 100  # Tokens to drop from start when exceeding MAX_CONTEXT_TOKENS
CHUNK_DURATION = 10  # seconds
ABANDONED_CALL_TIMEOUT = 30  # Seconds after which a call is considered abandoned
DATASET_VERSION = "1.0"

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
        # Add indexes for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_id ON call_records (call_id)")
        db.commit()

init_db()

# --- Model Loading ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
try:
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    print("Loaded fine-tuned model from:", MODEL_DIR)
    model_version = MODEL_DIR
except Exception as e:
    print(f"Could not load fine-tuned model: {e}. Loading pre-trained model.")
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2, cache_dir=CACHE_DIR)
    model_version = MODEL_NAME #default
model.to(device)
model.eval()

# --- In-Memory Call Context Storage ---
active_calls = {}  # {call_id: {context: "", chunk_count: 0, start_time: 0.0, last_chunk_time: 0.0}}

# --- FastAPI App ---
app = FastAPI(title="Scam Detection API")

# --- Helper Functions ---
def convert_audio_to_wav(file_bytes, file_format):
    try:
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format=file_format)
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        return wav_io
    except Exception as e:
        raise Exception(f"Error processing audio file: {e}")

def transcribe_audio(wav_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_file) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language="auto")
        return text
    except sr.UnknownValueError:
        raise Exception("Speech Recognition could not understand audio")
    except sr.RequestError as e:
        raise Exception(f"Could not request results from Speech Recognition service; {e}")

def predict_scam(text, model, tokenizer, device):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.nn.functional.softmax(logits, dim=-1)
    scam_prob = probabilities[0][1].item()
    return scam_prob

def get_status_details(scam_prob):
    if scam_prob >= 0.8:
        return "Scam", "red"
    elif scam_prob >= 0.4:
        return "Suspicious", "yellow"
    else:
        return "Safe", "green"

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

    # Combine previous context and new text
    full_context = active_calls[call_id]["context"] + " " + new_text

    # Tokenize and truncate if necessary
    tokens = tokenizer.tokenize(full_context)
    if len(tokens) > MAX_CONTEXT_TOKENS:
        truncated_tokens = tokens[len(tokens) - MAX_CONTEXT_TOKENS + CONTEXT_TRUNCATION:]
        full_context = tokenizer.convert_tokens_to_string(truncated_tokens)

    active_calls[call_id]["context"] = full_context
    active_calls[call_id]["chunk_count"] += 1
    active_calls[call_id]["last_chunk_time"] = time.time()
    active_calls[call_id]["chunks"].append(new_text)

    return full_context

# --- API Endpoints ---
@app.post("/detect-scam/")
async def detect_scam(
    file: UploadFile = File(...),
    call_id: str = Form(...),
    db: sqlite3.Connection = Depends(get_db)  # Database connection not used here, but good practice to keep
):
    """Detects scam probability in an audio chunk."""

    allowed_types = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/3gpp", "audio/m4a", "audio/ogg", "audio/flac"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid audio format.")

    file_bytes = await file.read()
    file_format = file.filename.split(".")[-1].lower()  # More robust format detection
    if file_format not in ["mp3", "wav", "3gp", "mpeg", "m4a", "ogg", "flac"]:
        file_format = "wav"

    try:
        wav_file = convert_audio_to_wav(file_bytes, file_format)
        transcription = transcribe_audio(wav_file)
        context = update_context(call_id, transcription, tokenizer) #update context
        scam_prob = predict_scam(context, model, tokenizer, device)  # Use CONTEXT
        status, _ = get_status_details(scam_prob)
        # No database interaction here, only in-memory updates

        return JSONResponse(content={"scam_probability": scam_prob, "status": status, "transcription": transcription})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-call/")
async def save_call(
    call_id: str = Form(...),
    caller_number: str = Form(None),
    user_feedback: str = Form(None),
    db: sqlite3.Connection = Depends(get_db)
):
    """Saves call data to the database after the call ends (with user consent)."""

    if call_id not in active_calls:
        raise HTTPException(status_code=404, detail="Call ID not found.")

    call_data = active_calls.pop(call_id)  # Retrieve AND remove from active_calls
    start_time = datetime.fromtimestamp(call_data['start_time'])
    end_time = datetime.now()
    duration = end_time.timestamp() - call_data['start_time']

    # Get the last status predicted
    if call_data['chunks']:
        last_chunk_text = call_data['chunks'][-1]
        last_scam_prob = predict_scam(last_chunk_text, model, tokenizer, device)
        final_status, _ = get_status_details(last_scam_prob)
    else:
        final_status = "Unknown" #no chunks

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
    abandoned_ids = []
    for call_id, call_data in active_calls.items():
        if now - call_data['last_chunk_time'] > ABANDONED_CALL_TIMEOUT:
            abandoned_ids.append(call_id)

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
    # Fetch model metadata from the database
    try:
        with sqlite3.connect(DATABASE_PATH) as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM model_metadata ORDER BY model_id DESC LIMIT 1")  # Get the latest model
            model_data = cursor.fetchone()

            if model_data:
                info = {
                    "model_name": model_data['model_name'],
                    "training_date": model_data['training_date'],
                    "dataset_version": model_data['dataset_version'],
                    "accuracy": model_data['accuracy'],
                    "training_epochs": model_data['training_epochs'],
                    "number_labels": model_data['number_labels']
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