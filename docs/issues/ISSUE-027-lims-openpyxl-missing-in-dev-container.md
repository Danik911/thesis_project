# ISSUE-027: LIMS Extraction Warning in Docker Dev - `ModuleNotFoundError: No module named 'openpyxl'`

**Date:** 2026-02-17  
**Status:** Resolved  
**Category:** Docker/API  
**Priority:** High

---

## Symptom

LIMS extraction worked locally (`uv run uvicorn` + `npm run dev`) but in Docker dev stack the UI showed:

- `Extraction Error`
- `MDA generation warning: ModuleNotFoundError: No module named 'openpyxl'`

---

## Root Cause

1. The running `pharma-api-dev` container image was stale (started without rebuild after dependency changes).
2. During rebuild/restart, API start failed once due missing bind-mount source path `main/output` on host.

---

## Verification

Inside running container before fix:

```bash
docker exec pharma-api-dev python -c "import openpyxl"
# ModuleNotFoundError
```

After rebuild and restart:

```bash
docker exec pharma-api-dev python -c "import openpyxl; print(openpyxl.__version__)"
# 3.1.5
```

---

## Resolution

From WSL project root:

```bash
docker compose -f docker-compose.dev.yml up -d --build api
```

If API start fails with output bind mount path error, ensure directory exists:

```bash
mkdir -p main/output
docker compose -f docker-compose.dev.yml up -d api
```

---

## Prevention

1. After Python dependency updates, always rebuild impacted services (`api`, `worker`) before testing:
   - `docker compose -f docker-compose.dev.yml up -d --build api worker`
2. Keep required bind-mount source directories present (`main/output` for dev stack).
3. Prefer `docker compose` (v2) consistently.
