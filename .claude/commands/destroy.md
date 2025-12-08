---
description: Destroy AWS ECS/Fargate infrastructure to save costs. Preserves S3 buckets, ECR repos, and Terraform state by default. Use at end of day or when not actively using the deployment.
argument-hint: [--yes] [--delete-ecr]
---

# Destroy AWS Infrastructure

Destroy the pharma-test-gen AWS ECS/Fargate infrastructure to save costs.

**Production URL (before destroy):** https://csvgeneration.com/

**Arguments:** $ARGUMENTS

## What Will Be Destroyed

| Resource | Hourly Cost |
|----------|-------------|
| ECS Cluster & Services (API, Worker, Frontend) | ~$0.12/hour |
| Application Load Balancers (2) | ~$0.04/hour |
| CloudFront distribution | ~$0.01/hour |
| SQS Queues | minimal |
| CloudWatch Log Groups | minimal |
| IAM Roles & Security Groups | free |

**Estimated savings:** ~$0.50-1.00/hour (~$12-24/day)

## What Will Be Preserved

| Resource | Monthly Cost |
|----------|-------------|
| S3: pharma-test-gen-terraform-state | ~$0.02 |
| S3: pharma-test-gen-chromadb-* | ~$0.00 |
| ECR repositories (api, worker, frontend) | ~$2.00 |
| DynamoDB: terraform-locks | ~$0.00 |

**Total preserved cost:** ~$2/month

## Arguments

| Argument | Description |
|----------|-------------|
| `--yes` | Auto-approve destruction without confirmation prompt |
| `--delete-ecr` | Also delete ECR images (not recommended - slows redeploy) |

## Execution

### Step 1: Parse Arguments

Arguments provided: `$ARGUMENTS`

Build command based on arguments:
- If `--yes` is present: add `--yes --skip-ecr` flags
- If `--delete-ecr` is present: remove `--skip-ecr` flag

### Step 2: Run Destroy Script

```bash
python aws/scripts/destroy.py $ARGUMENTS --skip-ecr
```

Run the destroy script with a 15-minute timeout. The script will:
1. Empty S3 buckets (vectors and output)
2. Scale down ECS services to 0
3. Remove ECR repos from Terraform state (prevent_destroy)
4. Run `terraform destroy`
5. Stop AWS Config recorder
6. Clean up local artifacts

### Step 3: Verify Destruction

After the script completes, verify resources are destroyed:

```bash
aws ecs list-services --cluster pharma-test-gen-cluster --region eu-west-2
```

Expected result: `{"serviceArns": []}`

### Step 4: Report Results

Report to the user:
- What was destroyed
- What was preserved
- Estimated monthly savings
- How to redeploy: `python aws/scripts/deploy.py`

## Troubleshooting

If destroy fails, common issues:

1. **ECR prevent_destroy error**: Run these commands manually:
   ```bash
   wsl bash -c 'export PATH=$HOME/bin:$PATH && cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform state rm "module.ecr.aws_ecr_repository.this[\"api\"]"'
   wsl bash -c 'export PATH=$HOME/bin:$PATH && cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform state rm "module.ecr.aws_ecr_repository.this[\"worker\"]"'
   wsl bash -c 'export PATH=$HOME/bin:$PATH && cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform state rm "module.ecr.aws_ecr_repository.this[\"frontend\"]"'
   ```

2. **S3 bucket not empty**: The chromadb bucket is preserved by design. Remove it from state:
   ```bash
   wsl bash -c 'export PATH=$HOME/bin:$PATH && cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform state rm aws_s3_bucket.chromadb'
   ```

3. **Terraform state lock**: Force unlock if needed:
   ```bash
   wsl bash -c 'export PATH=$HOME/bin:$PATH && cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && terraform force-unlock -force LOCK_ID'
   ```

For more troubleshooting, invoke the `aws-deployment` skill.

## To Redeploy Later

```bash
python aws/scripts/deploy.py
```

Or use the `/deploy` command.

---

## IMPORTANT: Post-Destroy Warnings

After running destroy, the following may need attention on next `/deploy`:

### 1. IAM Policies May Be Lost (ISSUE-005)

Terraform may not properly recreate inline IAM policies for task roles. After redeploying, verify:

```bash
aws iam list-role-policies --role-name pharma-test-gen-api-task-role
```

If empty, re-attach policies per `main/docs/issues/ISSUE-005-rebuild-uses-wrong-image-tag.md`.

### 2. ChromaDB Data Needs Re-upload

The S3 vectors bucket is preserved, but if emptied, you'll need to re-upload:

```bash
tar -czvf /tmp/chroma_db.tar.gz -C main chroma_db
aws s3 cp /tmp/chroma_db.tar.gz s3://pharma-test-gen-vectors-staging/chroma_db.tar.gz --region eu-west-2
```

### 3. Task Definition Revisions Reset

After redeploy, verify the ECS services are using task definitions with all secrets (ISSUE-006):

```bash
aws ecs describe-task-definition \
  --task-definition pharma-test-gen-api \
  --query "taskDefinition.containerDefinitions[0].secrets[*].name" \
  --region eu-west-2
```

Expected: `DATABASE_URL`, `CLERK_PEM_PUBLIC_KEY`, `CLERK_ISSUER`, `OPENROUTER_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
