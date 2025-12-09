# Troubleshooting Guide

Common issues and solutions for the pharmaceutical test generation system.

---

## AWS Deployment Issues

### Missing Secrets After Redeploy

**Symptom:**
```
CRITICAL: Authentication system not configured (missing CLERK_PEM_PUBLIC_KEY)
```

**Cause:** Terraform doesn't preserve manually-added secrets.

**Solution:**
```bash
# Register golden task definitions with secrets
aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-api-v19.json \
  --region eu-west-2

aws ecs register-task-definition \
  --cli-input-json file://aws/terraform/task-definition-worker-v21.json \
  --region eu-west-2

# Force redeploy
python aws/scripts/redeploy.py
```

---

### ECR "Already Exists" Error

**Symptom:**
```
Error: creating ECR Repository: RepositoryAlreadyExistsException
```

**Cause:** ECR repos preserved during destroy, but removed from Terraform state.

**Solution:**
```bash
# Import blocks are in aws/terraform/imports.tf
# Run terraform apply - it will import existing repos
cd aws/terraform && terraform apply
```

---

### CloudFront 502/504 Errors

**Symptom:** Site shows "502 Bad Gateway" after deployment.

**Causes:**
1. ALB targets unhealthy
2. ECS tasks not running
3. Health check timeout

**Solution:**
```bash
# Check ECS task status
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-frontend \
  --query 'services[*].[serviceName,runningCount,desiredCount]'

# Check task logs
aws logs tail /ecs/pharma-test-gen/api --since 5m --region eu-west-2

# Force new deployment
aws ecs update-service \
  --cluster pharma-test-gen-cluster \
  --service pharma-test-gen-api \
  --force-new-deployment
```

---

### OIDC Authentication Fails

**Symptom:**
```
Error: Could not assume role with OIDC
```

**Causes:**
1. Trust policy doesn't match repo/branch
2. OIDC provider missing
3. Role lacks permissions

**Solution:**
```bash
# Verify trust policy
aws iam get-role --role-name pharma-test-gen-github-actions \
  --query 'Role.AssumeRolePolicyDocument'

# Check OIDC provider
aws iam list-open-id-connect-providers
```

---

## Docker Issues

### Container Won't Start

**Symptom:** Container status "Restarting" or "Exited".

**Diagnosis:**
```bash
docker-compose -f docker-compose.dev.yml logs api
```

**Common causes:**

1. **Missing env var:**
   ```bash
   grep OPENAI_API_KEY .env.local
   ```

2. **Port conflict:**
   ```bash
   netstat -ano | findstr :8080  # Windows
   lsof -i :8080                 # Linux/Mac
   ```

3. **Database not ready:**
   ```bash
   docker-compose -f docker-compose.dev.yml restart postgres
   ```

---

### Worker Not Processing Jobs

**Symptom:** Job stuck at "pending" status.

**Diagnosis:**
```bash
docker-compose -f docker-compose.dev.yml logs worker
```

**Solutions:**

1. **Restart worker:**
   ```bash
   docker-compose -f docker-compose.dev.yml restart worker
   ```

2. **Recreate SQS queue:**
   ```bash
   docker-compose -f docker-compose.dev.yml restart localstack worker
   ```

3. **Verify LangFuse keys:**
   ```bash
   docker exec -it pharma-worker-dev python -c "
   from langfuse import Langfuse
   import os
   client = Langfuse()
   print('OK' if client else 'FAILED')
   "
   ```

---

### ChromaDB Empty Collections

**Symptom:**
```
CRITICAL: Context Provider cannot execute - ALL ChromaDB collections are empty
```

**Diagnosis:**
```bash
docker exec -it pharma-api-dev python -c "
import chromadb
client = chromadb.PersistentClient(path='/app/chroma_db')
for c in client.list_collections():
    print(f'{c.name}: {c.count()} docs')
"
```

**Solution:**
```bash
# Re-seed ChromaDB
docker exec -it pharma-api-dev python scripts/seed_chroma.py

# For AWS: Re-upload tarball
python aws/scripts/1_upload_chroma_to_s3.py
```

---

### Volume Permission Errors

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/app/output/job_123'
```

**Solution:** Use named volumes instead of bind mounts:
```yaml
# docker-compose.dev.yml
volumes:
  - output-data:/app/output  # Correct
  # NOT ./output:/app/output  # Wrong
```

---

## Build Issues

### QEMU Emulation Crash (ARM64)

**Symptom:**
```
qemu-x86_64: QEMU internal SIGBUS
fatal error: fault
```

**Cause:** Cross-compilation issue on ARM64 hosts (Snapdragon, Apple Silicon).

**Solution:**
```powershell
# Windows
wsl --shutdown
# Wait 5 seconds, retry build
```

For production, use AWS CodeBuild to build AMD64 images natively.

---

### Terraform Not Found (Windows)

**Symptom:**
```
terraform: command not found
```

**Cause:** Git Bash doesn't have terraform in PATH.

**Solution:**
```bash
# Install terraform in WSL at ~/bin/terraform
# Scripts use WSL wrapper automatically

# Or run manually via WSL
wsl -e bash -c "cd /mnt/c/.../aws/terraform && terraform apply"
```

---

## Authentication Issues

### Clerk JWT Validation Fails

**Symptom:**
```
401 Unauthorized: Invalid token
```

**Causes:**
1. `CLERK_PEM_PUBLIC_KEY` malformed
2. `CLERK_ISSUER` mismatch
3. Token expired

**Solution:**
```bash
# Verify key format (must have newlines)
echo "$CLERK_PEM_PUBLIC_KEY"
# Should show:
# -----BEGIN PUBLIC KEY-----
# MIIBIj...
# -----END PUBLIC KEY-----

# Check issuer matches Clerk dashboard
echo "$CLERK_ISSUER"
# Should be: https://your-instance.clerk.accounts.dev
```

---

### Frontend CORS Errors

**Symptom:**
```
Access-Control-Allow-Origin missing
```

**Solution:** Verify API CORS settings in `main/api/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://csvgeneration.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Workflow Issues

### Test Generation Fails

**Symptom:** Job completes but no tests generated.

**Diagnosis:**
```bash
# Check LangFuse traces
# https://cloud.langfuse.com

# Check job error
curl http://localhost:8080/jobs/{job_id}
```

**Common causes:**
1. **LLM API key invalid:** Check `OPENROUTER_API_KEY`
2. **Context retrieval empty:** Check ChromaDB
3. **Token limit exceeded:** Reduce `max_tokens` or URS size

---

### Job Stuck in Processing

**Symptom:** Job status "processing" for >15 minutes.

**Cause:** Worker crashed during execution.

**Solution:**
```bash
# Check worker logs
docker-compose -f docker-compose.dev.yml logs worker

# Restart worker (job will retry)
docker-compose -f docker-compose.dev.yml restart worker
```

---

## Monitoring

### Check Service Health

```bash
# Local
curl http://localhost:8080/health

# AWS
curl https://csvgeneration.com/health
```

### Check ECS Task Status

```bash
aws ecs describe-services \
  --cluster pharma-test-gen-cluster \
  --services pharma-test-gen-api pharma-test-gen-worker pharma-test-gen-frontend \
  --query 'services[*].[serviceName,runningCount,desiredCount,deployments[0].rolloutState]' \
  --output table
```

### View CloudWatch Logs

```bash
aws logs tail /ecs/pharma-test-gen/api --since 10m --region eu-west-2
aws logs tail /ecs/pharma-test-gen/worker --since 10m --region eu-west-2
```

---

## Quick Recovery Commands

### Local (Docker)

```bash
# Full restart
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# Nuclear option (remove volumes)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

### AWS

```bash
# Quick redeploy
python aws/scripts/redeploy.py --wait

# Full recovery
python aws/scripts/deploy.py
python aws/scripts/redeploy.py --wait

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id E1DTSJYZQGK50L \
  --paths "/*"
```
