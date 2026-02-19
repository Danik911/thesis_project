# ISSUE-033: Windows `uv run` Fails Due to Invalid Project `.venv`

**Date:** 2026-02-19  
**Status:** Open  
**Category:** Testing  
**Priority:** Medium

---

## Symptom

Running pytest from Windows PowerShell with `uv run` fails before test execution:

```bash
uv run pytest main/tests/lims/test_standards_loader.py -v
```

Observed error:

- `Project virtual environment directory ...\.venv cannot be used because it is not a valid Python environment (no Python executable was found)`

---

## Impact

- Blocks direct Windows-host test execution for LIMS task verification.
- Adds friction for PRP gate commands if executed outside WSL.

---

## Affected Files/Paths

- `.venv/` (project virtual environment path expected by `uv`)

---

## Workaround Used During L13

Run tests from WSL with ephemeral pytest dependency injection:

```bash
wsl -e bash -lc "cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project && uv run --with pytest pytest main/tests/lims/ -v"
```

This command passed for the LIMS suite during L13 validation.

---

## Suggested Fix Direction

1. Recreate `.venv` as a valid Python environment for Windows-host `uv` execution.
2. Standardize test execution docs to prefer WSL for this repository.
3. Optionally add a short troubleshooting note in `docs/TROUBLESHOOTING.md` for this exact `uv` error.
