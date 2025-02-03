import io
import torch
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from train import train_model
from predict import convert_audio_to_wav, transcribe_audio, predict_scam, get_status_details

# Load model and tokenizer for backend use
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model, tokenizer = train_model()
model.to(device)
model.eval()

app = FastAPI(title="Scam Detection API")

@app.post("/detect-scam/")
async def detect_scam(file: UploadFile = File(...)):
    # Validate input audio and process scam detection
    if file.content_type not in ["audio/mpeg", "audio/mp3", "audio/wav"]:
        raise HTTPException(status_code=400, detail="Invalid audio format. Only MP3 and WAV are supported.")
    file_bytes = await file.read()
    file_format = "mp3" if file.content_type in ["audio/mpeg", "audio/mp3"] else "wav"
    try:
        wav_file = convert_audio_to_wav(file_bytes, file_format)
        transcription = transcribe_audio(wav_file)
        scam_prob = predict_scam(transcription, model, tokenizer, device)
        status, _ = get_status_details(scam_prob)
        return JSONResponse(content={"scam_probability": scam_prob, "status": status})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/education/")
async def education_info():
    # Provide educational content about scam detection as HTML
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
    # Check API service health
    return {"status": "ok", "message": "Scam Detection API is running."}

@app.get("/model-info/")
async def model_info():
    # Return basic information about the model used
    info = {
        "model_name": "DistilBERT for Scam Detection",
        "num_labels": 2,
        "training_epochs": 5
    }
    return JSONResponse(content=info)

def run_fastapi():
    # Start the FastAPI server using uvicorn on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Run FastAPI backend if this module is executed directly
    run_fastapi()