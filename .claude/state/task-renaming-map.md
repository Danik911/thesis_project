# PRP Task Renaming Map

## Status: ✅ COMPLETED

All tasks have been renamed to ID format (0.1-5.3). Standalone tasks deleted as duplicates.

---

## Phase-Based Tasks (Active - 23 tasks)

### Phase 0: Foundations & Readiness (4 tasks)
- `task_phase0_01_service_quotas.md` → `0.1-service-quotas.md`
- `task_phase0_02_compliance_baseline.md` → `0.2-compliance-baseline.md`
- `task_phase0_03_terraform_backend.md` → `0.3-terraform-backend.md`
- `task_phase0_04_iam_roles.md` → `0.4-iam-roles.md`

### Phase 1: Backend Abstraction & Local MVP (4 tasks)
- `task_phase1_01_storage_adapter.md` → `1.1-storage-adapter.md`
- `task_phase1_02_vector_store_provider.md` → `1.2-vector-store-provider.md`
- `task_phase1_03_async_job_submission.md` → `1.3-async-job-submission.md`
- `task_phase1_04_clerk_auth.md` → `1.4-clerk-auth.md`

### Phase 2: Frontend Dashboard (4 tasks)
- `task_phase2_01_nextjs_setup.md` → `2.1-nextjs-setup.md`
- `task_phase2_02_clerk_provider.md` → `2.2-clerk-provider.md`
- `task_phase2_03_langfuse_dashboard.md` → `2.3-langfuse-dashboard.md`
- `task_phase2_04_frontend_accessibility.md` → `2.4-frontend-accessibility.md`

### Phase 3: Containerization & Local Orchestration (4 tasks)
- `task_phase3_01_docker_multistage.md` → `3.1-docker-multistage.md`
- `task_phase3_02_local_compose.md` → `3.2-local-compose.md`
- `task_phase3_03_local_rag_testing.md` → `3.3-local-rag-testing.md`
- `task_phase3_04_devops_readiness.md` → `3.4-devops-readiness.md`

### Phase 4: AWS Deployment & RAG Migration (4 tasks)
- `task_phase4_01_terraform_ecs_deploy.md` → `4.1-terraform-ecs-deploy.md`
- `task_phase4_02_aurora_data_api_cutover.md` → `4.2-aurora-data-api-cutover.md`
- `task_phase4_03_bedrock_deepseek_integration.md` → `4.3-bedrock-deepseek-integration.md`
- `task_phase4_04_traffic_cutover_plan.md` → `4.4-traffic-cutover-plan.md`

### Phase 5: Hardening & Backlog Grooming (3 tasks)
- `task_phase5_01_security_hardening.md` → `5.1-security-hardening.md`
- `task_phase5_02_performance_regression.md` → `5.2-performance-regression.md`
- `task_phase5_03_compliance_closeout.md` → `5.3-compliance-closeout.md`

---

## Summary

- **Total Tasks:** 23 files (0.1-5.3)
- **Deleted:** 6 standalone tasks (duplicates of phase-based tasks)
- **Format:** All tasks use ID format: `{phase}.{task}-{description}.md`

---

## Deleted Tasks (Duplicates)

The following standalone tasks were deleted as they fully duplicate the phase-based tasks:
- `task1_infrastructure_baseline.md` → Covered by 0.3, 0.4, 4.1
- `task2_container_ci_cd.md` → Covered by 3.1, 3.2
- `task3_aurora_data_api_migration.md` → Covered by 4.2
- `task4_s3_vectorstore_migration.md` → Covered by 1.2, 4.2, 4.3
- `task5_ecs_queue_orchestration.md` → Covered by 1.3, 4.1
- `task6_observability_compliance.md` → Covered by 2.3, 3.4
