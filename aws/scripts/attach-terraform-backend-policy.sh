#!/bin/bash
#
# Attach Terraform Backend IAM Policy - Task 0.3 Step 3
# Creates and attaches IAM policy for Terraform S3 backend and DynamoDB state locking
#
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - IAM user 'aiengineer' exists
# - S3 bucket 'pharma-tfstate-eu' will be created
# - DynamoDB table 'terraform-locks' will be created
#

set -e  # Exit on error

# Configuration
POLICY_NAME="PharmaTerraformBackendPolicy"
POLICY_FILE="../iam-policies/terraform-backend-policy.json"
IAM_USER="aiengineer"
ACCOUNT_ID="275333454012"
REGION="eu-west-2"

echo "============================================================"
echo "  Terraform Backend IAM Policy Setup - Task 0.3 Step 3"
echo "============================================================"
echo ""
echo "Policy Name: $POLICY_NAME"
echo "IAM User:    $IAM_USER"
echo "Region:      $REGION"
echo "Account:     $ACCOUNT_ID"
echo ""

# Check if policy file exists
if [ ! -f "$POLICY_FILE" ]; then
    echo "❌ ERROR: Policy file not found: $POLICY_FILE"
    exit 1
fi

echo "[1/5] Checking if policy already exists..."
EXISTING_POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>/dev/null || true)

if [ -n "$EXISTING_POLICY_ARN" ]; then
    echo "⚠️  Policy already exists: $EXISTING_POLICY_ARN"
    POLICY_ARN="$EXISTING_POLICY_ARN"
else
    echo "✓ Policy does not exist yet"

    # Create the policy
    echo ""
    echo "[2/5] Creating IAM policy..."
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "file://$POLICY_FILE" \
        --description "Terraform backend permissions for S3 state and DynamoDB locking" \
        --query 'Policy.Arn' \
        --output text)

    echo "✓ Policy created: $POLICY_ARN"
fi

# Check if policy is already attached to user
echo ""
echo "[3/5] Checking if policy is already attached to user..."
ATTACHED=$(aws iam list-attached-user-policies \
    --user-name "$IAM_USER" \
    --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN'].PolicyArn" \
    --output text 2>/dev/null || true)

if [ -n "$ATTACHED" ]; then
    echo "⚠️  Policy already attached to user $IAM_USER"
else
    echo "✓ Policy not yet attached"

    # Attach policy to user
    echo ""
    echo "[4/5] Attaching policy to user $IAM_USER..."
    aws iam attach-user-policy \
        --user-name "$IAM_USER" \
        --policy-arn "$POLICY_ARN"

    echo "✓ Policy attached successfully"
fi

# Verify attachment
echo ""
echo "[5/5] Verifying policy attachment..."
aws iam list-attached-user-policies \
    --user-name "$IAM_USER" \
    --query "AttachedPolicies[?PolicyArn=='$POLICY_ARN']" \
    --output table

echo ""
echo "============================================================"
echo "✅ Terraform Backend IAM Policy Setup Complete!"
echo "============================================================"
echo ""
echo "Summary:"
echo "  • Policy ARN: $POLICY_ARN"
echo "  • Attached to: $IAM_USER"
echo "  • Permissions granted:"
echo "    - S3 bucket: pharma-tfstate-eu (List, Get, Put, Delete)"
echo "    - DynamoDB table: terraform-locks (Put, Get, Delete, Describe)"
echo ""
echo "Next Steps:"
echo "  1. Create S3 bucket: pharma-tfstate-eu"
echo "  2. Create DynamoDB table: terraform-locks"
echo "  3. Configure Terraform backend in backend.tf"
echo "  4. Run: terraform init"
echo ""
