# ISSUE-026: Full `main/tests` Collection Fails from Archived Test `sys.exit(1)`

**Date:** 2026-02-17  
**Status:** Open  
**Category:** Testing  
**Priority:** Medium

---

## Symptom

Running the project-wide test command fails during collection:

```bash
uv run pytest main/tests/ -v
```

Observed output includes:

- `Loading .env from: .../main/tests/.env`
- `.env file not found .../main/tests/.env`
- `SystemExit: 1`
- Import-time failure in `main/tests/archived_root_scripts/test_config_init.py`

The run aborts before normal test execution completes.

---

## Impact

- Blocks the PRP gate command `uv run pytest main/tests/ -v` in environments without `main/tests/.env`.
- Produces a false-negative signal for unrelated changes (including LIMS work) because collection fails before most tests run.

---

## Affected Files

- `main/tests/archived_root_scripts/test_config_init.py`
- `main/tests/.env` (expected by archived test at import-time)

---

## Notes from L5 Execution

- LIMS-focused suite passed: `uv run pytest main/tests/lims/ -v` -> `87 passed, 4 skipped`.
- New L5 tests passed/skipped as designed.
- Failure is pre-existing and unrelated to L5 file additions.

---

## Suggested Fix Direction

1. Make archived test skip safely when `main/tests/.env` is missing (instead of `sys.exit(1)` at import-time).
2. Optionally exclude `main/tests/archived_root_scripts/` from default collection in `pyproject.toml` if these are not part of active CI scope.
