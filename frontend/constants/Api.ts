/**
 * Backend connection settings for the app.
 *
 * The detection endpoint used to be a hardcoded ngrok tunnel URL
 * (docs/AUDIT.md #19), which died with the hackathon tunnel and silently
 * swallowed every detection request. The base URL now lives here: change
 * `API_BASE_URL` to point at the machine running `uvicorn src.backend:app`
 * (for a device on your LAN, use your computer's IP instead of localhost).
 */

export const API_BASE_URL = 'http://localhost:8000';

export const DETECT_SCAM_ENDPOINT = `${API_BASE_URL}/detect-scam/`;

/** Recording chunk length in milliseconds (10 s balances latency vs. STT accuracy). */
export const CHUNK_INTERVAL_MS = 10_000;
