# Contributing

Thanks for considering a contribution to ScamShield. Review may be slow,
but every change is held to the same bar as the code already here.

## Ground rules

- **Tests stay offline.** The suite must never download model weights or
  call external services; ML boundaries are stubbed (see
  `tests/conftest.py`).
- **No import-time side effects.** Models and the database load in the
  FastAPI lifespan, not at module import.
- **No hacks.** No placeholders, no stubs treated as done, no suppressed
  warnings or skipped tests. If a rule fires, fix the cause or argue why
  the rule is wrong — in the open.
- **Timestamps** cross the sqlite3 boundary as strings via
  `db.to_sqlite_timestamp` (sqlite3's default adapters are deprecated).
- **Caller numbers are never stored in plaintext** (keyed HMAC; missing
  key is a hard 503, never a fallback).
- Frontend changes follow docs/style-guides/typescript-react-native.md;
  accessibility regressions are release blockers.

## Setup

```bash
uv sync --all-groups          # backend
cd frontend && npm ci         # frontend
```

## Quality gates (all required before a commit)

Backend (from the repo root):

```bash
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy src
uv run deptry . && uv run vulture src --min-confidence 80
uv run pytest --cov=src
```

Frontend (from `frontend/`):

```bash
npx tsc --noEmit
npx jest
npx knip --no-progress
npx expo-doctor
```

## Commit style

Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore(deps):`,
`ci:`), one logical change per commit.

## Security issues

Do not open a public issue; use GitHub's private security advisory.
