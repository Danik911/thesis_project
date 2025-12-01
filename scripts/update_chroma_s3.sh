#!/bin/bash
# Update ChromaDB with new regulatory documents and deploy to S3

set -e

echo "=== ChromaDB Update & Deploy ==="

# 1. Rebuild ChromaDB locally
echo "[1/4] Rebuilding ChromaDB..."
docker exec pharma-api-dev python /app/main/scripts/ingest-documents.py

# 2. Extract ChromaDB from container
echo "[2/4] Extracting ChromaDB from container..."
docker cp pharma-api-dev:/app/chroma_db ./chroma_db_temp

# 3. Compress and upload to S3
echo "[3/4] Uploading to S3..."
VERSION=$(date +%Y%m%d-%H%M%S)
tar -czf chroma_db.tar.gz -C chroma_db_temp .
aws s3 cp chroma_db.tar.gz s3://pharma-vectors-eu/ \
  --metadata version=$VERSION \
  --region eu-west-2

# 4. Restart ECS worker (downloads new tarball)
echo "[4/4] Restarting ECS worker..."
aws ecs update-service \
  --cluster pharma-cluster \
  --service pharma-worker \
  --force-new-deployment \
  --region eu-west-2

# Cleanup
rm -rf chroma_db_temp chroma_db.tar.gz

echo "✅ ChromaDB updated to version $VERSION"
echo "   Worker will download new version on next restart (~30s)"
