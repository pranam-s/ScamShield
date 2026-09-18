# Python style guide: ScamShield

Toolchain-enforced conventions for this repository. Anything marked
"enforced" is checked by ruff/mypy in CI (`.github/workflows/ci.yml`).

## Tooling

| Concern | Tool | Config |
|---|---|---|
| Lint | `ruff check` | `pyproject.toml → [tool.ruff.lint]` |
| Format | `ruff format` | line length 100 |
| Types | `mypy src` | `[tool.mypy]`, third-party ML libs ignored |
| Tests | `pytest` | `pythonpath = ["src"]`, tests in `tests/` |
| Deps | `uv` | locked in `uv.lock`, committed |

## Formatting

* 100-character lines (ruff format decides final wrapping; E501 is ignored
  in favour of the formatter's judgement).
* Double quotes, trailing commas, LF endings.
* Two blank lines between top-level definitions, one between methods.

## Naming

* `snake_case` functions/variables/modules, `PascalCase` classes,
  `UPPER_SNAKE_CASE` module constants.
* Booleans read as predicates: `is_loaded`, `has_feedback`.
* Constants shared across modules belong in `src/config.py`, not
  re-declared locally (historical bug source in this repo).

## Imports

* Order (ruff isort enforced): `__future__` → stdlib → third-party →
  first-party (`config`, `db`, `predict`, …) → local `from` imports.
* No wildcard imports; no unused imports (F401 enforced).
* Lazy imports are acceptable **only** to keep ML frameworks out of import
  time (e.g. `from transformers import …` inside `load_model()` /
  `get_tokenizer()`). Document why with a comment if non-obvious.

## Typing

* All new/edited functions get full annotations (`-> None` included);
  `from __future__ import annotations` at the top of every module.
* Use `X | None` not `Optional[X]`; `list[str]` not `List[str]` (UP rules).
* mypy must stay clean without blanket `# type: ignore`; prefer precise
  stubs in tests over silencing.

## Error handling

* Define and raise specific exceptions (`TranscriptionError`,
  `PredictionError`) instead of bare `Exception`.
* Always `raise … from exc` when wrapping (bugbear B904-style hygiene).
* Validate inputs early; map user errors to 4xx, dependency failures to
  502/503, and never include internal exception text in HTTP responses;
  log the detail, return a generic message.
* No silent `except: pass`.

## Logging vs printing

* Library modules (`src/`) use the `logging` module
  (`logger = logging.getLogger(__name__)`); `print` is reserved for CLI
  entry points. Log levels: DEBUG for per-request probabilities, INFO for
  lifecycle events, WARNING for fallbacks (e.g. untrained base model).

## FastAPI conventions

* Endpoints doing blocking work (inference, STT, DB) are `def`, not
  `async def`: FastAPI runs them in the threadpool and the event loop
  stays responsive.
* Request/response shapes via pydantic models or typed `Body()` params.
* Shared mutable state is guarded by a lock and owned by the module that
  created it.

## Testing

* Tests are **offline**: stub every network/ML boundary
  (`tests/conftest.py` fakes; `sys.modules` stub for transformers 5.x).
* One behaviour per test; name tests `test_<unit>_<scenario>`.
* Use `tmp_path` for filesystem, `monkeypatch` for config overrides;
  never write into the repo during tests.
* Coverage gate: core modules (`predict`, `backend`, `dataset_setup`,
  `db`, `config`) ≥ 90 % lines. Exemptions require written justification
  in `EVALUATION.md` (see the train.py entry).

## Git

* Conventional commits: `feat:`, `fix:`, `test:`, `ci:`, `docs:`,
  `chore:`; imperative mood, body explains *why*.
* One logical change per commit; the repo must be green at every commit.
* Never commit: `.venv`/venv dirs, model weights, `*.db`, caches
  (all gitignored; this repo has been burned before, see docs/AUDIT.md).
