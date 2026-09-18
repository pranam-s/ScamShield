# ADR-0001: Upgrade the Expo frontend from SDK 52 to SDK 57; migrate expo-av recording to expo-audio

Date: 2026-09-18
Status: Accepted
Related: docs/AUDIT.md #19 (dead ngrok URL), Dependabot triage 2026-09-17 (34 alerts gated on this upgrade)

## Context

The frontend is an Expo/React Native app left on SDK 52 (React Native 0.76.7,
React 18.3.1, jest-expo 52) from its hackathon scaffold. The 2026-09-17
Dependabot triage reduced 164 alerts to exactly 34, all of which are
npm-dependency alerts that can only clear by moving across the Expo SDK
major (the scaffold's transitive tree is pinned by the SDK). SDK 52 is also
past Expo Go support, so nobody can run the app from a fresh clone without
this work.

SDK 57 (current at the time of writing) ships React Native 0.86 and React
19.2. Upgrading from SDK 52 crosses several majors at once, which the Expo
docs advise against doing one version at a time only when you need to
pinpoint regressions in native code; this app has no custom native code (no
ios/android directories, no config plugins of its own), so the whole jump
lands in one pass and the risk concentrates in JavaScript API changes.

## Decision

1. **Upgrade in one jump to SDK 57** via the documented path:
   `npm install expo@^57.0.0` followed by `npx expo install --fix` (which
   aligns every expo-* / react / react-native package to the versions the
   SDK's bundled dependency table expects), then `npx expo-doctor` as the
   post-flight check. jest-expo is aligned to the SDK in the same pass.
2. **Migrate recording from expo-av to expo-audio.** expo-av is the
   deprecated audio/video package (deprecated SDK 53, removed from the SDK's
   aligned set), and expo-audio is its designated replacement. The chunked
   10-second recording flow in `app/recordscam.tsx` is rewritten against
   expo-audio's `useAudioRecorder` hook and `AudioModule` permissions API;
   the chunk→base64→POST pipeline and the alert UX are preserved.
3. **Delete dead native/JS dependencies** found during the upgrade audit:
   `react-native-fs`, `react-native-audio-record`, `uuid`, and
   `expo-random` are declared in package.json but imported nowhere (grep
   over app/, components/, hooks/, constants/). Call IDs are generated from
   `expo-crypto.getRandomBytesAsync`, which stays. `@types/react-native` is
   also dropped; React Native ships its own types.
4. **Move the detection endpoint URL out of a hardcoded ngrok string**
   (AUDIT #19) into `constants/` as the single API base URL constant with a
   localhost default, so the frontend targets the bundled backend instead of
   a dead tunnel.

## Alternatives considered

- **Incremental 52→53→54→55→56→57.** Rejected: its benefit (bisecting
  native regressions) does not apply to a CNG/managed app with no native
  directories; each intermediate step would still require resolving the
  same JavaScript migrations (expo-av, React 19), just more often.
- **Stay on SDK 52 and patch individual alerts.** Rejected: Expo's
  dependency table pins transitive versions; hand-bumping them fights the
  SDK and leaves the 34 alerts unresolvable. The whole point of the SDK
  upgrade is to clear them by adopting the aligned tree.
- **Replace react-native-fs usage instead of deleting it.** Moot: nothing
  imports it; audio reads already go through expo-file-system.

## Consequences

- React 18.3 → 19.2 and RN 0.76 → 0.86: `findNodeHandle`-era patterns and
  legacy lifecycle code would break, but this app uses only function
  components and Expo Router, so exposure is small; jest-expo 57 and
  `@types/react` move with the SDK.
- The app records audio in 10-second chunks exactly as before, but through
  the expo-audio lifecycle; recordings land in the cache directory by
  default, which matches the existing transient-chunk design.
- Dependabot alerts on the old scaffold tree are expected to clear once the
  aligned SDK 57 lockfile lands, verified by re-scan after push.
