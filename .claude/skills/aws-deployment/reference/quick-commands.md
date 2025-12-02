# AWS Quick Commands Reference

Copy-paste ready commands for pharma-test-gen deployment.

## Configuration
```bash
PROJECT=pharma-test-gen
REGION=eu-west-2
ACCOUNT=275333454012
ECR=$ACCOUNT.dkr.ecr.$REGION.amazonaws.com
```

## Deploy Workflow

### 1. ECR Login
```bash
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 275333454012.dkr.ecr.eu-west-2.amazonaws.com
```

### 2. Build & Push Images
```bash
# API
docker buildx build --platform linux/amd64 -f Dockerfile.api.pip -t 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-api:staging-latest --push .

# Worker
docker buildx build --platform linux/amd64 -f Dockerfile.worker.pip -t 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-worker:staging-latest --push .

# Frontend (needs CLERK key)
docker buildx build --platform linux/amd64 -f Dockerfile.frontend --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx -t 275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-frontend:staging-latest --push .
```

### 3. Terraform Deploy
```bash
cd aws/terraform
terraform init
terraform apply -var-file=environments/staging.tfvars -auto-approve
```

### 4. Upload ChromaDB to S3
```bash
# Create tarball
tar -czvf /tmp/chroma_db.tar.gz -C main chroma_db

# Upload
aws s3 cp /tmp/chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz --region eu-west-2
```

### 5. Force Service Redeployment
```bash
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-api --force-new-deployment --region eu-west-2
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-worker --force-new-deployment --desired-count 1 --region eu-west-2
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-frontend --force-new-deployment --region eu-west-2
```

### 6. Verify Services
```bash
aws ecs describe-services --cluster pharma-test-gen-cluster --services pharma-test-gen-api pharma-test-gen-worker pharma-test-gen-frontend --region eu-west-2 --query 'services[].{name:serviceName,desired:desiredCount,running:runningCount}' --output table
```

---

## Destroy Workflow

### 1. Run destroy.py
```bash
python aws/scripts/destroy.py --yes --skip-ecr
```

### 2. Manual Terraform Destroy (if script fails)
```bash
cd aws/terraform
terraform destroy -var-file=environments/staging.tfvars -auto-approve
```

### 3. Stop AWS Config (optional, saves ~$3-5/month)
```bash
aws configservice stop-configuration-recorder --configuration-recorder-name pharma --region eu-west-2
```

---

## Monitoring

### Check CloudWatch Logs
```bash
aws logs filter-log-events --log-group-name /ecs/pharma-test-gen/worker --start-time $(date -d '5 minutes ago' +%s000) --region eu-west-2 --query 'events[-10:].message' --output text
```

### Check ALB DNS
```bash
aws elbv2 describe-load-balancers --names pharma-test-gen-api-alb pharma-test-gen-frontend-alb --region eu-west-2 --query 'LoadBalancers[].{name:LoadBalancerName,dns:DNSName}' --output table
```

### Health Check
```bash
curl http://pharma-test-gen-api-alb-xxx.eu-west-2.elb.amazonaws.com/health
```

---

## WSL Wrapper (Windows)

All commands above need WSL wrapper on Windows:
```powershell
wsl -d Ubuntu -e bash -c "cd /mnt/c/Users/.../thesis_project && <command>"
```
