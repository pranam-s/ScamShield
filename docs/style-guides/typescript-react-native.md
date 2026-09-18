# TypeScript / React Native style guide (frontend)

Binding conventions for `frontend/`. The Python side has its own guide
(python.md). Where Expo's own template code disagrees with this document,
this document wins.

## Toolchain

- **TypeScript strict.** `npx tsc --noEmit` must be clean; no
  `@ts-ignore`/`@ts-expect-error`/suppressions without a documented,
  reviewed reason for that exact site.
- **jest via jest-expo** for component tests. Use
  `@testing-library/react-native` (not react-test-renderer, which React 19
  has deprecated). Remember v14's `render` is async — `await render(...)`.
- **Knip** (`npx knip`) must run clean. `knip.json` lists the RN platform
  files (`.ios.tsx`, `.web.ts`) as entries; platform twins of a used file
  belong there, not in an ignore list.
- **expo-doctor** must pass after any dependency change.

## Dependencies

- Versions come from Expo's bundled dependency table for the current SDK
  (`node_modules/expo/bundledNativeModules.json`), applied via
  `npx expo install`. Do not hand-pin React Native ecosystem versions.
- Every declared dependency must be imported somewhere, consumed by a
  config file, or removed. Helpers that Expo Router itself now vendors
  (React Navigation) are imported from `expo-router/build/react-navigation/*`
  instead of adding standalone packages.
- Never inline an endpoint URL in a screen. Backend addresses live in
  `constants/Api.ts`.

## React and Expo conventions

- Function components only; hooks for side effects; no class components.
- Prefer Expo modules over community equivalents when both exist
  (expo-audio over expo-av, expo-file-system's `File` API over the legacy
  functions, expo-crypto for randomness).
- Legacy API shims that throw at runtime (expo-file-system root exports)
  are not options; use the modern API the SDK ships.
- Platform differences are expressed with file extensions
  (`TabBarBackground.tsx` + `TabBarBackground.ios.tsx`), not runtime
  `Platform.OS` branching, when the difference is a whole component.

## Accessibility (non-negotiable)

- Every interactive element gets `accessibilityRole` and an
  `accessibilityLabel`; stateful controls add `accessibilityState`
  (e.g. `{ busy: isRecording }`).
- State is never conveyed by colour alone: a colour-coded status also
  carries its text (see the "Flagged" label in `app/call.tsx`).
- Decorative emoji and images must not be the only carrier of meaning;
  emoji used as bullet decoration are removed, not labelled.
- The app is keyboard/D-pad navigable because it uses real focusable
  controls — never break that with a View + onPress.

## Testing

- Tests run offline and stay offline.
- Assert behavior through the accessibility tree (`getByRole`,
  `getByText`) rather than implementation details.
- No snapshot-only tests; a snapshot that nobody would review on change is
  dead weight (the react-test-renderer snapshot was replaced by an
  on-screen assertion for exactly this reason).
