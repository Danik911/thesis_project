#!/bin/bash
# Setup EventBridge rule to keep Lambda warm
# Run: bash aws/scripts/5_setup_warmup.sh

set -e

FUNCTION_NAME="pharma-context-provider"
RULE_NAME="keep-lambda-warm"
REGION="eu-west-2"

echo "🔥 Setting up Lambda warm-up schedule"

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Configuration.FunctionArn' \
    --output text)

echo "📍 Lambda ARN: $LAMBDA_ARN"

# Create EventBridge rule (every 5 minutes)
echo "⏰ Creating EventBridge rule..."
aws events put-rule \
    --name $RULE_NAME \
    --description "Keep pharma Lambda warm" \
    --schedule-expression "rate(5 minutes)" \
    --region $REGION

# Get rule ARN
RULE_ARN=$(aws events describe-rule \
    --name $RULE_NAME \
    --region $REGION \
    --query 'Arn' \
    --output text)

# Add Lambda permission for EventBridge
echo "🔐 Adding Lambda permission..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id AllowEventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $RULE_ARN \
    --region $REGION 2>/dev/null || echo "Permission already exists"

# Add Lambda as target
echo "🎯 Adding Lambda target..."
aws events put-targets \
    --rule $RULE_NAME \
    --targets "Id=1,Arn=$LAMBDA_ARN" \
    --region $REGION

echo "✅ Warm-up configured!"
echo "   Rule: $RULE_NAME"
echo "   Schedule: Every 5 minutes"
echo "   Cost: ~$0.20/month"
echo ""
echo "To disable: aws events disable-rule --name $RULE_NAME --region $REGION"
