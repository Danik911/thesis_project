# ISSUE-018: Local WSL Startup Fails When Storage Path Uses `/app/output`

**Date:** 2026-02-17  
**Status:** Resolved  
**Category:** API  
**Priority:** High

---

## Symptom

Running local API in WSL:

`uv run uvicorn main.api.app:app --port 8080`

starts startup flow but worker crashes with:

`CRITICAL: Failed to create storage directory Path: /app/output Error: [Errno 13] Permission denied: '/app'`

and process then exits; logs also showed a secondary `address already in use` bind collision while retrying.

## Affected Files

| File | Area |
|------|------|
| `main/src/adapters/storage.py` | Local storage provider path selection |
| `main/src/adapters/local_adapter.py` | Local directory creation |
| Runtime env (`.env.local`) | Storage base path for local startup |

---

## Root Cause

`main/api/worker.py` hardcoded local storage base path to `/app/output`, which is valid in Docker containers but not writable in local WSL runs from the project directory.

This caused worker initialization to fail at startup when creating `LocalStorageAdapter`, terminating the app startup sequence.

---

## Resolution

Updated worker local storage adapter initialization to use environment-configured local path with local-safe default:

- Read `STORAGE_LOCAL_BASE_PATH`
- Default to `output` (project-relative) instead of hardcoded `/app/output`

Code change:

- `main/api/worker.py` now calls `StorageFactory.create_storage_provider(storage_mode="local", base_path=local_base_path)`
  where `local_base_path = os.getenv("STORAGE_LOCAL_BASE_PATH", "output")`

Verification:

1. Started API locally in WSL on port 8081
2. Worker initialized with local path:
	- `LocalStorageAdapter initialized: base_path=/mnt/c/.../thesis_project/output`
3. Health endpoint returned 200:
	- `GET /health -> HTTP 200`

---

## Files Modified

| File | Change |
|------|--------|
| `main/api/worker.py` | Replaced hardcoded `/app/output` with configurable local path (`STORAGE_LOCAL_BASE_PATH`, default `output`) |
| `docs/issues/ISSUE-018-local-wsl-storage-path-uses-app-output.md` | Added root cause and resolution details |

---

## Prevention Guidance

1. Avoid hardcoded container-only filesystem paths in local runtime code paths.
2. Keep storage paths environment-configurable for Docker/local parity.
3. If startup shows `address already in use`, free the port before retrying local validation.
