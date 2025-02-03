# ScamShield

Detect scam calls in real-time using AI—speech-to-text and NLP to safeguard Indian language users!

## Overview

This project is a prototype for detecting scam calls in real time using a fine-tuned DistilBERT model. It leverages speech-to-text transcription and natural language processing to predict the scam probability of an audio file. The project includes:

- **Data Setup**: Loading and tokenizing a dataset (`dataset.csv`) with entries in the top 10 Indian languages.
- **Model Training**: Fine-tuning a DistilBERT model with optimized training parameters. If a trained model exists in `model/scam_detector`, it is loaded instead of retraining.
- **User Interface**: A Gradio interface featuring two tabs:
  - **Detection Tab**: Upload an audio file (MP3/WAV) and view the transcript, scam probability, and a color-coded status (green for safe, yellow for suspicious, red for scam).
  - **Education Tab**: Detailed information about common scam call tactics and prevention tips.
- **FastAPI Backend**: A REST API backbone exposing endpoints for scam detection, educational content, health check, and model information.

## Project Structure

```
.
├── dataset.csv                 # Dataset file with 2000 entries
├── model/                      # Directory where the trained model is stored (scam_detector)
└── src/
    ├── __init__.py
    ├── dataset_setup.py        # Module for dataset loading & tokenization
    ├── train.py                # Module for model training & saving
    ├── predict.py              # Module for audio conversion, transcription, and prediction
    ├── gradio_interface.py     # Gradio interface with detection and educational modules
    └── backend.py              # FastAPI backend with API endpoints
```

## Setup Instructions

1. **Install Dependencies**

   Run the following commands to install required libraries:
   ```bash
   pip install transformers datasets torch scikit-learn fastapi uvicorn python-multipart SpeechRecognition pydub gradio
   ```

2. **Dataset**

   - Place your `dataset.csv` in the project root.
   - Ensure the CSV has a column named `"text"` containing the call transcripts.

3. **Train the Model**

   - To train (or load, if already saved) the model, run:
     ```bash
     python src/train.py
     ```
   - The model and tokenizer will be saved in the `model/scam_detector` directory.

4. **Launch the Gradio Interface**

   - To start the user-friendly interface, run:
     ```bash
     python src/gradio_interface.py
     ```
   - You will see a two-tab interface for audio-based scam detection and educational content.

5. **Run the FastAPI Backend**

   - To start the API server, execute:
     ```bash
     python src/backend.py
     ```
   - The API will be accessible at `http://0.0.0.0:8000` with endpoints such as:
     - `POST /detect-scam/` – for scam detection via audio upload.
     - `GET /education/` – for educational information.
     - `GET /health/` – for a health check.
     - `GET /model-info/` – for details about the model.

## Usage

- **Gradio Interface**
  - Navigate to the Detection tab to upload an audio file and get a transcription with scam probability.
  - The displayed result includes a color-coded status: **green** for safe (scam probability < 0.4), **yellow** for suspicious (0.4 to 0.8), and **red** for scam (≥ 0.8).
  - The Education tab offers best practices and warning signs to help avoid scam calls.

- **FastAPI Endpoints**
  - Use tools like Postman or cURL to interact with the backend API.
  - Example using cURL for scam detection:
    ```bash
    curl -X POST "http://0.0.0.0:8000/detect-scam/" -F "file=@your_audio_file.mp3"
    ```

## Additional Notes

- The code has been refactored to remove redundancy and improve clarity.
- Training parameters have been optimized (increased batch size and epochs) to enhance model accuracy.
- The Gradio interface has been beautified with a two-tab design and dynamic color indicators.
- The FastAPI backend is provided to demonstrate how the model can be deployed as an API.