#!/bin/bash
# Import existing ECR repositories into Terraform state

set -e

cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

echo "Importing ECR repositories into Terraform state..."

terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["api"]' pharma-test-gen-api || true
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["worker"]' pharma-test-gen-worker || true
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["frontend"]' pharma-test-gen-frontend || true

echo "ECR import complete!"
