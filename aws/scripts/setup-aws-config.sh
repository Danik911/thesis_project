#!/bin/bash
#
# AWS Config Setup Script for Phase 0.2
# Region: eu-west-2 (London)
# Account: 275333454012
#

set -e  # Exit on error

echo "========================================="
echo "AWS Config Setup - Phase 0.2"
echo "========================================="
echo ""

# Step 1: Create configuration recorder
echo "[1/4] Creating configuration recorder..."
aws configservice put-configuration-recorder \
  --configuration-recorder '{
    "name": "pharma",
    "roleARN": "arn:aws:iam::275333454012:role/AWSConfigRole",
    "recordingGroup": {
      "allSupported": true,
      "includeGlobalResourceTypes": true
    }
  }' \
  --region eu-west-2

echo "✓ Configuration recorder created"
echo ""

# Step 2: Create delivery channel
echo "[2/4] Creating delivery channel..."
aws configservice put-delivery-channel \
  --delivery-channel '{
    "name": "pharma-delivery",
    "s3BucketName": "pharma-config-logs-eu"
  }' \
  --region eu-west-2

echo "✓ Delivery channel created"
echo ""

# Step 3: Start configuration recorder
echo "[3/4] Starting configuration recorder..."
aws configservice start-configuration-recorder \
  --configuration-recorder-name pharma \
  --region eu-west-2

echo "✓ Configuration recorder started"
echo ""

# Step 4: Verify status
echo "[4/4] Verifying recorder status..."
aws configservice describe-configuration-recorder-status \
  --region eu-west-2

echo ""
echo "========================================="
echo "✓ AWS Config setup complete!"
echo "========================================="
