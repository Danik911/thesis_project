#!/bin/bash
# Deploy Context Provider Lambda function
# Run from project root: bash aws/scripts/3_deploy_lambda.sh

set -e

FUNCTION_NAME="pharma-context-provider"
REGION="eu-west-2"
ROLE_NAME="pharma-lambda-execution-role"
S3_BUCKET="pharma-vectors-eu"

echo "🚀 Deploying Lambda function: $FUNCTION_NAME"

# Get Layer ARN
if [ ! -f aws/lambda/layers/chromadb/layer_arn.txt ]; then
    echo "❌ Layer ARN not found. Run 2_create_lambda_layer.sh first"
    exit 1
fi
LAYER_ARN=$(cat aws/lambda/layers/chromadb/layer_arn.txt)
echo "📦 Using layer: $LAYER_ARN"

# Create IAM role if not exists
echo "🔐 Checking IAM role..."
if ! aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
    echo "Creating IAM role..."
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' \
        --region $REGION
    
    # Attach policies
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
    
    echo "⏳ Waiting for role to propagate..."
    sleep 10
fi

ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "✅ Role: $ROLE_ARN"

# Create deployment package
echo "📦 Creating deployment package..."
cd aws/lambda/context_provider
zip -r lambda.zip lambda_function.py requirements.txt -q
cd ../../../

# Deploy Lambda
echo "☁️  Deploying to AWS..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://aws/lambda/context_provider/lambda.zip \
        --region $REGION
    
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --layers $LAYER_ARN \
        --timeout 60 \
        --memory-size 1024 \
        --ephemeral-storage Size=1024 \
        --environment "Variables={S3_BUCKET=$S3_BUCKET,S3_KEY=chroma_db.tar.gz}" \
        --region $REGION
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.12 \
        --role $ROLE_ARN \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://aws/lambda/context_provider/lambda.zip \
        --timeout 60 \
        --memory-size 1024 \
        --ephemeral-storage Size=1024 \
        --layers $LAYER_ARN \
        --environment "Variables={S3_BUCKET=$S3_BUCKET,S3_KEY=chroma_db.tar.gz}" \
        --region $REGION
fi

# Clean up
rm aws/lambda/context_provider/lambda.zip

echo "✅ Lambda deployed successfully!"
echo "   Function: $FUNCTION_NAME"
echo "   Region: $REGION"

# Test invocation
echo ""
echo "🧪 Testing Lambda..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"source":"aws.events"}' \
    --region $REGION \
    response.json

cat response.json
rm response.json

echo ""
echo "✅ Done!"
