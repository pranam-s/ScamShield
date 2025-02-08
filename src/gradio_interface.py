import gradio as gr
import torch
from train import train_model
from predict import convert_audio_to_wav, transcribe_audio, predict_scam, get_status_details
import mimetypes

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Load the model (this loads from MODEL_DIR if available)
model, tokenizer, _ = train_model()
model.to(device)
model.eval()

def scam_detection_interface(audio_file_path):
    try:
        # Determine the file format from the file path
        mime_type, _ = mimetypes.guess_type(audio_file_path)
        if mime_type:
            file_format = mime_type.split("/")[-1]
            if file_format == "mpeg": 
                file_format = "mp3"
            if file_format == "wave":
                file_format = "wav"
            if file_format == "3gpp":
                file_format = "3gp"
        else:
            file_format = "wav"  # Default

        # Read file bytes and convert to wav using pydub
        with open(audio_file_path, "rb") as f:
            file_bytes = f.read()

        wav_file = convert_audio_to_wav(file_bytes, file_format)
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
    except Exception as e:
        return f"Error: {str(e)}", ""

def education_module():
    content = """
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
    return content

with gr.Blocks(css="""
    .gradio-container {background-color: #f9f9f9; font-family: Arial, sans-serif; padding: 20px;}
    .tab-header {padding: 10px; background-color: #e6e6e6; border-radius: 5px;}
    .output-row {display: flex; gap: 20px;}
    .output-row > * {flex: 1;}
""") as demo:
    gr.Markdown("# Real-Time Scam Call Detection")
    gr.Markdown("Upload an audio file to check if it's a scam call and get a detailed analysis based on the audio transcription.")

    with gr.Tabs():
        with gr.TabItem("Detection"):
            gr.Markdown("## Upload an Audio File for Scam Detection")
            audio_input = gr.Audio(type="filepath", label="Select Audio File")
            with gr.Row():
                result_text_output = gr.Textbox(label="Detection Result", interactive=False)
                status_html_output = gr.HTML(label="Scam Status")
            detect_button = gr.Button("Detect Scam")
            detect_button.click(fn=scam_detection_interface, inputs=audio_input,
                                outputs=[result_text_output, status_html_output])
        with gr.TabItem("Education"):
            gr.Markdown("## Scam Prevention Information")
            education_output = gr.HTML(label="Educational Content", value=education_module())

    gr.Markdown("### Powered by Real-Time Scam Detection Prototype")

if __name__ == "__main__":
    demo.launch(share=True, debug=True)