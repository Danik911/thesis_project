# Custom Agents (Copilot)

This repo defines GitHub Copilot custom agents in this folder:

- `aws-agent` — AWS deploy/destroy/debug
- `debugger` — fix failing tests/runtime bugs
- `context-generator` — map “where to change what” before implementing

## How to invoke (VS Code)

1. Open Copilot Chat.
2. Switch the agent/profile selector (agent dropdown) and choose one of:
   - `aws-agent`
   - `debugger`
   - `context-generator`
3. Paste one of the prompts from the smoke tests below.

If you don’t see the agents, reload the window and ensure you’re on a Copilot version that supports repository agents.

## Smoke tests

### 1) `context-generator` smoke test

Prompt:

> Map the end-to-end flow for a job from Next.js UI → FastAPI API → worker → UnifiedTestGenerationWorkflow → storage output. List the exact files/symbols to inspect for each stage, and the minimum set of changes needed to add a new job field persisted in Postgres.

Expected:
- Mentions key files like `main/frontend/`, `main/api/app.py`, `main/api/worker.py`, `main/api/worker_executor.py`, `main/src/core/unified_workflow.py`, `main/src/adapters/storage.py`.
- Produces a short plan and concrete file paths; avoids inventing new architecture.

### 2) `debugger` smoke test

Prompt:

> Run the smallest test command you can that fails, then fix it. Prefer a single root-cause fix with minimal diff and rerun the specific failing test. Do not add fallback logic.

Then run locally yourself:
- `uv run pytest main/tests/ -v`

Expected:
- Uses a reproduce → localize → fix → verify loop.
- Verifies with `pytest` and optionally `ruff`/`mypy`.
- Does not mask errors or invent placeholder outputs.

### 3) `aws-agent` smoke test (non-destructive)

Prompt:

> I want a deployment status report only. Use the repo scripts/workflows to determine what is deployed (ECS services, last deployment, health endpoint). Do not change infrastructure.

Expected:
- Focuses on read-only checks (workflow runs, ECS service/task state, `/health`).
- Calls out region `eu-west-2` and avoids destructive actions.
