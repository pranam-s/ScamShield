# Build log

Engineering history: what was built, what was tested, what was rejected and
why. Newest last. Point-in-time findings live in docs/AUDIT.md; measured
numbers in docs/EVALUATION.md and docs/STATUS.md.

## Phase 1 — hackathon build (original team)

The product was built end to end in a hackathon sprint: FastAPI backend,
DistilBERT classifier, SQLite storage, Gradio demo, Expo app. The sprint
left behind the debt the audit would later catalogue — an ngrok tunnel URL
hardcoded in the recording screen, a venv committed to git, plaintext
caller numbers, no migration story, and frontend dependencies pinned to
whatever the SDK 52 scaffold resolved on day one.

## Phase 2 — audit and privacy remediation (2026-09, AUDIT #1–#29)

A line-by-line audit (docs/AUDIT.md) drove a series of fixes, the largest
being #21: caller numbers are now stored only as keyed HMAC-SHA256 hashes
(missing key → hard 503, never plaintext fallback), legacy plaintext
values are scrubbed on init, and a 30-day retention purge deletes aged
call records. Alternatives weighed at the time: reversible encryption of
numbers (rejected — YAGNI on recoverability nobody asked for) and dropping
numbers entirely (rejected — dedup stays useful under a keyed hash).

## Phase 3 — Dependabot triage and the SDK question (2026-09-17)

The GitHub triage pass reduced 164 alerts to 34 by re-locking inside the
SDK 52 ranges, and showed the remaining 34 could only clear by crossing
the Expo SDK major — the scaffold pins transitive versions, so hand-bumping
fights the SDK. The upgrade itself was left as recorded planned work.

## Phase 4 — production-completion pass (2026-09-18)

### Python backend

- **Datetime adapter warnings fixed at the boundary.** The sqlite3
  "default datetime adapter is deprecated" warnings (12 in tests) came
  from passing raw datetimes in `save_call`. Fix: timestamps cross the
  boundary as `YYYY-MM-DD HH:MM:SS` strings through one helper,
  `db.to_sqlite_timestamp`, shared with the retention purge — text
  ordering equals time ordering, so the purge comparison is unchanged.
  Two alternative shapes were rejected: registering sqlite3 adapters
  globally (mutates process-wide state for one call site) and storing
  epoch floats (silent format change for any existing rows).
- **The remaining 2 warnings are upstream-internal** (starlette's anyio
  alias, SpeechRecognition's aifc notice) and are documented, not
  suppressed. One was fixable for real: starlette's testclient wanted the
  `httpx2` package, so the dev dependency moved from `httpx` to `httpx2`.
- **deptry + vulture adopted** with justified configuration; the scan
  exposed two imports riding transitively (pydantic, numpy) — both now
  declared.
- **Real-run verification** (recorded in docs/STATUS.md): the server came
  up on a fresh database, `/health/`, `/model-info/`, `/education/`,
  `/abandoned-calls/` answered; `/detect-scam/` was exercised with a
  synthetic tone (honest 422: "could not understand the audio") and with a
  real speech WAV, which came back 200 with a correct transcription and a
  base-model score — the full production pipeline, no stubs.
- A `/save-call/` request for an unknown call id correctly 404s: saving
  completes a call the app itself tracked (in-memory registry), it is not
  a free-form insert endpoint.

### Expo frontend: SDK 52 → 57 (docs/adr/0001)

The recorded decision was executed in one jump: `npm install expo@^57`,
`npx expo install --fix`, `expo-doctor` (21/21 after installing the
`expo-asset` and `react-native-worklets` peers and removing
`newArchEnabled` — New Architecture is the only mode in SDK 57 — and a
template-placeholder slug that failed the schema). What the jump actually
required, found by typecheck and by reading installed package code:

- **expo-av → expo-audio.** The chunked recording screen was rewritten on
  `useAudioRecorder` + `AudioModule` permissions. The chunk read moved
  from expo-file-system's legacy `readAsStringAsync` (which now throws at
  runtime — deprecated stubs in the root export) to `File.arrayBuffer()`
  plus a small `btoa` encoder over 32 KB slices.
- **Standalone React Navigation removed.** expo-router 57 vendors the
  stack and no longer declares the packages as peers, so the tab-bar
  helpers import from the vendored modules; the type conflicts that
  motivated this showed up as `BottomTabBarButtonProps` mismatches.
- **React 19 template fallout fixed at the root:** the RN `ColorSchemeName`
  union gained `'unspecified'` (theme hooks resolve it explicitly), an
  Ionicons glyph was renamed, a latent `Colors[...].secondary` lookup
  referenced a key that never existed, and the deprecated
  react-test-renderer snapshot test was replaced with an async
  @testing-library/react-native test (v14's `render` returns a promise).
- **Knip dead-code pass:** seven unused template components deleted, eight
  unused dependencies dropped, and the platform-file reality (`.ios.tsx`,
  `.web.ts` overrides) encoded in `knip.json`.
- **Real-run verification:** `expo export --platform web` builds all
  routes; the exported bundle was served and driven in headless Chromium,
  and the screenshots in docs/screenshots/ come from that run. The run
  also caught a real bug — the call screen's action image rendered at
  full intrinsic size because its style was never applied — fixed and
  re-verified in the same pass.
- **Dependabot:** the aligned SDK 57 lockfile is what the remaining 34
  alerts were gated on; re-scan after push is owner-side.

### Deliberately not done

- **NativeTabs migration** (the new SDK 57 template default): rejected —
  it changes product UX for no correctness gain.
- **Training a real model:** needs a training run the repo documents but
  does not fabricate; `/model-info/` stays honestly empty until then.
- **Incremental 52→53→…→57:** rejected in ADR-0001 for a CNG app with no
  native directories.
