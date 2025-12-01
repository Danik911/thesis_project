#!/bin/bash

###############################################################################
# IAM Policy Attachment Script for Phase 0
#
# This script creates and attaches the PharmaPhase0DeploymentPolicy to the
# "aiengineer" IAM user.
#
# REQUIREMENTS:
# - You must have AWS admin/root credentials configured
# - AWS CLI must be installed and configured
# - Run from project root directory
#
# USAGE:
#   bash aws/iam-policies/attach-phase0-policy.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Phase 0 IAM Policy Attachment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
POLICY_NAME="PharmaPhase0DeploymentPolicy"
USER_NAME="aiengineer"
ACCOUNT_ID="275333454012"
POLICY_FILE="aws/iam-policies/phase0-deployment-policy.json"
REGION="eu-west-2"

# Step 1: Verify AWS CLI is configured
echo -e "${YELLOW}[1/6] Verifying AWS CLI configuration...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not configured or no credentials found${NC}"
    echo "Please run: aws configure"
    exit 1
fi

CALLER_ARN=$(aws sts get-caller-identity --query Arn --output text)
echo -e "${GREEN}✓ Authenticated as: ${CALLER_ARN}${NC}"
echo ""

# Step 2: Verify policy file exists
echo -e "${YELLOW}[2/6] Checking policy file...${NC}"
if [ ! -f "$POLICY_FILE" ]; then
    echo -e "${RED}ERROR: Policy file not found: ${POLICY_FILE}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Policy file found: ${POLICY_FILE}${NC}"
echo ""

# Step 3: Check if policy already exists
echo -e "${YELLOW}[3/6] Checking if policy already exists...${NC}"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    echo -e "${YELLOW}⚠ Policy already exists: ${POLICY_ARN}${NC}"
    read -p "Do you want to create a new version? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Get default version and delete it if needed
        echo "Creating new policy version..."
        aws iam create-policy-version \
            --policy-arn "$POLICY_ARN" \
            --policy-document file://"$POLICY_FILE" \
            --set-as-default
        echo -e "${GREEN}✓ Policy version updated${NC}"
    else
        echo "Skipping policy creation. Using existing policy."
    fi
else
    # Step 4: Create the policy
    echo -e "${YELLOW}[4/6] Creating IAM policy...${NC}"
    CREATE_RESULT=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://"$POLICY_FILE" \
        --description "Permissions for Phase 0 AWS migration tasks (Service Quotas, CloudTrail, Config, KMS, S3, DynamoDB)" \
        --output json)

    POLICY_ARN=$(echo "$CREATE_RESULT" | jq -r '.Policy.Arn')
    echo -e "${GREEN}✓ Policy created: ${POLICY_ARN}${NC}"
fi
echo ""

# Step 5: Check if policy is already attached
echo -e "${YELLOW}[5/6] Checking if policy is already attached to user...${NC}"
if aws iam list-attached-user-policies --user-name "$USER_NAME" | grep -q "$POLICY_NAME"; then
    echo -e "${YELLOW}⚠ Policy already attached to user: ${USER_NAME}${NC}"
else
    # Attach policy to user
    echo -e "${YELLOW}Attaching policy to user: ${USER_NAME}...${NC}"
    aws iam attach-user-policy \
        --user-name "$USER_NAME" \
        --policy-arn "$POLICY_ARN"

    echo -e "${GREEN}✓ Policy attached successfully${NC}"
fi
echo ""

# Step 6: Verify attachment
echo -e "${YELLOW}[6/6] Verifying policy attachment...${NC}"
ATTACHED_POLICIES=$(aws iam list-attached-user-policies \
    --user-name "$USER_NAME" \
    --output json)

if echo "$ATTACHED_POLICIES" | grep -q "$POLICY_NAME"; then
    echo -e "${GREEN}✓ Verification successful!${NC}"
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Attached Policies for ${USER_NAME}:${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "$ATTACHED_POLICIES" | jq -r '.AttachedPolicies[] | "  - \(.PolicyName) (\(.PolicyArn))"'
    echo ""
    echo -e "${GREEN}SUCCESS: Phase 0 permissions granted!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Run verification script: bash aws/iam-policies/verify-phase0-permissions.sh"
    echo "2. Continue with Phase 0 tasks: /prp 0.1"
else
    echo -e "${RED}ERROR: Policy attachment verification failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Script completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
