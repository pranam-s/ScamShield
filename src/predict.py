import io
import torch
import speech_recognition as sr
from pydub import AudioSegment
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

def convert_audio_to_wav(input_data, file_format=None):
    """
    Converts audio to WAV format.
    If input_data is a file path (str), conversion is based on the filename extension.
    If input_data is bytes, file_format must be provided.
    Uses pydub for conversion.
    """
    if isinstance(input_data, bytes):
        if not file_format:
            raise ValueError("file_format must be provided when converting from bytes.")
        audio = AudioSegment.from_file(io.BytesIO(input_data), format=file_format)
    else:
        # input_data is assumed to be a file path
        file_format = file_format or input_data.split('.')[-1].lower()
        audio = AudioSegment.from_file(input_data, file_format)
    
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)
    return wav_io

def transcribe_audio(wav_file):
    """Transcribes WAV audio to text using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_file) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language="auto")
        print(f"Transcription successful: {text[:50]}...")
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
        print(f"Scam Probability: {scam_prob:.4f}")
        return scam_prob
    except Exception as e:
        print(f"Model prediction error: {e}")
        raise Exception(f"Error during model prediction: {e}")
