# Context Collector Result - 2025-12-06T14:30:00

## Agent Configuration
- Agent: context-collector
- Task ID: Ad-hoc research (AWS rate limiting and usage quotas)
- Invoked: 2025-12-06T14:30:00
- Duration: 25 minutes
- Status: SUCCESS

## Task Understanding

User requested comprehensive research on AWS rate limiting and usage quota mechanisms for their ECS/SQS/API Gateway-based pharmaceutical test generation system. The goal is to implement:

1. Request throttling at API layer (per second/per day)
2. Job submission limits (daily quotas per user/organization)
3. Cost control through usage budgets
4. Compliance-friendly audit trails (GAMP-5, ALCOA+)

**Current Architecture**: ECS Fargate (API + Worker + Frontend) → CloudFront → ALB → No API Gateway currently deployed

**Key Requirement**: All rate limiting must be auditable and traceable for pharmaceutical compliance.

---

## Research Findings

### 1. AWS WAF Rate-Based Rules (PRIMARY RECOMMENDATION)

**Best fit for current architecture**: Attach AWS WAF to existing CloudFront distribution and ALBs.

#### Capabilities
- **Rate limiting**: 100-20,000,000 requests per 5 minutes (configurable)
- **Scope**: Per IP, per session, per custom header (e.g., user ID, API key)
- **Actions**: Block (429 Too Many Requests), count (monitor mode), challenge (CAPTCHA)
- **Audit**: CloudWatch Logs, S3, Kinesis Data Firehose

#### Terraform Configuration Example

```hcl
# aws/terraform/modules/waf/main.tf
resource "aws_wafv2_web_acl" "rate_limiter" {
  name  = "${var.project_name}-rate-limiter"
  scope = "CLOUDFRONT"  # Use "REGIONAL" for ALB

  default_action {
    allow {}
  }

  # Rule 1: Global rate limit (100 requests per 5 minutes per IP)
  rule {
    name     = "GlobalRateLimit"
    priority = 1

    action {
      block {
        custom_response {
          response_code = 429
          custom_response_body_key = "rate_limit_exceeded"
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = 100  # Requests per 5 minutes
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "GlobalRateLimit"
      sampled_requests_enabled   = true
    }
  }

  # Rule 2: API endpoint rate limit (10 requests per 5 minutes per user)
  rule {
    name     = "APIEndpointRateLimit"
    priority = 2

    action {
      block {
        custom_response {
          response_code = 429
          custom_response_body_key = "api_rate_limit_exceeded"
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = 10
        aggregate_key_type = "CUSTOM_KEYS"

        custom_key {
          header {
            name = "x-user-id"
            text_transformation {
              priority = 0
              type     = "LOWERCASE"
            }
          }
        }

        scope_down_statement {
          byte_match_statement {
            field_to_match {
              uri_path {}
            }
            positional_constraint = "STARTS_WITH"
            search_string         = "/jobs"
            text_transformation {
              priority = 0
              type     = "LOWERCASE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "APIEndpointRateLimit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "RateLimiterWebACL"
    sampled_requests_enabled   = true
  }

  tags = {
    GAMP5       = "true"
    Compliance  = "rate-limiting"
  }
}

# Associate WAF with CloudFront
resource "aws_wafv2_web_acl_association" "cloudfront" {
  resource_arn = var.cloudfront_distribution_arn
  web_acl_arn  = aws_wafv2_web_acl.rate_limiter.arn
}

# Custom response bodies
resource "aws_wafv2_web_acl_logging_configuration" "rate_limiter" {
  resource_arn = aws_wafv2_web_acl.rate_limiter.arn

  log_destination_configs = [aws_cloudwatch_log_group.waf_logs.arn]

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }
}

resource "aws_cloudwatch_log_group" "waf_logs" {
  name              = "/aws/waf/${var.project_name}"
  retention_in_days = 90  # GAMP-5 audit requirement

  tags = {
    GAMP5 = "true"
  }
}
```

#### Pros
- Native AWS service, no application code changes
- Automatic CloudWatch metrics for monitoring
- Works with existing CloudFront + ALB architecture
- Per-IP, per-user, per-session aggregation
- No additional compute costs (WAF pricing only)

#### Cons
- Minimum 5-minute window (not per-second granularity)
- Limited to HTTP request attributes (headers, IP, URI)
- WAF costs: $5/month + $1/million requests

#### Sources
- https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html
- https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/WAF-one-click-rate-limiting.html

---

### 2. AWS API Gateway Throttling (ALTERNATIVE - NEW LAYER)

**Use if**: Adding API Gateway as new layer in front of ALB or replacing ALB entirely.

#### Capabilities
- **Account-level**: 10,000 RPS (burst: 5,000 RPS) - default, adjustable
- **Stage-level**: Custom per-stage throttling
- **Method-level**: Per-endpoint throttling
- **Usage Plans**: Per-API-key quotas (daily, weekly, monthly)

#### Terraform Configuration Example

```hcl
# aws/terraform/modules/api-gateway/main.tf
resource "aws_api_gateway_rest_api" "pharma_api" {
  name        = "${var.project_name}-api"
  description = "Pharmaceutical test generation API with throttling"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_stage" "production" {
  deployment_id = aws_api_gateway_deployment.production.id
  rest_api_id   = aws_api_gateway_rest_api.pharma_api.id
  stage_name    = "production"

  # Stage-level throttling
  throttle_settings {
    burst_limit = 100   # Max concurrent requests
    rate_limit  = 50    # Requests per second
  }
}

# Usage plan with daily quota
resource "aws_api_gateway_usage_plan" "basic_tier" {
  name        = "basic-tier"
  description = "Basic tier: 100 requests/day"

  api_stages {
    api_id = aws_api_gateway_rest_api.pharma_api.id
    stage  = aws_api_gateway_stage.production.stage_name
  }

  quota_settings {
    limit  = 100     # 100 requests per day
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 10   # Max concurrent requests
    rate_limit  = 5    # Requests per second
  }
}

resource "aws_api_gateway_usage_plan" "premium_tier" {
  name        = "premium-tier"
  description = "Premium tier: 1000 requests/day"

  api_stages {
    api_id = aws_api_gateway_rest_api.pharma_api.id
    stage  = aws_api_gateway_stage.production.stage_name
  }

  quota_settings {
    limit  = 1000
    period = "DAY"
  }

  throttle_settings {
    burst_limit = 50
    rate_limit  = 25
  }
}

# API Key for user
resource "aws_api_gateway_api_key" "user_key" {
  name        = "user-${var.user_id}"
  description = "API key for user ${var.user_id}"
  enabled     = true
}

resource "aws_api_gateway_usage_plan_key" "user_basic" {
  key_id        = aws_api_gateway_api_key.user_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.basic_tier.id
}

# CloudWatch logging for compliance
resource "aws_api_gateway_account" "api_gateway_account" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.pharma_api.id
  stage_name  = aws_api_gateway_stage.production.stage_name
  method_path = "*/*"

  settings {
    logging_level      = "INFO"
    data_trace_enabled = true
    metrics_enabled    = true

    # Method-level throttling (override stage settings)
    throttling_burst_limit = 20
    throttling_rate_limit  = 10
  }
}
```

#### Monitoring Usage via boto3

```python
# main/api/monitoring/api_gateway_quotas.py
import boto3
from datetime import datetime, timedelta

def check_usage_plan_quota(api_key_id: str, usage_plan_id: str) -> dict:
    """
    Check remaining quota for a user's API key.
    Returns current usage and remaining quota.
    """
    client = boto3.client('apigateway', region_name='eu-west-2')

    # Get usage data
    today = datetime.now().date()
    response = client.get_usage(
        usagePlanId=usage_plan_id,
        keyId=api_key_id,
        startDate=today.strftime('%Y-%m-%d'),
        endDate=today.strftime('%Y-%m-%d')
    )

    # Parse usage
    quota_limit = response['quota']['limit']
    quota_remaining = response['quota']['remaining']
    quota_used = quota_limit - quota_remaining

    return {
        'quota_limit': quota_limit,
        'quota_used': quota_used,
        'quota_remaining': quota_remaining,
        'period': response['quota']['period'],
        'percentage_used': (quota_used / quota_limit) * 100 if quota_limit > 0 else 0
    }

# Example: Check before submitting job
def can_submit_job(user_id: str) -> bool:
    """
    Check if user has quota remaining to submit a job.
    Logs check for GAMP-5 audit trail.
    """
    from main.utils.langfuse_client import langfuse

    api_key_id = get_api_key_for_user(user_id)
    usage_plan_id = get_usage_plan_for_user(user_id)

    quota_info = check_usage_plan_quota(api_key_id, usage_plan_id)

    # Log to LangFuse for audit trail
    langfuse.score(
        name="quota_check",
        value=quota_info['quota_remaining'],
        data_type="NUMERIC",
        comment=f"User {user_id} has {quota_info['quota_remaining']} requests remaining"
    )

    if quota_info['quota_remaining'] <= 0:
        # FAIL LOUDLY - no fallback
        raise QuotaExceededException(
            f"User {user_id} has exceeded daily quota. "
            f"Used: {quota_info['quota_used']}/{quota_info['quota_limit']}"
        )

    return True
```

#### Pros
- Built-in usage plans with daily/weekly/monthly quotas
- Per-API-key tracking (user-level quotas)
- Native CloudWatch metrics and X-Ray tracing
- Automatic 429 responses when quota exceeded
- Free tier: 1 million requests/month

#### Cons
- **Architectural change**: New layer between CloudFront and ALB
- Additional latency (~10-20ms)
- Requires API key distribution to users
- Costs: $3.50 per million requests (REST API)

#### Sources
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-create-usage-plans.html

---

### 3. Application-Level Rate Limiting (FastAPI SlowAPI)

**Use for**: Fine-grained per-endpoint, per-user rate limiting with custom business logic.

#### Implementation with SlowAPI + Redis

```bash
# Install SlowAPI
uv add slowapi redis
```

```python
# main/api/middleware/rate_limiter.py
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis

# Redis backend for distributed rate limiting
redis_client = redis.Redis(
    host='your-elasticache-endpoint.cache.amazonaws.com',
    port=6379,
    db=0,
    decode_responses=True
)

def get_user_id_from_request(request: Request) -> str:
    """
    Extract user ID from Clerk JWT token.
    Falls back to IP address if not authenticated.
    """
    # Extract from Clerk JWT
    user_id = request.state.user_id if hasattr(request.state, 'user_id') else None

    if not user_id:
        # FAIL LOUDLY - no fallback
        raise ValueError(
            f"Rate limiting requires authenticated user. "
            f"Request from {request.client.host} has no user_id."
        )

    return user_id

# Initialize limiter with Redis storage
limiter = Limiter(
    key_func=get_user_id_from_request,
    storage_uri=f"redis://{redis_client.connection_pool.connection_kwargs['host']}:6379",
    strategy="fixed-window"  # Options: fixed-window, moving-window
)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits to endpoints
@app.post("/jobs")
@limiter.limit("10/minute")  # 10 requests per minute per user
@limiter.limit("100/day")    # 100 requests per day per user
async def submit_job(request: Request, job_data: dict):
    """
    Submit test generation job.
    Rate limited to 10/min and 100/day per user.
    """
    from main.utils.langfuse_client import langfuse

    user_id = request.state.user_id

    # Log rate limit check to LangFuse (GAMP-5 audit trail)
    langfuse.score(
        name="rate_limit_check",
        value=1,  # Passed rate limit
        data_type="NUMERIC",
        comment=f"User {user_id} passed rate limit check for /jobs endpoint"
    )

    # Process job submission
    return {"status": "accepted", "job_id": "..."}

# Custom daily quota check
from datetime import datetime, timedelta

async def check_daily_quota(user_id: str, limit: int = 100) -> bool:
    """
    Check if user has exceeded daily quota using Redis.
    Returns True if under quota, raises exception if exceeded.
    """
    today = datetime.now().date().isoformat()
    redis_key = f"quota:{user_id}:{today}"

    current_count = redis_client.get(redis_key)

    if current_count is None:
        # First request of the day
        redis_client.setex(redis_key, timedelta(days=1), 1)
        return True

    current_count = int(current_count)

    if current_count >= limit:
        # FAIL LOUDLY - no fallback
        raise QuotaExceededException(
            f"User {user_id} has exceeded daily quota. "
            f"Used: {current_count}/{limit}"
        )

    # Increment counter
    redis_client.incr(redis_key)
    return True
```

#### SlowAPI Rate Limit Strategies

```python
# Fixed Window: Simple counter reset at interval boundaries
@limiter.limit("100/hour", strategy="fixed-window")

# Moving Window: More accurate, prevents burst at boundary
@limiter.limit("100/hour", strategy="moving-window")

# Multiple limits on same endpoint
@limiter.limit("10/second")  # Burst protection
@limiter.limit("100/minute")  # Short-term limit
@limiter.limit("1000/hour")   # Medium-term limit
@limiter.limit("5000/day")    # Daily quota
async def high_volume_endpoint(request: Request):
    pass
```

#### Pros
- Full control over rate limiting logic
- Per-user, per-endpoint, per-method granularity
- Custom business rules (e.g., premium users get higher limits)
- Integrates with existing Clerk authentication
- Distributed via Redis (works across multiple ECS tasks)

#### Cons
- Requires application code changes
- Redis dependency (ElastiCache cost: ~$15/month for cache.t3.micro)
- Must handle Redis failures (no fallback - fail loudly)
- Not infrastructure-level protection (malicious traffic still reaches app)

#### Sources
- https://github.com/laurentS/slowapi
- https://slowapi.readthedocs.io/

---

### 4. SQS Message Quotas and Visibility Timeout

**Current Setup**: SQS queue for worker jobs (`pharma-test-gen-worker-jobs`)

#### Key Quotas
- **Inflight messages**: 120,000 messages max (standard queue)
- **Visibility timeout**: 0 seconds - 12 hours
- **Message retention**: 1 minute - 14 days
- **Message size**: 256 KB max
- **Batch size**: 10 messages per `ReceiveMessage` call

#### Limiting Job Submissions via SQS Attributes

```python
# main/api/routes/jobs.py
import boto3
from fastapi import HTTPException

def check_queue_depth_before_submit(queue_url: str, max_depth: int = 10000) -> bool:
    """
    Check SQS queue depth before accepting new job submission.
    Prevents overwhelming worker with too many jobs.
    """
    sqs = boto3.client('sqs', region_name='eu-west-2')

    response = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
    )

    visible_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    inflight_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
    total_messages = visible_messages + inflight_messages

    if total_messages >= max_depth:
        # FAIL LOUDLY - no fallback
        raise HTTPException(
            status_code=503,
            detail=f"Queue depth exceeded. Current: {total_messages}/{max_depth}. "
                   f"Please try again later."
        )

    return True

@app.post("/jobs")
async def submit_job(job_data: dict):
    queue_url = os.environ['SQS_QUEUE_URL']

    # Check queue depth
    check_queue_depth_before_submit(queue_url, max_depth=10000)

    # Submit to SQS
    sqs = boto3.client('sqs', region_name='eu-west-2')
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(job_data)
    )

    return {"status": "queued"}
```

#### Terraform Configuration for SQS Limits

```hcl
# aws/terraform/modules/sqs/main.tf (already exists, enhancements)
resource "aws_sqs_queue" "worker_jobs" {
  name                       = "${var.queue_name}"
  visibility_timeout_seconds = var.visibility_timeout_seconds  # 900 (15 min)
  message_retention_seconds  = 86400   # 1 day
  receive_wait_time_seconds  = 10      # Long polling
  max_message_size           = 262144  # 256 KB

  # Redrive policy: Move to DLQ after 3 failed attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    GAMP5 = "true"
  }
}

# CloudWatch alarm for queue depth
resource "aws_cloudwatch_metric_alarm" "queue_depth" {
  alarm_name          = "${var.queue_name}-depth-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 5000  # Alert at 5k messages
  alarm_description   = "Alert when SQS queue depth exceeds 5k messages"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.worker_jobs.name
  }

  alarm_actions = [var.sns_alarm_topic_arn]
}
```

#### Sources
- https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html
- https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html

---

### 5. Daily Quota Tracking with DynamoDB Atomic Counters

**Best for**: High-throughput, low-latency daily quota tracking with strong consistency.

#### DynamoDB Table Design

```hcl
# aws/terraform/modules/dynamodb/quotas.tf
resource "aws_dynamodb_table" "user_quotas" {
  name         = "${var.project_name}-user-quotas"
  billing_mode = "PAY_PER_REQUEST"  # On-demand pricing
  hash_key     = "user_id"
  range_key    = "date"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"  # Format: "2025-12-06"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true  # GAMP-5 requirement
  }

  server_side_encryption {
    enabled = true  # GAMP-5 requirement
  }

  tags = {
    GAMP5 = "true"
  }
}
```

#### Python Implementation with Atomic Counters

```python
# main/api/services/quota_tracker.py
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('pharma-test-gen-user-quotas')

def increment_user_quota(user_id: str, limit: int = 100) -> dict:
    """
    Atomically increment user's daily quota counter.
    Returns current count and remaining quota.
    Raises QuotaExceededException if limit exceeded.
    """
    from main.utils.langfuse_client import langfuse

    today = datetime.now().date().isoformat()
    ttl = int((datetime.now() + timedelta(days=7)).timestamp())  # Auto-delete after 7 days

    try:
        # Atomic increment with conditional check
        response = table.update_item(
            Key={
                'user_id': user_id,
                'date': today
            },
            UpdateExpression='ADD request_count :inc SET #ttl = :ttl',
            ExpressionAttributeNames={
                '#ttl': 'ttl'
            },
            ExpressionAttributeValues={
                ':inc': 1,
                ':ttl': ttl,
                ':limit': limit
            },
            ConditionExpression='attribute_not_exists(request_count) OR request_count < :limit',
            ReturnValues='ALL_NEW'
        )

        current_count = response['Attributes']['request_count']
        remaining = limit - current_count

        # Log to LangFuse for audit trail
        langfuse.score(
            name="quota_increment",
            value=current_count,
            data_type="NUMERIC",
            comment=f"User {user_id} quota: {current_count}/{limit}"
        )

        return {
            'user_id': user_id,
            'date': today,
            'current_count': current_count,
            'limit': limit,
            'remaining': remaining
        }

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # User has exceeded quota - FAIL LOUDLY
            current = get_user_quota(user_id)
            raise QuotaExceededException(
                f"User {user_id} has exceeded daily quota. "
                f"Used: {current['request_count']}/{limit}"
            )
        else:
            # Unexpected error - FAIL LOUDLY
            raise RuntimeError(
                f"DynamoDB error for user {user_id}: {e.response['Error']['Message']}"
            )

def get_user_quota(user_id: str) -> dict:
    """
    Get current quota usage for user.
    Returns 0 if no record exists (first request of the day).
    """
    today = datetime.now().date().isoformat()

    response = table.get_item(
        Key={
            'user_id': user_id,
            'date': today
        }
    )

    if 'Item' not in response:
        return {
            'user_id': user_id,
            'date': today,
            'request_count': 0
        }

    return response['Item']

# FastAPI integration
from fastapi import Depends, HTTPException

async def check_user_quota(user_id: str = Depends(get_current_user_id)):
    """
    Dependency to check user quota before processing request.
    """
    try:
        quota_info = increment_user_quota(user_id, limit=100)
        return quota_info
    except QuotaExceededException as e:
        raise HTTPException(status_code=429, detail=str(e))

@app.post("/jobs")
async def submit_job(
    job_data: dict,
    quota_info: dict = Depends(check_user_quota)
):
    """
    Submit job with quota check.
    """
    return {
        "status": "accepted",
        "quota_remaining": quota_info['remaining']
    }
```

#### Cost Analysis
- **DynamoDB**: $1.25 per million write requests (on-demand)
- **Example**: 10k users × 100 requests/day = 1M writes/day = $1.25/day = $37.50/month
- **Alternative**: Provisioned capacity (1 WCU = $0.47/month) if predictable load

#### Pros
- Atomic counters (no race conditions)
- Strong consistency guarantees
- Auto-scaling (on-demand mode)
- TTL for automatic cleanup
- Point-in-time recovery for compliance

#### Cons
- Additional AWS service dependency
- Latency: ~5-10ms per request
- Costs scale with request volume

#### Sources
- https://aws.amazon.com/blogs/database/implement-resource-counters-with-amazon-dynamodb/
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html#WorkingWithItems.AtomicCounters

---

### 6. Daily Quota Tracking with Aurora PostgreSQL

**Alternative to DynamoDB**: Use existing Aurora database (if deploying Task 4.2).

#### PostgreSQL Table Schema

```sql
-- Aurora PostgreSQL table for user quotas
CREATE TABLE user_quotas (
    user_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    request_count INTEGER NOT NULL DEFAULT 0,
    quota_limit INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, date)
);

-- Index for efficient queries
CREATE INDEX idx_user_quotas_date ON user_quotas(date);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_quotas_updated_at BEFORE UPDATE
    ON user_quotas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### Python Implementation with Aurora Data API

```python
# main/api/services/quota_tracker_aurora.py
import boto3
from datetime import datetime

rds_data = boto3.client('rds-data', region_name='eu-west-2')

def increment_user_quota_aurora(
    user_id: str,
    limit: int = 100,
    cluster_arn: str = None,
    secret_arn: str = None,
    database: str = 'pharma_test_gen'
) -> dict:
    """
    Atomically increment user's daily quota using Aurora Data API.
    Uses INSERT ... ON CONFLICT for upsert with atomic increment.
    """
    from main.utils.langfuse_client import langfuse

    today = datetime.now().date().isoformat()

    # Atomic upsert with conditional check
    sql = """
    INSERT INTO user_quotas (user_id, date, request_count, quota_limit)
    VALUES (:user_id, :date, 1, :limit)
    ON CONFLICT (user_id, date)
    DO UPDATE SET
        request_count = user_quotas.request_count + 1,
        updated_at = NOW()
    WHERE user_quotas.request_count < :limit
    RETURNING request_count, quota_limit;
    """

    try:
        response = rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database,
            sql=sql,
            parameters=[
                {'name': 'user_id', 'value': {'stringValue': user_id}},
                {'name': 'date', 'value': {'stringValue': today}},
                {'name': 'limit', 'value': {'longValue': limit}}
            ]
        )

        if response['numberOfRecordsUpdated'] == 0:
            # WHERE clause failed - quota exceeded
            current = get_user_quota_aurora(user_id, cluster_arn, secret_arn, database)
            raise QuotaExceededException(
                f"User {user_id} has exceeded daily quota. "
                f"Used: {current['request_count']}/{limit}"
            )

        # Parse result
        record = response['records'][0]
        current_count = record[0]['longValue']
        quota_limit = record[1]['longValue']

        # Log to LangFuse
        langfuse.score(
            name="quota_increment_aurora",
            value=current_count,
            data_type="NUMERIC",
            comment=f"User {user_id} quota: {current_count}/{quota_limit}"
        )

        return {
            'user_id': user_id,
            'date': today,
            'current_count': current_count,
            'limit': quota_limit,
            'remaining': quota_limit - current_count
        }

    except Exception as e:
        # FAIL LOUDLY
        raise RuntimeError(
            f"Aurora quota increment failed for user {user_id}: {str(e)}"
        )

def get_user_quota_aurora(
    user_id: str,
    cluster_arn: str,
    secret_arn: str,
    database: str
) -> dict:
    """
    Get current quota usage from Aurora.
    """
    today = datetime.now().date().isoformat()

    sql = """
    SELECT request_count, quota_limit
    FROM user_quotas
    WHERE user_id = :user_id AND date = :date;
    """

    response = rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database,
        sql=sql,
        parameters=[
            {'name': 'user_id', 'value': {'stringValue': user_id}},
            {'name': 'date', 'value': {'stringValue': today}}
        ]
    )

    if len(response['records']) == 0:
        return {'request_count': 0, 'quota_limit': 100}

    record = response['records'][0]
    return {
        'request_count': record[0]['longValue'],
        'quota_limit': record[1]['longValue']
    }
```

#### Pros
- Uses existing Aurora infrastructure (no new service)
- ACID transactions (strong consistency)
- Familiar SQL interface
- Cheaper than DynamoDB at low volumes

#### Cons
- Requires Aurora Serverless v2 (Task 4.2)
- Slightly higher latency than DynamoDB (~10-20ms)
- Not as horizontally scalable as DynamoDB

#### Sources
- https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/data-api.html

---

### 7. AWS Budgets for Cost/Usage Alerts

**Use for**: Proactive alerts when spending or usage exceeds thresholds.

#### Terraform Configuration

```hcl
# aws/terraform/modules/budgets/main.tf
resource "aws_budgets_budget" "monthly_cost" {
  name              = "${var.project_name}-monthly-cost-budget"
  budget_type       = "COST"
  limit_amount      = "500"  # $500/month
  limit_unit        = "USD"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80  # Alert at 80% of budget
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["admin@example.com"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100  # Alert at 100% of budget
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["admin@example.com"]
  }
}

# Usage budget (API requests)
resource "aws_budgets_budget" "api_requests" {
  name         = "${var.project_name}-api-requests-budget"
  budget_type  = "USAGE"
  limit_amount = "1000000"  # 1 million requests
  limit_unit   = "Requests"
  time_unit    = "MONTHLY"

  cost_filter {
    name = "Service"
    values = [
      "Amazon API Gateway"
    ]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 90
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["admin@example.com"]
  }
}
```

#### Programmatic Budget Checks

```python
# main/api/monitoring/budget_checks.py
import boto3
from datetime import datetime

def check_monthly_budget_usage() -> dict:
    """
    Check current month's budget usage.
    Returns percentage of budget consumed.
    """
    budgets = boto3.client('budgets', region_name='us-east-1')  # Budgets is us-east-1 only

    response = budgets.describe_budget(
        AccountId=boto3.client('sts').get_caller_identity()['Account'],
        BudgetName='pharma-test-gen-monthly-cost-budget'
    )

    budget = response['Budget']
    limit = float(budget['BudgetLimit']['Amount'])
    actual = float(budget['CalculatedSpend']['ActualSpend']['Amount'])
    forecasted = float(budget['CalculatedSpend']['ForecastedSpend']['Amount'])

    return {
        'limit': limit,
        'actual': actual,
        'forecasted': forecasted,
        'percentage_used': (actual / limit) * 100,
        'percentage_forecasted': (forecasted / limit) * 100
    }

# Scheduled check (CloudWatch Events → Lambda)
def budget_alert_handler(event, context):
    """
    Lambda function to check budgets and send alerts.
    Triggered daily by CloudWatch Events.
    """
    budget_info = check_monthly_budget_usage()

    if budget_info['percentage_forecasted'] > 100:
        # Send alert via SNS
        sns = boto3.client('sns', region_name='eu-west-2')
        sns.publish(
            TopicArn='arn:aws:sns:eu-west-2:...',
            Subject='ALERT: Budget forecasted to exceed limit',
            Message=f"Forecasted spend: ${budget_info['forecasted']:.2f} / ${budget_info['limit']:.2f}"
        )
```

#### Sources
- https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html
- https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html

---

### 8. AWS Service Quotas API

**Use for**: Programmatic monitoring and requesting quota increases.

#### Python Implementation

```python
# main/api/monitoring/service_quotas.py
import boto3

def get_service_quota(service_code: str, quota_code: str) -> dict:
    """
    Get current quota value for an AWS service.

    Example service codes:
    - 'ecs' (ECS Fargate)
    - 'sqs' (SQS)
    - 'lambda' (Lambda)
    - 'apigateway' (API Gateway)
    """
    quotas = boto3.client('service-quotas', region_name='eu-west-2')

    response = quotas.get_service_quota(
        ServiceCode=service_code,
        QuotaCode=quota_code
    )

    return {
        'quota_name': response['Quota']['QuotaName'],
        'value': response['Quota']['Value'],
        'unit': response['Quota'].get('Unit', 'Count'),
        'adjustable': response['Quota']['Adjustable'],
        'global_quota': response['Quota']['GlobalQuota']
    }

def list_ecs_quotas() -> list:
    """
    List all ECS Fargate quotas.
    """
    quotas = boto3.client('service-quotas', region_name='eu-west-2')

    paginator = quotas.get_paginator('list_service_quotas')
    page_iterator = paginator.paginate(ServiceCode='ecs')

    all_quotas = []
    for page in page_iterator:
        for quota in page['Quotas']:
            all_quotas.append({
                'quota_name': quota['QuotaName'],
                'quota_code': quota['QuotaCode'],
                'value': quota['Value'],
                'adjustable': quota['Adjustable']
            })

    return all_quotas

def request_quota_increase(service_code: str, quota_code: str, desired_value: float) -> dict:
    """
    Request a quota increase.
    Returns request ID for tracking.
    """
    quotas = boto3.client('service-quotas', region_name='eu-west-2')

    response = quotas.request_service_quota_increase(
        ServiceCode=service_code,
        QuotaCode=quota_code,
        DesiredValue=desired_value
    )

    return {
        'request_id': response['RequestedQuota']['Id'],
        'status': response['RequestedQuota']['Status'],
        'desired_value': response['RequestedQuota']['DesiredValue']
    }

# Example: Monitor ECS task quota
def monitor_ecs_task_quota():
    """
    Check if ECS task count is approaching quota limit.
    """
    # Get quota (default: 100 Fargate tasks per region)
    quota_info = get_service_quota('ecs', 'L-3032A538')  # Fargate On-Demand vCPU limit

    # Get current usage
    ecs = boto3.client('ecs', region_name='eu-west-2')
    tasks = ecs.list_tasks(cluster='pharma-test-gen-cluster', desiredStatus='RUNNING')
    current_tasks = len(tasks['taskArns'])

    quota_limit = quota_info['value']
    percentage_used = (current_tasks / quota_limit) * 100

    if percentage_used > 80:
        # Alert: approaching quota limit
        print(f"WARNING: ECS tasks at {percentage_used:.1f}% of quota ({current_tasks}/{quota_limit})")

        if percentage_used > 90 and quota_info['adjustable']:
            # Automatically request increase
            request_quota_increase('ecs', 'L-3032A538', quota_limit * 2)

    return {
        'current_usage': current_tasks,
        'quota_limit': quota_limit,
        'percentage_used': percentage_used
    }
```

#### Common Service Quota Codes

```python
# ECS Fargate
ECS_FARGATE_VCPU_QUOTA = 'L-3032A538'  # Fargate On-Demand vCPU limit
ECS_TASKS_PER_SERVICE = 'L-9A5B0BD3'   # Tasks per service (1000 default)

# SQS
SQS_INFLIGHT_MESSAGES = 'L-F8DC7086'  # Inflight messages (120k standard)

# Lambda
LAMBDA_CONCURRENT_EXECUTIONS = 'L-B99A9384'  # Concurrent executions (1000)

# API Gateway
API_GATEWAY_THROTTLE_RATE = 'L-8A5B8E43'  # Throttle rate limit (10k RPS)
```

#### Sources
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html
- https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html

---

### 9. Lambda Concurrency Limits (If Applicable)

**Note**: Current architecture uses ECS Fargate, not Lambda. Include if migrating to Lambda.

#### Default Quotas
- **Account-level**: 1,000 concurrent executions (default, adjustable to 10k+)
- **Reserved concurrency**: Allocate specific concurrency to critical functions
- **Provisioned concurrency**: Pre-warm functions to avoid cold starts

#### Terraform Configuration

```hcl
# aws/terraform/modules/lambda/concurrency.tf
resource "aws_lambda_function" "job_processor" {
  function_name = "${var.project_name}-job-processor"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "main.handler"
  runtime       = "python3.12"

  # Reserved concurrency (prevents this function from using all account quota)
  reserved_concurrent_executions = 100

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }
}

# Provisioned concurrency (pre-warm 10 instances)
resource "aws_lambda_provisioned_concurrency_config" "job_processor" {
  function_name                     = aws_lambda_function.job_processor.function_name
  provisioned_concurrent_executions = 10
  qualifier                         = aws_lambda_alias.production.name
}
```

#### Sources
- https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html
- https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html

---

## Recommended Approach: Multi-Layer Strategy

For pharmaceutical compliance and robust protection, implement **defense in depth**:

### Layer 1: Infrastructure (AWS WAF) - PRIMARY
- **What**: AWS WAF rate-based rules on CloudFront distribution
- **Why**: Blocks malicious traffic before reaching application
- **Limits**:
  - Global: 1000 requests per 5 minutes per IP
  - /jobs endpoint: 20 requests per 5 minutes per user (via `x-user-id` header)
- **Cost**: $5/month + $1/million requests
- **Audit**: CloudWatch Logs (90-day retention)

### Layer 2: Application (FastAPI SlowAPI) - SECONDARY
- **What**: SlowAPI middleware with Redis backend
- **Why**: Fine-grained per-user, per-endpoint limits with business logic
- **Limits**:
  - 10 requests/minute per user
  - 100 requests/day per user (tracked in Redis)
- **Cost**: $15/month (ElastiCache t3.micro)
- **Audit**: LangFuse traces for every rate limit check

### Layer 3: Quota Tracking (DynamoDB) - DAILY LIMITS
- **What**: DynamoDB atomic counters for daily quota
- **Why**: Persistent daily limits across all endpoints
- **Limits**: 100 requests/day per user (configurable per tier)
- **Cost**: ~$1/day for 1M requests
- **Audit**: Point-in-time recovery, DynamoDB Streams → LangFuse

### Layer 4: Queue Depth (SQS) - BACKPRESSURE
- **What**: Check SQS queue depth before accepting jobs
- **Why**: Prevents overwhelming worker with too many jobs
- **Limits**: Reject new jobs if queue depth > 10,000
- **Cost**: Included in SQS pricing
- **Audit**: CloudWatch metrics

### Layer 5: Cost Control (AWS Budgets) - SPENDING ALERTS
- **What**: AWS Budgets with SNS alerts
- **Why**: Proactive cost monitoring
- **Limits**: $500/month budget (80% and 100% alerts)
- **Cost**: Free (first 2 budgets)
- **Audit**: Budget actions logged to CloudTrail

---

## Implementation Gotchas

### 1. WAF Rate Limiting Granularity
- **Issue**: WAF rate limits are per 5-minute windows, not per-second
- **Solution**: Use application-level rate limiting (SlowAPI) for per-second limits

### 2. Redis Single Point of Failure
- **Issue**: If Redis crashes, rate limiting fails
- **Solution**: Use ElastiCache with Multi-AZ failover, OR fail loudly (reject requests)

### 3. DynamoDB Conditional Check Failures
- **Issue**: `ConditionalCheckFailedException` when quota exceeded is not an error
- **Solution**: Catch exception and convert to HTTP 429 response

### 4. CloudFront Cache Bypasses Rate Limits
- **Issue**: Cached responses don't count against WAF rate limits
- **Solution**: Set `Cache-Control: no-cache` for API endpoints

### 5. Multiple API Task Instances Race Condition
- **Issue**: Two ECS tasks might increment quota simultaneously
- **Solution**: Use DynamoDB or Aurora atomic operations (not Redis counters)

---

## Compliance Considerations (GAMP-5, ALCOA+)

### ALCOA+ Principles for Rate Limiting

| Principle | Implementation |
|-----------|----------------|
| **Attributable** | Every rate limit event logs user_id, timestamp, endpoint |
| **Legible** | CloudWatch Logs in JSON format, LangFuse traces |
| **Contemporaneous** | Logs written in real-time (not batched) |
| **Original** | No log modification; use CloudWatch immutability |
| **Accurate** | Atomic counters (DynamoDB/Aurora) prevent double-counting |
| **Complete** | Log both allowed and denied requests |
| **Consistent** | Same quota logic across all endpoints |
| **Enduring** | 90-day CloudWatch retention, point-in-time recovery |
| **Available** | Logs queryable via CloudWatch Insights, LangFuse dashboard |

### Audit Trail Requirements

```python
# main/api/middleware/audit_logger.py
from main.utils.langfuse_client import langfuse

async def log_rate_limit_event(
    user_id: str,
    endpoint: str,
    action: str,  # "allowed" or "denied"
    quota_info: dict
):
    """
    Log rate limit event to LangFuse for GAMP-5 audit trail.
    """
    langfuse.score(
        name="rate_limit_event",
        value=1 if action == "allowed" else 0,
        data_type="NUMERIC",
        comment=f"User {user_id} {action} access to {endpoint}",
        metadata={
            'user_id': user_id,
            'endpoint': endpoint,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'quota_used': quota_info.get('current_count', 0),
            'quota_limit': quota_info.get('limit', 0),
            'quota_remaining': quota_info.get('remaining', 0)
        }
    )
```

---

## Required Libraries/Versions

```toml
# pyproject.toml additions
[project.dependencies]
slowapi = ">=0.1.9"  # FastAPI rate limiting
redis = ">=5.0.0"    # Redis client for distributed rate limiting
boto3 = ">=1.34.0"   # AWS SDK (WAF, DynamoDB, Budgets, Service Quotas)
```

Install with:
```bash
uv add slowapi redis
```

---

## Cost Analysis (Monthly)

| Component | Cost | Notes |
|-----------|------|-------|
| AWS WAF | $5 + $1/M requests | ~$6-10/month for typical usage |
| ElastiCache (Redis) | $15 | cache.t3.micro, Multi-AZ |
| DynamoDB | $1-5 | On-demand, ~1M writes/day |
| CloudWatch Logs | $2 | 90-day retention, 10 GB/month |
| AWS Budgets | $0 | First 2 budgets free |
| **Total** | **$23-32/month** | Scales with request volume |

---

## Next Agent Guidance

### For Task Executor

1. **Start with AWS WAF (Layer 1)**
   - Create `aws/terraform/modules/waf/` directory
   - Implement rate-based rule with IP and user-based aggregation
   - Associate with existing CloudFront distribution
   - Test in monitor mode first (count, don't block)

2. **Add Application-Level Rate Limiting (Layer 2)**
   - Install `slowapi` and `redis`
   - Create `main/api/middleware/rate_limiter.py`
   - Configure ElastiCache Redis cluster (Terraform)
   - Add SlowAPI middleware to FastAPI app
   - Test with integration tests

3. **Implement Daily Quota Tracking (Layer 3)**
   - **Option A (Recommended)**: DynamoDB atomic counters
     - Create `aws/terraform/modules/dynamodb/quotas.tf`
     - Implement `main/api/services/quota_tracker.py`
   - **Option B**: Aurora PostgreSQL (if Task 4.2 completed)
     - Create `user_quotas` table
     - Implement `main/api/services/quota_tracker_aurora.py`

4. **Add Queue Depth Check (Layer 4)**
   - Modify `main/api/routes/jobs.py` to check SQS queue depth
   - Add CloudWatch alarm for high queue depth

5. **Configure AWS Budgets (Layer 5)**
   - Create `aws/terraform/modules/budgets/`
   - Set monthly cost budget ($500)
   - Add SNS topic for alerts

6. **Testing Strategy**
   - Unit tests for quota increment logic
   - Integration tests for rate limiting
   - Load tests to verify limits (use Locust or k6)
   - Verify LangFuse audit logs

7. **Documentation**
   - Update API documentation with rate limit headers
   - Document quota tiers (basic: 100/day, premium: 1000/day)
   - Create runbook for quota increase requests

---

## Files Referenced

### AWS Documentation
- https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
- https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html
- https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html
- https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html

### Libraries
- https://github.com/laurentS/slowapi (FastAPI rate limiting)
- https://slowapi.readthedocs.io/
- https://redis.io/docs/latest/develop/connect/clients/python/

### Terraform Examples
- https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/wafv2_web_acl
- https://medium.com/devops-pro/terraform-wafv2-web-acl-manege-request-rate-limit-with-waf-ratelimit-41575dc1673f

### Community Resources
- https://xebia.com/blog/aws-api-gateway-throttling-explained/
- https://ezyinfra.dev/blog/handling-600-requestsmin-ip-rate-limiting-with-aws-waf-and-alb
- https://aws.amazon.com/blogs/database/implement-resource-counters-with-amazon-dynamodb/
