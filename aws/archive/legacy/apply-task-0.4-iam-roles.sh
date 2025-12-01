#!/bin/bash
#
# Apply Task 0.4 - Create IAM Roles and Policies
# Validates and applies Terraform configuration for baseline IAM roles
#

set -e

PROJECT_ROOT="/mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"

echo "============================================================"
echo "  Task 0.4: Create Baseline IAM Roles and Policies"
echo "============================================================"
echo ""
echo "This will create:"
echo "  • 3 IAM Roles (deploy, ecs-execution, ecs-task)"
echo "  • Least-privilege policies for each role"
echo "  • GitHub OIDC provider for CI/CD"
echo "  • 2 ECR repositories (backend, worker)"
echo ""
echo "Terraform Directory: $TERRAFORM_DIR"
echo ""

# Navigate to Terraform directory
cd "$TERRAFORM_DIR"

# Step 0: Initialize Terraform (download providers)
echo "[0/6] Initializing Terraform..."
terraform init -upgrade

if [ $? -eq 0 ]; then
    echo "✓ Terraform initialized successfully"
else
    echo "❌ Terraform initialization failed"
    exit 1
fi

echo ""

# Step 1: Validate Terraform files
echo "[1/6] Validating Terraform configuration..."
terraform validate

if [ $? -eq 0 ]; then
    echo "✓ Terraform configuration is valid"
else
    echo "❌ Terraform validation failed"
    exit 1
fi

echo ""

# Step 2: Format Terraform files
echo "[2/6] Formatting Terraform files..."
terraform fmt

echo "✓ Terraform files formatted"
echo ""

# Step 3: Show plan
echo "[3/6] Generating Terraform plan..."
terraform plan -out=tfplan

echo ""
echo "✓ Plan generated successfully"
echo ""

# Step 4: Review and confirm
echo "[4/6] Review the plan above."
echo ""
read -p "Do you want to apply these changes? (yes/no) " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Cancelled. Run 'terraform apply tfplan' when ready."
    exit 0
fi

# Step 5: Apply the plan
echo "[5/6] Applying Terraform changes..."
terraform apply tfplan

echo ""

# Step 6: Clean up plan file
echo "[6/6] Cleaning up..."
rm -f tfplan

echo ""
echo "============================================================"
echo "✅ Task 0.4 Complete!"
echo "============================================================"
echo ""
echo "Resources Created:"
terraform output
echo ""
echo "Next Steps:"
echo "  1. Copy the deploy role ARN to GitHub repository secrets:"
echo "     - Name: AWS_ROLE_ARN"
echo "     - Value: (see 'github_actions_role_arn' output above)"
echo ""
echo "  2. Create GitHub Actions workflow in .github/workflows/"
echo ""
echo "  3. Test role assumption:"
echo "     aws sts assume-role \\"
echo "       --role-arn $(terraform output -raw deploy_role_arn) \\"
echo "       --role-session-name test \\"
echo "       --duration-seconds 3600"
echo ""
