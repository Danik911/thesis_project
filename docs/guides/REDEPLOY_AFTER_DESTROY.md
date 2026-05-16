# Redeploy the Thesis App After `/destroy`

How to bring `https://csvgeneration.com/` back online after the AWS infrastructure has been destroyed via `/destroy` (or the `destroy.yml` workflow).

**Last verified:** 2026-04-28 (deploy run `25047539593`, branch `fix/deploy-workflow-dockerfile-names` — clean first-try redeploy after `/destroy`, all 6 stages green in ~22 min).
**Region:** `eu-west-2` · **Account:** `275333454012`

---

## TL;DR

```bash
# From repo root
gh workflow run deploy.yml --ref fix/deploy-workflow-dockerfile-names --repo Danik911/thesis_project
gh run watch --repo Danik911/thesis_project
```

That single workflow rebuilds all three Docker images, re-applies Terraform (auto-importing preserved resources), forces ECS service rollout, and invalidates CloudFront. Expected duration: **15–20 minutes**.

When it finishes:

```bash
curl -sI https://csvgeneration.com/ | head -1   # expect 200
```

---

## Why this works without re-uploading anything

`/destroy` is intentionally selective. It tears down the *running* stack but **preserves**:

| Preserved Resource | Region | Why |
|--------------------|--------|-----|
| `pharma-test-gen-{api,worker,frontend}` ECR repos | `eu-west-2` | Re-pushing 26 GB of images costs hours; preserving costs ~$2.6/month. |
| `pharma-test-gen-terraform-state` S3 bucket | `eu-west-2` | Holds the active Terraform state. |
| `pharma-test-gen-chromadb-275333454012` S3 bucket | `eu-west-2` | Holds the 21.6 MB `chroma_db.tar.gz` the worker needs for RAG. |
| `terraform-locks` DynamoDB table | `eu-west-2` | Coordinates concurrent Terraform runs. |
| Route 53 hosted zone for `csvgeneration.com` | global | DNS apex; recreating costs another zone fee + DNS propagation delay. |
| OIDC IAM role `pharma-test-gen-github-actions` | global | The role GitHub Actions assumes; can be recreated by Terraform but reuse is cheaper. |

The deploy workflow knows about each of these and contains an *import block* (lines 87–210 of `.github/workflows/deploy.yml`) that re-adopts them into the new Terraform state instead of trying to create duplicates. **No manual `terraform import` is needed.**

---

## What the workflow actually does

| Stage | Step | What happens |
|-------|------|--------------|
| 1 | `build-and-push` | Builds `Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.frontend` natively on AMD64 GitHub runners (no QEMU). Tags as `staging-latest` and pushes to the preserved ECR repos. ~3 min per image (parallel). |
| 2 | `deploy-infrastructure` | `terraform init` → import preserved resources → `terraform apply -var-file=environments/staging.tfvars`. ~10 min. |
| 3 | `update-services` | Registers task-definition revisions, calls `aws ecs update-service --force-new-deployment` for all three services, then waits for them to stabilize. ~3–5 min. |
| 4 | `invalidate-cloudfront` | Clears the CDN cache so the new frontend bundle goes live immediately. <30 s. |

---

## Prerequisites (verify once, then forget)

These should already be in place; confirm only if a deploy fails on infrastructure rather than build.

1. **GitHub auth** — `gh auth status` succeeds. If your shell has a stale `GITHUB_TOKEN` environment variable, prefix calls with `GITHUB_TOKEN= gh ...` (empty value) so it falls back to the keyring token.
2. **Repo secrets** in `Danik911/thesis_project` → Settings → Secrets and variables → Actions:
   - `AWS_OIDC_ROLE_ARN` = `arn:aws:iam::275333454012:role/pharma-test-gen-github-actions`
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (frontend build pulls this in)
   - `CLERK_SECRET_KEY`, `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` (read at runtime via Secrets Manager, but the deploy workflow re-creates the SM entries from these on apply if they are missing).
3. **Terraform state bucket exists**: `aws s3 ls s3://pharma-test-gen-terraform-state --region eu-west-2` returns one object (`prod/terraform.tfstate`).
4. **ChromaDB tarball is present**: `aws s3 ls s3://pharma-test-gen-chromadb-275333454012/ --region eu-west-2` shows `chroma_db.tar.gz`.

If any of these are missing, fix them before running the workflow — the workflow itself does not regenerate Clerk keys or upload the ChromaDB tarball.

---

## Choosing the branch to deploy from

The deploy workflow accepts `--ref <branch>` and runs against whatever that branch points at. Two branches matter:

| Branch | Use when |
|--------|----------|
| `fix/deploy-workflow-dockerfile-names` | **Default for redeploy.** Contains the six fixes that ISSUE-042 documents (Dockerfile rename in `deploy.yml`, `next.config.mjs` build-time bypasses, MDAViewer paste fix, `PYTHONPATH=/app/main` in `Dockerfile.api`/`Dockerfile.worker`, restored `main/src/utils/cost_tracker.py`). Deploy run `24796252803` succeeded from this branch on 2026-04-22. |
| `feature/mes-agentic-bi` | Only after the fixes above are merged into it. As of 2026-04-22 it does not contain them and will fail. |

Do **not** deploy from `main` or `AWS_deployment` for the thesis app right now — `main` lacks the runtime fixes; `AWS_deployment` is older and will diverge from the LIMS/MES-BI work.

---

## Verification after deploy

```bash
# 1. Services stable
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker \
  --query "services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}" \
  --output table --region eu-west-2
# Expect: status=ACTIVE and running==desired==1 for all three.

# 2. Site responds
curl -sI https://csvgeneration.com/ | head -1
# Expect: HTTP/2 200

# 3. End-to-end job
# - Visit https://csvgeneration.com/generate
# - Sign in with Clerk
# - Upload main/test_data/urs-001.md (or any URS sample)
# - The API should return 202 (job accepted), worker picks it up from SQS,
#   OpenRouter is invoked, and the result page shows generated tests.
```

If `POST /jobs` returns **503** with `Server: awselb/2.0` and `X-Cache: Error from cloudfront`, the API service has 0 healthy targets. Check container logs:

```bash
MSYS_NO_PATHCONV=1 aws logs tail /ecs/pharma-test-gen/api --since 10m --region eu-west-2 | tail -40
```

---

## Common failure modes (full details in ISSUE-042)

| Symptom in logs | Cause | Quick fix |
|-----------------|-------|-----------|
| `failed to read dockerfile: open Dockerfile.api.pip: no such file or directory` | Workflow drifted from a Dockerfile rename. | Already fixed on `fix/deploy-workflow-dockerfile-names`. |
| `ModuleNotFoundError: No module named 'src'` at `main/api/dependencies.py:23` | `PYTHONPATH` not set; `pyproject.toml` packages narrowed. | Already fixed via `ENV PYTHONPATH="/app/main"` in `Dockerfile.api` and `Dockerfile.worker`. |
| `Failed to import LLM provider ModelProvider.OPENROUTER: No module named 'src.utils'` (only at job time) | `main/src/utils/cost_tracker.py` was deleted. | Already restored. |
| `eslint` / `tsc` errors during frontend build for LIMS/BI components | New components have stricter rules than the rest of the codebase. | `next.config.mjs` already sets `eslint.ignoreDuringBuilds=true` and `typescript.ignoreBuildErrors=true`. |
| `503 Service Temporarily Unavailable` from awselb/2.0 *after* deploy succeeds | API/worker tasks are crashing on startup (not building). | Tail `/ecs/pharma-test-gen/api` and `/ecs/pharma-test-gen/worker` log groups; almost always a Python import error like the ones above. |

---

## Troubleshooting commands

```bash
# Latest deploy run
GITHUB_TOKEN= gh run list --workflow=deploy.yml --repo Danik911/thesis_project --limit 5

# Live logs for a failing job
GITHUB_TOKEN= gh run view <RUN_ID> --log-failed --repo Danik911/thesis_project

# Container logs (Git Bash on Windows mangles /ecs/... paths — disable conversion)
MSYS_NO_PATHCONV=1 aws logs tail /ecs/pharma-test-gen/api    --since 15m --region eu-west-2
MSYS_NO_PATHCONV=1 aws logs tail /ecs/pharma-test-gen/worker --since 15m --region eu-west-2

# What revision is each service running?
aws ecs describe-services --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker \
  --query 'services[].{name:serviceName,taskDef:taskDefinition}' \
  --output table --region eu-west-2

# Force a fresh rollout without rebuilding (e.g. after a Secrets Manager change)
gh workflow run redeploy.yml --repo Danik911/thesis_project
# OR locally: python aws/scripts/redeploy.py
```

---

## When *not* to use this workflow

- **Secret rotation only** (e.g. new `OPENROUTER_API_KEY`): use `/redeploy` (or `python aws/scripts/redeploy.py`). It skips Docker builds and just forces a new ECS deployment so containers pick up the rotated secret. ~3 min.
- **Code change in only one of the three services**: the workflow will rebuild all three because the matrix has no path filtering. That's fine for thesis-only redeploys but slower than a manual targeted build.
- **You destroyed and want to *fully* start over** (different domain, different account): do not use this — manual setup of ACM, Route 53 delegation, and the OIDC role is required first. See `docs/AWS_DEPLOYMENT.md`.

---

## Cost while idle (after `/destroy`)

Approximate monthly cost of the preserved resources alone, with no ECS/ALB/CloudFront running:

| Resource | Size | Rate (eu-west-2) | Monthly |
|----------|------|------------------|---------|
| ECR — api | 12.3 GB | $0.10/GB | $1.23 |
| ECR — worker | 13.1 GB | $0.10/GB | $1.31 |
| ECR — frontend | 0.96 GB | $0.10/GB | $0.10 |
| S3 — chromadb (21.6 MB) | <1 GB | $0.023/GB | <$0.01 |
| S3 — terraform-state (412 B) | negligible | — | $0 |
| DynamoDB — terraform-locks (idle) | — | pay-per-request | $0 |
| Route 53 hosted zone | 1 zone | $0.50/zone/month | $0.50 |
| CloudWatch — `containerinsights/.../performance` (~4 MB) | <1 GB | $0.03/GB | <$0.01 |
| **Total idle** | | | **~$3.15/month** |

ECR storage is the dominant cost. To trim it, run an ECR lifecycle policy keeping only the last 5 images per repo (workflow already pushes a single `staging-latest` tag, so old digests can be aged out aggressively).

---

## Related docs and issues

- `docs/AWS_DEPLOYMENT.md` — full deploy reference (first-time setup, IAM, DNS).
- `docs/GITHUB_ACTIONS_DEPLOYMENT.md` — workflow internals.
- `docs/issues/ISSUE-042-redeploy-after-mes-bi-refactor.md` — root cause of every blocker fixed in the 2026-04-22 redeploy cycle.
- `docs/issues/ISSUE-005-rebuild-uses-wrong-image-tag.md` — IAM policies sometimes detach after destroy/deploy; verify with `aws iam list-role-policies --role-name pharma-test-gen-api-task-role`.
- `docs/issues/ISSUE-006-api-task-definition-revision.md` — ECS may run a stale task-def revision lacking secrets; force-update if `/health` returns 500 with "Authentication system not configured".
- `.claude/commands/deploy.md`, `.claude/commands/destroy.md`, `.claude/commands/redeploy.md` — slash command references.
