#!/bin/bash
# =============================================================================
# LocalStack SQS Queue Initialization Script
# =============================================================================
#
# Purpose: Create SQS queues for pharmaceutical test generation job processing
# Execution: Runs automatically in LocalStack container at startup
# Mount Point: /etc/localstack/init/ready.d/init.sh (LocalStack 3.x convention)
#
# Queues Created:
# 1. testgen-jobs     - Main job queue (15min visibility, 24h retention)
# 2. testgen-jobs-dlq - Dead-letter queue (14-day retention)
#
# GAMP-5 Category 5: Development environment (mock AWS SQS)
# ALCOA+ Principles: Not enforced (development only, no regulated data)
#
# =============================================================================

set -e  # Exit immediately on error
set -u  # Error on undefined variables

echo "=================================================="
echo "LocalStack SQS Queue Initialization"
echo "=================================================="
echo ""
echo "Region: eu-west-2 (London - production parity)"
echo "Account: 000000000000 (LocalStack default)"
echo ""

# Wait for LocalStack services to be fully ready (additional safety margin)
echo "[1/5] Waiting for LocalStack to initialize..."
sleep 3

# =============================================================================
# Create Main Job Queue
# =============================================================================
echo "[2/5] Creating main job queue: testgen-jobs"

if ! awslocal sqs create-queue \
    --queue-name testgen-jobs \
    --region eu-west-2 \
    --attributes \
        VisibilityTimeout=900,MessageRetentionPeriod=86400; then
    # Verify queue exists if creation failed
    if awslocal sqs get-queue-url --queue-name testgen-jobs --region eu-west-2 >/dev/null 2>&1; then
        echo "   Queue already exists (verified)"
    else
        echo "ERROR: Failed to create testgen-jobs queue and queue does not exist" >&2
        exit 1
    fi
else
    echo "   Queue created successfully"
fi

# Queue Attributes:
# - VisibilityTimeout=900 (15 minutes)
#   Duration that a message is hidden from other consumers after being received
#   Matches expected workflow processing time (~5-10 min + buffer)
#
# - MessageRetentionPeriod=86400 (24 hours)
#   How long messages are retained if not processed
#   Development: 1 day (production: 4 days per AWS migration plan)

# =============================================================================
# Create Dead-Letter Queue (DLQ)
# =============================================================================
echo "[3/5] Creating dead-letter queue: testgen-jobs-dlq"

if ! awslocal sqs create-queue \
    --queue-name testgen-jobs-dlq \
    --region eu-west-2 \
    --attributes \
        MessageRetentionPeriod=1209600; then
    # Verify queue exists if creation failed
    if awslocal sqs get-queue-url --queue-name testgen-jobs-dlq --region eu-west-2 >/dev/null 2>&1; then
        echo "   Queue already exists (verified)"
    else
        echo "ERROR: Failed to create testgen-jobs-dlq queue and queue does not exist" >&2
        exit 1
    fi
else
    echo "   Queue created successfully"
fi

# DLQ Attributes:
# - MessageRetentionPeriod=1209600 (14 days)
#   Failed messages retained for troubleshooting
#   Longer than main queue to prevent data loss during debugging

# =============================================================================
# Get Queue URLs and ARNs
# =============================================================================
echo "[4/5] Retrieving queue metadata..."

MAIN_QUEUE_URL=$(awslocal sqs get-queue-url \
    --queue-name testgen-jobs \
    --region eu-west-2 \
    --query 'QueueUrl' \
    --output text)

DLQ_URL=$(awslocal sqs get-queue-url \
    --queue-name testgen-jobs-dlq \
    --region eu-west-2 \
    --query 'QueueUrl' \
    --output text)

DLQ_ARN=$(awslocal sqs get-queue-attributes \
    --queue-url "$DLQ_URL" \
    --attribute-names QueueArn \
    --region eu-west-2 \
    --query 'Attributes.QueueArn' \
    --output text)

# =============================================================================
# Configure DLQ Redrive Policy
# =============================================================================
echo "[5/5] Configuring DLQ redrive policy..."

# Redrive Policy: Send messages to DLQ after 3 failed processing attempts
# maxReceiveCount=3: Move to DLQ after being received 3 times without deletion
# This prevents infinite retry loops for permanently failing jobs

if ! awslocal sqs set-queue-attributes \
    --queue-url "$MAIN_QUEUE_URL" \
    --region eu-west-2 \
    --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"; then
    # Check if redrive policy is already set
    EXISTING_POLICY=$(awslocal sqs get-queue-attributes \
        --queue-url "$MAIN_QUEUE_URL" \
        --attribute-names RedrivePolicy \
        --region eu-west-2 \
        --query 'Attributes.RedrivePolicy' \
        --output text 2>/dev/null || echo "")

    if [ -n "$EXISTING_POLICY" ] && [ "$EXISTING_POLICY" != "None" ]; then
        echo "   Redrive policy already configured (verified)"
    else
        echo "ERROR: Failed to set redrive policy and no existing policy found" >&2
        exit 1
    fi
else
    echo "   Redrive policy configured successfully"
fi

# =============================================================================
# Verification & Summary
# =============================================================================
echo ""
echo "=================================================="
echo "SQS Initialization Complete!"
echo "=================================================="
echo ""
echo "Main Queue:"
echo "  Name: testgen-jobs"
echo "  URL:  $MAIN_QUEUE_URL"
echo ""
echo "Dead-Letter Queue:"
echo "  Name: testgen-jobs-dlq"
echo "  URL:  $DLQ_URL"
echo "  ARN:  $DLQ_ARN"
echo ""
echo "Redrive Policy: maxReceiveCount=3"
echo ""

# List all queues in the region (should show both queues)
echo "All queues in eu-west-2:"
awslocal sqs list-queues --region eu-west-2 || true

echo ""
echo "=================================================="
echo "API/Worker containers can now connect to SQS!"
echo "=================================================="
echo ""
echo "Environment variables for containers:"
echo "  AWS_ENDPOINT_URL=http://localstack:4566"
echo "  SQS_QUEUE_URL=$MAIN_QUEUE_URL"
echo "  AWS_REGION=eu-west-2"
echo ""
