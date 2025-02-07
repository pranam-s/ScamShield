import io
import torch
import speech_recognition as sr
import librosa
import soundfile as sf
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

MODEL_NAME = "distilbert-base-uncased"
CACHE_DIR = "./hf_models"
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)

def get_status_details(scam_prob):
    """Determines scam status based on probability."""
    if scam_prob >= 0.8:
        return "Scam", "red"
    elif scam_prob >= 0.4:
        return "Suspicious", "yellow"
    else:
        return "Safe", "green"

def convert_audio_to_wav(file_path): # Modified: Accepts file_path
    """Converts audio to WAV format using librosa and soundfile, now from file path."""
    try:
        file_format = file_path.split('.')[-1].lower()
        print(f"Attempting audio conversion from path: {file_path}, Format: {file_format}") # LOGGING

        # Load audio using librosa from file path
        y, sr = librosa.load(file_path, sr=22050, mono=True) # Load from path, format inferred

        print(f"Librosa load successful. Sample rate: {sr}, Audio shape: {y.shape}") # LOGGING

        # Convert to WAV format using soundfile
        wav_io = io.BytesIO()
        sf.write(wav_io, y, sr, format='WAV', subtype='PCM_16')
        wav_io.seek(0)

        print(f"WAV conversion successful. wav_io size: {wav_io.getbuffer().nbytes} bytes") # LOGGING
        return wav_io

    except Exception as e:
        print(f"Audio conversion error (librosa), File path: {file_path}: {e}") # LOGGING - Include file_path in error log
        raise Exception(f"Error processing audio file: {e}")

def transcribe_audio(wav_file):
    """Transcribes WAV audio to text using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="auto")
        print(f"Transcription successful: {text[:50]}...") # Log first 50 chars
        return text
    except sr.UnknownValueError:
        raise Exception("Speech Recognition could not understand audio")
    except sr.RequestError as e:
        raise Exception(f"Could not request results from Speech Recognition service; {e}")

def predict_scam(text, model, device):
    """Predicts scam probability using the DistilBERT model."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    try:
        with torch.no_grad():
            outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        scam_prob = probabilities[0][1].item()
        print(f"Scam Probability: {scam_prob:.4f}") # Log probability
        return scam_prob
    except Exception as e:
        print(f"Model prediction error: {e}") # Log prediction errors
        raise Exception(f"Error during model prediction: {e}")