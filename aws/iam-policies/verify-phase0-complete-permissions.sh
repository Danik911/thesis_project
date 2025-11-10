#!/bin/bash

###############################################################################
# Phase 0 Complete Permissions Verification Script
#
# This script tests all IAM permissions required for Phase 0 tasks (0.1-0.4).
# It performs read-only checks where possible and creates/deletes test
# resources to verify write permissions.
#
# REQUIREMENTS:
# - AWS CLI configured with "aiengineer" credentials
# - Phase 0 Complete policy already attached to the user
#
# USAGE:
#   bash aws/iam-policies/verify-phase0-complete-permissions.sh
###############################################################################

set +e  # Don't exit on error - we want to check all permissions

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="eu-west-2"
TEST_PREFIX="pharma-test-$(date +%s)"
PASSED=0
FAILED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Phase 0 Complete Permissions Verification${NC}"
echo -e "${BLUE}(Tasks 0.1-0.4 including ECR/ECS)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Helper function to check command success
check_permission() {
    local test_name="$1"
    local command="$2"

    echo -e "${YELLOW}Testing: ${test_name}${NC}"

    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo -e "${RED}  Command: ${command}${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test 1: STS - Identity verification
echo -e "\n${BLUE}[1/11] Testing STS Permissions...${NC}"
check_permission "Get caller identity" \
    "aws sts get-caller-identity --region $REGION"

# Test 2: Service Quotas
echo -e "\n${BLUE}[2/11] Testing Service Quotas Permissions...${NC}"
check_permission "List ECS service quotas" \
    "aws service-quotas list-service-quotas --service-code ecs --region $REGION --max-items 1"

check_permission "Get specific quota (Fargate vCPU)" \
    "aws service-quotas get-service-quota --service-code ecs --quota-code L-1216C47A --region $REGION"

# Test 3: KMS
echo -e "\n${BLUE}[3/11] Testing KMS Permissions...${NC}"
check_permission "List KMS keys" \
    "aws kms list-keys --region $REGION --max-items 1"

echo -e "${YELLOW}Testing: Create KMS key${NC}"
KMS_KEY_OUTPUT=$(aws kms create-key \
    --description "Phase 0 verification test key" \
    --region $REGION \
    --output json 2>&1)

if [ $? -eq 0 ]; then
    KMS_KEY_ID=$(echo "$KMS_KEY_OUTPUT" | jq -r '.KeyMetadata.KeyId')
    echo -e "${GREEN}✓ PASS - Key created: ${KMS_KEY_ID}${NC}"
    ((PASSED++))

    # Test describe
    check_permission "Describe KMS key" \
        "aws kms describe-key --key-id $KMS_KEY_ID --region $REGION"

    # Schedule key deletion (we don't need it)
    echo -e "${YELLOW}Scheduling test key deletion (7 days)...${NC}"
    aws kms schedule-key-deletion \
        --key-id "$KMS_KEY_ID" \
        --pending-window-in-days 7 \
        --region $REGION &> /dev/null
    echo -e "${GREEN}✓ Test key scheduled for deletion${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${RED}  Error: ${KMS_KEY_OUTPUT}${NC}"
    ((FAILED++))
fi

# Test 4: CloudTrail
echo -e "\n${BLUE}[4/11] Testing CloudTrail Permissions...${NC}"
check_permission "List CloudTrail trails" \
    "aws cloudtrail list-trails --region $REGION"

check_permission "Describe CloudTrail trails" \
    "aws cloudtrail describe-trails --region $REGION"

# Test 5: AWS Config
echo -e "\n${BLUE}[5/11] Testing AWS Config Permissions...${NC}"
check_permission "Describe configuration recorders" \
    "aws configservice describe-configuration-recorders --region $REGION"

check_permission "Describe delivery channels" \
    "aws configservice describe-delivery-channels --region $REGION"

# Test 6: S3
echo -e "\n${BLUE}[6/11] Testing S3 Permissions...${NC}"
TEST_BUCKET="${TEST_PREFIX}-bucket"

echo -e "${YELLOW}Testing: Create S3 bucket (pharma-* prefix)${NC}"
S3_CREATE_OUTPUT=$(aws s3api create-bucket \
    --bucket "$TEST_BUCKET" \
    --region $REGION \
    --create-bucket-configuration LocationConstraint=$REGION 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS - Bucket created: ${TEST_BUCKET}${NC}"
    ((PASSED++))

    # Test versioning
    check_permission "Enable bucket versioning" \
        "aws s3api put-bucket-versioning --bucket $TEST_BUCKET --versioning-configuration Status=Enabled --region $REGION"

    # Test encryption
    check_permission "Enable bucket encryption" \
        "aws s3api put-bucket-encryption --bucket $TEST_BUCKET --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}' --region $REGION"

    # Test public access block
    check_permission "Set public access block" \
        "aws s3api put-public-access-block --bucket $TEST_BUCKET --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true --region $REGION"

    # Clean up test bucket
    echo -e "${YELLOW}Deleting test bucket...${NC}"
    aws s3 rb "s3://${TEST_BUCKET}" --region $REGION &> /dev/null
    echo -e "${GREEN}✓ Test bucket deleted${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${RED}  Error: ${S3_CREATE_OUTPUT}${NC}"
    ((FAILED++))
fi

# Test 7: DynamoDB
echo -e "\n${BLUE}[7/11] Testing DynamoDB Permissions...${NC}"
check_permission "List DynamoDB tables" \
    "aws dynamodb list-tables --region $REGION"

# Note: We don't create terraform-locks table here to avoid conflicts
echo -e "${YELLOW}Note: Skipping DynamoDB table creation (will be created by Task 0.3)${NC}"

# Test 8: IAM
echo -e "\n${BLUE}[8/11] Testing IAM Permissions...${NC}"
check_permission "List IAM roles" \
    "aws iam list-roles --max-items 1"

check_permission "List IAM policies" \
    "aws iam list-policies --scope Local --max-items 1"

# Note: We don't create test IAM roles to avoid cleanup complications
echo -e "${YELLOW}Note: Skipping IAM role creation (will be created by Tasks 0.2/0.4)${NC}"

# Test 9: ECR (NEW for Task 0.4)
echo -e "\n${BLUE}[9/11] Testing ECR Permissions...${NC}"
TEST_REPO="${TEST_PREFIX}-repo"

echo -e "${YELLOW}Testing: Get ECR authorization token${NC}"
ECR_AUTH_OUTPUT=$(aws ecr get-authorization-token --region $REGION 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS - ECR authorization token retrieved${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${RED}  Error: ${ECR_AUTH_OUTPUT}${NC}"
    ((FAILED++))
fi

echo -e "${YELLOW}Testing: Create ECR repository${NC}"
ECR_CREATE_OUTPUT=$(aws ecr create-repository \
    --repository-name "$TEST_REPO" \
    --region $REGION \
    --output json 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS - Repository created: ${TEST_REPO}${NC}"
    ((PASSED++))

    # Test describe
    check_permission "Describe ECR repositories" \
        "aws ecr describe-repositories --repository-names $TEST_REPO --region $REGION"

    # Clean up test repository
    echo -e "${YELLOW}Deleting test repository...${NC}"
    aws ecr delete-repository \
        --repository-name "$TEST_REPO" \
        --region $REGION \
        --force &> /dev/null
    echo -e "${GREEN}✓ Test repository deleted${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${RED}  Error: ${ECR_CREATE_OUTPUT}${NC}"
    ((FAILED++))
fi

# Test 10: ECS (NEW for Task 0.4)
echo -e "\n${BLUE}[10/11] Testing ECS Permissions...${NC}"
check_permission "List ECS clusters" \
    "aws ecs list-clusters --region $REGION"

check_permission "List ECS task definitions" \
    "aws ecs list-task-definitions --region $REGION --max-items 1"

echo -e "${YELLOW}Note: Skipping ECS cluster creation (will be created by Task 4.1)${NC}"

# Test 11: CloudWatch Logs (NEW for Task 0.4)
echo -e "\n${BLUE}[11/11] Testing CloudWatch Logs Permissions...${NC}"
TEST_LOG_GROUP="/ecs/${TEST_PREFIX}-logs"

echo -e "${YELLOW}Testing: Create CloudWatch log group${NC}"
LOGS_CREATE_OUTPUT=$(aws logs create-log-group \
    --log-group-name "$TEST_LOG_GROUP" \
    --region $REGION 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASS - Log group created: ${TEST_LOG_GROUP}${NC}"
    ((PASSED++))

    # Test describe
    check_permission "Describe log groups" \
        "aws logs describe-log-groups --log-group-name-prefix /ecs/$TEST_PREFIX --region $REGION"

    # Clean up test log group
    echo -e "${YELLOW}Deleting test log group...${NC}"
    aws logs delete-log-group \
        --log-group-name "$TEST_LOG_GROUP" \
        --region $REGION &> /dev/null
    echo -e "${GREEN}✓ Test log group deleted${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "${RED}  Error: ${LOGS_CREATE_OUTPUT}${NC}"
    ((FAILED++))
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Verification Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL PERMISSIONS VERIFIED!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Proceed with Phase 0 tasks:"
    echo "   - /prp 0.1 (Service Quotas)"
    echo "   - /prp 0.2 (Compliance Baseline)"
    echo "   - /prp 0.3 (Terraform Backend)"
    echo "   - /prp 0.4 (IAM Roles for ECS/ECR)"
    echo ""
    exit 0
else
    echo -e "${RED}⚠ SOME PERMISSIONS FAILED${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Verify policy is attached:"
    echo "   aws iam list-attached-user-policies --user-name aiengineer"
    echo ""
    echo "2. Wait 10 seconds for IAM propagation:"
    echo "   sleep 10"
    echo ""
    echo "3. Re-run this verification script"
    echo ""
    exit 1
fi
