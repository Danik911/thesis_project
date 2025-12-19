# ISSUE-014: Destroy/Deploy Cycle Reliability

## Date
2025-12-19

## Symptom
After running destroy.yml followed by deploy.yml, the deployment fails due to:
1. Missing IAM permissions preventing resource creation
2. IAM policies being destroyed during terraform destroy (not removed from state)
3. S3 bucket sub-resources not imported after fresh deploy

## Root Cause

### 1. IAM Permission Gaps

The GitHub Actions IAM role had incomplete permissions for a full destroy/deploy cycle:

| Policy | Before | After |
|--------|--------|-------|
| Route53 | READ-ONLY | + `route53:ChangeResourceRecordSets` |
| ACM | READ-ONLY | + `acm:RequestCertificate`, `acm:DeleteCertificate`, `acm:AddTagsToCertificate` |
| CloudFront | READ + Invalidation | + `CreateDistribution`, `UpdateDistribution`, `DeleteDistribution`, `TagResource`, OAC permissions |
| Secrets Manager | READ-ONLY | + `CreateSecret`, `DeleteSecret`, `PutSecretValue`, `UpdateSecret`, `TagResource` |
| RDS | MISSING | NEW policy with full RDS management permissions |

### 2. Destroy.yml Missing Policy Removals

Only 10 of 18 IAM policies were removed from Terraform state before destroy:

**Previously Preserved:**
- ecr, ecs, terraform_state, iam, acm, route53, cloudfront, cloudwatch

**NOT Preserved (destroyed):**
- networking, logs, sqs, secrets, s3, xray, autoscaling, config, rds (new)

When policies are destroyed but the role is preserved, the GitHub Actions role loses critical permissions and subsequent deploys fail.

### 3. ChromaDB S3 Sub-Resources Not Imported

The destroy.yml removes these from state:
- `aws_s3_bucket_versioning.chromadb`
- `aws_s3_bucket_server_side_encryption_configuration.chromadb`
- `aws_s3_bucket_public_access_block.chromadb`

But deploy.yml only imported the bucket itself, causing "already exists" errors on sub-resources.

## Files Modified

### 1. `aws/terraform/github-actions-oidc.tf`

| Change | Lines |
|--------|-------|
| Route53: Added `route53:ChangeResourceRecordSets` | 498-506 |
| ACM: Added write permissions | 522-533 |
| CloudFront: Added distribution management + OAC | 392-422 |
| Secrets Manager: Added write permissions | 436-463 |
| RDS: Added new policy | 579-617 |

### 2. `.github/workflows/destroy.yml`

Added 9 missing policy state removals (lines 107-123):
```yaml
terraform state rm 'aws_iam_role_policy.github_actions_networking' || true
terraform state rm 'aws_iam_role_policy.github_actions_logs' || true
terraform state rm 'aws_iam_role_policy.github_actions_sqs' || true
terraform state rm 'aws_iam_role_policy.github_actions_secrets' || true
terraform state rm 'aws_iam_role_policy.github_actions_s3' || true
terraform state rm 'aws_iam_role_policy.github_actions_xray' || true
terraform state rm 'aws_iam_role_policy.github_actions_autoscaling' || true
terraform state rm 'aws_iam_role_policy.github_actions_config' || true
terraform state rm 'aws_iam_role_policy.github_actions_rds' || true
```

### 3. `.github/workflows/deploy.yml`

Added ChromaDB sub-resource imports (lines 201-214):
```yaml
# Import ChromaDB bucket sub-resources (preserved by destroy.yml)
terraform import aws_s3_bucket_versioning.chromadb "$CHROMA_BUCKET" || true
terraform import aws_s3_bucket_server_side_encryption_configuration.chromadb "$CHROMA_BUCKET" || true
terraform import aws_s3_bucket_public_access_block.chromadb "$CHROMA_BUCKET" || true
```

## Prevention

1. **Complete IAM Policy Audit**: When adding new IAM policies to `github-actions-oidc.tf`, ALWAYS:
   - Add the policy removal to `destroy.yml`
   - Ensure the policy has write permissions if the resource needs to be created from scratch

2. **S3 Sub-Resource Pattern**: When preserving an S3 bucket in destroy.yml, ALWAYS:
   - Remove ALL sub-resources from state (versioning, encryption, public_access_block)
   - Import ALL sub-resources in deploy.yml

3. **Workflow Testing Checklist**:
   - [ ] Run deploy.yml on fresh infrastructure
   - [ ] Run destroy.yml
   - [ ] Run deploy.yml again
   - [ ] Verify https://csvgeneration.com/ works
   - [ ] Verify https://csvgeneration.com/health returns healthy

## Related

- [ISSUE-013](ISSUE-013-route53-trailing-dot-mismatch.md) - Route53 validation import issues
- GitHub Actions Role: `pharma-test-gen-github-actions`
- IAM Policies: 18 inline policies attached to GitHub Actions role
