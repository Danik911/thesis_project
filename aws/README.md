# AWS Lambda + ChromaDB Deployment Guide

## 🎯 Overview

This directory contains scripts and code to deploy your ChromaDB-based Context Provider Agent to AWS Lambda.

## 📁 Structure

```
aws/
├── lambda/
│   └── context_provider/
│       ├── lambda_function.py      # Lambda handler
│       └── requirements.txt        # Dependencies
├── scripts/
│   ├── 1_upload_chroma_to_s3.py   # Upload ChromaDB to S3
│   ├── 2_create_lambda_layer.sh   # Create ChromaDB layer
│   ├── 3_deploy_lambda.sh         # Deploy Lambda function
│   ├── 4_test_lambda.py           # Test deployment
│   └── 5_setup_warmup.sh          # Configure warm-up schedule
└── README.md                       # This file
```

## 🚀 Deployment Steps

### Prerequisites

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# Enter: Access Key, Secret Key, Region (eu-central-1), Output (json)

# Install boto3
pip install boto3
```

### Step 1: Upload ChromaDB to S3

```bash
# From project root
python aws/scripts/1_upload_chroma_to_s3.py
```

**What it does:**
- Creates tarball of `chroma_db/` directory
- Uploads to S3 bucket `pharma-vectors-eu`
- Enables versioning and encryption

**Output:**
```
✅ Uploaded to s3://pharma-vectors-eu/chroma_db.tar.gz
```

### Step 2: Create Lambda Layer

```bash
# Run in WSL/Linux (not Windows PowerShell)
bash aws/scripts/2_create_lambda_layer.sh
```

**What it does:**
- Installs ChromaDB and dependencies
- Creates Lambda layer zip (~150 MB)
- Publishes to AWS Lambda

**Output:**
```
✅ Layer published: arn:aws:lambda:eu-central-1:ACCOUNT:layer:chromadb-layer:1
```

### Step 3: Deploy Lambda Function

```bash
bash aws/scripts/3_deploy_lambda.sh
```

**What it does:**
- Creates IAM role with S3 read permissions
- Deploys Lambda function
- Attaches ChromaDB layer
- Configures environment variables

**Output:**
```
✅ Lambda deployed successfully!
   Function: pharma-context-provider
   Region: eu-central-1
```

### Step 4: Test Deployment

```bash
python aws/scripts/4_test_lambda.py
```

**Expected output:**
```
✅ Status: 200
📄 Found 5 documents

1. Distance: 0.2341
   Metadata: {'category': 'GAMP-5', 'page': 42}
   Preview: GAMP 5 Category 5 software requires...
```

### Step 5: Setup Warm-Up (Optional)

```bash
bash aws/scripts/5_setup_warmup.sh
```

**What it does:**
- Creates EventBridge rule (every 5 minutes)
- Keeps Lambda warm (reduces cold starts)
- Cost: ~$0.20/month

## 🔧 Integration with Your Code

### Option 1: Use Lambda Backend

```python
# main/src/core/unified_workflow.py
from src.agents.parallel.context_provider_lambda import LambdaContextProvider

# Replace local ChromaDB
context_provider = LambdaContextProvider(
    function_name="pharma-context-provider",
    region="eu-central-1"
)

# Query context
contexts = context_provider.get_gamp5_context(
    "What are Category 5 validation requirements?"
)
```

### Option 2: Environment-Based Switching

```python
import os
from src.agents.parallel.context_provider_lambda import ContextProviderAgent

# Automatically uses Lambda if AWS credentials available
use_lambda = os.environ.get('USE_LAMBDA', 'true').lower() == 'true'
context_provider = ContextProviderAgent(use_lambda=use_lambda)

# Same API for both local and Lambda
contexts = context_provider.get_context("GAMP-5 requirements")
```

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Cold Start** | 400-700ms |
| **Warm Start** | 10-20ms |
| **Memory Usage** | ~200 MB |
| **Cost (1000 invocations/month)** | ~$2 |
| **S3 Storage** | $0.12/month |

## 🔒 Security Configuration

### IAM Role Permissions

The Lambda function has:
- ✅ S3 read access (download ChromaDB)
- ✅ CloudWatch Logs (monitoring)
- ❌ No write permissions (read-only)

### S3 Bucket Security

- ✅ Versioning enabled (audit trail)
- ✅ AES-256 encryption at rest
- ✅ Private (no public access)

## 🐛 Troubleshooting

### Issue: "Layer too large"

```bash
# Check layer size
du -sh aws/lambda/layers/chromadb/python/
# Should be < 250 MB

# If too large, remove test files
find aws/lambda/layers/chromadb/python/ -name "tests" -exec rm -rf {} +
```

### Issue: "ChromaDB not found in /tmp/"

```bash
# Verify S3 upload
aws s3 ls s3://pharma-vectors-eu/chroma_db.tar.gz

# Check Lambda logs
aws logs tail /aws/lambda/pharma-context-provider --follow
```

### Issue: "Cold starts too slow"

```bash
# Enable warm-up schedule
bash aws/scripts/5_setup_warmup.sh

# Or use provisioned concurrency (more expensive)
aws lambda put-provisioned-concurrency-config \
    --function-name pharma-context-provider \
    --provisioned-concurrent-executions 1
```

## 💰 Cost Breakdown

```yaml
Monthly Costs (Low Traffic):
  - Lambda compute: $1.67 (1000 invocations, 1024 MB)
  - S3 storage: $0.12 (5 GB)
  - EventBridge warm-up: $0.20 (8640 invocations)
  - Data transfer: $0.01 (negligible)
  Total: ~$2/month
```

## 🔄 Updating ChromaDB

When you add new regulatory documents:

```bash
# 1. Update local ChromaDB
python main/scripts/index_documents.py

# 2. Re-upload to S3
python aws/scripts/1_upload_chroma_to_s3.py

# 3. Lambda will automatically use new version on next cold start
# Or force refresh:
aws lambda update-function-configuration \
    --function-name pharma-context-provider \
    --environment "Variables={S3_BUCKET=pharma-vectors-eu,S3_KEY=chroma_db.tar.gz,REFRESH=$(date +%s)}"
```

## 📚 Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Lambda Layers Guide](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)

## 🆘 Support

For issues, check:
1. CloudWatch Logs: `/aws/lambda/pharma-context-provider`
2. Lambda metrics: AWS Console → Lambda → Monitoring
3. S3 bucket: `s3://pharma-vectors-eu/`
