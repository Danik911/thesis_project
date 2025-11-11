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
- **Frontend:** ECS Fargate (containerized Next.js) + CloudFront with Clerk authentication (EU endpoints)
- **Estimated Cost:** ~$1,083/month production average (78% LLM cost reduction vs Claude)
- **Note:** Frontend deployment changed from S3 static to ECS Fargate in Task 2.3 to support API routes

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

#### Frontend (ECS Fargate + CloudFront) - UPDATED Task 2.3
- **Stack:** Next.js 14+ with Pages Router + API Routes
- **Hosting:** ECS Fargate (containerized) + CloudFront CDN
- **Resources:** 1 vCPU, 2 GB RAM, 1-2 tasks
- **Authentication:** Clerk React components (EU endpoints)
- **Pages:** Dashboard, Job Status, Test Suite Viewer, Compliance Reports, Observability (Task 2.3)
- **API Routes:** `/api/langfuse/summary` - LangFuse metrics proxy (Task 2.3)
- **Build:** GitHub Actions → ECR → ECS deployment
- **Cost:** ~$90/month (ECS Fargate + CloudFront)
- **Note:** Changed from S3 static hosting to support server-side API routes for LangFuse integration

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

## 6. Delivery Structure & Stage Gates

### 6.1 Workstream Overview
| Workstream | Scope Focus | Primary Owner | Key Dependencies | Example Alignment |
| --- | --- | --- | --- | --- |
| Backend Services | FastAPI API, ECS workers, async workflow queue | Platform Eng | Storage adapter, Aurora Data API, Bedrock access | Mirrors queue + worker split described in `examples/alex/README.md` and keeps `main/src/core/unified_workflow.py` orchestration intact |
| Frontend Experience | Next.js dashboard, Clerk auth, job polling | Product Eng | Clerk EU tenancy, API contract stability | Follows Alex dashboard pattern for minimal upload/status flows |
| Local Developer Stack | Docker Compose, Phoenix, local RAG parity | DevEx | Storage adapter toggles, vector store abstraction | Uses Alex local stack scripts and avoids new tooling |
| AWS Infrastructure & Observability | Terraform modules, ECS, SQS, LangFuse, CloudWatch | Cloud Platform | IAM guardrails, networking, cost controls | Aligns with Alex IAM & Terraform guide and reuses existing module layout |

### 6.2 Stage Gates With Operational Readiness Reviews
- **Stage 0 - Local Parity:** Harden adapters, jobs API, and UI while retaining local Docker Compose parity. Deliver a lightweight ORR checklist draft that maps existing controls to [AWS OPS07-BP02](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/ops_ready_to_support_const_orr.html) requirements.
- **Stage 1 - Staging (AWS pre-production):** Deploy minimal AWS footprint (ECS/Fargate, S3, Aurora Data API, SQS, LangFuse) using current Terraform modules. Execute a staging ORR and record mitigations using the [Operational Readiness Review whitepaper](https://docs.aws.amazon.com/wellarchitected/latest/operational-readiness-reviews/wa-operational-readiness-reviews.html) template.
- **Stage 2 - Production GA:** Promote staging artifacts after a final ORR sign-off, including rollback drill evidence, cost alarms, and audit runbooks. Gate cutover on demonstrated CloudWatch/LangFuse parity and approval from compliance.

Each gate must include: (1) updated ORR checklist, (2) rollback validation, (3) monitoring dashboards linked in the ORR annex, and (4) open risk log with owners.

### 6.3 Minimal-Change Guardrails
- **Backend Services:** Preserve FastAPI routes and Pydantic schemas; reuse `StorageAdapter`/`VectorStoreProvider` toggles instead of new services; limit workflow edits to dependency injection and logging hooks; no long-running state persisted outside Aurora/S3.
- **Frontend Experience:** Keep existing Next.js routing and Tailwind scaffolding; only add Clerk wrappers, upload widget, and status polling; defer any design refresh; reuse SWR polling cadence from Alex example; no breaking API assumptions.
- **Local Developer Stack:** Maintain current Docker Compose layout and Phoenix instrumentation; feature flags (`ENVIRONMENT`, `USE_S3`, `RAG_MODE`) must default to local-friendly values; avoid extra containers beyond optional LangFuse; continue supporting ChromaDB for offline use.
- **AWS Infrastructure & Observability:** Stick to current Terraform module boundaries; prefer managed defaults (Fargate, Aurora Data API, S3 Vectors) over custom VPC changes; reuse IAM roles/policies already drafted; add logging/alarms through existing observability module to avoid duplicate tooling.

### 6.4 Task Matrix by Stage
| Workstream | Stage 0 - Local Parity (Evidence) | Stage 1 - Staging Hardened (Evidence) | Stage 2 - Production GA (Evidence) |
| --- | --- | --- | --- |
| Backend Services | Finalize storage/vector adapters, Clerk auth verifier, async job submission; run local integration + Locust smoke (`tests/load/locustfile.py`). | Deploy API + worker to staging cluster, connect SQS/Aurora; verify LangFuse traces and S3 Object Lock in staging; run P95 latency + RAG overlap tests. | Enable autoscaling, DLQ alarms, and rollback drill; deliver signed ORR packet with LangFuse dashboards + CloudWatch alert screenshots. |
| Frontend Experience | Implement Clerk wrappers, upload/status pages, compliance badges; Cypress smoke against local API. | Point staging build to AWS endpoints via env config; validate Clerk EU tenancy and job polling; bundle Lighthouse report. | Promote static build to prod S3/CloudFront; capture GA playbook (cache invalidation, feature flag) and monitoring links in ORR annex. |
| Local Developer Stack | Update Docker Compose, ensure phoenix/langfuse toggles, document local run steps in README; record parity demo. | Provide staging vs local comparison doc; run `docker compose` regression with staged feature flags; collect feedback for ORR. | Maintain hotfix workflow (local override path) documented in rollback playbook; ensure developers can reproduce prod issues locally. |
| AWS Infrastructure & Observability | Refresh Terraform backend, IAM scaffolding, cost guardrails; draft ORR checklist sections for compliance/audit. | Apply staging stack, configure S3 Vectors migration test, CloudWatch dashboards, LangFuse in ECS; capture drift reports. | Promote Terraform workspace to prod, enable Object Lock + Secrets Manager, execute cost/monitoring alarms, attach signed rollback drill to ORR package. |

### 6.5 Validation & ORR Packet Contents
- Current ORR checklist with status/mitigations, traceable to OPS05-BP02 (test & validation), OPS06-BP03 (safe deployments), and OPS07-BP02 (operational readiness review cadence).
- Evidence bundle: integration/load-test reports, RAG overlap metrics (>=80%), CloudWatch dashboard exports, LangFuse trace IDs, Clerk audit logs.
- Runbooks: rollback, incident response, and compliance review hosted under `docs/runbooks/` and linked in the ORR annex.
- Sign-off log capturing stakeholders (Platform Eng, Product Eng, Compliance, Security) with decision timestamps.

### 6.6 Post-GA Backlog & Change Control
- Track deferred items (GuardDuty enablement, Aurora pgvector evaluation, digital signature support) in a shared backlog labeled by workstream.
- Enforce change control: any backlog promotion requires reassessing guardrails and updating the ORR checklist before the next release cycle.
- Use LangFuse cost dashboards and Terraform cost estimates to feed quarterly optimization reviews; flag savings opportunities as backlog entries.

## 7. Cost Analysis

### 7.1 Production Cost Estimate (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| **Compute** |
| ECS Fargate (Frontend) | 1 vCPU, 2 GB, 1 task × 24h (Task 2.3) | $40 |
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
| **Total** | | **~$1,230/month** |

**Note:** Frontend cost increased by $40/month vs original S3 static hosting due to Task 2.3 requirement for Next.js API routes (LangFuse observability dashboard).

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

2. **Phase 0 Progress (In Progress):**
   - ✅ **DONE:** Create Terraform backend (S3 state + DynamoDB lock) - Task 0.3 completed
   - ✅ **DONE:** Establish IAM roles for deployment and ECS tasks - Task 0.4 completed
     - Created: pharma-test-gen-deploy (GitHub Actions), pharma-test-gen-ecs-execution, pharma-test-gen-ecs-task
     - Created: GitHub OIDC provider, ECR repositories (backend, worker)
   - ✅ **DONE:** Enable CloudTrail and Config recording - Task 0.2 completed (verified 2025-11-10)
   - 🔄 **PENDING:** Validate S3 Vectors availability in eu-west-2

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

**Document Version:** 2.1
**Last Updated:** 2025-11-10
**Next Review:** 2025-11-17 (Phase 0 completion)
**Approved By:** [Pending stakeholder review]

---

*This Production Readiness Plan is a living document and will be updated as the project progresses. All changes should be tracked in version control and communicated to stakeholders.*


