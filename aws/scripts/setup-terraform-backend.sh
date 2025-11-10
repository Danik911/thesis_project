#!/bin/bash
#
# Terraform Backend Setup Script - Task 0.3 Steps 4-6
# Installs Terraform (if needed) and initializes S3 backend
#
# Prerequisites:
# - S3 bucket 'pharma-tfstate-eu' must exist
# - DynamoDB table 'terraform-locks' must exist
# - IAM permissions for S3 and DynamoDB must be configured
#

set -e

TERRAFORM_VERSION="1.7.0"
REGION="eu-west-2"
BUCKET_NAME="pharma-tfstate-eu"
DYNAMODB_TABLE="terraform-locks"
PROJECT_ROOT="/mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project"

echo "============================================================"
echo "  Terraform Backend Setup - Task 0.3"
echo "============================================================"
echo ""

# Check if Terraform is installed
echo "[1/6] Checking Terraform installation..."
if command -v terraform &> /dev/null; then
    INSTALLED_VERSION=$(terraform version -json | grep -oP '"terraform_version":"\K[^"]+' || terraform version | head -n1 | cut -d'v' -f2)
    echo "✓ Terraform already installed: v$INSTALLED_VERSION"
else
    echo "⚠️  Terraform not found. Installing..."

    # Install Terraform
    echo ""
    echo "[2/6] Installing Terraform v$TERRAFORM_VERSION..."

    # Download and install
    cd /tmp
    wget -q "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip"

    # Unzip
    sudo apt-get update -qq && sudo apt-get install -y -qq unzip
    unzip -q "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"

    # Move to PATH
    sudo mv terraform /usr/local/bin/

    # Cleanup
    rm "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"

    echo "✓ Terraform v$TERRAFORM_VERSION installed successfully"
fi

# Verify Terraform
echo ""
echo "[3/6] Verifying Terraform installation..."
terraform version

# Check S3 bucket exists
echo ""
echo "[4/6] Verifying S3 bucket exists..."
if aws s3 ls "s3://$BUCKET_NAME" --region "$REGION" &>/dev/null; then
    echo "✓ S3 bucket exists: $BUCKET_NAME"
else
    echo "❌ ERROR: S3 bucket does not exist: $BUCKET_NAME"
    echo "   Run the following command to create it:"
    echo "   aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION --create-bucket-configuration LocationConstraint=$REGION"
    exit 1
fi

# Check DynamoDB table exists
echo ""
echo "[5/6] Verifying DynamoDB table exists..."
if aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --region "$REGION" &>/dev/null; then
    echo "✓ DynamoDB table exists: $DYNAMODB_TABLE"
else
    echo "❌ ERROR: DynamoDB table does not exist: $DYNAMODB_TABLE"
    echo "   Run the following command to create it:"
    echo "   aws dynamodb create-table --table-name $DYNAMODB_TABLE --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region $REGION"
    exit 1
fi

# Initialize Terraform
echo ""
echo "[6/6] Initializing Terraform backend..."
cd "$PROJECT_ROOT/terraform"

# Convert backend.tf to LF if needed
if command -v dos2unix &> /dev/null; then
    dos2unix backend.tf 2>/dev/null || true
fi

terraform init

echo ""
echo "============================================================"
echo "✅ Terraform Backend Setup Complete!"
echo "============================================================"
echo ""
echo "Summary:"
echo "  • Backend type: S3"
echo "  • State bucket: $BUCKET_NAME"
echo "  • Lock table: $DYNAMODB_TABLE"
echo "  • Region: $REGION"
echo "  • Encryption: Enabled"
echo ""
echo "Next Steps:"
echo "  • Create Terraform infrastructure files (*.tf)"
echo "  • Run: terraform plan"
echo "  • Run: terraform apply"
echo ""
