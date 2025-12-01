#!/bin/bash
#
# MASTER SCRIPT: Complete Task 0.3 - Terraform Backend Setup
# Runs all steps in correct order
#
# This script will:
# 1. Create S3 bucket and DynamoDB table
# 2. Attach IAM policy for Terraform permissions
# 3. Install Terraform (if needed)
# 4. Initialize Terraform backend
#

set -e

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo "  TASK 0.3: Complete Terraform Backend Setup"
echo "============================================================"
echo ""
echo "This will run all Task 0.3 steps in order:"
echo "  1. Create S3 bucket (pharma-tfstate-eu)"
echo "  2. Create DynamoDB table (terraform-locks)"
echo "  3. Attach IAM policy (PharmaTerraformBackendPolicy)"
echo "  4. Install Terraform (if needed)"
echo "  5. Initialize Terraform backend"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "============================================================"
echo "STEP 1: Create S3 Bucket & DynamoDB Table"
echo "============================================================"
echo ""
bash "$SCRIPTS_DIR/create-terraform-infrastructure.sh"

echo ""
echo "============================================================"
echo "STEP 2: Attach IAM Policy"
echo "============================================================"
echo ""
bash "$SCRIPTS_DIR/attach-terraform-backend-policy.sh"

echo ""
echo "============================================================"
echo "STEP 3: Install Terraform & Initialize Backend"
echo "============================================================"
echo ""
bash "$SCRIPTS_DIR/setup-terraform-backend.sh"

echo ""
echo "============================================================"
echo "🎉 TASK 0.3 COMPLETE!"
echo "============================================================"
echo ""
echo "✅ S3 bucket created: pharma-tfstate-eu"
echo "✅ DynamoDB table created: terraform-locks"
echo "✅ IAM policy attached: PharmaTerraformBackendPolicy"
echo "✅ Terraform installed and initialized"
echo "✅ backend.tf configured"
echo ""
echo "Your Terraform backend is now ready!"
echo ""
echo "Test it with:"
echo "  cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/terraform"
echo "  terraform plan"
echo ""
