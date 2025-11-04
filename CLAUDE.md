# CLAUDE.md

Guidance for Claude Code when working with this pharmaceutical test generation thesis project.

---

## 🚨 CRITICAL OPERATING PRINCIPLES

### Never Claim Success Without User Confirmation
- ❌ NEVER say "working", "successful", "complete" without explicit user verification
- ✅ ALWAYS ask "Did you see the expected result?" before claiming success
- ✅ ALWAYS wait for user confirmation before marking tasks complete

### Zero Tolerance for Fallback Logic
- ❌ NEVER implement fallback values, default behaviors, or "safe" alternatives
- ❌ NEVER mask errors with artificial confidence scores or deceptive logic
- ✅ ALWAYS throw errors with full stack traces when something fails
- ✅ ALWAYS preserve genuine confidence levels and expose real system state
- **If something doesn't work - FAIL LOUDLY with complete diagnostic information**

### Package Installation Policy
- **NEVER skip** package installation due to permission issues
- **ALWAYS ask user** to install missing packages instead of proceeding without them
- **NEVER assume** packages are optional if required for functionality

---

## 🎯 Current Project Status

**Phase:** AWS Production Migration (10-week timeline)
**MVP Status:** ✅ Complete (9/9 tasks - DeepSeek V3, Phoenix, ChromaDB)
**Current Focus:** Migrating local system to AWS production (ECS Fargate, Aurora, S3 Vectors, Bedrock)

---

## 🚀 AWS Migration Goals

**Objective:** Migrate GAMP-5 compliant pharmaceutical test generation system to AWS production

### Timeline: 10 Weeks, 5 Phases
1. **Foundations** (Week 0.5) - Terraform backend, IAM scaffolding, service quotas
2. **Backend Abstraction** (Weeks 1-3) - Storage/RAG adapters, Clerk auth, local MVP
3. **Frontend Dashboard** (Weeks 2-4) - Next.js dashboard, job management, Clerk (EU)
4. **Containerization** (Weeks 4-6) - Docker Compose, load testing, LangFuse local
5. **AWS Deployment** (Weeks 6-9) - Infrastructure deployment, RAG migration, validation
6. **Hardening** (Weeks 9-10) - S3 Object Lock, autoscaling, monitoring, rollback procedures

### Success Criteria
- ≥80% RAG retrieval quality (ChromaDB → S3 Vectors)
- P95 workflow latency ≤15 minutes
- Full trace capture (131 spans maintained)
- GAMP-5 compliance preserved
- Estimated cost: ~$1,190/month production (~$865 with optimizations)

**Complete Details:** [AWS Migration PRP](PRPs/aws-migration-updated.md)

---

## 🤖 Technology Stack

### Local Development
- **Backend:** Python 3.12, FastAPI, uvicorn
- **Frontend:** Next.js (when implemented)
- **RAG:** ChromaDB (persistent client)
- **LLM:** DeepSeek V3 (671B MoE) via OpenRouter
- **Observability:** Phoenix (Arize)
- **Auth:** Clerk (test mode)
- **Storage:** Local filesystem (`./output/`)

### AWS Production Target
- **Compute:** ECS Fargate (2 vCPU/4 GB API, 4 vCPU/8 GB worker)
- **Database:** Aurora Serverless v2 (PostgreSQL 15, Data API)
- **RAG:** S3 Vectors (1536 dims, cosine similarity)
- **LLM:** Amazon Bedrock (DeepSeek-V3.1) - $0.90/1M input, $2.61/1M output
- **Region:** eu-west-2 (London)
- **Queue:** Amazon SQS + DLQ
- **Observability:** LangFuse (self-hosted) + CloudWatch
- **Auth:** Clerk (EU endpoints)
- **Storage:** S3 (Object Lock, 7-year retention)
- **CDN:** CloudFront (frontend)
- **Secrets:** AWS Secrets Manager
- **IaC:** Terraform

---

## 📂 Project Structure

```
thesis_project/
├── .claude/agents/           # 9 specialized subagents
├── .taskmaster/              # Task-Master AI (MVP complete)
├── PRPs/                     # Production Readiness Plans
│   └── aws-migration-updated.md   # AWS migration plan
├── examples/                 # Course reference materials
│   ├── alex/                # Example production app
│   └── production/guides/   # Course Jupyter notebooks
├── main/                     # Main application
│   ├── src/
│   │   ├── core/unified_workflow.py   # LlamaIndex workflow
│   │   ├── agents/          # Multi-agent system
│   │   └── adapters/        # Storage/RAG abstraction (TODO)
│   ├── api/                 # FastAPI backend (TODO)
│   ├── docs/                # Documentation
│   │   ├── plans/mvp_implementation_plan.md
│   │   └── guides/QUICK_START_GUIDE.md
│   ├── tests/               # Test suites
│   └── output/              # Generated test suites
└── terraform/               # AWS infrastructure (TODO)
```

---

## 🎯 Task-Master AI Integration

### Quick Commands
```bash
# Get next task
mcp__task-master-ai__next_task

# View task details
mcp__task-master-ai__get_task --id=X

# Update task status
mcp__task-master-ai__set_task_status --id=X --status=in-progress
mcp__task-master-ai__set_task_status --id=X --status=done

# Log progress
mcp__task-master-ai__update_subtask --id=X.Y --prompt="Implementation notes"

# Research support
mcp__task-master-ai__expand_task --id=X --research
```

**Full Guide:** [Task-Master AI Tutorial](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/tutorial.md)

---

## 🤖 Specialized Subagents

Located at `.claude/agents/`. Always provide comprehensive context when delegating.

| Agent | Purpose | Key Restriction |
|-------|---------|----------------|
| **context-collector** | Research GAMP-5, LlamaIndex, pharmaceutical standards | - |
| **task-analyzer** | Analyze Task-Master AI tasks, check dependencies | - |
| **task-executor** | Execute specific tasks following GAMP-5 patterns | NO FALLBACKS |
| **tester-agent** | Validate implementations, run tests | NO FALLBACKS |
| **debugger** | Advanced debugging with Ultrathink methodology | NO FALLBACKS |
| **monitor-agent** | Phoenix observability analysis | NO FALLBACKS |
| **end-to-end-tester** | Complete workflow testing with Phoenix | NO FALLBACKS |
| **cv-validation-tester** | Cross-validation testing (DeepSeek only) | NO FALLBACKS |
| **cv-analyzer** | Trace and span analysis for validation | - |

**Critical:** All subagents must fail explicitly rather than mask problems with fallback logic.

---

## 🏗️ Development Workflow

### Phase 1: Local Development (Current)
```bash
# Set environment
export ENVIRONMENT=local
export USE_S3=false
export RAG_MODE=chromadb

# Run workflow
uv run python main/main.py

# Monitor
phoenix serve  # http://localhost:6006
```

### Phase 2: AWS Migration (Next)
1. Implement storage abstraction layer (`main/src/adapters/storage.py`)
2. Implement vector store provider (`main/src/adapters/vector_store.py`)
3. Build FastAPI backend (`main/api/app.py`)
4. Containerize with Docker
5. Deploy infrastructure via Terraform
6. Migrate ChromaDB → S3 Vectors
7. Configure LangFuse + CloudWatch

**Follow:** [AWS Migration PRP](PRPs/aws-migration-updated.md)

---

## 📚 Key Documentation

### AWS Migration
- [AWS Migration PRP](PRPs/aws-migration-updated.md) - Complete 10-week plan
- [Example Production App](examples/alex/README.md) - Reference architecture
- [Production Course Guides](examples/production/guides/) - Jupyter notebooks

### MVP Documentation
- [MVP Implementation Plan](main/docs/plans/mvp_implementation_plan.md)
- [Quick Start Guide](main/docs/guides/QUICK_START_GUIDE.md)
- [OSS Migration Summary](main/docs/guides/OSS_MIGRATION_SUMMARY.md)

### External References
- [Task-Master AI Guide](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/tutorial.md)
- [LlamaIndex Workflows](https://docs.llamaindex.ai/en/stable/module_guides/workflow/)

---

## 🧪 Critical Requirements

### Architecture Principles
- **Event-driven multi-agent** system via LlamaIndex 0.12.0+ workflows
- **GAMP-5 categorization** as mandatory first step
- **Compliance validation** (ALCOA+, 21 CFR Part 11)
- **Comprehensive error handling** with full diagnostic information
- **NO FALLBACK LOGIC** - fail explicitly with stack traces

### Compliance Standards
- **GAMP-5:** Software categorization and validation
- **ALCOA+:** Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available
- **21 CFR Part 11:** Electronic records and signatures (post-MVP)
- **Data Residency:** EU (eu-west-2 region, London)

### Development Standards
- **Research first:** Check context7, official docs, course examples
- **Incremental validation:** Test after each change
- **Error prevention:** Address known issues proactively
- **No assumptions:** Verify paths, dependencies, configurations

---

## ⚡ Quick References

**Task Status:** `pending`, `in-progress`, `done`, `blocked`, `deferred`, `cancelled`
**Task Format:** Main (1, 2, 3), Subtasks (1.1, 1.2, 2.1)
**Priority:** `high`, `medium`, `low`

**Working Directory:** `C:\Users\anteb\Desktop\Courses\Projects\thesis_project`
**Git Branch:** `backend` (main branch: `main`)

---

**Remember:** This project requires regulatory compliance and pharmaceutical validation standards. Always prioritize compliance over speed. **NEVER IMPLEMENT FALLBACKS - FAIL EXPLICITLY WITH FULL DIAGNOSTIC INFORMATION.**
