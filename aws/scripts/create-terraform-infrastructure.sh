#!/bin/bash
#
# Create Terraform Backend Infrastructure - Task 0.3 Steps 1-2
# Creates S3 bucket and DynamoDB table for Terraform state management
#
# Account: 275333454012
# Region: eu-west-2
#

set -e

REGION="eu-west-2"
BUCKET_NAME="pharma-tfstate-eu"
DYNAMODB_TABLE="terraform-locks"

echo "============================================================"
echo "  Create Terraform Backend Infrastructure - Task 0.3"
echo "============================================================"
echo ""
echo "Region: $REGION"
echo "S3 Bucket: $BUCKET_NAME"
echo "DynamoDB Table: $DYNAMODB_TABLE"
echo ""

# Step 1: Create S3 bucket
echo "[1/5] Creating S3 bucket for Terraform state..."
if aws s3 ls "s3://$BUCKET_NAME" --region "$REGION" &>/dev/null; then
    echo "⚠️  S3 bucket already exists: $BUCKET_NAME"
else
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION"

    echo "✓ S3 bucket created: $BUCKET_NAME"
fi

# Step 2: Enable versioning
echo ""
echo "[2/5] Enabling versioning on S3 bucket..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

echo "✓ Versioning enabled"

# Step 3: Block public access
echo ""
echo "[3/5] Blocking public access..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

echo "✓ Public access blocked"

# Step 4: Enable encryption
echo ""
echo "[4/5] Enabling default encryption..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

echo "✓ Default encryption enabled (AES256)"

# Step 5: Create DynamoDB table
echo ""
echo "[5/5] Creating DynamoDB table for state locking..."
if aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --region "$REGION" &>/dev/null; then
    echo "⚠️  DynamoDB table already exists: $DYNAMODB_TABLE"
else
    aws dynamodb create-table \
        --table-name "$DYNAMODB_TABLE" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --no-cli-pager

    echo "✓ DynamoDB table created: $DYNAMODB_TABLE"

    # Wait for table to be active
    echo "   Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name "$DYNAMODB_TABLE" --region "$REGION"
fi

# Verify everything
echo ""
echo "============================================================"
echo "✅ Terraform Backend Infrastructure Created!"
echo "============================================================"
echo ""
echo "Summary:"
echo ""
echo "S3 Bucket ($BUCKET_NAME):"
aws s3api get-bucket-versioning --bucket "$BUCKET_NAME" --query 'Status' --output text | awk '{print "  • Versioning: " $0}'
echo "  • Public Access: Blocked"
echo "  • Encryption: AES256 (SSE-S3)"
echo ""
echo "DynamoDB Table ($DYNAMODB_TABLE):"
aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --region "$REGION" --query 'Table.TableStatus' --output text | awk '{print "  • Status: " $0}'
echo ""
echo "Next Steps:"
echo "  1. Attach IAM policy for Terraform backend permissions"
echo "  2. Run: bash setup-terraform-backend.sh"
echo ""
