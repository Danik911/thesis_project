# Copilot instructions (thesis_project)

## Big picture
- Product: pharmaceutical OQ test-suite generation from URS docs, using a multi-agent LLM workflow with GAMP-5 + ALCOA+ / 21 CFR Part 11 concerns.
- Main flow: Next.js UI → FastAPI job API → background worker runs `UnifiedTestGenerationWorkflow` → outputs artifacts (local or S3) and traces to LangFuse.

## Key locations
- FastAPI backend: `main/api/` (entrypoint: `main/api/app.py`).
- Worker loop + HIL pause/resume: `main/api/worker.py`, execution wrapper: `main/api/worker_executor.py`.
- Workflow orchestrator: `main/src/core/unified_workflow.py`.
- Agents:
  - Categorization (structured Pydantic output, confidence/HIL): `main/src/agents/categorization/agent.py`.
  - RAG context provider (ChromaDB): `main/src/agents/parallel/context_provider.py`.
  - OQ generation + YAML parsing: `main/src/agents/oq_generator/`.
- Frontend (Next.js Pages Router): `main/frontend/` (Dockerfile uses `main/frontend/package.json`).

## Local development (recommended)
- Day-to-day dev: run from Ubuntu (WSL2) even on Windows (see `CLAUDE.md` + `docs/DOCKER.md`).
- Start the full dev stack:
  - `docker-compose -f docker-compose.dev.yml up -d`
  - Health check: `curl http://localhost:8080/health`
  - Logs: `docker-compose -f docker-compose.dev.yml logs -f`
- Dev stack services: postgres (job state), localstack (+ init), api (8080), worker, frontend (3000).

## Python toolchain
- Python: 3.12 (see `pyproject.toml`). Prefer `uv` for running tooling:
  - Tests: `uv run pytest main/tests/ -v`
  - Lint/fix: `uv run ruff check --fix`
  - Typecheck (strict): `uv run mypy .`

## Config + runtime expectations
- `.env.local` is the source of truth for keys in local dev; API/worker also try to load it at startup (see `main/api/app.py`, `main/api/worker.py`).
- Common env vars you’ll see wired through:
  - Auth: `CLERK_*` (JWT validation in `main/api/dependencies.py`).
  - LLM: `OPENROUTER_API_KEY` (generation) + `OPENAI_API_KEY` (embeddings for RAG).
  - Observability: `LANGFUSE_*` (see `main/api/observability.py`).
  - HIL + shared state: `DATABASE_URL` enables Postgres-backed job/approval persistence.
  - Storage: `STORAGE_MODE=local|s3`, `STORAGE_TEST_OUTPUT_BUCKET`, `AWS_REGION` (default eu-west-2).
  - RAG: `RAG_VECTOR_STORE_PATH` (Docker uses `/app/chroma_db` volume).

## Project-specific conventions
- “No fallbacks”: don’t invent placeholder outputs, fake confidence, or silent error recovery; raise with full diagnostic context. This is repeatedly enforced in docs and code (e.g., `main/api/worker_executor.py`, `main/src/adapters/storage.py`).
- HIL behavior is intentional: low-confidence categorization should pause and require human approval (not auto-guess).
- Be cautious editing early logging setup in `main/api/app.py` (it’s ordered to avoid recursion/GC logging issues).
- If you hit a novel bug, follow the repo’s issue protocol: check `docs/issues/ISSUE-CATALOG.md`, and add a new `docs/issues/ISSUE-###-*.md` before implementing a fix (see `CLAUDE.md`).

## AWS / CI integration (when relevant)
- AWS region is `eu-west-2`; deployment automation lives in `aws/scripts/` (e.g., `python aws/scripts/redeploy.py --status-only`).
- Final end-to-end validation: use GitHub Actions to deploy to AWS, then validate the live app (e.g., `https://csvgeneration.com/health`).
- Custom agent: use the `aws-agent` profile in `.github/agents/aws-agent.agent.md` for AWS deploy/destroy/debug tasks (Terraform/ECS/ECR/CloudFront/SQS).
- Custom agent: use `debugger` in `.github/agents/debugger.agent.md` for failing tests, runtime crashes, or sticky workflow/HIL bugs.
- Custom agent: use `context-generator` in `.github/agents/context-generator.agent.md` to quickly map “where to change what” before implementing multi-file changes.
- CI/CD workflows:
  - `.github/workflows/deploy.yml`: runs on pushes to `main` and `deploy` (plus manual `workflow_dispatch`). Uses AWS OIDC to assume `pharma-test-gen-github-actions`, builds/pushes 3 images to ECR (`api`, `worker`, `frontend`), applies Terraform from `aws/terraform`, then forces ECS redeploy + health checks + CloudFront invalidation.
    - Build inputs: `frontend` uses `Dockerfile.frontend` and requires build args `NEXT_PUBLIC_API_BASE_URL` (empty for CloudFront-relative) + `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (GitHub secret). `api/worker` use `Dockerfile.api.pip` / `Dockerfile.worker.pip`.
  - `.github/workflows/destroy.yml`: manual only and gated by typing `yes`. Scales ECS services to 0, removes “preserved” resources from Terraform state (ECR repos, ChromaDB bucket, GitHub OIDC provider + role), then `terraform destroy`.