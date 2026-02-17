# ISSUE-025: LIMS Local Dev Connectivity & Runtime Runbook (Consolidated)

**Date:** 2026-02-17  
**Status:** Resolved  
**Category:** Frontend/API  
**Priority:** High

---

## Scope (Consolidates)

This issue consolidates and supersedes:

- ISSUE-019 (Windows localhost -> WSL forwarding)
- ISSUE-020 (frontend API base URL mismatch)
- ISSUE-021 (Next dev manifest corruption -> 404)
- ISSUE-022 (`_next/static` 404 with standalone startup)
- ISSUE-023 (`NEXT_PUBLIC_API_BASE_URL=localhost` override mismatch)
- ISSUE-024 (API CORS blocking WSL IP frontend origin)

Keywords for searchability: `ERR_CONNECTION_REFUSED`, `_next/static 404`, `Failed to fetch`, `CORS`, `172.28`, `standalone`, `localhost`, `WSL`.

---

## Symptoms Seen

1. Frontend reachable but Extract fails with `Failed to fetch` / `ERR_CONNECTION_REFUSED`
2. Browser console shows `_next/static/...` 404/400 and missing page chunk JS
3. `/lims` intermittently 404s in dev despite existing page
4. API healthy at `/health` but browser requests blocked/preflight rejected
5. Port conflicts on `3002` / `8080` (`EADDRINUSE`)

---

## Root Causes

1. **Network origin mismatch** between frontend URL (`172.28.*`) and API default (`localhost`)
2. **CORS allowlist too narrow** for private-network dev origins
3. **Corrupted/dirty `.next` dev artifacts** causing manifest parsing failures
4. **Standalone serving mismatch**: `next start` with `output: standalone` in this env + missing copied `.next/static`
5. **Stale background processes** occupying required ports

---

## Final Working Baseline

### API (WSL)

```bash
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project
uv run uvicorn main.api.app:app --host 0.0.0.0 --port 8080
```

### Frontend Build + Standalone Runtime (WSL)

```bash
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/main/frontend
npm run build
mkdir -p .next/standalone/.next
rm -rf .next/standalone/.next/static
cp -r .next/static .next/standalone/.next/static
set -a; source .env.local; set +a
PORT=3002 HOSTNAME=0.0.0.0 node .next/standalone/server.js
```

### Access URL

Use WSL IP URL from Windows browser:

`http://<wsl-ip>:3002/lims/`

---

## Code Fixes Applied (Persistent)

1. `main/api/worker.py`
   - Local storage path uses env/default `output` (not hardcoded `/app/output`).
2. `main/frontend/pages/lims.tsx`
   - L3 UI implemented (`MDAViewer`, staged loading text, improved error block).
3. `main/frontend/lib/authenticatedFetch.ts`
   - API base URL helper handles localhost/IP-hosted frontend mismatch.
4. `main/api/app.py`
   - CORS extended for private-network dev origins (`10.*`, `172.16-31.*`, `192.168.*`, localhost on `300x`).

---

## Verification Checklist

1. `curl http://<wsl-ip>:8080/health` -> `200`
2. `OPTIONS /lims/extract` with `Origin: http://<wsl-ip>:3002` -> `200` + allow-origin header
3. `GET /lims/` from frontend URL -> `200`
4. Upload + Extract executes and returns `raw_extraction` + validation status
