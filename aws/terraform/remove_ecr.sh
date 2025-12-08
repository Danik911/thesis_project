#!/bin/bash
export PATH=$HOME/bin:$PATH
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform

echo "Removing ECR resources from Terraform state..."
terraform state rm 'module.ecr.aws_ecr_repository.this["api"]' || true
terraform state rm 'module.ecr.aws_ecr_repository.this["worker"]' || true
terraform state rm 'module.ecr.aws_ecr_repository.this["frontend"]' || true
terraform state rm 'module.ecr.aws_ecr_lifecycle_policy.this["api"]' || true
terraform state rm 'module.ecr.aws_ecr_lifecycle_policy.this["worker"]' || true
terraform state rm 'module.ecr.aws_ecr_lifecycle_policy.this["frontend"]' || true

echo "Running terraform destroy..."
terraform destroy -var-file=environments/staging.tfvars -auto-approve
