# ISSUE-017: WSL NumPy/OpenBLAS Import Failure Blocks Local API Startup

**Date:** 2026-02-17  
**Status:** Resolved  
**Category:** API  
**Priority:** High

---

## Symptom

Running local API startup in WSL fails:

`uv run uvicorn main.api.app:app --port 8080`

with import errors rooted in NumPy C-extension loading:

- `ImportError: libopenblas64_p-r0-17488984.3.23.dev.so: cannot open shared object file`
- Followed by NumPy import failure during `llama_index` import.

This blocks local LIMS manual testing on `localhost:8080`.

## Affected Files

| File | Area |
|------|------|
| Local WSL virtual environment (`.venv`) | Python binary dependency resolution |
| `main/api/app.py` (startup path) | Fails on import chain due to environment |

---

## Root Cause

The NumPy installation inside the WSL project virtual environment was incomplete/corrupted: bundled binary runtime libraries were missing from `site-packages/numpy.libs`.

Specifically, the required shared library

`libopenblas64_p-r0-17488984.3.23.dev.so`

was absent, causing NumPy C-extension imports to fail during API startup when `llama_index` imports `numpy`.

---

## Resolution

Reinstalled NumPy directly in the WSL virtual environment:

```bash
uv pip install --python .venv/bin/python --force-reinstall "numpy==1.26.4"
```

Verification:

1. `numpy.libs` directory contains `libopenblas64_p-r0-17488984.3.23.dev.so`
2. API starts without NumPy traceback
3. Health check passes:

```bash
curl http://localhost:8080/health
# {"status":"healthy", ...}
```

---

## Files Modified

| File | Change |
|------|--------|
| `docs/issues/ISSUE-017-wsl-numpy-openblas-import-failure.md` | Added root cause and remediation details |

---

## Prevention Guidance

1. If NumPy/OpenBLAS import failures appear in WSL, force-reinstall NumPy in `.venv` before broader debugging.
2. Keep Python dependency installs scoped to the same runtime (WSL vs Windows) to avoid binary mismatch/corruption.
3. Optional: set `UV_LINK_MODE=copy` in WSL to suppress cross-filesystem hardlink fallback warnings.
