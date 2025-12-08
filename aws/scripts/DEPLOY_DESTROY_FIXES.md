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
                       d861au413p5o2.cloudfront.net
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
curl https://d861au413p5o2.cloudfront.net
```

Expected outcome:
- New ALBs created with new DNS names
- CloudFront auto-updates to point to new ALBs
- UI accessible via https://d861au413p5o2.cloudfront.net
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

## Issues Fixed (2025-12-08)

### Issue 8: Worker Task Role Missing IAM Policies (S3 403 Forbidden) ✅ FIXED

**Date Fixed:** 2025-12-08

**Problem:**
Worker service fails to start with error:
```
RuntimeError: S3 download failed (403): An error occurred (403) when calling the HeadObject operation: Forbidden.
Check bucket permissions and verify s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz exists.
```

**Root Cause:**
The Worker task role `pharma-test-gen-worker-task-role` was created by Terraform but had **NO IAM policies attached**. The role existed but had zero permissions.

**Diagnosis:**
```bash
# Check attached policies (returns empty)
aws iam list-attached-role-policies --role-name pharma-test-gen-worker-task-role
# {"AttachedPolicies": []}

# Check inline policies (returns empty)
aws iam list-role-policies --role-name pharma-test-gen-worker-task-role
# {"PolicyNames": []}
```

**Solution Implemented:**
Created and attached `WorkerAccessPolicy` inline policy with permissions for:
- **S3**: GetObject, PutObject, DeleteObject, ListBucket, HeadObject on vectors and output buckets
- **SQS**: ReceiveMessage, DeleteMessage, GetQueueAttributes, ChangeMessageVisibility
- **CloudWatch Logs**: CreateLogStream, PutLogEvents
- **Bedrock**: InvokeModel, InvokeModelWithResponseStream

**Fix Command:**
```bash
# Create policy JSON
cat << 'EOF' > /tmp/worker-s3-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3Access",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:HeadObject"
            ],
            "Resource": [
                "arn:aws:s3:::pharma-test-gen-vectors-staging",
                "arn:aws:s3:::pharma-test-gen-vectors-staging/*",
                "arn:aws:s3:::pharma-test-gen-output-staging",
                "arn:aws:s3:::pharma-test-gen-output-staging/*"
            ]
        },
        {
            "Sid": "SQSAccess",
            "Effect": "Allow",
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ChangeMessageVisibility"
            ],
            "Resource": "arn:aws:sqs:eu-west-2:275333454012:pharma-test-gen-worker-jobs"
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:eu-west-2:275333454012:log-group:/ecs/pharma-test-gen/worker:*"
        },
        {
            "Sid": "BedrockAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Attach policy to role
aws iam put-role-policy \
  --role-name pharma-test-gen-worker-task-role \
  --policy-name WorkerAccessPolicy \
  --policy-document file:///tmp/worker-s3-policy.json \
  --region eu-west-2

# Force new deployment
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker --force-new-deployment --region eu-west-2
```

**Future Fix:** Add IAM policy to Terraform `aws/terraform/modules/ecs-service/` for worker role.

---

### Issue 9: ChromaDB Vector Database Missing from S3 ✅ FIXED

**Date Fixed:** 2025-12-08

**Problem:**
Worker fails even after IAM fix because the ChromaDB file doesn't exist in S3:
```
S3 download failed (403): ... verify s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz exists.
```

**Root Cause:**
The S3 bucket `pharma-test-gen-vectors-staging` was created by Terraform but never populated with the ChromaDB vector database. The local `lib/chroma_db/` directory contains the vectors but was never uploaded.

**Solution Implemented:**
Package and upload local ChromaDB to S3:

```bash
# Package ChromaDB (from project root)
cd lib
tar -czvf chroma_db.tar.gz chroma_db/

# Upload to S3
aws s3 cp chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz --region eu-west-2

# Verify upload
aws s3 ls s3://pharma-test-gen-vectors-staging/ --region eu-west-2
# 2025-12-08 10:19:00   21692416 chroma_db.tar.gz

# Force worker redeployment
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-worker --force-new-deployment --region eu-west-2
```

**Worker logs after fix:**
```
INFO: Downloading ChromaDB from s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz
INFO: Downloaded 20.65 MB
INFO: ChromaDB extracted to /app/chroma_db
INFO: Worker heartbeat #1: Ready to process jobs via SQS
```

**Future Fix:** Add ChromaDB upload step to `deploy.py` script.

---

### Issue 10: Worker Missing LangFuse Credentials ⚠️ KNOWN LIMITATION

**Status:** Non-critical warning (traces are local only)

**Problem:**
Worker logs show:
```
ERROR: LangFuse credentials missing. Required environment variables:
  - LANGFUSE_PUBLIC_KEY (current: MISSING)
  - LANGFUSE_SECRET_KEY (current: MISSING)
```

**Impact:** Worker operates normally but traces are not sent to LangFuse Cloud. Only affects observability, not functionality.

**Fix (Optional):**
Add LangFuse secrets to Worker task definition similar to API task definition.

---

### Issue 11: ECS Circuit Breaker Rollback Confusion ✅ DOCUMENTED

**Date Documented:** 2025-12-08

**Problem:**
When debugging deployment issues, the ECS circuit breaker automatically rolls back deployments that appear to fail health checks. This can be confusing because:
1. New task definition registered successfully
2. New task starts and appears healthy in logs
3. Circuit breaker rolls back to old revision
4. Developer sees old revision still running, unclear why

**Symptoms:**
- New task definition registered (e.g., revision 33)
- Service update initiated
- CloudWatch shows new container starting
- Service still running old revision (e.g., revision 32)
- Deployment shows `rolloutState: COMPLETED` but with wrong revision

**Root Cause:**
ECS deployment circuit breaker (enabled by default since 2022) monitors new tasks during deployment. If new tasks fail health checks or crash before stabilizing, the circuit breaker:
1. Stops the deployment
2. Rolls back to the last stable deployment
3. Marks the deployment as COMPLETED (rollback completed, not your update)

**Key Insight:** A `rolloutState: COMPLETED` does NOT mean your update succeeded - it might mean the rollback completed.

**Diagnosis:**
```bash
# Check full service events timeline (shows circuit breaker actions)
aws ecs describe-services --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query "services[0].events[:10]" --region eu-west-2

# Look for events like:
# "service pharma-test-gen-api was unable to place a task"
# "service pharma-test-gen-api has reached a steady state"
# "circuit breaker rolled back deployment"

# Check which revision is ACTUALLY running
aws ecs describe-services --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query "services[0].taskDefinition" --region eu-west-2

# Check what's in each revision
aws ecs describe-task-definition --task-definition pharma-test-gen-api:32 \
  --query "taskDefinition.containerDefinitions[0].secrets[*].name" --region eu-west-2
```

**Fix:**
Explicitly specify the correct task definition revision:
```bash
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api:33 \
  --force-new-deployment --region eu-west-2
```

**Prevention:**
1. Always specify task definition revision explicitly: `--task-definition family:REVISION`
2. Before updating, verify latest revision has correct config: `aws ecs describe-task-definition --task-definition family --query "taskDefinition.revision"`
3. After update, verify service picked up correct revision
4. If rollback occurred, check CloudWatch logs for why new tasks failed

**Related:** See `main/docs/issues/ISSUE-006-api-task-definition-revision.md` for detailed example.

---

## Post-Redeploy Checklist

After running `destroy.py` + `deploy.py`:

- [ ] Wait for Terraform to complete
- [ ] Register API task definition v15 (has all secrets)
- [ ] Update API service with new task definition **specifying revision explicitly**
- [ ] **Verify correct revision is running**: `aws ecs describe-services --cluster pharma-test-gen-cluster --services pharma-test-gen-api --query "services[0].taskDefinition"`
- [ ] Wait for API to be healthy
- [ ] Rebuild frontend with `NEXT_PUBLIC_API_BASE_URL=` (empty)
- [ ] Register frontend task definition v13
- [ ] Update frontend service
- [ ] **Upload ChromaDB to S3** (if not present): `aws s3 cp lib/chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/`
- [ ] **Attach Worker IAM policy** (if missing): See Issue 8 fix commands
- [ ] Force Worker redeployment: `aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-worker --force-new-deployment`
- [ ] Verify all services running: `aws ecs describe-services --cluster pharma-test-gen-cluster --services pharma-test-gen-api pharma-test-gen-frontend pharma-test-gen-worker --query 'services[*].{name:serviceName,running:runningCount,desired:desiredCount}'`
- [ ] Invalidate CloudFront cache: `aws cloudfront create-invalidation --distribution-id E3CO1HBNMIUKPB --paths '/*'`
- [ ] Test: https://d861au413p5o2.cloudfront.net/generate/
