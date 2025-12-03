# Deploy/Destroy Script Issues & Fixes

## Solutions Implemented (2025-12-03)

### Solution 1: CloudFront Managed by Terraform

**Problem:** CloudFront was created manually outside Terraform. When ALBs were recreated after destroy, CloudFront pointed to old ALB DNS names.

**Solution:** Added CloudFront module to Terraform (`aws/terraform/modules/cloudfront/`):
- CloudFront distribution auto-updates when ALB DNS names change
- Imported existing distribution: `E3CO1HBNMIUKPB`
- Path-based routing: `/jobs*`, `/api/*`, `/health*` → API ALB, default → Frontend ALB

**Files Created:**
- `aws/terraform/modules/cloudfront/main.tf`
- `aws/terraform/modules/cloudfront/variables.tf`
- `aws/terraform/modules/cloudfront/outputs.tf`

### Solution 2: ECR Repositories Protected with Lifecycle Rules

**Problem:** ECR repos deleted/recreated during destroy/deploy cycle caused "already exists" errors.

**Solution:**
1. Added `prevent_destroy = true` lifecycle rule to ECR repos
2. `destroy.py` removes ECR from Terraform state before destroy (repos kept in AWS)
3. `deploy.py` imports ECR repos back into state if they exist but aren't tracked

**Files Modified:**
- `aws/terraform/modules/ecr/main.tf` - Added lifecycle rule
- `aws/scripts/destroy.py` - Removes ECR from state before destroy
- `aws/scripts/deploy.py` - Imports existing ECR repos

### Solution 3: ALB Create-Before-Destroy Lifecycle

**Problem:** ALBs deleted before new ones created caused brief downtime.

**Solution:** Added `create_before_destroy = true` to ALB resource for zero-downtime updates.

**Files Modified:**
- `aws/terraform/modules/alb/main.tf` - Added lifecycle rule

### Solution 4: Lock File Preserved

**Problem:** `.terraform.lock.hcl` deleted during destroy caused "inconsistent lock file" errors.

**Solution:** `destroy.py` no longer deletes `.terraform.lock.hcl` - only deletes `tfplan`.

---

## Original Issues (Fixed)

### Issue 1: Missing `terraform init` in deploy.py
**Status:** FIXED - deploy.py now checks for initialization and runs `terraform init` if needed.

### Issue 2: ECR Repositories Not in Terraform State After Destroy
**Status:** FIXED - deploy.py imports existing ECR repos, destroy.py removes from state cleanly.

### Issue 3: CloudFront Pointing to Old ALBs
**Status:** FIXED - CloudFront now managed by Terraform, auto-updates with ALB changes.

---

## Quick Reference Commands

### When deploy fails with "lock file inconsistent":
```bash
cd aws/terraform
terraform init
terraform apply -var-file=environments/staging.tfvars -auto-approve
```

### When deploy fails with "ECR already exists":
```bash
cd aws/terraform
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["api"]' pharma-test-gen-api
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["worker"]' pharma-test-gen-worker
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["frontend"]' pharma-test-gen-frontend
terraform apply -var-file=environments/staging.tfvars -auto-approve
```

### When deploy fails with "state lock":
```bash
cd aws/terraform
terraform force-unlock -force <LOCK_ID_FROM_ERROR>
```

### Import existing CloudFront distribution:
```bash
cd aws/terraform
terraform import -var-file=environments/staging.tfvars \
  module.cloudfront.aws_cloudfront_distribution.this E3CO1HBNMIUKPB
```

### Rollback CloudFront to manual management (if needed):
```bash
cd aws/terraform
terraform state rm module.cloudfront.aws_cloudfront_distribution.this
# CloudFront continues working - just not managed by Terraform
```

---

## Architecture Overview

```
                         CloudFront (HTTPS)
                       d2yiysdqio0ryi.cloudfront.net
                              |
              +---------------+---------------+
              |                               |
    /jobs*, /api/*, /health*             Default (/*)
              |                               |
        API ALB (HTTP:80)           Frontend ALB (HTTP:80)
              |                               |
        ECS API Service            ECS Frontend Service
```

**Key Points:**
- CloudFront provides HTTPS termination
- ALBs run HTTP-only (CloudFront → ALB is HTTP)
- Terraform manages all components
- Destroy/deploy cycle works cleanly

---

## Prevention Strategy (Implemented)

1. **CloudFront in Terraform** - Auto-updates with ALB changes
2. **ECR prevent_destroy** - Images preserved across deployments
3. **ALB create_before_destroy** - Zero-downtime ALB updates
4. **Preserve .terraform.lock.hcl** - Consistent provider versions
5. **Import existing resources** - deploy.py handles ECR repo imports

---

## Testing the Solution

To verify the destroy/deploy cycle works:

```bash
# 1. Destroy infrastructure
python aws/scripts/destroy.py --yes --skip-ecr

# 2. Wait for destruction to complete

# 3. Redeploy
python aws/scripts/deploy.py

# 4. Verify CloudFront URL works
curl https://d2yiysdqio0ryi.cloudfront.net
```

Expected outcome:
- New ALBs created with new DNS names
- CloudFront auto-updates to point to new ALBs
- UI accessible via https://d2yiysdqio0ryi.cloudfront.net
- No manual intervention required

---

## Issues Fixed (2025-12-03)

### Issue 5: Mixed Content Error (HTTPS/HTTP) ✅ FIXED

**Date Fixed:** 2025-12-03

**Problem:**
Frontend served via CloudFront (HTTPS) made API calls directly to ALB (HTTP), causing browser Mixed Content errors.

**Root Causes (Two bugs):**

1. **JavaScript bug:** Used `||` instead of `??` for fallback
   ```typescript
   // BUG: Empty string "" is falsy, falls back to localhost
   process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'

   // FIX: Nullish coalescing only falls back for null/undefined
   process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8080'
   ```

2. **Terraform task definition:** Had `NEXT_PUBLIC_API_BASE_URL` as runtime env var pointing to HTTP ALB, overriding build-time value.

**Solution Implemented:**
1. Changed `||` to `??` in 4 frontend files
2. Updated `deploy.py` to use empty string for `NEXT_PUBLIC_API_BASE_URL`
3. Removed `NEXT_PUBLIC_API_BASE_URL` from frontend task definition (v13)

**Files Modified:**
- `main/frontend/lib/authenticatedFetch.ts`
- `main/frontend/hooks/useJobStatusPolling.ts`
- `main/frontend/pages/history.tsx`
- `main/frontend/components/ApprovalModal.tsx`
- `aws/scripts/deploy.py`
- `aws/terraform/task-definition-frontend-v13.json`

---

### Issue 6: QEMU Emulation Crash (ARM64 → AMD64) ⚠️ KNOWN LIMITATION

**Status:** Intermittent issue on ARM64 hosts

**Problem:**
Building `linux/amd64` Docker images on ARM64 host (Snapdragon X Elite) with QEMU emulation can crash.

**Workarounds:**
1. **Retry after crash:** `wsl --shutdown` then retry
2. **Use AWS CodeBuild** for production (native AMD64)
3. Build often succeeds on second attempt

**WSL Recovery:**
```powershell
wsl --shutdown
# Wait a few seconds
wsl
# Retry the build
```

---

### Issue 7: API Task Definition Missing Secrets After Redeploy ✅ FIXED

**Date Fixed:** 2025-12-03

**Problem:**
After `destroy.py` + `deploy.py`, the API couldn't authenticate users:
```
CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)
```

**Root Cause:**
Terraform recreates task definitions from scratch, but **Terraform doesn't include the manually-added secrets** (Clerk, OpenRouter, LangFuse). Only `DATABASE_URL` was in Terraform.

**Solution Implemented:**
Created `task-definition-api-v15.json` with ALL required secrets:
- `DATABASE_URL` (plain string secret)
- `CLERK_PEM_PUBLIC_KEY` (JSON key from clerk secret)
- `CLERK_ISSUER` (JSON key from clerk secret)
- `OPENROUTER_API_KEY` (JSON key from openrouter secret)
- `OPENAI_API_KEY` (JSON key from openrouter secret)
- `LANGFUSE_PUBLIC_KEY` (JSON key from langfuse secret)
- `LANGFUSE_SECRET_KEY` (JSON key from langfuse secret)

**CRITICAL: After every destroy/deploy, manually register the API task definition:**
```bash
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-api-v15.json \
  --region eu-west-2

aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api \
  --force-new-deployment --region eu-west-2
```

**Future Fix:** Add all secrets to Terraform `aws/terraform/modules/ecs-service/`.

---

## Golden Task Definitions (Use After Redeploy)

After `destroy.py` + `deploy.py`, register these task definitions:

### API Task Definition
```bash
# Register API with all secrets
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-api-v15.json \
  --region eu-west-2

# Update service
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api --task-definition pharma-test-gen-api \
  --force-new-deployment --region eu-west-2
```

**File:** `aws/terraform/task-definition-api-v15.json`
- Image: `staging-latest`
- All secrets: Clerk, OpenRouter, LangFuse, Database

### Frontend Task Definition
```bash
# Register frontend without API URL env var
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-frontend-v13.json \
  --region eu-west-2

# Update service
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-frontend --task-definition pharma-test-gen-frontend \
  --force-new-deployment --region eu-west-2
```

**File:** `aws/terraform/task-definition-frontend-v13.json`
- Image: `staging-nullish-fix`
- NO `NEXT_PUBLIC_API_BASE_URL` env var (uses build-time empty string)

---

## Post-Redeploy Checklist

After running `destroy.py` + `deploy.py`:

- [ ] Wait for Terraform to complete
- [ ] Register API task definition v15 (has all secrets)
- [ ] Update API service with new task definition
- [ ] Wait for API to be healthy
- [ ] Rebuild frontend with `NEXT_PUBLIC_API_BASE_URL=` (empty)
- [ ] Register frontend task definition v13
- [ ] Update frontend service
- [ ] Invalidate CloudFront cache: `aws cloudfront create-invalidation --distribution-id E3CO1HBNMIUKPB --paths '/*'`
- [ ] Test: https://d2yiysdqio0ryi.cloudfront.net/generate/
