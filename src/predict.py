# predict.py (MODIFIED with Extensive Logging)
import io
import torch
import speech_recognition as sr
import librosa
import soundfile as sf

def get_status_details(scam_prob):
    if scam_prob >= 0.8:
        return "Scam", "red"
    elif scam_prob >= 0.4:
        return "Suspicious", "yellow"
    else:
        return "Safe", "green"

def convert_audio_to_wav(file_bytes, file_format):
    try:
        print(f"Attempting audio conversion. File format: {file_format}, File size: {len(file_bytes)} bytes") # LOGGING

        # Load audio using librosa, automatically resampling to 22050 Hz
        y, sr = librosa.load(io.BytesIO(file_bytes), sr=22050, mono=True, format=file_format) # Explicitly pass format

        print(f"Librosa load successful. Sample rate: {sr}, Audio shape: {y.shape}") # LOGGING

        # Convert to WAV format using soundfile
        wav_io = io.BytesIO()
        sf.write(wav_io, y, sr, format='WAV', subtype='PCM_16')
        wav_io.seek(0)

        print(f"WAV conversion successful. wav_io size: {wav_io.getbuffer().nbytes} bytes") # LOGGING
        return wav_io

    except Exception as e:
        print(f"Audio conversion error (librosa), File format: {file_format}: {e}") # LOGGING - Include file_format in error log
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