# ISSUE-005: Rebuild Uses Wrong Image Tag + Task Role Missing IAM Policies

## Date
2025-12-08

## Symptoms

1. **Old UI still showing** after `--rebuild` deployment
2. **GET /jobs returns 500** with error "CLERK_PEM_PUBLIC_KEY not configured"
3. **New API tasks failing** with S3 403 Forbidden errors

---

## Root Causes Identified

### Issue 5a: Task Definition Has Hardcoded Old Image Tag

**Problem:** Task definition JSON had hardcoded old image tag (`trace-fix-v3-20251207`) but `--rebuild` pushes to `staging-latest`.

**File:** `aws/terraform/task-definition-frontend-v15.json`

```json
// BUG: Hardcoded old tag
"image": "275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend:trace-fix-v3-20251207"

// FIX: Use staging-latest to match --rebuild behavior
"image": "275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend:staging-latest"
```

**Why This Happens:**
1. Developer makes code changes
2. Runs `redeploy.py --rebuild` which builds and pushes to `staging-latest`
3. Script registers task definition from JSON file
4. JSON file still references old tag (e.g., `trace-fix-v3-20251207`)
5. ECS pulls OLD image, not the newly built one
6. Code changes never appear

---

### Issue 5b: ALB Health Check Missing Trailing Slash

**Problem:** Next.js `trailingSlash: true` causes 308 redirects. ALB health check on `/api/health` fails with HTTP 308.

**Fix:**
```bash
aws elbv2 modify-target-group \
  --target-group-arn <frontend-target-group-arn> \
  --health-check-path "/api/health/" \
  --region eu-west-2
```

Also update container health check in task definition:
```json
"healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:3000/api/health/ || exit 1"]
}
```

---

### Issue 5d: Service Running Wrong Task Definition Revision

**Problem:** After registering a new task definition with all required secrets, the ECS service continued running an old revision that was missing critical secrets.

**Symptoms:**
- API returns 500 with `"CLERK_PEM_PUBLIC_KEY not configured"`
- New task definition was registered (revision 33) but service uses old revision (32)
- Health checks pass but authentication fails

**Root Cause:**
1. New task definition registered (creates revision 33 with all secrets)
2. Service update command doesn't specify revision explicitly
3. Service continues using previous revision (32)
4. Circuit breaker may roll back new tasks if they fail for any reason

**Diagnosis:**
```bash
# Check which revision is running
aws ecs describe-services --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api \
  --query "services[0].taskDefinition" --region eu-west-2

# Compare secrets between revisions
aws ecs describe-task-definition --task-definition pharma-test-gen-api:32 \
  --query "taskDefinition.containerDefinitions[0].secrets[*].name" --region eu-west-2
# Output: ["DATABASE_URL"]  ← Missing other secrets!

aws ecs describe-task-definition --task-definition pharma-test-gen-api:33 \
  --query "taskDefinition.containerDefinitions[0].secrets[*].name" --region eu-west-2
# Output: ["DATABASE_URL", "CLERK_PEM_PUBLIC_KEY", "CLERK_ISSUER", ...]
```

**Fix:**
```bash
aws ecs update-service --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --task-definition pharma-test-gen-api:33 \
  --force-new-deployment --region eu-west-2
```

**See Also:** [ISSUE-006](ISSUE-006-api-task-definition-revision.md) for detailed documentation of this issue.

---

### Issue 5c: API Task Role Missing IAM Policies

**Problem:** API task role `pharma-test-gen-api-task-role` had NO IAM policies attached. Tasks couldn't access:
- S3 ChromaDB bucket (403 Forbidden)
- SQS queue
- CloudWatch Logs

**Diagnosis:**
```bash
aws iam list-attached-role-policies --role-name pharma-test-gen-api-task-role
# {"AttachedPolicies": []}

aws iam list-role-policies --role-name pharma-test-gen-api-task-role
# {"PolicyNames": []}
```

**Fix:**
```bash
cat > /tmp/api-access-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3Access",
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:HeadObject"],
            "Resource": [
                "arn:aws:s3:::pharma-test-gen-chromadb-275333454012",
                "arn:aws:s3:::pharma-test-gen-chromadb-275333454012/*",
                "arn:aws:s3:::pharma-test-gen-output-staging",
                "arn:aws:s3:::pharma-test-gen-output-staging/*"
            ]
        },
        {
            "Sid": "SQSAccess",
            "Effect": "Allow",
            "Action": ["sqs:SendMessage", "sqs:GetQueueAttributes"],
            "Resource": "arn:aws:sqs:eu-west-2:275333454012:pharma-test-gen-worker-jobs"
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": "arn:aws:logs:eu-west-2:275333454012:log-group:/ecs/pharma-test-gen/api:*"
        }
    ]
}
EOF

aws iam put-role-policy \
  --role-name pharma-test-gen-api-task-role \
  --policy-name APIAccessPolicy \
  --policy-document file:///tmp/api-access-policy.json
```

---

## Files Modified

| File | Change |
|------|--------|
| `aws/terraform/task-definition-frontend-v15.json` | Image tag `trace-fix-v3-20251207` -> `staging-latest` |
| `aws/terraform/task-definition-frontend-v15.json` | Health check path `/api/health` -> `/api/health/` |
| ALB Target Group (AWS Console/CLI) | Health check path -> `/api/health/` |
| IAM Role (AWS Console/CLI) | Added APIAccessPolicy inline policy |

---

## Prevention

1. **Always use `staging-latest` tag** in task definition JSON files for staging environments
2. **Check task role policies** after `destroy.py` + `deploy.py` cycles
3. **Match health check paths** to Next.js `trailingSlash` config
4. **Add IAM policies to Terraform** so they're not lost on redeploy

---

## Related Issues

- ISSUE-004: redeploy.py doesn't rebuild images (same pattern - task def references old tag)
- ISSUE-006: API Service Running Wrong Task Definition Revision (detailed guide for revision mismatch)
- ISSUE-008: Worker task role missing IAM policies (same pattern - role created but empty)

---

## Quick Fix Commands

```bash
# 1. Fix frontend task definition image tag (edit JSON then)
aws ecs register-task-definition --cli-input-json file://aws/terraform/task-definition-frontend-v15.json --region eu-west-2

# 2. Fix ALB health check path
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:eu-west-2:275333454012:targetgroup/pharma-test-gen-frontend-alb-tg/5e735cd4ea874736 \
  --health-check-path "/api/health/" \
  --region eu-west-2

# 3. Add API task role policy
aws iam put-role-policy --role-name pharma-test-gen-api-task-role --policy-name APIAccessPolicy --policy-document file:///tmp/api-access-policy.json

# 4. Force redeploy
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-frontend --force-new-deployment --region eu-west-2
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-api --force-new-deployment --region eu-west-2
```
