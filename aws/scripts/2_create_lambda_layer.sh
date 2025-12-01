#!/bin/bash
# Create Lambda layer with ChromaDB
# Run from project root: bash aws/scripts/2_create_lambda_layer.sh

set -e

LAYER_NAME="chromadb-layer"
REGION="eu-west-2"
PYTHON_VERSION="3.12"

echo "🚀 Creating Lambda layer: $LAYER_NAME"

# Create layer directory
mkdir -p aws/lambda/layers/chromadb/python
cd aws/lambda/layers/chromadb

# Install ChromaDB and dependencies
echo "📦 Installing ChromaDB..."
pip install \
    chromadb==0.4.22 \
    --target python/ \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version $PYTHON_VERSION

# Remove unnecessary files to reduce size
echo "🧹 Cleaning up..."
find python/ -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find python/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find python/ -name "*.pyc" -delete
find python/ -name "*.pyo" -delete

# Check size
SIZE=$(du -sh python/ | cut -f1)
echo "📊 Layer size: $SIZE"

# Create zip
echo "📦 Creating layer zip..."
zip -r chromadb-layer.zip python/ -q

# Upload to AWS
echo "☁️  Publishing layer to AWS..."
LAYER_ARN=$(aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --description "ChromaDB for pharmaceutical RAG system" \
    --zip-file fileb://chromadb-layer.zip \
    --compatible-runtimes python$PYTHON_VERSION \
    --region $REGION \
    --query 'LayerVersionArn' \
    --output text)

echo "✅ Layer published: $LAYER_ARN"
echo "$LAYER_ARN" > layer_arn.txt

# Clean up
rm chromadb-layer.zip
cd ../../../../

echo "✅ Done! Layer ARN saved to aws/lambda/layers/chromadb/layer_arn.txt"
