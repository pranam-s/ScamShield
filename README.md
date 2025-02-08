# 🛡️ ScamShield: Real-Time Scam Call Detection 🛡️


**Stop phone scams before they start.  ScamShield is an AI-powered mobile application that provides real-time protection against scam calls, especially for vulnerable users and those speaking Indian languages.**

## The Urgent Problem: Phone Scams are Exploding

Phone scams are a pervasive and devastating problem, with traditional spam filters offering no defense against live, conversational fraud. Scammers are sophisticated social engineers, and their tactics are becoming increasingly complex.  Our research underscores the urgency:

![Google form data](form 1.jpg)

## ScamShield:  AI-Powered Real-Time Protection

ScamShield is a revolutionary approach to phone security. We go beyond simple number blocking, using cutting-edge AI to analyze the *conversation itself* as it happens. ScamShield provides:

*   **Instant Scam Detection:**  Our fine-tuned DistilBERT AI model, leveraging Natural Language Processing, analyzes speech in real-time for scam indicators.
*   **Proactive, Actionable Alerts:**  When a scam is detected, ScamShield immediately alerts the user with clear warnings and suggests actions to take, empowering them to hang up and stay safe.
*   **Privacy-First Design:**  We prioritize user privacy. While demonstrating cloud deployment for this hackathon, our vision includes complete on-device processing for maximum security.
*   **Adaptive AI - Always Learning:** ScamShield's backend is built for continuous improvement. With user feedback, our AI model learns and adapts to new scam tactics, ensuring long-term protection.
*   **Empowering Education:**  ScamShield isn't just about technology; it's about user empowerment.  We include a built-in educational module to inform users about scam tactics and prevention, a feature users overwhelmingly requested.

![Google form data](form2.jpg)

## Under the Hood: How ScamShield Works

1.  **Live Call Analysis:**  Built with React Native, ScamShield seamlessly integrates with phone calls.
2.  **Real-Time Transcription:**  Audio is converted to text using advanced Speech-to-Text technology.
3.  **AI Brain:**  Our fine-tuned DistilBERT model analyzes the text for scam indicators like:
    *   OTP and personal information requests
    *   Urgency and pressure tactics
    *   Remote access software demands
    *   Suspicious offers or threats
4.  **Immediate Alerts:**  Based on AI analysis, ScamShield delivers instant, color-coded alerts: Green (Safe), Yellow (Suspicious), Red (Scam).

## Technology Powerhouse

*   **Frontend:** React Native & Expo (for cross-platform reach)
*   **Backend:** FastAPI (Python - for speed and scalability)
*   **AI Engine:** Fine-tuned DistilBERT (Hugging Face Transformers - state-of-the-art NLP)
*   **Speech-to-Text:** Google Speech Recognition
*   **Database:** SQLite (for metadata and adaptive learning data)
*   **Deployment:** Render (cloud-based for scalability demonstration)

## Get Started - Run ScamShield

**1. Install Dependencies:**

```bash
pip install -r requirements.txt
```

**(See `requirements.txt` in GitHub repository for full list)**

**2. Train the AI Model (Optional):**

```bash
python src/train.py
```

**3. Launch the Backend API:**

```bash
python src/backend.py
```

(API accessible at `http://0.0.0.0:8000`)

**4. Run the Gradio Demo Interface (for quick testing):**

```bash
python src/gradio_interface.py
```

**5. Start the Expo Frontend App:**

```bash
npx expo start
```

Expo credentials:
Username: gourang1
Password: Josh@123

(Follow Expo instructions to run on emulator/device)

## Project Impact and Future Vision

Our user research confirms the desperate need for real-time scam protection. ScamShield is not just a tech demo; it's a solution with real-world impact.

**Future Roadmap:**

*   **Full On-Device AI:**  Prioritize local AI processing for enhanced user privacy.
*   **Adaptive Learning Toggle:**  Give users control over data contribution for model improvement.
*   **Expand Language Support:**  Focus on comprehensive support for Indian languages and beyond.
*   **Advanced Alerting:**  Integrate emergency contacts and reporting features.
*   **Personalized Protection:**  User-customizable whitelists/blacklists and integration with existing security tools.

## Team TechnoTitans

We are TechnoTitans, driven by a passion to use technology to build a safer world. ScamShield is our commitment to protecting vulnerable individuals from the growing threat of phone scams.

## Project Structure

```
.
├── dataset.csv
├── model/
├── app/
└── src/
    ├── dataset_setup.py
    ├── train.py
    ├── predict.py
    ├── gradio_interface.py
    └── backend.py
```


---
