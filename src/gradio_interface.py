"""Gradio demo UI: upload an audio file, get a scam verdict plus education tab."""

from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any

import gradio as gr
import torch

from predict import (
    convert_audio_to_wav,
    get_status_details,
    predict_scam,
    transcribe_audio,
)
from train import train_model

logger = logging.getLogger(__name__)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_resources: tuple[Any, Any] | None = None


def get_resources() -> tuple[Any, Any]:
    """Load (or train, if no weights exist) the model on first use."""
    global _resources
    if _resources is None:
        model, tokenizer, _ = train_model()
        model.to(device)
        model.eval()
        _resources = (model, tokenizer)
    return _resources


def guess_audio_format(file_path: str) -> str:
    """Map a file path to a pydub-compatible format name."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type or "/" not in mime_type:
        return "wav"  # sensible default for unlabeled uploads
    fmt = mime_type.split("/")[-1]
    return {"mpeg": "mp3", "wave": "wav", "3gpp": "3gp", "x-wav": "wav", "aac": "adts"}.get(
        fmt, fmt
    )


def scam_detection_interface(audio_file_path: str) -> tuple[str, str]:
    model, _tokenizer = get_resources()
    try:
        file_format = guess_audio_format(audio_file_path)
        file_bytes = Path(audio_file_path).read_bytes()

        wav_file = convert_audio_to_wav(file_bytes, file_format=file_format)
        transcription = transcribe_audio(wav_file)
        scam_prob = predict_scam(transcription, model, device)
        status, color = get_status_details(scam_prob)

        status_box_html = f"""
        <div style="padding: 10px; border: 1px solid #ccc; border-radius: 8px; display: flex; align-items: center; background-color: #fff;">
            <div style="flex:1; font-weight: bold; color: {color};">{status}</div>
            <div style="width: 20px; height: 20px; border-radius: 50%; background-color: {color};"></div>
        </div>
        """
        result_text = f"Transcription: {transcription}\nScam Probability: {scam_prob:.2f}"
        return result_text, status_box_html
    except Exception as exc:
        logger.exception("Detection failed")
        return f"Error: {exc}", ""


def education_module() -> str:
    return """
    <h2>Scam Detection Educational Module</h2>
    <p>This module provides information on how to identify scam calls and avoid fraud.</p>
    <h3>Common Signs of Scam Calls:</h3>
    <ul>
        <li><strong>Urgency:</strong> Scammers create urgency to force quick decisions.</li>
        <li><strong>Request for personal details:</strong> Asking for bank details, OTPs, or personal data.</li>
        <li><strong>Unsolicited contact:</strong> Unexpected calls or messages offering rewards or threats.</li>
        <li><strong>Pressure tactics:</strong> Pushing you to act immediately without time to verify.</li>
    </ul>
    <h3>Protection Tips:</h3>
    <ul>
        <li>Never share sensitive information over the phone.</li>
        <li>Verify the caller using official contact channels.</li>
        <li>Do not rush; take your time to assess any request.</li>
        <li>Report suspicious communication to relevant authorities.</li>
    </ul>
    <p>This project leverages machine learning to help detect scam calls in real time using audio analysis and NLP.</p>
    """


with gr.Blocks(
    css="""
    .gradio-container {background-color: #f9f9f9; font-family: Arial, sans-serif; padding: 20px;}
    .tab-header {padding: 10px; background-color: #e6e6e6; border-radius: 5px;}
    .output-row {display: flex; gap: 20px;}
    .output-row > * {flex: 1;}
"""
) as demo:
    gr.Markdown("# Real-Time Scam Call Detection")
    gr.Markdown(
        "Upload an audio file to check if it's a scam call and get a detailed "
        "analysis based on the audio transcription."
    )

    with gr.Tabs():
        with gr.TabItem("Detection"):
            gr.Markdown("## Upload an Audio File for Scam Detection")
            audio_input = gr.Audio(type="filepath", label="Select Audio File")
            with gr.Row():
                result_text_output = gr.Textbox(label="Detection Result", interactive=False)
                status_html_output = gr.HTML(label="Scam Status")
            detect_button = gr.Button("Detect Scam")
            detect_button.click(
                fn=scam_detection_interface,
                inputs=audio_input,
                outputs=[result_text_output, status_html_output],
            )
        with gr.TabItem("Education"):
            gr.Markdown("## Scam Prevention Information")
            education_output = gr.HTML(label="Educational Content", value=education_module())

    gr.Markdown("### Powered by Real-Time Scam Detection Prototype")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # share=True exposes a public gradio tunnel; enable only for demos.
    demo.launch(share=True, debug=True)
