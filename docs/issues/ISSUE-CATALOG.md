# Issue Catalog

Quick reference for all documented issues in the pharmaceutical test generation project.

**Last Updated:** 2025-12-12
**Maintained By:** doc-updater agent

---

## How to Use This Catalog

1. **Search First**: Before creating a new issue, search this catalog for existing solutions
2. **Follow Naming**: Issues use format `ISSUE-###-short-description.md`
3. **Update Status**: When resolving an issue, update its status here AND in the issue file
4. **Next Issue Number**: ISSUE-013

---

## Active Issues (OPEN)

| ID | Title | Date Created | Category | Priority |
|----|-------|--------------|----------|----------|
| *No open issues* | | | | |

---

## Resolved Issues (CLOSED)

| ID | Title | Date Created | Date Resolved | Category |
|----|-------|--------------|---------------|----------|
| [ISSUE-012](ISSUE-012-documentation-aurora-inconsistency.md) | Documentation Aurora DB Inconsistency | 2025-12-12 | 2025-12-12 | Documentation |
| [ISSUE-011](ISSUE-011-chromadb-s3-bucket-mismatch.md) | ChromaDB S3 Bucket Mismatch | 2025-12-09 | 2025-12-09 | Deployment |
| [ISSUE-010](ISSUE-010-html-json-export-fails-aws.md) | HTML/JSON Export Fails in AWS | 2025-12-09 | 2025-12-09 | API |
| [ISSUE-009](ISSUE-009-deployment-failure-summary-20251209.md) | Deployment Failure Summary | 2025-12-09 | 2025-12-09 | Deployment |
| [ISSUE-008](ISSUE-008-docker-build-context-canceled.md) | Docker Build Context Canceled | 2025-12-08 | 2025-12-08 | Docker |
| [ISSUE-007](ISSUE-007-slow-arm-to-amd64-docker-builds.md) | Slow ARM to AMD64 Docker Builds | 2025-12-08 | 2025-12-08 | Docker |
| [ISSUE-006](ISSUE-006-api-task-definition-revision.md) | API Task Definition Revision | 2025-12-08 | 2025-12-08 | Deployment |
| [ISSUE-005](ISSUE-005-rebuild-uses-wrong-image-tag.md) | Rebuild Uses Wrong Image Tag | 2025-12-08 | 2025-12-08 | Deployment |
| [ISSUE-004](ISSUE-004-redeploy-doesnt-rebuild-images.md) | Redeploy Doesn't Rebuild Images | 2025-12-07 | 2025-12-07 | Deployment |
| [ISSUE-003](ISSUE-003-langfuse-trace-unknown.md) | LangFuse Trace Unknown | 2025-12-06 | 2025-12-06 | Observability |
| [ISSUE-002](ISSUE-002-403-auth-error.md) | 403 Auth Error | 2025-12-06 | 2025-12-06 | Auth |
| [ISSUE-001](ISSUE-001-cloudfront-404-errors.md) | CloudFront 404 Errors | 2025-12-06 | 2025-12-06 | Deployment |

---

## Legacy Issues (Non-Standard Names)

These issues were created before the standard naming convention:

| File | Topic | Status | Category |
|------|-------|--------|----------|
| [2025-12-03-chromadb-empty-collections.md](2025-12-03-chromadb-empty-collections.md) | ChromaDB Empty Collections | Resolved | Database |
| [2025-12-06-langfuse-trace-dashboard-403.md](2025-12-06-langfuse-trace-dashboard-403.md) | LangFuse Dashboard 403 | Resolved | Observability |
| [chromadb-debugger-agent-prompt.md](chromadb-debugger-agent-prompt.md) | ChromaDB Debugger Prompt | Reference | Database |

---

## Issue Categories

| Category | Description | Common Triggers |
|----------|-------------|-----------------|
| **API** | Backend API issues | Endpoint errors, auth failures, response issues |
| **Frontend** | Next.js/React issues | Rendering, routing, state management |
| **Deployment** | AWS/Docker deployment | ECS, task definitions, IAM, CloudFront |
| **Docker** | Container/build issues | Build failures, image problems, compose issues |
| **Auth** | Authentication | Clerk JWT, CORS, permissions |
| **Workflow** | Multi-agent workflow | Agent failures, workflow errors |
| **Database** | PostgreSQL/ChromaDB | Connection, query, vector store issues |
| **Documentation** | Doc inconsistencies | Outdated info, incorrect architecture claims |
| **Observability** | LangFuse/Tracing | Trace issues, dashboard problems |

---

## Statistics

- **Total Issues:** 15
- **Open:** 0
- **Resolved:** 15
- **Most Common Category:** Deployment (7 issues)

---

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Issue Management Protocol
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Common solutions
- [AWS_DEPLOYMENT.md](../AWS_DEPLOYMENT.md) - Deployment guide
