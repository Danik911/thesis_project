# Migration Handoff: Split `thesis_project` into Two Corporate Repos

**Audience:** an AI coding agent (Claude Code, Cursor, or similar) executing this migration end-to-end on a fresh workstation. You should be able to follow this document mechanically without needing the prior conversation that produced it.

**Source repo:** `https://github.com/Danik911/thesis_project` (branch `fix/deploy-workflow-dockerfile-names`, commit `03c3dcf` or later) — personal monorepo containing the thesis pharmaceutical test-generation app, the AI4LIMS PoC additively bolted into it, and a third unrelated project (MES Agentic BI) that **is not migrated**.

**Targets:**

| # | New repo | Contents |
|---|----------|----------|
| A | `<org>/pharma-test-gen` (or whatever name the user chooses) | The thesis app only. Production-deployable to AWS. |
| B | `<org>/ai4lims-poc` (or chosen name) | A *slim* LIMS PoC: only the FastAPI app, frontend, and shared infrastructure that LIMS actually uses. |

Each target repo gets a **fresh single commit** (no history transfer). The user explicitly chose this.

**Out of scope:** `mes-agentic-bi/`, `main/src/bi/`, `main/api/bi_router.py`, `main/api/bi_voice_router.py`, `main/frontend/pages/agentic-bi.tsx`, `main/frontend/pages/bi-charts.tsx`, `main/frontend/components/bi/`, `PRPs/data-copilot-poc.md` — drop these in **both** target repos.

---

## 0. Pre-flight

1. **Confirm scope with the user before starting.** Verify the two target repo URLs (the user must create them empty in the corporate org first) and the exact names. Ask which Default branch they want (`main` is the safe default).
2. **AWS infrastructure must be destroyed** before this migration — if it is running on `csvgeneration.com`, the migration is still safe, but secret rotation (step 3) breaks the live deployment.
3. **Rotate every secret** that ever sat in this repo's `.env.local` files, because the local working tree on the originating laptop contained:
   - OpenRouter (`OPENROUTER_API_KEY`)
   - OpenAI (`OPENAI_API_KEY`)
   - Anthropic (`ANTHROPIC_API_KEY`)
   - Clerk publishable + secret + JWT signing
   - LangFuse public + secret
   - GitHub PAT
   - Tavily, Perplexity, Firecrawl, Cerebras, Gemini, Brave, Qdrant
   - LIMS-specific: LlamaCloud / LlamaExtract API keys
     None of these are in the git history of `origin/*` (verified — `.env.local` is correctly gitignored), but the new corporate environments should not reuse old keys.
4. **Stale local state to ignore (never copy into target repos):** the source repo has 1 GB of build caches, a 742 MB Terraform binary in unpushed commit `91410d2`, and many tracked Claude/MCP user-config files. The procedure below produces a clean tree from scratch — do *not* try to "clean up in place." Always start from a fresh clone.

---

## 1. Common setup (do once, before either target)

```bash
# 1.1 Pick a workspace
mkdir -p ~/migration && cd ~/migration

# 1.2 Fresh clone of the source — do not reuse the user's laptop checkout
git clone --branch fix/deploy-workflow-dockerfile-names \
  https://github.com/Danik911/thesis_project.git source

# 1.3 Verify expected HEAD
cd source && git log -1 --oneline   # expect 03c3dcf or newer
cd ..

# 1.4 Make two working directories by COPYING (not cloning) source.
#     Copy avoids carrying any history into the new repos.
cp -R source pharma-test-gen
cp -R source ai4lims-poc

# 1.5 Drop git history from each working dir — fresh single commit will follow.
rm -rf pharma-test-gen/.git ai4lims-poc/.git
```

> Use `robocopy` on Windows native, or `cp -R` in WSL/Git Bash. Verify the new dirs are not symlinks back to `source`.

---

## 2. Target A — `pharma-test-gen` (thesis-only)

### 2.1 What stays

| Path | Notes |
|------|-------|
| `main/api/` *(see edits in 2.3)* | FastAPI app, worker, dependencies, models, audit, observability, export, job repo |
| `main/src/adapters/` | Storage abstraction (S3/local) |
| `main/src/agents/` | Multi-agent test-generation pipeline |
| `main/src/compliance/`, `main/src/config/`, `main/src/core/` | GAMP-5 compliance, configuration, core workflow |
| `main/src/document_processing/` | URS parsing, document loaders |
| `main/src/llms/` | OpenRouter compat, model providers |
| `main/src/monitoring/` | LangFuse integration |
| `main/src/security/` | Clerk JWT verification |
| `main/src/shared/` | Shared utilities |
| `main/src/utils/` | `cost_tracker.py` etc. (restored from `00dcaf1~1`) |
| `main/src/validation/` | Output validation |
| `main/frontend/` *(see edits in 2.3)* | Next.js app — remove LIMS/BI pages and components |
| `Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.frontend` | Already have `PYTHONPATH=/app/main` fix applied |
| `docker-compose.dev.yml` | Local dev compose |
| `aws/` | Terraform, deploy scripts, IAM policies, task definitions |
| `.github/workflows/deploy.yml`, `destroy.yml`, `redeploy.yml` | CI/CD |
| `pyproject.toml` *(see edits)*, `uv.lock` | Python deps |
| `docs/ARCHITECTURE.md`, `AWS_DEPLOYMENT.md`, `DOCKER.md`, `GITHUB_ACTIONS_DEPLOYMENT.md`, `PROJECT_STRUCTURE.md`, `README.md`, `TROUBLESHOOTING.md`, `docs/regulatory_guides/`, `docs/guides/REDEPLOY_AFTER_DESTROY.md`, `docs/issues/` (cleanup in 2.3) | Thesis-relevant docs |
| `PRPs/tasks/` | Production Readiness Plan tasks (audit/GAMP-5 trail) |
| `CLAUDE.md` *(rewrite — see 2.3)* | Project guidance for Claude Code, scrubbed of LIMS/BI |
| `README.md` *(rewrite)*  | Repo overview |
| `.env.example` *(scrubbed — see 2.3)* | Template env file |

### 2.2 What goes away

```bash
cd ~/migration/pharma-test-gen

# Apps to remove entirely
rm -rf mes-agentic-bi/
rm -rf main/src/lims/
rm -rf main/src/bi/
rm -rf docs/project_p/
rm -rf docs/client-handover/      # If client-handover refers to MES-BI (verify first — keep if it's thesis client handover docs)
rm   PRPs/data-copilot-poc.md      # MES-BI PRP

# LIMS/BI API routers
rm main/api/lims_router.py
rm main/api/bi_router.py
rm main/api/bi_voice_router.py

# LIMS/BI frontend pages
rm main/frontend/pages/lims.tsx
rm main/frontend/pages/agentic-bi.tsx
rm main/frontend/pages/bi-charts.tsx

# LIMS/BI frontend components
rm -rf main/frontend/components/bi/
rm    main/frontend/components/MDAViewer.tsx
rm    main/frontend/components/LIMSStepIndicator.tsx
rm    main/frontend/components/ProvenanceBadge.tsx       # LIMS-only — verify
rm    main/frontend/components/TemplateSelector.tsx      # ALSO used by generate.tsx — see 2.3 caveat
rm    main/frontend/components/TemplateEditor.tsx        # LIMS-only — verify
rm    main/frontend/components/TemplatePreview.tsx       # LIMS-only — verify
rm    main/frontend/components/ChatInterface.tsx         # LIMS-only — only imported by lims.tsx

# LIMS compose
rm docker-compose.lims.yml

# Personal / user-machine pollution (these are tracked in the source repo)
rm -f .claude.json .mcp.json
rm -rf .serena/ .amazonq/ .playwright-mcp/

# Local build caches / artifacts that snuck into the working copy
rm -rf .next/ node_modules/ .venv/ .venv_ppocr/ \
       .mypy_cache/ .pytest_cache/ .ruff_cache/ \
       cache/ output/ uploads/ logs/ screenshots/ event_retrospective_images/ \
       chroma_db/ chroma_db_lims/ archive/ \
       main/frontend/.next/ main/frontend/node_modules/ \
       main/.mypy_cache/
rm -f chroma_db.tar.gz lib/chroma_db.tar.gz .coverage
```

### 2.3 Code edits inside the files that stay

**(a) `main/api/app.py` — remove the LIMS/BI router mounts and the LIMS ChromaDB auto-seed**

Open `main/api/app.py`. As of source commit `03c3dcf`:

- Lines **216–235** contain a block beginning with `# Auto-seed LIMS ChromaDB collections from bundled JSONL if empty` and ending with the matching `except`. Delete this entire block.
- Lines **1489–1491** mount the LIMS router (`from .lims_router import router as lims_router` then `app.include_router(lims_router, prefix="/lims")`). Delete these 3 lines.
- Lines **1493–1497** mount the BI router and BI voice router. Delete this block as well.

Use line numbers as a hint; the source may shift. Search anchors:

```bash
grep -n "Auto-seed LIMS\|from .lims_router\|from .bi_router\|from .bi_voice_router\|include_router(lims_router\|include_router(bi_router\|include_router(bi_voice_router" main/api/app.py
```

After edits, **run `python -c "import ast; ast.parse(open('main/api/app.py').read())"`** to confirm syntactic validity, then **`python -c "from main.api.app import app"`** to confirm imports resolve.

**(b) `main/frontend/pages/generate.tsx`** — verify it does *not* import `TemplateSelector`. If it does (the source DOES use it for thesis template selection — confirmed via `grep -rl TemplateSelector main/frontend/pages/`), **keep** `TemplateSelector.tsx` in the thesis repo and remove only the LIMS-only components above. Re-run the deletion of `TemplateSelector.tsx` only if the grep shows it is unused.

**(c) `main/frontend/components/Layout.tsx`, `Header.tsx`** — remove any navigation links pointing to `/lims`, `/agentic-bi`, `/bi-charts`. Search:

```bash
grep -rn "/lims\|/agentic-bi\|/bi-charts\|/bi/" main/frontend/components/ main/frontend/pages/
```

Delete the matching anchor / link elements.

**(d) `pyproject.toml`** — remove LIMS-specific dependencies. From the dependency list, **delete** these lines:

```
"llama-cloud-services==0.6.93",      # LlamaExtract — LIMS only
"llama-cloud==0.1.46",               # LIMS only
"openpyxl>=3.1.0",                   # LIMS XLSX export only
"fpdf2>=2.7.0",                      # LIMS PDF preview only
"PyMuPDF>=1.24.0",                   # LIMS PDF processing only
"rank-bm25>=0.2.2",                  # LIMS hybrid retrieval only
"snowflake-connector-python[pandas]>=3.6.0",  # MES-BI only
```

Then **regenerate the lock file**:

```bash
uv lock           # produces a clean uv.lock for the thesis-only deps
```

**(e) `.env.example`** — scrub LIMS/BI keys. Open `.env.example` and remove every line containing `LIMS_`, `LLAMA_CLOUD`, `LLAMA_EXTRACT`, `BI_`, `SNOWFLAKE_`, or `BEDROCK_`. Leave the thesis ones (Clerk, OpenRouter, LangFuse, AWS, ChromaDB-S3-bucket).

**(f) `CLAUDE.md`** — rewrite to thesis-only. Remove the `## AI4LIMS PoC` and `## MES Agentic BI` sections entirely, and the rows referencing them in the Documentation References table and Key Commands. The Subagents, Skills, PRP Workflow, Tech Stack, Development Environment sections stay.

**(g) `docs/issues/ISSUE-CATALOG.md`** — remove rows referencing LIMS or MES-BI (ISSUE-015 through ISSUE-041 are a mix; keep thesis ones, drop the LIMS/BI ones). Cross-reference each ISSUE-*.md file title before deleting its row. Also delete the corresponding ISSUE-*.md files from `docs/issues/`. **Be conservative — when in doubt, keep the issue file.**

**(h) `README.md`** — rewrite from scratch (or use a slim template):

```md
# Pharma Test Generation

GAMP-5 compliant pharmaceutical Computer System Validation test generator powered by a multi-agent LLM pipeline. Production-deployed to AWS ECS/Fargate.

## Quick Start

\`\`\`bash
docker-compose -f docker-compose.dev.yml up -d
\`\`\`

## Deployment

See `docs/AWS_DEPLOYMENT.md` and `docs/guides/REDEPLOY_AFTER_DESTROY.md`.

## Documentation

- `docs/ARCHITECTURE.md` — system architecture
- `docs/AWS_DEPLOYMENT.md` — AWS infrastructure
- `docs/GITHUB_ACTIONS_DEPLOYMENT.md` — CI/CD
- `docs/PROJECT_STRUCTURE.md` — codebase layout
- `docs/regulatory_guides/` — GAMP-5, ALCOA+, 21 CFR Part 11, ICH Q9

## License

See `LICENSE`.
```

### 2.4 Verification (must pass before commit)

```bash
# (a) Python imports resolve
uv sync --frozen --no-dev
uv run python -c "from main.api.app import app; print('OK')"

# (b) Backend boots (kills after 5s)
uv run uvicorn main.api.app:app --host 0.0.0.0 --port 8080 &
sleep 5
curl -sf http://localhost:8080/health | grep -q '"status"' && echo "API healthy"
kill %1

# (c) Frontend builds (uses output: 'standalone')
cd main/frontend && npm ci && npm run build && cd ../..

# (d) Docker image builds
docker build -f Dockerfile.api .   # smoke build only — no push
docker build -f Dockerfile.frontend .

# (e) No leftover LIMS/BI references
! grep -rn "lims_router\|bi_router\|bi_voice_router\|from main.src.lims\|from main.src.bi" \
    main/ aws/ docs/ .github/ pyproject.toml
```

If any of these fail, **fix before committing** — do not push a broken tree.

### 2.5 Init git + push

```bash
cd ~/migration/pharma-test-gen
git init -b main
git add -A
git commit -m "Initial commit: pharmaceutical test generation system

Multi-agent LLM pipeline for GAMP-5 compliant Computer System
Validation test generation. Production-deployed to AWS ECS/Fargate at
csvgeneration.com.

Components:
- FastAPI backend with Clerk JWT authentication
- Background worker pulling jobs from SQS
- Next.js 14 frontend (App Router)
- ChromaDB RAG for regulatory standards
- LangFuse Cloud (EU) observability
- Terraform IaC for AWS deployment
- GitHub Actions deploy/destroy/redeploy workflows
"
git remote add origin <THESIS_REPO_URL>     # confirmed with user at step 0
git push -u origin main
```

---

## 3. Target B — `ai4lims-poc` (slim LIMS)

### 3.1 What LIMS actually needs

The LIMS PoC reuses three things from the thesis app:
1. **Clerk JWT auth** (`main/src/security/`) — but LIMS is currently flag-gated off (`NEXT_PUBLIC_AUTH_ENABLED=false`). Keep the module; you can disable the dependency by simply not setting the env var. Decision: **keep `main/src/security/`** so re-enabling auth later is trivial.
2. **Storage adapter** (`main/src/adapters/`) — wraps local/S3. LIMS uses local; the abstraction stays.
3. **FastAPI app shell** (`main/api/app.py`) — but heavily slimmed (see 3.3).

Everything else in `main/src/` is thesis-only and gets removed.

### 3.2 What to keep / remove

**Keep:**

| Path | Notes |
|------|-------|
| `main/src/lims/` | The PoC core (17 files). |
| `main/src/adapters/` | Storage abstraction. |
| `main/src/security/` | Clerk middleware (kept disabled by env). |
| `main/src/shared/` *(only if non-thesis-specific — audit)* | Generic helpers. Check imports. |
| `main/api/lims_router.py` | LIMS routes. |
| `main/api/app.py` *(rewritten — see 3.3)* | Minimal FastAPI app that mounts only `lims_router` + `/health`. |
| `main/api/dependencies.py` *(slimmed — see 3.3)* | Only LIMS-relevant deps. |
| `main/frontend/pages/lims.tsx` | LIMS UI page. |
| `main/frontend/pages/_app.tsx`, `_document.tsx`, `index.tsx`, `404.tsx` | Next.js scaffolding. Rewrite `index.tsx` to redirect to `/lims`. |
| `main/frontend/components/{MDAViewer,LIMSStepIndicator,ProvenanceBadge,TemplateSelector,TemplateEditor,TemplatePreview,ChatInterface,Layout,Header,FileUpload}.tsx` | Components imported by `lims.tsx`. **Verify each via grep before keeping.** |
| `main/frontend/components/ui/` | Shadcn / shared UI primitives (audit — keep only what `lims.tsx` and its components import). |
| `Dockerfile.api`, `Dockerfile.frontend` | API + frontend container builds. **No worker.** |
| `docker-compose.lims.yml` | Minimal compose for local dev. |
| `pyproject.toml` *(slimmed — see 3.3)* | LIMS-only deps. |
| `uv.lock` *(regenerate)* | |
| `.env.example` *(slimmed)* | LIMS env vars only. |
| `docs/project_p/` | LIMS PoC documentation, `LIMS-001`..`LIMS-014`. |
| `docs/regulatory_guides/` *(if relevant)* | GAMP-5 background. Audit each file. |
| `CLAUDE.md` *(slim rewrite)* | LIMS-only project guidance. |
| `README.md` *(new)* | LIMS-focused. |

**Remove everything else.** In particular:

```bash
cd ~/migration/ai4lims-poc

# Thesis core
rm -rf main/src/agents/ main/src/compliance/ main/src/config/ main/src/core/ \
       main/src/document_processing/ main/src/llms/ main/src/monitoring/ \
       main/src/utils/ main/src/validation/ main/src/bi/

# Thesis API surface
rm main/api/audit.py main/api/bi_router.py main/api/bi_voice_router.py \
   main/api/export_formats.py main/api/job_repository.py main/api/langfuse_routes.py \
   main/api/observability.py main/api/verify_db_persistence.py \
   main/api/worker.py main/api/worker_executor.py main/api/models.py

# Thesis frontend
rm main/frontend/pages/generate.tsx main/frontend/pages/history.tsx \
   main/frontend/pages/agentic-bi.tsx main/frontend/pages/bi-charts.tsx \
   main/frontend/pages/sign-in.tsx main/frontend/pages/sign-up.tsx
rm -rf main/frontend/pages/jobs/
rm -rf main/frontend/components/bi/ main/frontend/components/3d/ \
       main/frontend/components/landing/ main/frontend/components/quiz/

# Thesis frontend components — REMOVE only the ones not imported by lims.tsx
# Audit first: `grep -E "import.*from '@/components" main/frontend/pages/lims.tsx`
# Common thesis-only components to delete (verify each):
rm -f main/frontend/components/{ApprovalModal,Background3D,ClassificationPanel,\
ComplianceDashboard,CustomCursor,HowItWorksModal,JobProgress,LangfuseTraceDashboard,\
MergeConflictPanel,PipelineStageDetail,PlatformPillars,TrustBanner,WorkflowDiagramModal}.tsx

# Thesis Dockerfile.worker (LIMS has no worker)
rm Dockerfile.worker

# Thesis AWS deployment (LIMS is local-dev-only PoC)
rm -rf aws/
rm -rf .github/workflows/   # No CI/CD for the PoC at handoff time

# Thesis dev compose (LIMS uses docker-compose.lims.yml)
rm docker-compose.dev.yml

# Other apps + personal pollution + caches (same list as 2.2)
rm -rf mes-agentic-bi/ docs/client-handover/ PRPs/  # PRPs is thesis-only
rm -f .claude.json .mcp.json
rm -rf .serena/ .amazonq/ .playwright-mcp/ archive/
rm -rf .next/ node_modules/ .venv/ .venv_ppocr/ \
       .mypy_cache/ .pytest_cache/ .ruff_cache/ \
       cache/ output/ uploads/ logs/ screenshots/ event_retrospective_images/ \
       chroma_db/ main/frontend/.next/ main/frontend/node_modules/ main/.mypy_cache/
rm -f chroma_db.tar.gz lib/chroma_db.tar.gz .coverage

# Thesis-specific docs (keep ARCHITECTURE/AWS_DEPLOYMENT only if LIMS gets AWS later)
rm -f docs/AWS_DEPLOYMENT.md docs/GITHUB_ACTIONS_DEPLOYMENT.md \
      docs/PROJECT_STRUCTURE.md docs/ARCHITECTURE.md docs/DOCKER.md \
      docs/TROUBLESHOOTING.md docs/README.md
rm -rf docs/guides/ docs/issues/
# Keep docs/project_p/ and docs/regulatory_guides/
```

### 3.3 Edits inside the slim LIMS tree

**(a) Rewrite `main/api/app.py` to be LIMS-only.** Replace the entire file with:

```python
"""FastAPI application for AI4LIMS PoC (slim).

Mounts only the LIMS router under /lims and a /health endpoint.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import chromadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed LIMS standards collection on first boot.
    try:
        lims_chroma_path = os.getenv("LIMS_CHROMADB_PATH", "./chroma_db_lims")
        client = chromadb.PersistentClient(path=lims_chroma_path)
        standards = client.get_or_create_collection("lims_standards")
        if standards.count() == 0:
            logger.info("[LIMS] lims_standards empty — seeding from bundled JSONL")
            from main.src.lims.standards_loader import seed_all_from_bundled
            results = seed_all_from_bundled(chroma_path=lims_chroma_path)
            logger.info("[LIMS] auto-seed complete: %s", results)
        else:
            logger.info(
                "[LIMS] standards already populated (%d chunks)", standards.count()
            )
    except Exception as exc:  # pragma: no cover
        logger.warning("[LIMS] auto-seed skipped: %s", exc)
    yield


app = FastAPI(title="AI4LIMS PoC", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


from main.api.lims_router import router as lims_router
app.include_router(lims_router, prefix="/lims")
```

**(b) Audit `main/api/lims_router.py`** for imports that point at thesis modules you deleted (`main.src.agents`, `main.src.compliance`, `main.src.llms.*`, etc.). Either:
- delete the offending route handler if it's thesis-only, or
- inline the small helpers it needs (only do this if the helper is < 20 lines).

Run `python -c "from main.api.lims_router import router"` after each edit until it imports cleanly.

**(c) `main/api/dependencies.py`** — keep only the symbols actually imported by `lims_router.py`. The file currently imports `from src.adapters.storage import StorageFactory, StorageProvider`; that stays (still needed by LIMS file uploads via `main/src/adapters/`). Delete every other function/class that the new `lims_router.py` does not reference. Verify with:

```bash
grep -E "from .dependencies import|from main.api.dependencies import" main/api/lims_router.py
```

**(d) `main/frontend/pages/index.tsx`** — replace contents with a redirect to `/lims`:

```tsx
import { useEffect } from "react";
import { useRouter } from "next/router";

export default function Index() {
  const router = useRouter();
  useEffect(() => { router.replace("/lims"); }, [router]);
  return null;
}
```

**(e) Frontend cleanup**

- `Layout.tsx` / `Header.tsx`: remove every nav link pointing at `/generate`, `/history`, `/jobs`, `/agentic-bi`. Keep `/lims` and `/`.
- For each remaining component file, ensure no `import` references a deleted file. Iterate until `npm run build` succeeds.
- `main/frontend/package.json`: leave dependencies as-is (Next.js / Clerk / TanStack) — they are not LIMS-specific and pruning is high effort for no real saving.

**(f) `pyproject.toml`** — this is where the slim repo really diverges. **Replace the `dependencies` list** with the LIMS-only subset:

```toml
dependencies = [
    # Web framework
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.9",

    # LlamaExtract for PDF extraction (LIMS core)
    "llama-cloud-services==0.6.93",
    "llama-cloud==0.1.46",

    # RAG: ChromaDB for the standards collection
    "chromadb==1.0.20",
    "llama-index>=0.10.0",
    "llama-index-vector-stores-chroma>=0.3.0",
    "llama-index-embeddings-openai>=0.1.0",

    # LLM clients (the chat agent uses OpenAI-compatible APIs)
    "openai>=1.12.0",
    "httpx>=0.25.0",

    # PDF processing
    "pdfplumber>=0.10.0",
    "PyMuPDF>=1.24.0",
    "PyPDF2>=3.0.1",

    # XLSX export
    "openpyxl>=3.1.0",
    "fpdf2>=2.7.0",

    # Hybrid retrieval
    "rank-bm25>=0.2.2",

    # Auth (feature-flagged off)
    "clerk-backend-api==4.0.0",
    "pyjwt[crypto]==2.9.0",

    # Observability
    "langfuse==3.5.2",

    # Storage abstraction
    "boto3>=1.40.61",
    "aiobotocore>=2.11.0",
    "moto[s3]>=4.2.0",

    # Misc
    "python-dotenv>=1.0.0",
    "aiofiles>=23.2.1",
    "pandas>=2.0.0",
    "json-repair>=0.54.2",
]
```

Keep the `[tool.hatch.build.targets.wheel]` block. Keep `packages = ["main"]` *and* set `PYTHONPATH=/app/main` in the Dockerfile (issue ISSUE-042 carry-over — if you do not, `from src.adapters.storage` will not resolve).

Regenerate the lock:

```bash
uv lock
```

**(g) `Dockerfile.api`** — change the CMD to point at the slim app:

```dockerfile
CMD ["uvicorn", "main.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

(That is what it already says; no change needed if the source was unchanged.) **Verify** that `ENV PYTHONPATH="/app/main"` is set in the runtime stage — this was added in commit `3b34c7d` and must survive the migration.

**(h) `.env.example`** — replace with the LIMS minimum:

```
# AI4LIMS PoC — minimum env

# Storage (local for PoC; switch to s3 in production)
STORAGE_PROVIDER=local
STORAGE_PATH=/app/output

# LlamaExtract (LIMS PDF extraction)
LLAMA_CLOUD_API_KEY=

# ChromaDB
LIMS_CHROMADB_PATH=/app/chroma_db_lims

# LLM (chat agent)
OPENAI_API_KEY=
# OR use OpenRouter:
# OPENROUTER_API_KEY=

# Observability
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# Auth (feature-flagged; leave empty to disable Clerk)
NEXT_PUBLIC_AUTH_ENABLED=false
CLERK_SECRET_KEY=
CLERK_PEM_PUBLIC_KEY=
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=

# CORS
CORS_ALLOW_ORIGINS=http://localhost:3000
```

**(i) `CLAUDE.md`** — slim down to LIMS-only guidance. Delete the Thesis and MES-BI sections. Keep only the LIMS section, renamed from `## AI4LIMS PoC` to `## Project Overview`, and the Critical Operating Principles block.

**(j) New `README.md`:**

```md
# AI4LIMS PoC

Proof-of-concept LIMS template generator using LlamaExtract for PDF extraction and ChromaDB RAG over regulatory standards.

## Local Dev

\`\`\`bash
docker-compose -f docker-compose.lims.yml up -d
\`\`\`

Then open http://localhost:3000/lims.

## Architecture

- Backend: FastAPI (`main/api/app.py`) mounted at `/lims/*`.
- LIMS core: `main/src/lims/` — PDF extraction, MDA schema, RAG, classifier.
- Frontend: Next.js page at `main/frontend/pages/lims.tsx`.

## Documentation

See `docs/project_p/` for the PoC plan, feature notes, and LIMS-### issue records.
```

### 3.4 Verification

```bash
# (a) Python imports
uv sync --frozen --no-dev
uv run python -c "from main.api.app import app; print('OK')"

# (b) Backend boots
uv run uvicorn main.api.app:app --port 8080 &
sleep 5
curl -sf http://localhost:8080/health | grep -q '"status"' && echo "API healthy"
curl -sf http://localhost:8080/lims/health 2>&1 | head -1   # may 404; that's fine if lims_router has no /health
kill %1

# (c) Frontend builds
cd main/frontend && npm ci && npm run build && cd ../..

# (d) Compose smoke (full integration)
docker-compose -f docker-compose.lims.yml build
docker-compose -f docker-compose.lims.yml up -d
sleep 30
curl -sf http://localhost:3000/lims/ | head -1
docker-compose -f docker-compose.lims.yml down

# (e) No dangling thesis imports
! grep -rn "from main.src.agents\|from main.src.compliance\|from main.src.core\|from main.src.document_processing\|from main.src.llms\|from main.src.monitoring\|from main.src.utils\|from main.src.validation\|from main.src.bi" \
    main/ pyproject.toml
```

### 3.5 Init git + push

```bash
cd ~/migration/ai4lims-poc
git init -b main
git add -A
git commit -m "Initial commit: AI4LIMS PoC (slim)

Proof-of-concept LIMS template generator. LlamaExtract for PDF
extraction, ChromaDB RAG for regulatory standards, Next.js frontend
served at /lims. Local-dev-only at this stage — no AWS deployment.

Extracted from the original monorepo (Danik911/thesis_project) with
thesis-specific code, agents, and AWS infrastructure removed."
git remote add origin <LIMS_REPO_URL>     # confirmed with user at step 0
git push -u origin main
```

---

## 4. `.gitignore` for both repos

Each target repo gets a clean `.gitignore`. The source has accumulated 7 KB of rules; trim to what each repo actually needs.

**Use this template for both** (drop in as `.gitignore` at repo root):

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
.venv_*/
.mypy_cache/
.pytest_cache/
.ruff_cache/
.coverage
*.egg-info/
build/
dist/

# Node / Next.js
node_modules/
.next/
out/
*.tsbuildinfo

# Env / secrets
.env
.env.local
.env.*.local

# IDE / OS
.idea/
.vscode/
.DS_Store
Thumbs.db

# Project artifacts
output/
uploads/
logs/
screenshots/
cache/
chroma_db/
chroma_db_*/
*.tar.gz

# Claude Code / MCP user config (must never be committed)
.claude.json
.mcp.json
.claude/settings.local.json
.serena/
.amazonq/
.playwright-mcp/

# Terraform local state (CI uses S3 backend)
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl
```

---

## 5. Known gotchas (read before executing)

1. **`PYTHONPATH=/app/main` in Dockerfiles** is required because `pyproject.toml` exports `packages = ["main"]` while the code imports `from src.adapters.storage`. The source commits `3b34c7d` and `e014b7b` (ISSUE-042) added this; do not regress.
2. **`main/src/utils/cost_tracker.py` is essential** — `main/src/llms/openrouter_compat.py` imports it lazily. If the file is missing, jobs fail at OpenRouter init only (not at boot). The source has it restored as of `e014b7b`. Both target repos that include `main/src/llms/` must also include `main/src/utils/cost_tracker.py`.
3. **Frontend `eslint` and `typescript` build errors** are bypassed in `next.config.mjs` (`eslint.ignoreDuringBuilds: true`, `typescript.ignoreBuildErrors: true`). This is fine for the corporate handoff and is documented in ISSUE-042. The next agent should *not* try to re-enable strict mode without fixing the underlying errors.
4. **`docs/issues/ISSUE-042-redeploy-after-mes-bi-refactor.md`** narrates the source-repo history; it is **thesis-relevant** because the AWS deploy depends on its fixes. Keep it in the thesis repo. Do not move it to LIMS.
5. **`main/frontend/components/TemplateSelector.tsx`** is used by *both* `generate.tsx` (thesis) and `lims.tsx` (LIMS). Re-check before deleting; the safer move is to keep it in the thesis repo, copy it into the LIMS repo, and accept the duplication.
6. **AWS state preservation**: when the thesis repo is pushed to the corporate org and re-deployed, it will re-adopt the same ECR/S3/Terraform-state buckets at account `275333454012` via the auto-import block in `deploy.yml`. If the corporate AWS account differs, the auto-import will fail; the workflow then creates fresh resources. Confirm with the user which AWS account the thesis repo targets before the first deploy.
7. **`PRPs/` directory** is thesis-governance and contains audit trail records. Drop it from the LIMS repo; keep it in the thesis repo.
8. **`docs/MIGRATION_HANDOFF.md` (this file)** — delete from both target repos before commit. It is a transient artifact.

---

## 6. Checklist (use this in the handoff agent's TODO list)

- [ ] Confirm two target repo URLs with the user
- [ ] Confirm rotation of every secret listed in step 0
- [ ] Verify AWS infrastructure state with the user (running? destroyed? matters for thesis push)
- [ ] Step 1: clean clone + two working copies
- [ ] Step 2: thesis repo — delete, edit, verify, commit, push
- [ ] Step 3: LIMS repo — delete, edit, verify, commit, push
- [ ] Step 4: `.gitignore` is the clean template in each
- [ ] Step 5: known gotchas all addressed
- [ ] Step 6: delete this handoff doc from both target trees
- [ ] Report two PR / commit URLs back to the user
