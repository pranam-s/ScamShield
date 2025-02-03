import io
import torch
import speech_recognition as sr
from pydub import AudioSegment

def get_status_details(scam_prob):
    # Return status and color based on scam probability thresholds:
    # >=0.8 -> red ("Scam"), between 0.4 and 0.8 -> yellow ("Suspicious"), <0.4 -> green ("Safe")
    if scam_prob >= 0.8:
        return "Scam", "red"
    elif scam_prob >= 0.4:
        return "Suspicious", "yellow"
    else:
        return "Safe", "green"

def convert_audio_to_wav(file_bytes, file_format):
    # Convert input audio file bytes to wav format for transcription
    try:
        audio = AudioSegment.from_file(io.BytesIO(file_bytes), format=file_format)
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        return wav_io
    except Exception as e:
        raise Exception(f"Error processing audio file: {e}")

def transcribe_audio(wav_file):
    # Convert audio input into text using SpeechRecognition
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
    # Tokenize the text and predict scam probability using the model
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probabilities = torch.nn.functional.softmax(logits, dim=-1)
    scam_prob = probabilities[0][1].item()
    return scam_prob