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
├── .claude/commands/         # Custom slash commands (e.g., /prp)
├── .claude/state/            # PRP workflow state management
├── PRPs/                     # Production Readiness Plans
│   ├── tasks/               # PRP task definitions (0.1-5.3)
│   └── aws-migration-updated.md   # AWS migration plan
├── aws/                      # AWS infrastructure and configuration
│   ├── iam-policies/        # IAM policy definitions
│   │   ├── phase0-deployment-policy.json (Tasks 0.1-0.3)
│   │   ├── phase0-complete-policy.json (Tasks 0.1-0.4)
│   │   ├── attach-phase0-policy.sh
│   │   ├── attach-phase0-complete-policy.sh
│   │   ├── verify-phase0-permissions.sh
│   │   ├── verify-phase0-complete-permissions.sh
│   │   └── IAM-SETUP-GUIDE.md
│   ├── terraform/           # Infrastructure as Code (TODO)
│   ├── scripts/             # AWS automation scripts (TODO)
│   └── docs/                # AWS-specific documentation (TODO)
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
```

---

## 🤖 Specialized Subagents

Located at `.claude/agents/`. Always provide comprehensive context when delegating.

| Agent | Purpose | Key Restriction |
|-------|---------|----------------|
| **context-collector** | Research GAMP-5, LlamaIndex, pharmaceutical standards | - |
| **task-analyzer** | Pre-flight checker for manual AWS/Clerk/infrastructure setup BEFORE /prp | READ-ONLY |
| **task-executor** | Execute specific tasks following GAMP-5 patterns | NO FALLBACKS |
| **tester-agent** | Validate implementations, run tests | NO FALLBACKS |
| **debugger** | Advanced debugging with Ultrathink methodology | NO FALLBACKS |
| **monitor-agent** | Phoenix observability analysis | NO FALLBACKS |
| **end-to-end-tester** | Complete workflow testing with Phoenix | NO FALLBACKS |
| **cv-validation-tester** | Cross-validation testing (DeepSeek only) | NO FALLBACKS |
| **cv-analyzer** | Trace and span analysis for validation | - |

**Critical:** All subagents must fail explicitly rather than mask problems with fallback logic.

---

## 🎬 PRP Task Execution Workflow

### Overview
Orchestrated multi-agent workflow for executing Production Readiness Plan (PRP) tasks from `PRPs/tasks/` with state management, compliance tracking, and zero-fallback error handling.

### Quick Start
```bash
# Execute a PRP task (e.g., Phase 1, Task 2)
/prp 1.2
```

### Task Naming Convention
All PRP tasks use ID format: `{phase}.{task}` (e.g., 0.1, 1.2, 5.3)
- **Range:** 0.1-5.3 (23 tasks across 6 phases)
- **Files:** `PRPs/tasks/{id}-{description}.md`
- **Example:** `PRPs/tasks/1.2-vector-store-provider.md`

### Workflow Architecture

```
User: /prp 1.2
    ↓
Main Orchestrator:
  1. Validate task exists
  2. Initialize state files
  3. Mark task 'in-progress'
    ↓
🟢 context-collector (Research & Context)
  → Research LlamaIndex, GAMP-5, AWS patterns
  → Save findings: .claude/state/results/context-collector-{timestamp}.md
    ↓
🟡 task-executor (Implementation)
  → Read context-collector results
  → Implement with NO FALLBACK logic
  → Track all file modifications
  → Save results: .claude/state/results/task-executor-{timestamp}.md
    ↓
🔴 tester-agent (Validation & Testing)
  → Read task-executor results
  → Run tests (pytest, mypy, ruff)
  → HONEST assessment (failures included)
  → Save results: .claude/state/results/tester-agent-{timestamp}.md
    ↓
Conditional Branch:
  IF tester-agent status = FAIL:
    🟣 debugger (Issue Resolution)
      → Read failure diagnostics
      → Systematic debugging (max 5 iterations)
      → Save results: .claude/state/results/debugger-{timestamp}.md
    ↓
Main Orchestrator:
  - Aggregate all results
  - Present comprehensive summary
  - REQUEST USER CONFIRMATION
  - Wait for "Yes" before marking 'done'
```

### State Management

#### Directory Structure
```
.claude/state/
├── prp-workflow-state.md          # Main orchestrator state (Git tracked)
├── current-task-context.md         # Active task details (Git tracked)
└── results/                        # Agent result files (Git tracked)
    ├── context-collector-YYYYMMDD-HHMMSS.md
    ├── task-executor-YYYYMMDD-HHMMSS.md
    ├── tester-agent-YYYYMMDD-HHMMSS.md
    └── debugger-YYYYMMDD-HHMMSS.md  (conditional)
```

#### State Transfer Protocol
- **Each agent**: Reads previous agent results from `.claude/state/results/`
- **Main orchestrator**: Provides COMPLETE context to each agent (NO ASSUMPTIONS)
- **Result files**: Tracked in Git for GAMP-5 audit compliance
- **No conversation history**: Agents rely ONLY on state files

### Critical Requirements

#### Zero Tolerance for Fallback Logic
- ❌ NO default values masking missing data
- ❌ NO success responses on failures
- ❌ NO artificial confidence scores
- ✅ ALL errors throw with full stack traces
- ✅ ALL failures report complete diagnostics

#### User Confirmation Gate
- ❌ NEVER mark task 'done' without explicit user "Yes"
- ✅ ALWAYS wait for user verification
- ✅ ALWAYS ask "Did you see the expected result?"

#### Model Enforcement
- ✅ MUST USE: DeepSeek V3 (deepseek/deepseek-chat) via OpenRouter
- ❌ FORBIDDEN: GPT-4, O3, O1, Claude, or any OpenAI generation models

### Workflow Duration
**Estimated Total Time:** 20-60 minutes depending on task complexity
- context-collector: 5-15 min
- task-executor: 10-30 min
- tester-agent: 5-10 min
- debugger (if needed): 10-20 min

### Example Execution

```bash
# Execute task 1.2 (Vector Store Provider)
/prp 1.2

# Workflow executes agents sequentially
# Main orchestrator presents summary at end
# User confirms success before marking 'done'
```

### Success Criteria
✅ Task file found and read successfully
✅ All 3-4 agents completed (context, executor, tester, optional debugger)
✅ Result files created by all agents
✅ NO FALLBACK LOGIC violations = 0
✅ GAMP-5 compliance requirements met
✅ Tests passing (or failures acceptable per user)
✅ User explicitly confirmed success
✅ State files updated and tracked in Git

**For detailed workflow specification:** See `.claude/commands/prp.md`

---

## 🔍 Pre-Flight Check: Task Analyzer Workflow

**Purpose:** Identify manual prerequisites BEFORE executing `/prp` tasks to ensure engineers have completed all AWS Console actions, third-party registrations, and credential collection.

**NOT part of automated /prp workflow** - this is a separate, optional helper step.

### Invocation Pattern
```
1. Engineer wants to execute Task X
2. Engineer runs: "Analyze prerequisites for task X" (invokes task-analyzer)
3. task-analyzer generates action list → saves to .claude/state/results/
4. Engineer completes manual steps
5. Engineer confirms readiness
6. Engineer executes: /prp X
```

### Task Categories by Manual Setup Intensity

#### 🔴 **HEAVY MANUAL SETUP** (2-8 hours + wait time)
**Tasks:** 0.1-0.4, 1.4, 4.1-4.3

**Manual Actions Required:**
- AWS Console access (Service Quotas, IAM, RDS, Bedrock, etc.)
- Third-party account signups (Clerk, LangFuse)
- Approval-gated steps (quota requests: 5 days, Bedrock access: 2-7 days)
- Resource creation (ECR repositories, VPC, Aurora clusters)
- Credential collection (ARNs, IDs, API keys)

**Examples:**
- **Task 0.1:** Submit Fargate vCPU quota increase → Wait 5 business days
- **Task 1.4:** Sign up for Clerk → Copy publishable/secret keys → Configure EU endpoints
- **Task 4.3:** Request Bedrock DeepSeek-V3.1 access → Wait for approval

#### 🟡 **MODERATE MANUAL SETUP** (15-60 minutes)
**Tasks:** 2.2, 2.3, 5.1

**Manual Actions Required:**
- Reuse credentials from earlier tasks
- Simple service configurations
- Optional account signups

**Examples:**
- **Task 2.2:** Copy Clerk keys from Task 1.4 (no new signup)
- **Task 2.3:** Sign up for LangFuse → Copy keys

#### 🟢 **LOW/NO MANUAL SETUP** (0-5 minutes)
**Tasks:** 1.1-1.3, 2.1, 3.1-3.4, 4.4, 5.2-5.3

**Manual Actions Required:**
- None (pure coding tasks)
- Dependencies automated by Terraform (IAM roles, etc.)

**Response:** "No manual setup required. Ready for /prp execution after dependency tasks complete."

### Agent Output Format
task-analyzer generates a concise action list with:
- **Setup intensity categorization** (🔴🟡🟢)
- **Manual prerequisites checklist** (AWS resources, third-party accounts, approval steps)
- **Blocking items** highlighted upfront (e.g., "Cannot proceed without quota approval")
- **Required reading** from `examples/alex/guides/` with time estimates
- **Setup sequence** ordered by dependencies
- **Total prep time** estimate (manual steps + waiting time + reading time)
- **Resource collection templates** (ARN: _______, Key: _______)

**Saved to:** `.claude/state/results/task-analyzer-{timestamp}.md` (GAMP-5 audit trail)

### When to Use task-analyzer

✅ **Use BEFORE /prp for:**
- All Phase 0 tasks (0.1-0.4) - Foundation setup
- Task 1.4 - Clerk authentication
- Task 4.1 - ECS deployment (ECR, VPC setup)
- Task 4.2 - Aurora cluster creation
- Task 4.3 - Bedrock model access

❌ **Skip for:**
- Pure coding tasks (1.1-1.3, 2.1, 3.1-3.4, etc.)
- Tasks with only Terraform-automated dependencies

### Example: Analyzing Task 0.1 (Service Quotas)

**Engineer Request:**
```
Analyze prerequisites for task 0.1
```

**task-analyzer Output:**
```markdown
# Pre-Flight Check: Task 0.1

**Setup Intensity:** 🔴 HEAVY (Est. 2 hours + 5-day wait)

## Manual Prerequisites

### AWS Console Actions
1. **Service Quotas** (5-day lead time)
   - Navigate: AWS Console → Service Quotas → Amazon ECS
   - Check: Fargate On-Demand vCPU (quota code L-1216C47A)
   - Action: Request increase to 64 vCPU if below 20
   - Status: ⏸️ Not started

2. **Collect Account ID**
   - Run: `aws sts get-caller-identity --query Account --output text`
   - Store: `AWS_ACCOUNT_ID=____________`

## Required Reading (Est. 20 min)
- **examples/alex/guides/1_permissions.md** (IAM setup) – 10 min
- **AWS Service Quotas Docs** – 10 min

## Setup Sequence
1. ⏸️ **Week -1:** Submit quota requests → Wait 5 days
2. ⏸️ **Day 0:** Review guides (20 min)
3. ✅ **Day 1:** Ready for `/prp 0.1`

## Blocking Items
❌ Fargate vCPU quota approval pending (cannot provision tasks without approval)

---
**When all steps complete, execute:** `/prp 0.1`
```

**For complete agent specification:** See `.claude/agents/task-analyzer.md`

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
- **Research hierarchy:**
  1. ✅ Check examples/ directory for proven working implementations FIRST
  2. ✅ If example exists, match its architecture exactly (Pages Router, versions, etc.)
  3. ✅ Only deviate if task explicitly requires different approach
  4. ✅ Check context7, official docs for specific implementation details
- **Incremental validation:** Test after each change
- **Error prevention:** Address known issues proactively
- **No assumptions:** Verify paths, dependencies, configurations

### Architecture Decision Protocol

When implementing frontend/infrastructure tasks:
1. **Check reference:** Does examples/alex/ have similar functionality?
2. **Match pattern:** If yes, replicate architecture exactly:
   - Use same Next.js router (Pages vs App)
   - Use same package versions (especially auth libraries)
   - Follow same file structure and patterns
3. **Document deviation:** If task requires different approach, explicitly document why
4. **Validation:** Compare final implementation to reference for consistency

**Example reference:**
- Frontend with Clerk auth → Use examples/alex/frontend/ as template (Pages Router + Clerk v6)

---

## ⚡ Quick References

**Task Status:** `pending`, `in-progress`, `done`, `blocked`, `deferred`, `cancelled`
**Task Format:** Main (1, 2, 3), Subtasks (1.1, 1.2, 2.1)
**Priority:** `high`, `medium`, `low`

**Working Directory:** `C:\Users\anteb\Desktop\Courses\Projects\thesis_project`
**Git Branch:** `backend` (main branch: `main`)

---

**Remember:** This project requires regulatory compliance and pharmaceutical validation standards. Always prioritize compliance over speed. **NEVER IMPLEMENT FALLBACKS - FAIL EXPLICITLY WITH FULL DIAGNOSTIC INFORMATION.**
