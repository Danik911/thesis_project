# CLAUDE.md

Guidance for Claude Code on the pharmaceutical test generation thesis project and AI4LIMS PoC.

## Critical Operating Principles

### Never Claim Success Without User Confirmation
- NEVER say "working", "successful", "complete" without explicit user verification
- ALWAYS wait for user confirmation before marking tasks complete

### Zero Tolerance for Fallback Logic
- NEVER implement fallback values, default behaviors, or "safe" alternatives
- NEVER mask errors with artificial confidence scores
- ALWAYS throw errors with full stack traces when something fails
- **If something doesn't work - FAIL LOUDLY with complete diagnostic information**

### Package Installation Policy
- NEVER skip package installation due to permission issues
- ALWAYS ask user to install missing packages

### Issue Management Protocol
When encountering bugs, errors, or unexpected behavior:

1. **Search First** - Check `docs/issues/ISSUE-CATALOG.md` for existing solutions
2. **Create Before Solving** - If no solution exists, create new issue file BEFORE attempting fix:
   - Format: `ISSUE-###-short-description.md` (see catalog for next number)
   - Include: Date, Symptom, Error messages, Affected files
3. **Document Solution** - After resolving, update the issue file with:
   - Root Cause analysis
   - Files Modified (table format)
   - Code changes (Before/After)
   - Prevention guidance
4. **Cross-Reference** - Link related issues when applicable
5. **Update Catalog** - Run doc-updater agent OR manually update `docs/issues/ISSUE-CATALOG.md`

**Issue Catalog**: `docs/issues/ISSUE-CATALOG.md` - Quick lookup for all issues
**Issue Template**: See `docs/issues/ISSUE-001-cloudfront-404-errors.md` for format example.

---

## Documentation References

| Topic | File |
|-------|------|
| Quick Start | `README.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| AWS Deployment | `docs/AWS_DEPLOYMENT.md` |
| CI/CD Pipeline | `docs/GITHUB_ACTIONS_DEPLOYMENT.md` |
| Docker Development | `docs/DOCKER.md` |
| Project Structure | `docs/PROJECT_STRUCTURE.md` |
| Troubleshooting | `docs/TROUBLESHOOTING.md` |
| Development Guides | `docs/guides/` (workflow usage, RAG, Clerk, Docker builds) |
| Regulatory Standards | `docs/regulatory_guides/` (GAMP-5, FDA Part 11, ICH Q9, ALCOA+) |
| PRP Workflow | `.claude/commands/prp.md` |
| PRP Tasks | `PRPs/tasks/` (0.1-5.3, 23 tasks) |
| Issues | `docs/issues/` |
| Issue Catalog | `docs/issues/ISSUE-CATALOG.md` |
| AI4LIMS PoC Plan | `docs/project_p/AI4LIMS_PoC_Plan.md` |

---

## Subagents

Located at `.claude/agents/`. All subagents must fail explicitly (NO FALLBACKS).

| Agent | Purpose | Model |
|-------|---------|-------|
| context-collector | Research GAMP-5, LlamaIndex patterns, pharmaceutical standards | Sonnet |
| debugger | Fix complex issues with max 5 iterations (Ultrathink methodology) | Opus |
| doc-updater | Update documentation after code changes, maintain issue catalog | Sonnet |
| security-auditor | READ-ONLY vulnerability scanning (OWASP, secrets, AWS misconfig) | Sonnet |
| task-analyzer | Pre-flight checker for manual AWS/infrastructure setup | Sonnet |
| task-executor | Implement PRP tasks following GAMP-5 patterns | Opus |
| tester-agent | Validate implementations with real data first | Sonnet |

---

## Skills

Located at `.claude/skills/`. Invoke via skill name.

| Skill | Use When |
|-------|----------|
| aws-deployment | AWS ECS/Terraform deployment, cost management |
| bold-frontend-design | Creative/bold UI design, 3D, animations |
| clerk-token-ops | JWT token generation for integration tests |
| debugging-docker | Docker build/runtime, ECR/ECS, ARM64/AMD64 issues |
| debugging-mastery | Complex multi-file bug investigation |
| langfuse-dashboard | Dashboard automation via Playwright MCP |
| langfuse-extraction | Trace extraction, ALCOA+ audit trails |
| langfuse-integration | Phoenix to LangFuse migration |
| meta-skill-guide | Creating new custom skills |
| prompt-writing | Agent prompts, Task tool delegation |
| testing-api-authentication | FastAPI + Clerk JWT testing |
| testing-api-manual | Manual API workflow testing (Docker) |

---

## PRP Workflow

```bash
/prp {task-id}   # Execute task (e.g., /prp 1.2)
```

- **Flow**: context-collector -> task-executor -> tester-agent -> debugger (if needed)
- **State**: `.claude/state/results/` (Git tracked for GAMP-5 compliance)
- **Details**: See `.claude/commands/prp.md`

---

## AI4LIMS PoC

**Branch**: `prjoject_p_protatype` | **Routes**: `/lims/*` | **Plan**: `docs/project_p/AI4LIMS_PoC_Plan.md`

| Component | Technology |
|-----------|-----------|
| Extraction | LlamaExtract (LlamaIndex Cloud) |
| Chat LLM | GPT-5 / Claude Opus 4.6 via OpenRouter |
| RAG | ChromaDB (`mda_templates` collection) |
| Export | openpyxl (4-sheet XLSX) |
| Auth | Clerk (feature-flagged off: `NEXT_PUBLIC_AUTH_ENABLED=false`) |
| Docker | `docker-compose.lims.yml` (minimal: frontend + API) |

**Key files**: `main/src/lims/mda_schema.py`, `main/src/lims/`, `main/api/lims_router.py`, `main/frontend/pages/lims.tsx`

**Strategy**: Additive only — never modify thesis files. Separate router, compose, config, collection.

---

## Key Commands

```bash
# Local Development (Docker Compose)
docker-compose -f docker-compose.dev.yml up -d

# AI4LIMS PoC (Docker Compose)
docker-compose -f docker-compose.lims.yml up -d

# AWS Deployment
python aws/scripts/redeploy.py              # Redeploy services
python aws/scripts/redeploy.py --status-only # Check status

# Testing
uv run pytest main/tests/ -v
uv run ruff check --fix && uv run mypy .
```

---

## Tech Stack

| Environment | LLM | Observability | Region |
|-------------|-----|---------------|--------|
| Production (AWS) | DeepSeek V3.1 via OpenRouter | LangFuse Cloud (EU) | eu-west-2 |
| Development | Gemini 2.5 Flash Lite | LangFuse Cloud (EU) | - |

**Auth**: Clerk | **IaC**: Terraform | **Queue**: SQS

---

## Development Environment

- **OS**: Windows with WSL2 (Ubuntu Linux)
- **Docker**: Runs in WSL Ubuntu (NOT Docker Desktop)
- **Terraform**: Installed in WSL at `~/bin/terraform`
- **AWS CLI**: Available in both Windows and WSL

**Important**: All Docker and Terraform commands should be run via `wsl -e bash -c "..."` wrapper.

---

**Remember**: Regulatory compliance (GAMP-5, ALCOA+, 21 CFR Part 11) over speed. NEVER IMPLEMENT FALLBACKS.
