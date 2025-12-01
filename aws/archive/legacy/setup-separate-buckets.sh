#!/bin/bash
set -e

echo "=== Setting Up Separate Buckets for CloudTrail and Config ==="
echo ""

REGION=eu-west-2
CLOUDTRAIL_BUCKET=pharma-cloudtrail-logs-eu
CONFIG_BUCKET=pharma-config-logs-eu

# Step 1: Create CloudTrail logs bucket
echo "Step 1: Creating CloudTrail logs bucket..."
aws s3api create-bucket --bucket ${CLOUDTRAIL_BUCKET} --region ${REGION} --create-bucket-configuration LocationConstraint=${REGION}
aws s3api put-bucket-versioning --bucket ${CLOUDTRAIL_BUCKET} --versioning-configuration Status=Enabled --region ${REGION}
aws s3api put-public-access-block --bucket ${CLOUDTRAIL_BUCKET} --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" --region ${REGION}
aws s3api put-bucket-encryption --bucket ${CLOUDTRAIL_BUCKET} --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' --region ${REGION}
echo "✓ CloudTrail logs bucket created"
echo ""

# Step 2: Create AWS Config logs bucket
echo "Step 2: Creating AWS Config logs bucket..."
aws s3api create-bucket --bucket ${CONFIG_BUCKET} --region ${REGION} --create-bucket-configuration LocationConstraint=${REGION}
aws s3api put-bucket-versioning --bucket ${CONFIG_BUCKET} --versioning-configuration Status=Enabled --region ${REGION}
aws s3api put-public-access-block --bucket ${CONFIG_BUCKET} --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" --region ${REGION}
aws s3api put-bucket-encryption --bucket ${CONFIG_BUCKET} --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' --region ${REGION}
echo "✓ AWS Config logs bucket created"
echo ""

# Step 3: Apply bucket policies
echo "Step 3: Applying bucket policies..."
aws s3api put-bucket-policy --bucket ${CLOUDTRAIL_BUCKET} --policy file:///mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/cloudtrail-logs-bucket-policy.json --region ${REGION}
aws s3api put-bucket-policy --bucket ${CONFIG_BUCKET} --policy file:///mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/config-logs-bucket-policy.json --region ${REGION}
echo "✓ Bucket policies applied"
echo ""

# Step 4: Update CloudTrail
echo "Step 4: Updating CloudTrail to use new bucket..."
aws cloudtrail update-trail --name pharma-trail --s3-bucket-name ${CLOUDTRAIL_BUCKET} --region ${REGION}
echo "✓ CloudTrail updated"
echo ""

# Step 5: Verify
echo "Step 5: Verifying configuration..."
echo "CloudTrail bucket:"
aws cloudtrail describe-trails --trail-name-list pharma-trail --region ${REGION} --query 'trailList[0].S3BucketName' --output text
echo ""
echo "=== Setup Complete! ==="
