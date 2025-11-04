# AWS Migration Production Readiness Plan (PRP)

**Owner:** Platform Engineering (AI Systems)
**Date:** 2025-11-03
**Version:** 2.0 (Enhanced)
**Scope:** Migrate LLM-driven pharmaceutical test generation platform to AWS (single account, EU region) while preserving current functionality and regulatory posture.

---

## Executive Summary

This PRP outlines a 10-week migration of a GAMP-5 compliant pharmaceutical test generation system from local development to AWS production. The system uses LlamaIndex workflows with multi-agent orchestration, RAG capabilities (ChromaDB → S3 Vectors), and regulatory observability (Phoenix local → LangFuse AWS).

**Key Decisions:**
- **Compute:** ECS Fargate (handles 7-8 min workflows, no Lambda timeout risk)
- **Database:** Aurora Serverless v2 with Data API (no VPC complexity)
- **RAG Storage:** S3 Vectors (90% cost reduction vs alternatives)
- **LLM Provider:** Amazon Bedrock (DeepSeek-V3.1) - $0.90/1M input, $2.61/1M output
- **Region:** eu-west-2 (London, UK)
- **Observability:** Phoenix (local dev) + LangFuse (AWS production) + CloudWatch
- **Frontend:** S3 + CloudFront with Clerk authentication (EU endpoints)
- **Estimated Cost:** ~$1,043/month production average (78% LLM cost reduction vs Claude)

---

## 1. Objectives & Success Criteria

### Functional Requirements
- **Workflow Parity:** Unified LlamaIndex workflow generates compliant OQ test suites end-to-end
- **RAG Quality:** ≥80% top-5 retrieval overlap vs. ChromaDB baseline
- **Observability:** Full trace capture (131 spans/workflow maintained)
- **Authentication:** Clerk JWT validation with EU data residency

### Performance Targets
- **Throughput:** 50 documents/day processing capacity
- **Concurrency:** ≤10 concurrent jobs without SLA breaches
- **Latency:** P95 workflow completion ≤15 minutes
- **RAG Performance:** P95 retrieval latency ≤200ms

### Operational Requirements
- **Infrastructure as Code:** All resources provisioned via Terraform
- **Reproducibility:** Full stack runnable via Docker Compose locally
- **Rollback:** Documented procedure to revert to local stack within 1 hour
- **Monitoring:** CloudWatch dashboards + LangFuse traces + alerts

### Compliance Baseline
- **Data Residency:** eu-west-2 region (London, UK - GDPR compliant)
- **Audit Trail:** S3 Object Lock (WORM) with 7-year retention
- **Authentication:** Clerk (EU endpoints) with JWT verification
- **Secrets Management:** AWS Secrets Manager for API keys
- **Access Control:** IAM roles with least-privilege policies

### Timeline
- **Total Duration:** 10 weeks
- **Stage Gates:** Phase completion reviews with rollback criteria
- **MVP Definition:** Single-account production deployment with core features
- **Post-MVP Backlog:** Advanced security controls, multi-account, digital signatures

---

## 2. Architecture Overview

### 2.1 Local Development Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL DEVELOPMENT                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Next.js    │────▶ │   FastAPI    │                     │
│  │   Frontend   │      │   Backend    │                     │
│  │  (Port 3000) │      │  (Port 8000) │                     │
│  └──────────────┘      └───────┬──────┘                     │
│                                 │                             │
│                    ┌────────────┼────────────┐               │
│                    │            │            │               │
│                    ▼            ▼            ▼               │
│            ┌───────────┐ ┌──────────┐ ┌──────────┐          │
│            │  ChromaDB │ │  Phoenix │ │ LangFuse │          │
│            │  (RAG)    │ │  (Trace) │ │(Optional)│          │
│            │ Port 8001 │ │ Port 6006│ │Port 3001 │          │
│            └───────────┘ └──────────┘ └──────────┘          │
│                                                               │
│  Storage: ./output/test_suites/                              │
│  Config:  .env.local (OpenAI, Clerk test keys)              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 AWS Production Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS PRODUCTION (eu-west-2 London)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Internet                                                             │
│     │                                                                 │
│     ▼                                                                 │
│  ┌──────────────┐         ┌──────────────────┐                      │
│  │  CloudFront  │────────▶│  S3 (Frontend)   │                      │
│  │  (CDN)       │         │  Static Hosting  │                      │
│  └──────────────┘         └──────────────────┘                      │
│     │                                                                 │
│     │ (API Calls)                                                     │
│     ▼                                                                 │
│  ┌──────────────┐                                                    │
│  │     ALB      │                                                    │
│  │ (HTTPS)      │                                                    │
│  └───────┬──────┘                                                    │
│          │                                                            │
│          ▼                                                            │
│  ┌──────────────────┐                                                │
│  │  ECS Fargate     │                                                │
│  │  Backend API     │                                                │
│  │  (2 vCPU/4GB)    │────┐                                           │
│  └──────────────────┘    │                                           │
│          │                │                                           │
│          │ (submit job)   │                                           │
│          ▼                │                                           │
│  ┌──────────────────┐    │                                           │
│  │  Amazon SQS      │    │                                           │
│  │  Job Queue + DLQ │    │                                           │
│  └──────┬───────────┘    │                                           │
│         │                 │                                           │
│         │ (poll)          │                                           │
│         ▼                 │                                           │
│  ┌──────────────────┐    │                                           │
│  │  ECS Fargate     │    │                                           │
│  │  Worker Service  │    │                                           │
│  │  (4 vCPU/8GB)    │◀───┘                                           │
│  │  LlamaIndex      │                                                │
│  │  Workflows       │                                                │
│  └────┬─────┬───────┘                                                │
│       │     │                                                         │
│       │     └────────────────────┐                                   │
│       │                          │                                   │
│       ▼                          ▼                                   │
│  ┌─────────────┐      ┌──────────────────┐                          │
│  │   Bedrock   │      │   S3 Vectors     │                          │
│  │  Claude 3.5 │      │   (RAG Index)    │                          │
│  │   Sonnet    │      │   1536 dims      │                          │
│  └─────────────┘      └──────────────────┘                          │
│       │                          │                                   │
│       │                          │                                   │
│       └───────────┬──────────────┘                                   │
│                   │                                                   │
│                   ▼                                                   │
│  ┌────────────────────────────────────┐                              │
│  │     Aurora Serverless v2           │                              │
│  │     PostgreSQL (Data API)          │                              │
│  │  - Job metadata                    │                              │
│  │  - Audit logs                      │                              │
│  │  - User sessions                   │                              │
│  └────────────────────────────────────┘                              │
│                   │                                                   │
│                   ▼                                                   │
│  ┌────────────────────────────────────┐                              │
│  │           S3 Buckets               │                              │
│  │  - test-output (Object Lock)       │                              │
│  │  - rag-vectors                     │                              │
│  │  - terraform-state                 │                              │
│  └────────────────────────────────────┘                              │
│                                                                       │
│  ┌────────────────────────────────────┐                              │
│  │         Observability              │                              │
│  │  ┌──────────────┐ ┌─────────────┐ │                              │
│  │  │  LangFuse    │ │  CloudWatch │ │                              │
│  │  │  (ECS)       │ │  Logs/Metrics│ │                              │
│  │  │  + ClickHouse│ │  Dashboards │ │                              │
│  │  └──────────────┘ └─────────────┘ │                              │
│  └────────────────────────────────────┘                              │
│                                                                       │
│  ┌────────────────────────────────────┐                              │
│  │      Secrets Manager               │                              │
│  │  - Bedrock credentials             │                              │
│  │  - Clerk API keys                  │                              │
│  │  - Database passwords              │                              │
│  └────────────────────────────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Details

#### Frontend (S3 + CloudFront)
- **Stack:** Next.js 14+ with App Router
- **Hosting:** S3 static website + CloudFront distribution
- **Authentication:** Clerk React components (EU endpoints)
- **Pages:** Dashboard, Job Status, Test Suite Viewer, Compliance Reports
- **Build:** GitHub Actions → S3 deployment
- **Cost:** ~$50/month (CloudFront + S3)

#### Backend API (ECS Fargate)
- **Stack:** FastAPI + uvicorn
- **Resources:** 2 vCPU, 4 GB RAM
- **Scaling:** 1-4 tasks based on CPU (target 70%)
- **Endpoints:**
  - `POST /jobs` - Submit workflow
  - `GET /jobs/{id}` - Poll status
  - `GET /jobs/{id}/results` - Download test suite
  - `GET /health` - Health check
- **Cost:** ~$100/month

#### Worker Service (ECS Fargate)
- **Stack:** Python 3.12 + LlamaIndex + LangFuse
- **Resources:** 4 vCPU, 8 GB RAM (workflow average 7-8 min)
- **Scaling:** 1-4 tasks based on SQS queue depth
- **Job Flow:**
  1. Poll SQS for job message
  2. Download URS from S3
  3. Execute unified workflow (GAMP-5 categorization → parallel agents → test generation)
  4. Persist results to S3 (Object Lock bucket)
  5. Update Aurora with job status
  6. Emit LangFuse traces
- **Cost:** ~$300/month

#### Database (Aurora Serverless v2)
- **Engine:** PostgreSQL 15.x
- **Scaling:** 0.5-2 ACU (auto-pause after 5 min idle)
- **Access:** Data API (no VPC needed)
- **Schema:** Jobs, test_suites, audit_logs, compliance_metadata
- **Backups:** Automated snapshots (7-day retention)
- **Cost:** ~$50/month (dev), ~$150/month (prod)

#### RAG Storage (S3 Vectors)
- **Dimensions:** 1536 (OpenAI text-embedding-3-small)
- **Similarity:** Cosine
- **Metadata:** document_type, gamp_category, version, upload_date
- **Strategy:** Over-fetch + post-filter (S3 Vectors limitation)
- **Migration:** ChromaDB export → S3 Vectors import script
- **Cost:** ~$5/month (200 documents)

#### LLM Provider (Amazon Bedrock)
- **Model:** DeepSeek-V3.1 (deepseek-ai.DeepSeek-V3)
- **Region:** eu-west-2
- **Access:** IAM role-based (ECS task role)
- **Pricing:** $0.90 / 1M input tokens, $2.61 / 1M output tokens
- **Estimated:** ~$70/month (50 workflows/day)

#### Observability (LangFuse + CloudWatch)
- **LangFuse:** Self-hosted on ECS (Postgres + ClickHouse + Redis)
- **Purpose:** LLM trace capture, prompt versioning, cost tracking
- **Integration:** Native LlamaIndex instrumentation
- **CloudWatch:** Metrics (queue depth, latency, errors), logs, alarms
- **Cost:** ~$450/month (LangFuse infra), ~$50/month (CloudWatch)

### 2.4 Alternatives Evaluated

| Component | Options Evaluated | Decision | Rationale |
|-----------|-------------------|----------|-----------|
| **Compute** | Lambda, ECS Fargate, EKS | ECS Fargate | Workflows average 7-8 min (50% of Lambda 15-min limit = risky), heavy dependencies, no cold starts |
| **RAG Storage** | OpenSearch, Aurora pgvector, S3 Vectors | S3 Vectors | 90% cheaper (~$5 vs $50/month), sufficient for use case, native S3 integration |
| **Database** | RDS, Aurora Serverless v2, DynamoDB | Aurora Serverless v2 | Relational audit requirements, Data API simplifies access, auto-scaling |
| **Observability** | Phoenix only, CloudWatch only, LangFuse | LangFuse + CloudWatch | LangFuse for LLM-specific traces, CloudWatch for infrastructure, Phoenix for local dev |
| **LLM Provider** | OpenRouter, Bedrock, Direct OpenAI | Bedrock | Cost reduction, EU sovereignty, integrated IAM, no API key rotation |

---

## 3. Observability Strategy

### 3.1 Dual-Mode Architecture

**Design Principle:** Environment-based observability switching to maintain local development simplicity while achieving production-grade monitoring.

```python
# main/src/core/observability.py
import os
from phoenix.otel import register as phoenix_register
from langfuse import Langfuse
from opentelemetry import trace

def init_observability():
    """Initialize observability based on environment."""
    env = os.getenv("ENVIRONMENT", "local")

    if env == "local":
        return _init_phoenix()
    elif env in ["production", "staging"]:
        return _init_langfuse()
    else:
        raise ValueError(f"Unknown environment: {env}")

def _init_phoenix() -> dict:
    """Phoenix for local development."""
    phoenix_register(
        project_name="pharma-test-gen-local",
        endpoint="http://localhost:6006"
    )
    return {
        "provider": "phoenix",
        "endpoint": "http://localhost:6006",
        "project": "pharma-test-gen-local"
    }

def _init_langfuse() -> dict:
    """LangFuse for AWS production."""
    langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://langfuse.pharma.internal")
    )

    # LangFuse auto-instruments LlamaIndex via callback handler
    from langfuse.llama_index import LlamaIndexCallbackHandler
    callback_handler = LlamaIndexCallbackHandler()

    return {
        "provider": "langfuse",
        "client": langfuse,
        "callback_handler": callback_handler
    }
```

### 3.2 Phoenix (Local Development)

**Purpose:** Lightweight trace visualization during development.

**Setup:**
```yaml
# docker-compose.yml (local)
services:
  phoenix:
    image: arizephoenix/phoenix:latest
    ports:
      - "6006:6006"
    environment:
      - PHOENIX_SQL_DATABASE_URL=sqlite:////phoenix/phoenix.db
    volumes:
      - phoenix-data:/phoenix
```

**Features Used:**
- Real-time trace visualization (131 spans/workflow)
- Span timeline analysis
- LLM token usage tracking
- Error inspection

**Access:** http://localhost:6006

### 3.3 LangFuse (AWS Production)

**Purpose:** Production-grade LLM observability with prompt management and cost tracking.

**Architecture:**
```
┌─────────────────────────────────────────────┐
│          LangFuse Production Stack           │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────┐       ┌─────────────┐    │
│  │  LangFuse    │──────▶│  PostgreSQL │    │
│  │  Web + API   │       │  (Metadata) │    │
│  │  (ECS)       │       │  (Aurora)   │    │
│  └──────┬───────┘       └─────────────┘    │
│         │                                    │
│         ▼                                    │
│  ┌──────────────┐       ┌─────────────┐    │
│  │  ClickHouse  │       │    Redis    │    │
│  │  (Events)    │       │  (Cache)    │    │
│  │  (ECS)       │       │  (ElastiC.) │    │
│  └──────────────┘       └─────────────┘    │
└─────────────────────────────────────────────┘
```

**Deployment:**
```yaml
# docker-compose.langfuse.yml (self-hosted on ECS)
version: '3.8'
services:
  langfuse-server:
    image: langfuse/langfuse:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@aurora-endpoint/langfuse
      - CLICKHOUSE_URL=http://clickhouse:8123
      - REDIS_HOST=redis-cluster.cache.amazonaws.com
      - NEXTAUTH_URL=https://langfuse.pharma.internal
      - NEXTAUTH_SECRET=${LANGFUSE_AUTH_SECRET}
    ports:
      - "3000:3000"
```

**Integration:**
```python
# main/src/workflows/unified_workflow.py
from llama_index.core.workflow import Workflow
from langfuse.llama_index import LlamaIndexCallbackHandler

class UnifiedWorkflow(Workflow):
    def __init__(self):
        super().__init__()

        # Auto-instrument with LangFuse
        if os.getenv("ENVIRONMENT") == "production":
            from main.src.core.observability import init_observability
            obs_config = init_observability()
            self.callback_handler = obs_config["callback_handler"]

    @Workflow.step
    async def categorize(self, ev: StartEvent) -> CategorizeEvent:
        """GAMP-5 categorization with automatic trace capture."""
        # LangFuse automatically captures:
        # - Prompt template + variables
        # - LLM calls (model, tokens, latency, cost)
        # - Agent decisions
        # - Errors and retries
        result = await self.categorization_agent.run(ev.urs_text)
        return CategorizeEvent(category=result.category)
```

**Features:**
- **Trace Capture:** All LLM calls, embeddings, retrievals
- **Prompt Management:** Version control for prompts
- **Cost Tracking:** Per-workflow cost attribution
- **User Feedback:** Link traces to user ratings
- **Datasets:** Test case management for regression testing
- **Dashboards:** Custom metrics (compliance score, test count, error rates)

**Cost:** ~$450/month (2 vCPU Postgres, 4 vCPU ClickHouse, Redis cache)

### 3.4 CloudWatch Integration

**Metrics:**
- `WorkflowDuration` (P50, P95, P99)
- `SQSQueueDepth` (current, age of oldest message)
- `ErrorRate` (by error type)
- `TestSuiteGenerationCount` (success vs failure)
- `RAGRetrievalLatency` (P95)
- `BedrockThrottling` (count)

**Alarms:**
- Queue depth > 50 messages (scale up workers)
- P95 latency > 15 minutes (investigate bottleneck)
- Error rate > 5% (page on-call)
- DLQ messages > 0 (investigate failures)

**Dashboard:**
```python
# terraform/modules/observability/cloudwatch.tf
resource "aws_cloudwatch_dashboard" "pharma_test_gen" {
  dashboard_name = "pharma-test-generation"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", {service = "worker-service"}],
            [".", "MemoryUtilization", {service = "worker-service"}]
          ]
          period = 300
          stat = "Average"
          region = "eu-west-2"
          title = "Worker Resource Usage"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["PharmaTestGen", "WorkflowDuration", {stat = "p95"}],
            [".", ".", {stat = "p50"}]
          ]
          period = 300
          region = "eu-west-2"
          title = "Workflow Latency"
        }
      }
    ]
  })
}
```

### 3.5 Trace Correlation

**Goal:** Link CloudWatch logs → LangFuse traces → Phoenix local traces

```python
# main/src/core/correlation.py
import structlog
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default=None)

def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )

async def execute_workflow(job_id: str, urs_text: str):
    """Execute workflow with trace correlation."""
    import uuid
    trace_id = str(uuid.uuid4())
    trace_id_var.set(trace_id)

    logger = structlog.get_logger()
    logger = logger.bind(
        job_id=job_id,
        trace_id=trace_id,
        environment=os.getenv("ENVIRONMENT")
    )

    try:
        logger.info("workflow_started")

        # LangFuse will use trace_id for correlation
        workflow = UnifiedWorkflow()
        result = await workflow.run(urs_text=urs_text)

        logger.info("workflow_completed", test_count=len(result.tests))
        return result

    except Exception as e:
        logger.error("workflow_failed", error=str(e), exc_info=True)
        raise
```

**CloudWatch Insights Query:**
```
fields @timestamp, job_id, trace_id, @message
| filter environment = "production" and trace_id = "abc-123"
| sort @timestamp asc
```

**LangFuse Correlation:**
- Navigate to trace via `trace_id` in CloudWatch
- View full LLM conversation, prompts, costs
- Export for debugging or compliance review

---

## 4. Amazon Bedrock Integration

### 4.1 Provider Implementation

```python
# main/src/llm/bedrock_provider.py
import boto3
import json
from typing import Optional, Dict, Any
from langfuse.decorators import observe
from llama_index.core.llms import ChatMessage, MessageRole

class BedrockLLMProvider:
    """Amazon Bedrock LLM provider with LangFuse observability."""

    def __init__(
        self,
        region: str = "eu-west-2",
        model_id: str = "deepseek-ai.DeepSeek-V3"
    ):
        self.region = region
        self.model_id = model_id
        self.client = boto3.client('bedrock-runtime', region_name=region)

    @observe(as_type="generation")
    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate completion via Bedrock.

        LangFuse automatically captures:
        - Model ID and parameters
        - Input messages and system prompt
        - Output text and token counts
        - Latency and errors
        """

        # Convert LlamaIndex messages to Bedrock format
        bedrock_messages = []
        for msg in messages:
            bedrock_messages.append({
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": [{"text": msg.content}]
            })

        # Construct request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": bedrock_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if system_prompt:
            request_body["system"] = [{"text": system_prompt}]

        # Invoke model
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=bedrock_messages,
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature
                },
                system=[{"text": system_prompt}] if system_prompt else None
            )

            # Extract response
            output_message = response["output"]["message"]
            content = output_message["content"][0]["text"]

            # Token counts
            usage = response["usage"]
            input_tokens = usage["inputTokens"]
            output_tokens = usage["outputTokens"]

            # LangFuse will auto-capture these via decorator
            return content

        except self.client.exceptions.ThrottlingException as e:
            # Handle Bedrock rate limits
            raise RuntimeError(f"Bedrock throttled: {e}")
        except Exception as e:
            raise RuntimeError(f"Bedrock error: {e}")
```

### 4.2 LlamaIndex Integration

```python
# main/src/workflows/unified_workflow.py
from llama_index.core.llms import LLM
from main.src.llm.bedrock_provider import BedrockLLMProvider

class UnifiedWorkflow(Workflow):
    def __init__(self):
        super().__init__()

        # Initialize Bedrock LLM
        self.llm = BedrockLLMProvider(
            region="eu-west-2",
            model_id="deepseek-ai.DeepSeek-V3"
        )

        # Pass to agents
        self.categorization_agent = CategorizationAgent(llm=self.llm)
        self.context_agent = ContextProviderAgent(llm=self.llm)
        self.sme_agent = SMEAgent(llm=self.llm)
```

### 4.3 IAM Permissions

```hcl
# terraform/modules/compute/iam.tf
resource "aws_iam_role_policy" "ecs_task_bedrock" {
  name = "bedrock-access"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:eu-west-2::foundation-model/deepseek-ai.DeepSeek-V3"
        ]
      }
    ]
  })
}
```

### 4.4 Cost Optimization

**Pricing (DeepSeek-V3.1 via Bedrock):**
- Input: $0.90 / 1M tokens ($0.000899985 / 1K)
- Output: $2.61 / 1M tokens ($0.002606853 / 1K)

**Typical Workflow:**
- Categorization: 2K input, 500 output = $0.003
- Context Provider: 1K input, 200 output = $0.001
- SME Agent: 5K input (RAG context), 1K output = $0.007
- Research Agent: 3K input, 800 output = $0.005
- Test Generation: 10K input, 8K output = $0.030

**Total per workflow:** ~$0.046 (79% reduction vs Claude 3.5 Sonnet)
**Monthly (50 workflows/day):** ~$70 (vs $330 with Claude)

**Optimizations:**
- Cache system prompts (Bedrock prompt caching)
- Batch similar requests
- Monitor token usage per agent for optimization opportunities
- Maintain cost tracking via LangFuse dashboards

---

## 5. Aurora Serverless v2 Database Design

### 5.1 Schema

```sql
-- main/db/schema.sql

-- Jobs table: workflow execution tracking
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Clerk user ID
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Input
    urs_document_key VARCHAR(1024) NOT NULL, -- S3 key
    urs_hash VARCHAR(64) NOT NULL, -- SHA-256 for deduplication

    -- Results
    test_suite_key VARCHAR(1024), -- S3 key for generated suite
    test_count INTEGER,
    gamp_category VARCHAR(10),

    -- Observability
    trace_id VARCHAR(255), -- LangFuse trace ID
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Compliance
    compliance_validated BOOLEAN DEFAULT FALSE,
    validation_errors JSONB,

    CONSTRAINT valid_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'cancelled')
    )
);

CREATE INDEX idx_jobs_user_created ON jobs(user_id, created_at DESC);
CREATE INDEX idx_jobs_status ON jobs(status) WHERE status IN ('pending', 'running');
CREATE INDEX idx_jobs_urs_hash ON jobs(urs_hash);

-- Test suites table: generated OQ tests
CREATE TABLE test_suites (
    suite_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,

    -- Metadata
    suite_type VARCHAR(10) NOT NULL DEFAULT 'OQ',
    gamp_category VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Storage
    s3_key VARCHAR(1024) NOT NULL UNIQUE,
    s3_version_id VARCHAR(255),
    object_lock_retention_until TIMESTAMPTZ,

    -- Content summary
    test_count INTEGER NOT NULL,
    test_ids TEXT[], -- Array of test IDs for quick lookup

    -- Compliance metadata
    alcoa_compliant BOOLEAN DEFAULT FALSE,
    cfr_part11_compliant BOOLEAN DEFAULT FALSE,
    metadata JSONB -- Flexible metadata storage
);

CREATE INDEX idx_suites_job ON test_suites(job_id);
CREATE INDEX idx_suites_created ON test_suites(created_at DESC);

-- Audit logs table: GAMP-5 compliance trail
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(job_id),

    -- Who/What/When/Where/Why
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL, -- e.g., 'job_submitted', 'test_generated'
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address INET,

    -- Details
    resource_type VARCHAR(50), -- 'job', 'test_suite', 'document'
    resource_id VARCHAR(255),
    changes JSONB, -- Before/after state

    -- Compliance
    alcoa_attributable VARCHAR(255), -- User who performed action
    alcoa_legible BOOLEAN DEFAULT TRUE,
    alcoa_contemporaneous BOOLEAN DEFAULT TRUE,
    alcoa_original BOOLEAN DEFAULT TRUE,
    alcoa_accurate BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_job ON audit_logs(job_id);

-- RAG document metadata (S3 Vectors metadata cache)
CREATE TABLE rag_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    s3_key VARCHAR(1024) NOT NULL UNIQUE,

    -- Content
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(100), -- 'SOP', 'guideline', 'template'
    gamp_category VARCHAR(10),
    version VARCHAR(50),

    -- Embedding
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    embedding_dimensions INTEGER DEFAULT 1536,
    vector_id VARCHAR(255), -- S3 Vectors ID

    -- Lifecycle
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    indexed BOOLEAN DEFAULT FALSE,

    -- Metadata for filtering
    metadata JSONB
);

CREATE INDEX idx_rag_type_category ON rag_documents(document_type, gamp_category);
CREATE INDEX idx_rag_indexed ON rag_documents(indexed) WHERE indexed = FALSE;
```

### 5.2 Data API Access Pattern

```python
# main/src/db/client.py
import boto3
import json
from typing import Optional, Dict, Any

class AuroraDataAPIClient:
    """Aurora Serverless v2 Data API client (no VPC needed)."""

    def __init__(
        self,
        cluster_arn: str,
        secret_arn: str,
        database: str = "pharma_test_gen",
        region: str = "eu-west-2"
    ):
        self.client = boto3.client('rds-data', region_name=region)
        self.cluster_arn = cluster_arn
        self.secret_arn = secret_arn
        self.database = database

    async def execute_statement(
        self,
        sql: str,
        parameters: Optional[list] = None
    ) -> Dict[str, Any]:
        """Execute SQL statement via Data API."""

        request = {
            'resourceArn': self.cluster_arn,
            'secretArn': self.secret_arn,
            'database': self.database,
            'sql': sql
        }

        if parameters:
            request['parameters'] = parameters

        response = self.client.execute_statement(**request)
        return response

    async def create_job(
        self,
        user_id: str,
        urs_s3_key: str,
        urs_hash: str
    ) -> str:
        """Create new job record."""

        sql = """
        INSERT INTO jobs (user_id, urs_document_key, urs_hash, status)
        VALUES (:user_id, :urs_key, :urs_hash, 'pending')
        RETURNING job_id::text
        """

        result = await self.execute_statement(
            sql,
            parameters=[
                {'name': 'user_id', 'value': {'stringValue': user_id}},
                {'name': 'urs_key', 'value': {'stringValue': urs_s3_key}},
                {'name': 'urs_hash', 'value': {'stringValue': urs_hash}}
            ]
        )

        job_id = result['records'][0][0]['stringValue']
        return job_id

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update job status."""

        sql = """
        UPDATE jobs
        SET status = :status,
            error_message = :error,
            completed_at = CASE WHEN :status IN ('completed', 'failed')
                                THEN NOW() ELSE completed_at END
        WHERE job_id = :job_id::uuid
        """

        await self.execute_statement(
            sql,
            parameters=[
                {'name': 'job_id', 'value': {'stringValue': job_id}},
                {'name': 'status', 'value': {'stringValue': status}},
                {'name': 'error', 'value': {'stringValue': error_message or ''}}
            ]
        )
```

### 5.3 Terraform Configuration

```hcl
# terraform/modules/database/aurora.tf
resource "aws_rds_cluster" "pharma_test_gen" {
  cluster_identifier      = "pharma-test-gen-${var.environment}"
  engine                  = "aurora-postgresql"
  engine_mode             = "provisioned"
  engine_version          = "15.5"
  database_name           = "pharma_test_gen"
  master_username         = "admin"
  master_password         = random_password.db_password.result

  # Serverless v2 scaling
  serverlessv2_scaling_configuration {
    min_capacity = 0.5  # 0.5 ACU = 1 GB RAM
    max_capacity = 2.0  # Scale up for load tests
  }

  # Data API enabled (no VPC needed)
  enable_http_endpoint = true

  # Backups
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"

  # Encryption
  storage_encrypted = true
  kms_key_id        = aws_kms_key.db.arn

  # Maintenance
  preferred_maintenance_window = "sun:04:00-sun:05:00"

  skip_final_snapshot = var.environment == "dev"

  tags = {
    Environment = var.environment
    Project     = "pharma-test-generation"
  }
}

resource "aws_rds_cluster_instance" "pharma_test_gen" {
  identifier         = "pharma-test-gen-${var.environment}-instance"
  cluster_identifier = aws_rds_cluster.pharma_test_gen.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.pharma_test_gen.engine
  engine_version     = aws_rds_cluster.pharma_test_gen.engine_version
}

# Store credentials in Secrets Manager
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "pharma-test-gen-db-${var.environment}"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = aws_rds_cluster.pharma_test_gen.master_username
    password = aws_rds_cluster.pharma_test_gen.master_password
    host     = aws_rds_cluster.pharma_test_gen.endpoint
    port     = aws_rds_cluster.pharma_test_gen.port
    database = aws_rds_cluster.pharma_test_gen.database_name
  })
}

output "cluster_arn" {
  value = aws_rds_cluster.pharma_test_gen.arn
}

output "secret_arn" {
  value = aws_secretsmanager_secret.db_credentials.arn
}
```

---

## 6. Phased Delivery Plan (10 Weeks)

### Phase 0: Foundations & Readiness (Week 0.5)

**Objectives:**
- Validate AWS service availability in eu-west-2
- Establish Terraform backend
- Create IAM scaffolding
- Define rollback criteria

**Tasks:**
1. **Service Quotas:** Confirm Fargate, S3 Vectors, Aurora limits
2. **Compliance Foundation:** Enable CloudTrail, Config recording, GuardDuty (optional)
3. **Terraform Backend:**
   ```bash
   # Create S3 bucket for state
   aws s3 mb s3://pharma-test-gen-tfstate-eu --region eu-west-2
   aws s3api put-bucket-versioning --bucket pharma-test-gen-tfstate-eu --versioning-configuration Status=Enabled

   # Create DynamoDB lock table
   aws dynamodb create-table \
     --table-name terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --region eu-west-2
   ```

4. **IAM Roles:**
   - `pharma-test-gen-deploy` (GitHub Actions)
   - `pharma-test-gen-ecs-task` (ECS tasks)
   - `pharma-test-gen-ecs-execution` (ECS launch)

**Deliverables:**
- [ ] Service quota confirmation doc
- [ ] Terraform backend configured (`terraform/backend.tf`)
- [ ] IAM roles created with least-privilege policies
- [ ] Rollback playbook drafted

---

### Phase 1: Backend Abstraction & Local MVP (Weeks 1-3)

**Objectives:**
- Refactor backend for cloud portability
- Implement storage/RAG abstraction layers
- Add Clerk authentication
- Maintain local functionality

**Tasks:**

1. **Storage Adapter** (`main/src/adapters/storage.py`):
   ```python
   class StorageAdapter:
       """Dual-mode storage (local filesystem or S3)."""

       def __init__(self):
           self.use_s3 = os.getenv("USE_S3", "false").lower() == "true"
           if self.use_s3:
               self.s3_client = boto3.client('s3', region_name='eu-west-2')
               self.bucket = os.getenv("S3_BUCKET_TEST_OUTPUT")

       async def save_test_suite(self, suite_id: str, data: dict) -> str:
           if self.use_s3:
               key = f"test-suites/{suite_id}.json"
               self.s3_client.put_object(
                   Bucket=self.bucket,
                   Key=key,
                   Body=json.dumps(data),
                   Metadata={
                       'suite-id': suite_id,
                       'gamp-category': data.get('gamp_category'),
                       'created-at': datetime.utcnow().isoformat()
                   }
               )
               return f"s3://{self.bucket}/{key}"
           else:
               path = Path(f"./output/test_suites/{suite_id}.json")
               path.parent.mkdir(parents=True, exist_ok=True)
               with open(path, 'w') as f:
                   json.dump(data, f, indent=2)
               return str(path)
   ```

2. **Vector Store Provider** (`main/src/adapters/vector_store.py`):
   ```python
   class VectorStoreProvider:
       """Dual-mode RAG (ChromaDB local, S3 Vectors AWS)."""

       def __init__(self):
           self.mode = os.getenv("RAG_MODE", "chromadb")

           if self.mode == "chromadb":
               import chromadb
               self.client = chromadb.PersistentClient(path="./chroma_db")
               self.collection = self.client.get_or_create_collection("pharma_docs")
           elif self.mode == "s3_vectors":
               self.s3_vectors = boto3.client('s3-vectors', region_name='eu-west-2')
               self.index_name = os.getenv("S3_VECTORS_INDEX")

       async def query(
           self,
           query_embedding: list[float],
           top_k: int = 5,
           filters: Optional[dict] = None
       ) -> list[dict]:
           if self.mode == "chromadb":
               results = self.collection.query(
                   query_embeddings=[query_embedding],
                   n_results=top_k,
                   where=filters
               )
               return self._format_chromadb_results(results)

           elif self.mode == "s3_vectors":
               # S3 Vectors doesn't support pre-filtering, so over-fetch
               results = self.s3_vectors.query(
                   IndexName=self.index_name,
                   QueryVector=query_embedding,
                   TopK=top_k * 3  # Over-fetch for post-filtering
               )

               # Post-filter
               filtered = self._post_filter(results, filters)
               return filtered[:top_k]
   ```

3. **FastAPI Async Job Submission** (`main/api/app.py`):
   ```python
   from fastapi import FastAPI, UploadFile, Depends
   from main.src.auth.clerk import verify_clerk_token

   app = FastAPI()

   @app.post("/jobs")
   async def submit_job(
       file: UploadFile,
       user: dict = Depends(verify_clerk_token)
   ):
       """Submit workflow job (async processing)."""

       # Save URS document
       storage = StorageAdapter()
       urs_key = await storage.save_document(file)

       # Create job record
       db = AuroraDataAPIClient()
       job_id = await db.create_job(
           user_id=user['sub'],
           urs_s3_key=urs_key,
           urs_hash=hashlib.sha256(await file.read()).hexdigest()
       )

       # Submit to queue (local: in-memory, AWS: SQS)
       if os.getenv("USE_SQS", "false") == "true":
           await submit_to_sqs(job_id, urs_key)
       else:
           # Local: execute immediately in background
           asyncio.create_task(execute_workflow_local(job_id, urs_key))

       return {"job_id": job_id, "status": "pending"}
   ```

4. **Clerk Authentication** (`main/src/auth/clerk.py`):
   ```python
   from clerk_backend_api import Clerk
   from fastapi import HTTPException, Header

   clerk = Clerk(api_key=os.getenv("CLERK_SECRET_KEY"))

   async def verify_clerk_token(authorization: str = Header(None)):
       """Verify Clerk JWT token."""
       if not authorization or not authorization.startswith("Bearer "):
           raise HTTPException(401, "Missing or invalid authorization header")

       token = authorization.split(" ")[1]

       try:
           # Verify JWT
           payload = clerk.verify_token(token)
           return payload  # Contains user_id, email, etc.
       except Exception as e:
           raise HTTPException(401, f"Invalid token: {e}")
   ```

**Testing:**
```bash
# Local mode (no AWS dependencies)
export ENVIRONMENT=local
export USE_S3=false
export RAG_MODE=chromadb
uv run uvicorn main.api.app:app --reload

# Test upload
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer <clerk-test-token>" \
  -F "file=@test_urs.txt"
```

**Deliverables:**
- [ ] Storage adapter with unit tests
- [ ] Vector store provider with ChromaDB/S3 Vectors parity tests
- [ ] FastAPI async job submission endpoint
- [ ] Clerk authentication middleware
- [ ] Local integration test suite passing

---

### Phase 2: Frontend Dashboard (Weeks 2-4)

**Objectives:**
- Build Next.js dashboard for workflow management
- Implement job status polling and results viewer
- Integrate Clerk authentication (EU endpoints)
- Add compliance badges and LangFuse snapshot viewer

**Tasks:**

1. **Project Setup:**
   ```bash
   cd main/frontend
   npx create-next-app@latest . --typescript --tailwind --app
   npm install @clerk/nextjs axios swr recharts
   ```

2. **Clerk Provider** (`app/layout.tsx`):
   ```typescript
   import { ClerkProvider } from '@clerk/nextjs'

   export default function RootLayout({ children }) {
     return (
       <ClerkProvider
         publishableKey={process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}
         domain="clerk.pharma.eu"  // EU endpoint
       >
         <html>
           <body>{children}</body>
         </html>
       </ClerkProvider>
     )
   }
   ```

3. **Dashboard Page** (`app/dashboard/page.tsx`):
   ```typescript
   'use client'
   import { useUser } from '@clerk/nextjs'
   import useSWR from 'swr'

   export default function Dashboard() {
     const { user } = useUser()
     const { data: jobs } = useSWR('/api/jobs', fetcher, { refreshInterval: 5000 })

     return (
       <div className="p-8">
         <h1>Pharmaceutical Test Generation</h1>
         <JobUploader />
         <JobList jobs={jobs} />
       </div>
     )
   }
   ```

4. **Job Status Viewer** (`app/jobs/[id]/page.tsx`):
   ```typescript
   export default function JobDetail({ params }: { params: { id: string } }) {
     const { data: job } = useSWR(`/api/jobs/${params.id}`, fetcher)

     if (job?.status === 'completed') {
       return <TestSuiteViewer suiteId={job.test_suite_id} />
     }

     return <JobProgress job={job} />
   }
   ```

**Deliverables:**
- [ ] Next.js app running locally
- [ ] Clerk authentication working (test mode)
- [ ] Job upload and status polling functional
- [ ] Test suite viewer displaying JSON results
- [ ] Compliance badges (ALCOA+, 21 CFR Part 11)

---

### Phase 3: Containerization & Local Orchestration (Weeks 4-6)

**Objectives:**
- Containerize backend and worker services
- Create Docker Compose stack for local testing
- Integrate LangFuse locally (optional)
- Load test with 10 concurrent jobs

**Tasks:**

1. **Dockerfile (Multi-stage)** (`Dockerfile`):
   ```dockerfile
   FROM python:3.12-slim AS builder

   WORKDIR /app

   # Install uv
   RUN pip install uv

   # Copy dependency files
   COPY pyproject.toml uv.lock ./

   # Install dependencies
   RUN uv sync --frozen --no-dev

   FROM python:3.12-slim

   WORKDIR /app

   # Copy virtualenv from builder
   COPY --from=builder /app/.venv /app/.venv

   # Copy application
   COPY main/ ./main/

   # Healthcheck
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:8000/health || exit 1

   ENV PATH="/app/.venv/bin:$PATH"

   CMD ["uvicorn", "main.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Docker Compose Stack** (`docker-compose.yml`):
   ```yaml
   version: '3.8'

   services:
     backend:
       build: .
       command: uvicorn main.api.app:app --host 0.0.0.0 --port 8000 --reload
       ports:
         - "8000:8000"
       environment:
         - ENVIRONMENT=local
         - USE_S3=false
         - RAG_MODE=chromadb
         - CLERK_SECRET_KEY=${CLERK_SECRET_KEY}
       volumes:
         - ./main:/app/main
         - ./output:/app/output
         - chroma-data:/app/chroma_db
       depends_on:
         - chromadb
         - phoenix

     worker:
       build: .
       command: python main/worker.py
       environment:
         - ENVIRONMENT=local
         - USE_S3=false
         - RAG_MODE=chromadb
       volumes:
         - ./main:/app/main
         - ./output:/app/output
         - chroma-data:/app/chroma_db
       depends_on:
         - chromadb
         - phoenix

     chromadb:
       image: chromadb/chroma:latest
       ports:
         - "8001:8000"
       volumes:
         - chroma-data:/chroma/chroma

     phoenix:
       image: arizephoenix/phoenix:latest
       ports:
         - "6006:6006"
       volumes:
         - phoenix-data:/phoenix

     # Optional: LangFuse for testing AWS observability locally
     langfuse:
       image: langfuse/langfuse:latest
       ports:
         - "3001:3000"
       environment:
         - DATABASE_URL=postgresql://langfuse:password@postgres:5432/langfuse
         - NEXTAUTH_SECRET=${LANGFUSE_AUTH_SECRET}
         - NEXTAUTH_URL=http://localhost:3001
       depends_on:
         - postgres

     postgres:
       image: postgres:15
       environment:
         - POSTGRES_USER=langfuse
         - POSTGRES_PASSWORD=password
         - POSTGRES_DB=langfuse
       volumes:
         - postgres-data:/var/lib/postgresql/data

   volumes:
     chroma-data:
     phoenix-data:
     postgres-data:
   ```

3. **Load Testing** (`tests/load/locustfile.py`):
   ```python
   from locust import HttpUser, task, between

   class WorkflowUser(HttpUser):
       wait_time = between(1, 3)

       @task
       def submit_job(self):
           with open("test_urs.txt", "rb") as f:
               self.client.post(
                   "/jobs",
                   files={"file": f},
                   headers={"Authorization": f"Bearer {self.token}"}
               )
   ```

   Run: `locust -f tests/load/locustfile.py --users 10 --spawn-rate 2`

**Deliverables:**
- [ ] Docker images built successfully
- [ ] `docker compose up` runs full stack
- [ ] 10 concurrent jobs processed successfully
- [ ] Resource usage profiled (CPU, memory)
- [ ] Load test report with bottleneck analysis

---

### Phase 4: AWS Deployment & RAG Migration (Weeks 6-9)

**Objectives:**
- Deploy all AWS resources via Terraform
- Migrate ChromaDB embeddings to S3 Vectors
- Validate RAG quality (≥80% overlap)
- Configure autoscaling and monitoring

**Tasks:**

1. **Terraform Modules:**
   ```
   terraform/
   ├── main.tf
   ├── variables.tf
   ├── outputs.tf
   └── modules/
       ├── networking/      # VPC, subnets (minimal, for Aurora only)
       ├── storage/         # S3 buckets, S3 Vectors
       ├── database/        # Aurora Serverless v2
       ├── compute/         # ECS cluster, services, task definitions
       ├── queue/           # SQS queue + DLQ
       ├── observability/   # CloudWatch, LangFuse
       └── edge/            # CloudFront, S3 frontend
   ```

2. **Deploy Infrastructure:**
   ```bash
   cd terraform
   terraform init
   terraform plan -var-file=production.tfvars
   terraform apply
   ```

3. **RAG Migration Script** (`scripts/migrate_rag.py`):
   ```python
   import chromadb
   import boto3
   import json

   # Export from ChromaDB
   chroma_client = chromadb.PersistentClient(path="./chroma_db")
   collection = chroma_client.get_collection("pharma_docs")

   # Get all embeddings
   results = collection.get(include=["embeddings", "metadatas", "documents"])

   # Upload to S3 Vectors
   s3_vectors = boto3.client('s3-vectors', region_name='eu-west-2')

   for i, (embedding, metadata, document) in enumerate(zip(
       results['embeddings'],
       results['metadatas'],
       results['documents']
   )):
       s3_vectors.put_item(
           IndexName='pharma-docs-prod',
           ItemId=f"doc-{i}",
           Vector=embedding,
           Metadata=metadata
       )

   print(f"Migrated {len(results['embeddings'])} documents")
   ```

4. **RAG Validation Test** (`tests/test_rag_migration.py`):
   ```python
   import pytest
   from main.src.adapters.vector_store import VectorStoreProvider

   @pytest.mark.asyncio
   async def test_rag_quality_parity():
       """Validate S3 Vectors retrieval matches ChromaDB (≥80% overlap)."""

       # Load test queries
       queries = load_test_queries()

       # Query both stores
       chromadb_provider = VectorStoreProvider(mode="chromadb")
       s3_provider = VectorStoreProvider(mode="s3_vectors")

       overlaps = []
       for query in queries:
           chromadb_results = await chromadb_provider.query(query, top_k=5)
           s3_results = await s3_provider.query(query, top_k=5)

           # Calculate top-5 overlap
           chromadb_ids = {r['id'] for r in chromadb_results}
           s3_ids = {r['id'] for r in s3_results}
           overlap = len(chromadb_ids & s3_ids) / 5
           overlaps.append(overlap)

       avg_overlap = sum(overlaps) / len(overlaps)
       assert avg_overlap >= 0.80, f"RAG quality degraded: {avg_overlap:.2%}"
   ```

5. **Deploy Application:**
   ```bash
   # Build and push images
   aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <account>.dkr.ecr.eu-west-2.amazonaws.com

   docker build -t pharma-backend:latest .
   docker tag pharma-backend:latest <account>.dkr.ecr.eu-west-2.amazonaws.com/pharma-backend:latest
   docker push <account>.dkr.ecr.eu-west-2.amazonaws.com/pharma-backend:latest

   # Deploy ECS services (Terraform handles this)
   terraform apply -target=module.compute
   ```

**Deliverables:**
- [ ] All Terraform modules applied successfully
- [ ] ECS services running (API + worker)
- [ ] SQS queue integrated
- [ ] ChromaDB migrated to S3 Vectors with ≥80% quality validation
- [ ] CloudWatch dashboards displaying metrics
- [ ] LangFuse capturing traces from production workflows
- [ ] Frontend deployed to S3 + CloudFront
- [ ] End-to-end workflow test passing

---

### Phase 5: Hardening & Backlog Grooming (Weeks 9-10)

**Objectives:**
- Enable S3 Object Lock for audit trail
- Migrate secrets to Secrets Manager
- Configure autoscaling and alarms
- Document rollback procedures
- Groom post-MVP backlog

**Tasks:**

1. **S3 Object Lock:**
   ```hcl
   resource "aws_s3_bucket" "test_output" {
     bucket = "pharma-test-output-prod-eu"

     object_lock_configuration {
       object_lock_enabled = "Enabled"
       rule {
         default_retention {
           mode = "GOVERNANCE"  # Compliance mode for 21 CFR Part 11
           years = 7
         }
       }
     }
   }
   ```

2. **Secrets Manager Migration:**
   ```python
   # main/src/config/secrets.py
   import boto3

   def get_secret(secret_name: str) -> dict:
       client = boto3.client('secretsmanager', region_name='eu-west-2')
       response = client.get_secret_value(SecretId=secret_name)
       return json.loads(response['SecretString'])

   # Usage
   bedrock_key = get_secret("pharma-test-gen/bedrock")
   clerk_key = get_secret("pharma-test-gen/clerk")
   ```

3. **Autoscaling Policies:**
   ```hcl
   resource "aws_appautoscaling_policy" "worker_scale_up" {
     name               = "worker-scale-up"
     service_namespace  = "ecs"
     resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.worker.name}"
     scalable_dimension = "ecs:service:DesiredCount"

     step_scaling_policy_configuration {
       adjustment_type         = "ChangeInCapacity"
       cooldown                = 60
       metric_aggregation_type = "Average"

       step_adjustment {
         metric_interval_lower_bound = 0
         scaling_adjustment          = 1
       }
     }
   }

   resource "aws_cloudwatch_metric_alarm" "sqs_queue_depth" {
     alarm_name          = "worker-queue-depth-high"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "ApproximateNumberOfMessagesVisible"
     namespace           = "AWS/SQS"
     period              = "60"
     statistic           = "Average"
     threshold           = "10"

     alarm_actions = [aws_appautoscaling_policy.worker_scale_up.arn]
   }
   ```

4. **Rollback Playbook** (`docs/runbooks/rollback.md`):
   ```markdown
   # AWS Rollback Procedure

   ## Trigger Conditions
   - Error rate > 10% for 5 minutes
   - P95 latency > 20 minutes
   - Data loss or corruption detected

   ## Steps
   1. Switch DNS to local backup (if available)
   2. Drain SQS queue:
      ```bash
      aws sqs purge-queue --queue-url <queue-url>
      ```
   3. Stop ECS services:
      ```bash
      aws ecs update-service --cluster pharma-prod --service worker --desired-count 0
      aws ecs update-service --cluster pharma-prod --service backend --desired-count 0
      ```
   4. Revert to local stack:
      ```bash
      export ENVIRONMENT=local
      docker compose up -d
      ```
   5. Notify users via status page
   6. Root cause analysis in post-mortem
   ```

**Deliverables:**
- [ ] S3 Object Lock enabled on audit bucket
- [ ] All secrets migrated to Secrets Manager
- [ ] Autoscaling policies tested (scale up/down)
- [ ] CloudWatch alarms configured and validated
- [ ] Rollback playbook validated in staging
- [ ] Post-MVP backlog documented (GuardDuty, Aurora pgvector, digital signatures)
- [ ] Final acceptance review completed

---

## 7. Cost Analysis

### 7.1 Production Cost Estimate (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| **Compute** |
| ECS Fargate (Backend) | 2 vCPU, 4 GB, 2 tasks × 24h | $100 |
| ECS Fargate (Worker) | 4 vCPU, 8 GB, 2 tasks avg × 12h/day | $300 |
| **Database** |
| Aurora Serverless v2 | 1 ACU avg (0.5-2 range) | $150 |
| **Storage** |
| S3 (test output + vectors) | 100 GB standard, 10K PUT, 50K GET | $5 |
| S3 Object Lock | Governance mode, 7-year retention | $10 |
| **RAG** |
| S3 Vectors | 200 docs, 1M queries/month | $5 |
| **LLM** |
| Amazon Bedrock | 50 workflows/day, DeepSeek-V3.1 | $70 |
| **Networking** |
| CloudFront | 10 GB transfer, 1M requests | $5 |
| ALB | 2 ALB, 1M LCU-hours | $40 |
| **Observability** |
| LangFuse Infrastructure | ECS (2 vCPU) + Aurora (0.5 ACU) + Redis | $450 |
| CloudWatch | Logs (10 GB), Metrics (100), Dashboards (5) | $50 |
| **Secrets & Security** |
| Secrets Manager | 10 secrets, 10K retrievals | $5 |
| **Queue** |
| SQS | 1M requests | $0.40 |
| **Total** | | **~$1,190/month** |

### 7.2 Development Cost Estimate (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| ECS Fargate | 1 task each (API + Worker), 8h/day | $40 |
| Aurora Serverless v2 | 0.5 ACU, auto-pause enabled | $20 |
| S3 + CloudFront | Minimal usage | $2 |
| Bedrock (DeepSeek-V3.1) | Testing only, 10 workflows/week | $3 |
| CloudWatch | Basic monitoring | $10 |
| **Total** | | **~$75/month** |

### 7.3 Cost Optimization Strategies

1. **Auto-pause Aurora:** Enable 5-min idle pause in dev/staging
2. **Spot Instances:** Use Fargate Spot for worker tasks (70% savings) - potential $210/month savings
3. **S3 Lifecycle:** Move old test suites to Glacier after 90 days
4. **Bedrock Caching:** Enable prompt caching for system prompts (up to 50% reduction) - potential $35/month savings
5. **Reserved Capacity:** Commit to 1-year Fargate Savings Plan (20% discount) - potential $80/month savings

**Potential Savings:** ~$325/month (27% reduction) = **$865/month** with optimizations

**Cost Comparison:**
- Original estimate (Claude 3.5 Sonnet): $1,320/month
- With DeepSeek-V3.1: $1,190/month (10% reduction)
- With DeepSeek + optimizations: $865/month (34% total reduction)

---

## 8. RAG Migration Guide

### 8.1 Export from ChromaDB

```python
# scripts/export_chromadb.py
import chromadb
import json
from pathlib import Path

def export_chromadb(output_path: str = "rag_export.jsonl"):
    """Export all ChromaDB embeddings to JSONL."""

    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("pharma_docs")

    # Get all documents
    results = collection.get(
        include=["embeddings", "metadatas", "documents"]
    )

    # Write JSONL
    with open(output_path, 'w') as f:
        for i, (emb, meta, doc) in enumerate(zip(
            results['embeddings'],
            results['metadatas'],
            results['documents']
        )):
            record = {
                "id": f"doc-{i}",
                "embedding": emb,
                "metadata": meta,
                "document": doc
            }
            f.write(json.dumps(record) + '\n')

    print(f"Exported {len(results['embeddings'])} documents to {output_path}")

if __name__ == "__main__":
    export_chromadb()
```

### 8.2 Import to S3 Vectors

```python
# scripts/import_s3_vectors.py
import boto3
import json

def import_to_s3_vectors(
    input_path: str = "rag_export.jsonl",
    index_name: str = "pharma-docs-prod",
    region: str = "eu-west-2"
):
    """Import embeddings to S3 Vectors."""

    client = boto3.client('s3-vectors', region_name=region)

    # Create index if not exists
    try:
        client.create_index(
            IndexName=index_name,
            Dimensions=1536,
            Similarity="cosine"
        )
        print(f"Created index: {index_name}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"Index already exists: {index_name}")

    # Import documents
    with open(input_path) as f:
        for line in f:
            record = json.loads(line)

            client.put_item(
                IndexName=index_name,
                ItemId=record['id'],
                Vector=record['embedding'],
                Metadata=record['metadata']
            )

    print(f"Import complete")

if __name__ == "__main__":
    import_to_s3_vectors()
```

### 8.3 Validation

```python
# tests/test_rag_migration.py
import pytest
from main.src.adapters.vector_store import VectorStoreProvider

@pytest.mark.asyncio
async def test_retrieval_parity():
    """Validate S3 Vectors matches ChromaDB."""

    test_queries = [
        "GAMP-5 category 4 software validation",
        "21 CFR Part 11 electronic signatures",
        "ALCOA+ data integrity principles"
    ]

    chromadb = VectorStoreProvider(mode="chromadb")
    s3_vectors = VectorStoreProvider(mode="s3_vectors")

    for query in test_queries:
        # Get embeddings
        from openai import OpenAI
        client = OpenAI()
        embedding = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        ).data[0].embedding

        # Query both
        chromadb_results = await chromadb.query(embedding, top_k=5)
        s3_results = await s3_vectors.query(embedding, top_k=5)

        # Compare IDs
        chromadb_ids = {r['id'] for r in chromadb_results}
        s3_ids = {r['id'] for r in s3_results}

        overlap = len(chromadb_ids & s3_ids) / 5
        print(f"Query: {query[:50]}... | Overlap: {overlap:.0%}")

        assert overlap >= 0.80, f"Low overlap for query: {query}"

@pytest.mark.asyncio
async def test_metadata_filtering():
    """Validate metadata filters work correctly."""

    s3_vectors = VectorStoreProvider(mode="s3_vectors")

    # Query with filter
    results = await s3_vectors.query(
        query_embedding=[0.1] * 1536,  # Dummy
        top_k=5,
        filters={"gamp_category": "4"}
    )

    # Validate all results match filter
    for result in results:
        assert result['metadata']['gamp_category'] == "4"

@pytest.mark.asyncio
async def test_latency():
    """Validate P95 latency ≤ 200ms."""

    import time
    s3_vectors = VectorStoreProvider(mode="s3_vectors")

    latencies = []
    for _ in range(100):
        start = time.time()
        await s3_vectors.query([0.1] * 1536, top_k=5)
        latencies.append((time.time() - start) * 1000)

    latencies.sort()
    p95 = latencies[94]

    print(f"P95 latency: {p95:.1f}ms")
    assert p95 <= 200, f"Latency too high: {p95:.1f}ms"
```

Run migration:
```bash
# 1. Export ChromaDB
python scripts/export_chromadb.py

# 2. Import to S3 Vectors
python scripts/import_s3_vectors.py

# 3. Validate
pytest tests/test_rag_migration.py -v
```

---

## 9. Deployment Procedures

### 9.1 Initial Deployment

```bash
#!/bin/bash
# scripts/deploy_production.sh

set -e

REGION="eu-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

echo "🚀 Starting production deployment"

# 1. Build Docker images
echo "📦 Building images..."
docker build -t pharma-backend:latest -f Dockerfile .
docker build -t pharma-worker:latest -f Dockerfile.worker .

# 2. Tag images
echo "🏷️  Tagging images..."
docker tag pharma-backend:latest $ECR_REGISTRY/pharma-backend:latest
docker tag pharma-worker:latest $ECR_REGISTRY/pharma-worker:latest

# 3. Push to ECR
echo "📤 Pushing to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
docker push $ECR_REGISTRY/pharma-backend:latest
docker push $ECR_REGISTRY/pharma-worker:latest

# 4. Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
cd terraform
terraform init
terraform apply -var-file=production.tfvars -auto-approve

# 5. Run database migrations
echo "💾 Running migrations..."
aws ecs run-task \
  --cluster pharma-prod \
  --task-definition migrate-db \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"

# 6. Deploy frontend
echo "🌐 Deploying frontend..."
cd ../main/frontend
npm run build
aws s3 sync out/ s3://pharma-frontend-prod --delete
aws cloudfront create-invalidation --distribution-id E1234567890 --paths "/*"

# 7. Health check
echo "🏥 Running health checks..."
sleep 30
BACKEND_URL=$(terraform output -raw backend_url)
curl -f $BACKEND_URL/health || exit 1

echo "✅ Deployment complete!"
echo "🔗 Backend: $BACKEND_URL"
echo "🔗 Frontend: https://pharma.example.com"
echo "📊 Monitoring: https://langfuse.pharma.internal"
```

### 9.2 Rollback Procedure

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

echo "⏪ Starting rollback"

# 1. Get previous task definition
PREVIOUS_REVISION=$(aws ecs describe-services \
  --cluster pharma-prod \
  --services backend worker \
  --query 'services[0].deployments[1].taskDefinition' \
  --output text | grep -oP '\d+$')

echo "Rolling back to revision: $PREVIOUS_REVISION"

# 2. Update services
aws ecs update-service \
  --cluster pharma-prod \
  --service backend \
  --task-definition pharma-backend:$PREVIOUS_REVISION \
  --force-new-deployment

aws ecs update-service \
  --cluster pharma-prod \
  --service worker \
  --task-definition pharma-worker:$PREVIOUS_REVISION \
  --force-new-deployment

# 3. Wait for stability
echo "⏳ Waiting for services to stabilize..."
aws ecs wait services-stable \
  --cluster pharma-prod \
  --services backend worker

# 4. Verify health
BACKEND_URL=$(terraform output -raw backend_url)
if curl -f $BACKEND_URL/health; then
  echo "✅ Rollback successful"
else
  echo "❌ Rollback failed - manual intervention required"
  exit 1
fi
```

### 9.3 Update Procedure

```bash
#!/bin/bash
# scripts/update.sh

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Usage: ./update.sh <version>"
  exit 1
fi

echo "🔄 Updating to version $VERSION"

# 1. Build and tag
docker build -t pharma-backend:$VERSION .
docker tag pharma-backend:$VERSION $ECR_REGISTRY/pharma-backend:$VERSION

# 2. Push
docker push $ECR_REGISTRY/pharma-backend:$VERSION

# 3. Update task definition
NEW_TASK_DEF=$(aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

# 4. Rolling update (no downtime)
aws ecs update-service \
  --cluster pharma-prod \
  --service backend \
  --task-definition $NEW_TASK_DEF \
  --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100"

echo "✅ Update initiated"
echo "📊 Monitor: aws ecs describe-services --cluster pharma-prod --services backend"
```

---

## 10. Risks & Mitigations

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| **S3 Vectors quota/availability** | Low | High | Pre-validate service in eu-west-2; maintain ChromaDB fallback; escalate to AWS TAM if needed | Platform Eng |
| **Workflow spikes beyond Fargate limits** | Medium | Medium | Right-size tasks (4 vCPU/8GB); autoscaling min=1, max=4; consider Step Functions if complex orchestration needed | Platform Eng |
| **Bedrock throttling** | Low | Medium | Implement exponential backoff; request quota increase; cache embeddings; evaluate Bedrock Provisioned Throughput | Platform Eng |
| **LangFuse operational complexity** | Medium | Low | Maintain CloudWatch-only fallback profile; consider managed LangFuse Cloud if self-hosted becomes burden | Platform Eng |
| **RAG quality degradation** | Low | High | Validate ≥80% overlap before cutover; A/B test in staging; maintain ChromaDB rollback path for 2 weeks | Data Eng |
| **Clerk EU compliance** | Low | Medium | Use EU data residency settings; document DPIA; validate with legal team | Compliance |
| **Cost overruns** | Medium | Low | Monitor spend daily; set billing alarms at $1,500/month threshold; optimize Fargate Spot + Savings Plans | Finance |
| **Digital signature compliance gap** | Low | Medium | Document as post-MVP enhancement; evaluate AWS Private CA + eIDAS bridge | Compliance |
| **Aurora cold start latency** | Medium | Low | Set min ACU=0.5; consider reserved capacity for prod; pre-warm connections | Platform Eng |
| **Multi-region data residency** | Low | Low | Deferred to post-MVP; evaluate S3 Cross-Region Replication with encryption | Platform Eng |

---

## 11. Post-MVP Backlog

### Security Enhancements
- [ ] Enable AWS GuardDuty for threat detection
- [ ] Integrate AWS Security Hub for compliance dashboard
- [ ] Enable AWS Audit Manager for GAMP-5 automated audits
- [ ] Implement AWS WAF on ALB (DDoS protection, rate limiting)
- [ ] Enable VPC Flow Logs for network forensics
- [ ] Rotate secrets automatically (Secrets Manager rotation)

### Observability Improvements
- [ ] Add AWS X-Ray for distributed tracing
- [ ] Integrate CloudWatch RUM for frontend monitoring
- [ ] Create synthetic canaries (CloudWatch Synthetics)
- [ ] Implement anomaly detection (CloudWatch Anomaly Detection)
- [ ] Export logs to S3 for long-term retention (7 years)

### Compliance & Validation
- [ ] Implement digital signatures (AWS Private CA + eIDAS bridge)
- [ ] Add automated ALCOA+ validation in CI/CD
- [ ] Create compliance report generator (PDF + metadata)
- [ ] Integrate with regulatory submission systems (eCTD)
- [ ] Implement change control workflow (version control + approvals)

### Performance & Scalability
- [ ] Evaluate Aurora pgvector for richer metadata queries
- [ ] Implement Step Functions for complex orchestration
- [ ] Add Redis cache layer for frequently accessed data
- [ ] Evaluate Bedrock Provisioned Throughput for cost predictability
- [ ] Implement multi-region active-active (if needed)

### Developer Experience
- [ ] Create staging environment (multi-account landing zone)
- [ ] Implement blue-green deployments
- [ ] Add automated rollback triggers (error rate thresholds)
- [ ] Create local development seed data generator
- [ ] Improve Terraform module reusability

---

## 12. Acceptance Criteria

### Functional
- [ ] End-to-end workflow completes successfully in AWS (URS upload → test suite download)
- [ ] RAG retrieval matches ChromaDB baseline (≥80% top-5 overlap)
- [ ] All 131 workflow spans captured in LangFuse
- [ ] Clerk authentication functional with EU endpoints
- [ ] Frontend displays job status and test suite viewer

### Performance
- [ ] P95 workflow latency ≤15 minutes (50 documents/day workload)
- [ ] 10 concurrent jobs processed without errors
- [ ] RAG retrieval P95 latency ≤200ms
- [ ] Frontend page load ≤2 seconds (CloudFront cached)

### Operational
- [ ] Infrastructure fully reproducible via Terraform
- [ ] `docker compose up` runs full stack locally
- [ ] Rollback procedure validated (≤1 hour recovery)
- [ ] CloudWatch dashboards displaying all critical metrics
- [ ] LangFuse traces correlated with CloudWatch logs
- [ ] Secrets stored in AWS Secrets Manager (no hardcoded keys)

### Compliance
- [ ] S3 Object Lock enabled on audit bucket (7-year retention)
- [ ] CloudTrail capturing all API calls
- [ ] Clerk JWT verification functional
- [ ] Audit logs table populated with ALCOA+ fields
- [ ] Data residency confirmed (eu-west-2 only)

### Documentation
- [ ] Architecture diagrams updated
- [ ] Runbooks completed (deployment, rollback, incident response)
- [ ] Developer onboarding guide updated
- [ ] Cost analysis report finalized
- [ ] Post-MVP backlog groomed and prioritized

---

## 13. Next Steps

1. **Stakeholder Review:**
   - Present PRP to platform engineering, compliance, and finance teams
   - Confirm region, service limits, and ECS/SQS architecture choice
   - Align on 10-week timeline and MVP scope

2. **Phase 0 Kickoff:**
   - Validate S3 Vectors availability in eu-west-2
   - Create Terraform backend (S3 state + DynamoDB lock)
   - Establish IAM roles for deployment and ECS tasks
   - Enable CloudTrail and Config recording

3. **Weekly Checkpoints:**
   - Monday: Review previous week's deliverables
   - Wednesday: Mid-week progress check and blocker resolution
   - Friday: Demo completed features and adjust timeline if needed

4. **Task-Master AI Integration:**
   - Create tasks in Task-Master AI referencing this PRP
   - Track progress via task status updates
   - Use research capabilities for technical deep-dives

5. **Risk Reviews:**
   - Bi-weekly risk assessment meetings
   - Escalate blockers to AWS TAM or Clerk support as needed
   - Maintain rollback readiness at each phase gate

---

## Appendix A: Technology Stack Summary

| Layer | Local | AWS |
|-------|-------|-----|
| **Frontend** | Next.js (localhost:3000) | S3 + CloudFront |
| **Backend** | FastAPI (localhost:8000) | ECS Fargate + ALB |
| **Worker** | Python async | ECS Fargate |
| **Database** | SQLite / Postgres (dev) | Aurora Serverless v2 |
| **RAG** | ChromaDB | S3 Vectors |
| **LLM** | OpenRouter (dev) | Amazon Bedrock |
| **Queue** | In-memory / Redis | Amazon SQS |
| **Observability** | Phoenix | LangFuse + CloudWatch |
| **Auth** | Clerk (test mode) | Clerk (EU prod) |
| **Secrets** | .env files | Secrets Manager |
| **Deployment** | Docker Compose | Terraform + GitHub Actions |

---

## Appendix B: Contact Information

| Role | Name | Email | Escalation |
|------|------|-------|------------|
| **Platform Engineering Lead** | TBD | platform@pharma.com | CTO |
| **Compliance Officer** | TBD | compliance@pharma.com | VP Quality |
| **AWS Technical Account Manager** | TBD | aws-tam@pharma.com | AWS Support |
| **Clerk Support** | - | support@clerk.dev | Slack channel |
| **LangFuse Support** | - | support@langfuse.com | GitHub issues |

---

**Document Version:** 2.0
**Last Updated:** 2025-11-03
**Next Review:** 2025-11-10 (Phase 0 completion)
**Approved By:** [Pending stakeholder review]

---

*This Production Readiness Plan is a living document and will be updated as the project progresses. All changes should be tracked in version control and communicated to stakeholders.*
