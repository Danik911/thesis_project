# Issue Catalog

Quick reference for all documented issues in the pharmaceutical test generation project.

**Last Updated:** 2026-02-27 (ISSUE-041 resolved: MES Agentic BI RBAC hardening and client handover artifacts)
**Maintained By:** doc-updater agent

---

## How to Use This Catalog

1. **Search First**: Before creating a new issue, search this catalog for existing solutions
2. **Follow Naming**: Issues use format `ISSUE-###-short-description.md`
3. **Update Status**: When resolving an issue, update its status here AND in the issue file
4. **Next Issue Number**: ISSUE-042

---

## Active Issues (OPEN)

| ID | Title | Date Created | Category | Priority |
|----|-------|--------------|----------|----------|
| [ISSUE-040](ISSUE-040-l18-extraction-quality-gate-and-merge-admission-control.md) | L18 Extraction Quality Gate and Merge Admission Control (merge admission control part implemented via template-locked mode; pending E2E validation) | 2026-02-23 | API/Data Quality | High |
| [ISSUE-034](ISSUE-034-l13-standards-seeding-latency.md) | L13 Standards RAG Seeding Latency on First Ingestion | 2026-02-19 | Database | Medium |
| [ISSUE-033](ISSUE-033-windows-uv-invalid-project-venv.md) | Windows `uv run` Fails Due to Invalid Project `.venv` | 2026-02-19 | Testing | Medium |
| [ISSUE-026](ISSUE-026-full-suite-collection-systemexit.md) | Full `main/tests` Collection Fails from Archived Test `sys.exit(1)` | 2026-02-17 | Testing | Medium |

---

## Resolved Issues (CLOSED)

| ID | Title | Date Created | Date Resolved | Category |
|----|-------|--------------|---------------|----------|
| [ISSUE-041](ISSUE-041-mes-bi-rbac-hardening-and-client-handover-gaps.md) | MES Agentic BI RBAC Hardening and Client Handover Gaps | 2026-02-27 | 2026-02-27 | Auth/API/Documentation |
| [ISSUE-039](ISSUE-039-lims-xlsx-export-null-and-truncated-analysis-refs.md) | LIMS XLSX Export Fails — Null and Truncated Analysis References | 2026-02-21 | 2026-02-21 | API/Data Quality |
| [ISSUE-038](ISSUE-038-lims-chat-missing-grounded-context-and-provenance.md) | LIMS Chat Missing Grounded Context and Provenance Attribution | 2026-02-21 | 2026-02-21 | API/Workflow |
| [ISSUE-037](ISSUE-037-l15-frontend-delivery-and-local-e2e-consolidated.md) | L15 Frontend Delivery + Local E2E Validation (Consolidated) | 2026-02-20 | 2026-02-20 | Frontend/API/Config |
| [ISSUE-032](ISSUE-032-l7-extraction-quality-consolidated.md) | L7 Extraction Quality — Consolidated Resolution Record | 2026-02-18 | 2026-02-18 | API/Data Quality |
| [ISSUE-027](ISSUE-027-lims-openpyxl-missing-in-dev-container.md) | LIMS Extraction Warning in Docker Dev - `ModuleNotFoundError: No module named 'openpyxl'` | 2026-02-17 | 2026-02-17 | Docker/API |
| [ISSUE-025](ISSUE-025-lims-local-dev-connectivity-runbook.md) | LIMS Local Dev Connectivity & Runtime Runbook (Consolidated) | 2026-02-17 | 2026-02-17 | Frontend/API |
| [ISSUE-018](ISSUE-018-local-wsl-storage-path-uses-app-output.md) | Local WSL Startup Fails When Storage Path Uses `/app/output` | 2026-02-17 | 2026-02-17 | API |
| [ISSUE-017](ISSUE-017-wsl-numpy-openblas-import-failure.md) | WSL NumPy/OpenBLAS Import Failure Blocks Local API Startup | 2026-02-17 | 2026-02-17 | API |
| [ISSUE-016](ISSUE-016-lims-upload-dropzone-a11y-lint-failure.md) | LIMS Upload Dropzone Accessibility Lint Failure | 2026-02-17 | 2026-02-17 | Frontend |
| [ISSUE-015](ISSUE-015-lims-llamaextract-agent-name-collision.md) | LIMS LlamaExtract Agent Name Collision | 2026-02-17 | 2026-02-17 | API |
| [ISSUE-014](ISSUE-014-destroy-deploy-cycle-reliability.md) | Destroy/Deploy Cycle Reliability | 2025-12-19 | 2025-12-19 | Deployment |
| [ISSUE-013](ISSUE-013-route53-trailing-dot-mismatch.md) | Route53 Certificate Validation Import Failure | 2025-12-19 | 2025-12-19 | Deployment |
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

### Consolidated into ISSUE-032

The following detailed L7 records are preserved for audit traceability and merged under the consolidated closure entry above:

- [ISSUE-028](ISSUE-028-lims-extraction-missing-normalization-layer.md)
- [ISSUE-029](ISSUE-029-lims-llama-cloud-services-deprecation-migration-risk.md)
- [ISSUE-030](ISSUE-030-lims-sdk-pin-conflict-llama-cloud-version.md)
- [ISSUE-031](ISSUE-031-lims-llamaextract-semantic-enum-mismatch.md)

### Consolidated into ISSUE-037

The following detailed L15 records are preserved for audit traceability and merged under the consolidated closure entry above:

- [ISSUE-035](ISSUE-035-l15-frontend-blocked-by-l14-contract-gaps.md)
- [ISSUE-036](ISSUE-036-lims-duplicate-llamaextract-key-env-precedence.md)

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

- **Total Issues:** 33
- **Open:** 4
- **Resolved:** 29
- **Most Common Category:** Deployment (9 issues)

---

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Issue Management Protocol
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Common solutions
- [AWS_DEPLOYMENT.md](../AWS_DEPLOYMENT.md) - Deployment guide
