# Frontend Containerization & Verification Report

**Date:** 2025-11-20  
**Author:** GitHub Copilot (GPT-5.1-Codex Preview)

---

## 1. Context
- Goal: Run the Next.js frontend inside Docker alongside the existing API/worker stack and keep it ready for AWS deployment.
- Stack: Next.js 14, Clerk auth, Tailwind, Docker multi-stage build, docker-compose.dev.yml orchestrating postgres/localstack/api/worker/frontend.

---

## 2. Actions Completed

| Area | Change | Files/Commands |
|------|--------|----------------|
| Docker build fix | Added missing `main/frontend/public/` directory so `Dockerfile.frontend` copy step succeeds. | `mkdir main/frontend/public` (already present). |
| Next.js build optimisation | Enabled standalone output for smaller runtime image. | `main/frontend/next.config.mjs`. |
| Accessibility lint fix | Updated `FileUpload.tsx` to support keyboard activation (required for `npm run build`). | `main/frontend/components/FileUpload.tsx`. |
| Docker Compose integration | Added `frontend` service, including `env_file: .env.local` so Clerk/REST API env vars reach the container. | `docker-compose.dev.yml`. |
| Local rebuild/run | `docker-compose -f docker-compose.dev.yml up -d --build frontend` to ensure env changes applied. | command run successfully. |
| Issue triage | Investigated 500 error via `docker logs pharma-frontend-dev`, traced to missing Clerk secrets, resolved by mounting `.env.local`. | logs screenshot, same command. |
| Browser validation | Used Playwright to hit `http://localhost:3000/`, confirmed homepage renders (see screenshot). | `.playwright-mcp/frontend_fixed.png`. |

---

## 3. Verification Results

1. **Container status**
   - `docker ps` shows `pharma-frontend-dev` running, mapped to `0.0.0.0:3000`.
   - Logs show standard Next.js banner with no remaining errors after env fix.
2. **Browser smoke test**
   - Playwright navigation succeeded (no CSP errors aside from Next.js dev warning about Clerk dev keys).
   - Screenshot `frontend_fixed.png` captured in repo root `.playwright-mcp/` directory.
3. **Auth behaviour**
   - Landing page renders and prompts user to sign in. Clerk dev keys load correctly; warning only notes dev environment limits.
4. **API connectivity**
   - `NEXT_PUBLIC_API_BASE_URL` now injected via build arg and container env, enabling Dashboard to call FastAPI once user signs in (not re-tested end-to-end in this session, but env wiring verified).

---

## 4. Remaining Considerations

- **Clerk prod keys:** Current setup uses dev keys (`pk_test_*`, `sk_test_*`). Replace with production keys before deploying to AWS.
- **CSP warning:** Browser devtools flagged `unsafe-eval` restriction earlier; ensure no dependencies require it in production builds.
- **Docker Compose version warning:** Compose CLI warns `version` field is obsolete. Consider removing the top-level `version: '3.9'` in `docker-compose.dev.yml` later to silence warnings.
- **Automated tests:** No automated UI/API tests executed after the fix; recommend running existing E2E suite if available.

---

## 5. How to Reproduce Locally

```powershell
# From repo root
docker-compose -f docker-compose.dev.yml up -d --build frontend
# Inspect logs if needed
docker logs -f pharma-frontend-dev
# Open browser
start http://localhost:3000/
```

Stop the stack via:

```powershell
docker-compose -f docker-compose.dev.yml down
```

---

## 6. Next Steps
1. Replace Clerk dev keys with production-ready secrets before AWS deployment.
2. Add ECS task definition + CI pipeline to push `thesis_project-frontend` image to the new `pharma-test-gen-frontend` ECR repo (Terraform config ready).
3. Run full end-to-end tests (sign-in → upload URS → job completion) inside Docker to confirm API integration.
4. Address Compose schema warning when convenient.

---

_Saved at `docs/FRONTEND_DOCKER_STATUS.md`_
