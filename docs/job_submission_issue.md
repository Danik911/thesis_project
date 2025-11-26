# API Job Submission Failure Report (2025-11-26)

## 1. Problem Statement
- Goal: Execute `curl -X POST http://localhost:8080/jobs -H "Authorization: Bearer $TOKEN" -F "file=@datasets/urs_corpus_v2/category_3/URS-020.md"` after minting a Clerk token with `scripts/get_clerk_token.py`.
- Actual behavior: Request never succeeds. Depending on the shell and form syntax, the API responds with **401 / 403**, **422**, or **500**. Frontend workflow remains stuck in "pending".

## 2. Environment Snapshot
- OS: Windows 11 with Docker Desktop + Ubuntu WSL2 backend.
- Repo branch: `frontend`.
- Containers via `docker-compose.dev.yml` (services: api, worker, postgres, localstack, frontend).
- Authentication: Clerk session token minted locally (user `user_35KgiAcvIC0tdtFvJUN1vDkrNYc`).

## 3. Files Accessed (read-only)
- `main/api/app.py` – reviewed `submit_job` implementation.
- `main/api/dependencies.py` – reviewed `require_clerk_user` and file validation logic.
- `scripts/get_clerk_token.py` – used to generate JWT.
- `test_submit.sh` – attempted but failed due to CRLF and `bash` on Windows.
- `main/logs/langfuse/trace-with-observations-2json.json` – inspected Langfuse trace showing storage failure.
- No files were modified.

## 4. Attempt Log
| # | Command / Action | Result |
|---|------------------|--------|
| 1 | `python scripts/get_clerk_token.py --user-id user_35KgiAcvIC0tdtFvJUN1vDkrNYc --env-file .env.local` | Successfully prints JWT (RS256). Token used in later requests. |
| 2 | `bash test_submit.sh` (PowerShell) | Script fails due to CRLF line endings, missing `python` alias, and Windows `curl` rejecting multipart quoting. Output shows `curl: (3) URL rejected` and `Not authenticated`. |
| 3 | Manual PowerShell command:<br>`$token = python ...; C:\Windows\System32\curl.exe -X POST ... -F "urs_file=@..."` | API responds with `{"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required"}]}` because Windows curl treated form name as `urs_file`. API expects `file`. |
| 4 | Corrected form field (`-F "file=@..."`) using Windows `curl.exe` | Command returns nothing (PowerShell prompt reappears). Shortly after, API logs show `POST /jobs HTTP/1.1 403 Forbidden` (invalid token or header quoting). |
| 5 | `docker compose -f docker-compose.dev.yml logs api --tail 200` (via WSL docker CLI) | Logs repeat container restarts after each OPTIONS/POST. Warnings: `JWT missing 'email' claim` and `JWT decode error: Not enough segments`. Multiple `POST /jobs` entries with `403`, `401`, and `422`. |
| 6 | Attempted full workflow inside WSL: `TOKEN=$(python3 scripts/get_clerk_token.py ...) && curl ...` | `python3` command unavailable in PowerShell-callable WSL wrapper (command terminated before entering bash). Subsequent attempt to open WSL shell ended with `wsl.exe` exit code `-1`. |
| 7 | `wsl -l -v` | Confirms Ubuntu distribution exists but earlier shell crashed; manual restart required. |
| 8 | Langfuse trace (`main/logs/langfuse/trace-with-observations-2json.json`) | Captured `create_test_generation_job` span ending with `500: CRITICAL: Job submission failed: CRITICAL: Storage service unavailable`, indicating the storage adapter throws `RuntimeError`. |

## 5. Key Observations
- **Authentication variability:** Windows `curl.exe` quoting caused malformed tokens (e.g., `JWT decode error: Not enough segments`) leading to 401/403 responses. Need to run curl inside WSL or use a PowerShell-native REST client to preserve header formatting.
- **422 Validation error:** API strictly expects the form field name `file`. Using `urs_file` (from earlier script) or quoting mistakes triggers FastAPI validation failure.
- **Storage backend failure:** When a request does make it through authentication and validation, Langfuse shows the worker hitting `RuntimeError: CRITICAL: Storage service unavailable` in `storage.save_artifact`. This yields a 500 response and leaves no job record.
- **Docker logs show restarts:** After OPTIONS/POST attempts, the API container restarts, suggesting the unhandled storage exception terminates the process (restart count `>4`).
- **WSL instability:** The attempt to run the workflow inside WSL terminated with exit code `-1`, preventing a clean reproduction using Linux `curl`.

## 6. Current Status
- Issue remains unresolved: every submission attempt fails before a job ID is returned.
- No code changes applied; only diagnostic commands run.
- Accurate reproduction requires a stable WSL session plus verification of storage configuration (volume `./main/output:/app/output`, permissions, environment variables such as `LOCAL_STORAGE_BASE_PATH`).

## 7. Recommended Next Steps
1. Re-run the workflow fully inside WSL (after ensuring `python3` is installed and WSL is running) to eliminate Windows `curl` quirks.
2. Inside the API container, verify that `/app/output` exists and is writable (`docker compose exec api ls -l /app/output`).
3. Confirm storage settings via `src/shared/config` (e.g., `storage_mode=local`, correct `local_base_path`). Fix any missing directories or permissions causing `Storage service unavailable`.
4. Once storage writes succeed, monitor `docker compose logs api -f` while submitting a job to ensure the container no longer restarts and that a `201 Created` response returns a `job_id`.
