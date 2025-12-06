# CLAUDE.md

Guidance for Claude Code on the pharmaceutical test generation thesis project.

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

---

## Documentation References

| Topic | File |
|-------|------|
| Architecture & Quick Start | `README.md` |
| Technical Details | `TECHNICAL_ARCHITECTURE_REPORT.md` |
| AWS Deployment | `aws/README.md`, `aws/docs/AWS-ARCHITECTURE.md` |
| File Structure | `main/docs/guides/PROJECT_CORE_FILES_SCHEME.md` |
| PRP Workflow | `.claude/commands/prp.md` |
| PRP Tasks | `PRPs/tasks/` (0.1-5.3, 23 tasks) |
| Issues & Gotchas | `main/docs/issues/` (common deployment pitfalls) |

---

## Subagents

Located at `.claude/agents/`. All subagents must fail explicitly (NO FALLBACKS).

| Agent | Purpose | Model |
|-------|---------|-------|
| context-collector | Research GAMP-5, LlamaIndex patterns, pharmaceutical standards | Sonnet |
| debugger | Fix complex issues with max 5 iterations (Ultrathink methodology) | Opus |
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

## Key Commands

```bash
# Local Development (Docker Compose)
docker-compose -f docker-compose.dev.yml up -d

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
