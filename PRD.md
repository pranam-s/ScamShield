# PRD — ScamShield: Real-Time Scam Call Detection

**Owner:** Team TechnoTitans · **Status:** hackathon prototype, actively hardened
**Last updated:** 2026-09-14

## 1. Problem

Phone-based fraud is a mass-market crime that disproportionately harms the
people least equipped to resist it:

* **Vulnerable populations are the target.** Elderly users, first-time
  smartphone owners, and non-English speakers are systematically targeted by
  caller-ID spoofing, bank/KYC impersonation and OTP-harvesting scripts.
  Existing defences (number blocking, carrier spam flags) only act on the
  *identity* of the caller — they do nothing against a scammer calling from
  a fresh number, and nothing during the live conversation.
* **The attack is conversational.** Modern scams are social-engineering
  scripts: manufactured urgency ("your account will be blocked in 30
  minutes"), authority impersonation ("I am calling from your bank"),
  and extraction of one-time passwords or remote-access installs. Detecting
  this requires understanding the *content* of the call, not its metadata.
* **Victims lack a feedback loop.** Scam education is usually after the fact.
  Users asked for in-the-moment guidance and a way to learn the warning
  signs.

Our own pre-hackathon survey (`form 1.jpg`, `form2.jpg`) echoed this:
respondents reported frequent scam attempts against family members and
overwhelmingly requested real-time warnings plus built-in education.

## 2. Product goal

Reduce successful phone-scam victimisation by warning a user **during the
call**, in plain language, with an action they can take immediately.

## 3. Users and scenarios

| User | Scenario | Need |
|---|---|---|
| Elderly / non-tech-savvy user | "Bank officer" asks for OTP over a call | Clear red/green signal + simple instruction (hang up) |
| Family member / caregiver | Wants parents protected remotely | Reliable detection, education content they can share |
| User who already took a suspicious call | Unsure if it was a scam | Call history, verdicts, and scam-education module |

## 4. Scope

### In scope (current prototype)

1. **Real-time detection API** (`/detect-scam/`): base64 audio chunk in →
   transcript + scam probability + colour-coded status out, with rolling
   per-call conversation context (512-token window).
2. **Call record storage** (`/save-call/`): transcript, verdict and optional
   user feedback stored in SQLite *after* the call, with consent.
3. **Adaptive retraining**: feedback labels ("correct"/"incorrect") are
   converted to training examples and merged into the dataset on retrain.
4. **Education module**: scam warning signs and protection tips (API +
   Gradio tab + mobile screens).
5. **Mobile app** (Expo/React Native) and a **Gradio demo UI** for
   desktop testing.
6. **Dataset & training pipeline** (`src/dataset_setup.py`, `src/train.py`)
   on a 1,245-record English scam/normal dataset.

### Out of scope (for now)

* On-device inference (current pipeline is cloud/demo-hosted).
* Non-English transcription/classification (STT language is configurable;
  training data is English-only today).
* Carrier/telephony integration (call audio capture relies on the mobile
  app's recording capability).
* Automated scammer number reporting to authorities.

## 5. Functional requirements

1. Detect per audio chunk within a call session identified by `call_id`.
2. Classification thresholds: ≥0.8 Scam (red), ≥0.4 Suspicious (yellow),
   else Safe (green) — shared by backend, Gradio UI and app.
3. Conversation context must survive across chunks of the same call
   (truncated to the most recent ~512 tokens).
4. Stale sessions (>30 s without a chunk) must be reclaimable.
5. User feedback must be stored and usable for retraining without
   re-labelling the base dataset.
6. Invalid input (bad base64, unknown/disallowed audio type, oversized
   payloads) must fail fast with 4xx responses — never 500.

## 6. Non-functional requirements

* **Safety-first failure mode:** if the model or STT is unavailable the API
  must say so (503/502), never guess.
* **Privacy:** audio is transient; transcripts stored only via explicit
  save; caller numbers are PII and are stored only as keyed hashes, never
  plaintext, with a 30-day retention purge (residual limitation in
  EVALUATION.md §3).
* **Quality gates:** ruff + mypy clean, pytest offline-safe, ≥90 % line
  coverage on core modules, enforced in CI.

## 7. Success criteria

* Detection pipeline returns a verdict for a 3–10 s audio chunk on CPU
  without event-loop blocking.
* Zero 500s on the documented invalid-input paths (covered by tests).
* A trained model whose eval accuracy is recorded in `model_metadata` and
  served by `/model-info/` (see EVALUATION.md for the honest current status).
* Core-module test coverage ≥90 % in CI (currently 100 %).

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| False positives annoy users; false negatives cost money | Two-tier yellow/red thresholds; user feedback loop for tuning |
| STT errors degrade classification | Transcription failure returns 422 rather than a wrong verdict |
| Model drift as scam scripts change | Retrain path folds in feedback (`train_model(retrain=True)`) |
| PII exposure from stored transcripts/numbers | Consent-gated saving; caller numbers keyed-hashed at rest + 30-day retention purge (AUDIT #21); transcripts remain plaintext until at-rest encryption is added |
