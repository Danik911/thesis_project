#!/bin/bash
# Import ECR repositories into Terraform state

cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

echo "Importing ECR repositories..."

terraform import -var-file=environments/staging.tfvars \
  'module.ecr.aws_ecr_repository.this["api"]' pharma-test-gen-api

terraform import -var-file=environments/staging.tfvars \
  'module.ecr.aws_ecr_repository.this["frontend"]' pharma-test-gen-frontend

terraform import -var-file=environments/staging.tfvars \
  'module.ecr.aws_ecr_repository.this["worker"]' pharma-test-gen-worker

echo "Done!"
