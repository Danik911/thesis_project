#!/bin/bash
# Verify Task 0.2 Status - CloudTrail and AWS Config

set -e

REGION="eu-west-2"

echo "=========================================="
echo "Task 0.2 Status Verification"
echo "=========================================="
echo ""

# ============================================
# Part 1: CloudTrail Verification
# ============================================
echo "🔍 Checking CloudTrail status..."
echo ""

# Check if trail exists
TRAIL_STATUS=$(aws cloudtrail describe-trails --region $REGION --query 'trailList[?Name==`pharma-trail`]' --output json 2>/dev/null || echo "[]")

if [ "$TRAIL_STATUS" = "[]" ]; then
    echo "❌ CloudTrail trail 'pharma-trail' NOT found"
    CLOUDTRAIL_EXISTS=false
else
    echo "✅ CloudTrail trail 'pharma-trail' exists"
    CLOUDTRAIL_EXISTS=true

    # Get trail details
    echo ""
    echo "Trail Details:"
    aws cloudtrail describe-trails --region $REGION --query 'trailList[?Name==`pharma-trail`].[Name,S3BucketName,IsMultiRegionTrail,IncludeGlobalServiceEvents]' --output table
fi

echo ""

# Check if CloudTrail is logging
if [ "$CLOUDTRAIL_EXISTS" = true ]; then
    LOGGING_STATUS=$(aws cloudtrail get-trail-status --name pharma-trail --region $REGION --query 'IsLogging' --output text 2>/dev/null || echo "false")

    if [ "$LOGGING_STATUS" = "True" ]; then
        echo "✅ CloudTrail is actively logging"

        # Get last delivery time
        LAST_DELIVERY=$(aws cloudtrail get-trail-status --name pharma-trail --region $REGION --query 'LatestDeliveryTime' --output text 2>/dev/null || echo "N/A")
        echo "   Last log delivery: $LAST_DELIVERY"
    else
        echo "⚠️  CloudTrail trail exists but is NOT logging"
    fi
fi

echo ""
echo "=========================================="

# ============================================
# Part 2: AWS Config Verification
# ============================================
echo "🔍 Checking AWS Config status..."
echo ""

# Check if configuration recorder exists
RECORDER_STATUS=$(aws configservice describe-configuration-recorders --region $REGION --query 'ConfigurationRecorders[?name==`pharma`]' --output json 2>/dev/null || echo "[]")

if [ "$RECORDER_STATUS" = "[]" ]; then
    echo "❌ AWS Config recorder 'pharma' NOT found"
    CONFIG_RECORDER_EXISTS=false
else
    echo "✅ AWS Config recorder 'pharma' exists"
    CONFIG_RECORDER_EXISTS=true

    # Get recorder details
    echo ""
    echo "Recorder Details:"
    aws configservice describe-configuration-recorders --region $REGION --query 'ConfigurationRecorders[?name==`pharma`].[name,roleArn]' --output table
fi

echo ""

# Check if Config recorder is recording
if [ "$CONFIG_RECORDER_EXISTS" = true ]; then
    RECORDING_STATUS=$(aws configservice describe-configuration-recorder-status --region $REGION --query 'ConfigurationRecordersStatus[?name==`pharma`].recording' --output text 2>/dev/null || echo "false")

    if [ "$RECORDING_STATUS" = "True" ]; then
        echo "✅ AWS Config is actively recording"

        # Get last status
        LAST_STATUS=$(aws configservice describe-configuration-recorder-status --region $REGION --query 'ConfigurationRecordersStatus[?name==`pharma`].[lastStatus,lastStartTime,lastStopTime]' --output table 2>/dev/null)
        echo ""
        echo "Recording Status:"
        echo "$LAST_STATUS"
    else
        echo "⚠️  AWS Config recorder exists but is NOT recording"
    fi
fi

echo ""

# Check if delivery channel exists
CHANNEL_STATUS=$(aws configservice describe-delivery-channels --region $REGION --query 'DeliveryChannels[?name==`pharma-delivery`]' --output json 2>/dev/null || echo "[]")

if [ "$CHANNEL_STATUS" = "[]" ]; then
    echo "❌ AWS Config delivery channel 'pharma-delivery' NOT found"
else
    echo "✅ AWS Config delivery channel 'pharma-delivery' exists"

    echo ""
    echo "Delivery Channel Details:"
    aws configservice describe-delivery-channels --region $REGION --query 'DeliveryChannels[?name==`pharma-delivery`].[name,s3BucketName]' --output table
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

# Generate summary
CLOUDTRAIL_DONE=false
CONFIG_DONE=false

if [ "$CLOUDTRAIL_EXISTS" = true ] && [ "$LOGGING_STATUS" = "True" ]; then
    echo "✅ CloudTrail: COMPLETE (trail exists and logging)"
    CLOUDTRAIL_DONE=true
else
    echo "❌ CloudTrail: INCOMPLETE"
fi

if [ "$CONFIG_RECORDER_EXISTS" = true ] && [ "$RECORDING_STATUS" = "True" ]; then
    echo "✅ AWS Config: COMPLETE (recorder exists and recording)"
    CONFIG_DONE=true
else
    echo "❌ AWS Config: INCOMPLETE"
fi

echo ""

# Overall status
if [ "$CLOUDTRAIL_DONE" = true ] && [ "$CONFIG_DONE" = true ]; then
    echo "📊 Task 0.2 Status: ✅ COMPLETE"
elif [ "$CLOUDTRAIL_DONE" = true ] || [ "$CONFIG_DONE" = true ]; then
    echo "📊 Task 0.2 Status: ⏸️  PARTIAL"
else
    echo "📊 Task 0.2 Status: ❌ NOT STARTED"
fi

echo ""
echo "=========================================="
