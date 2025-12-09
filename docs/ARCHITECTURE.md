# System Architecture

Multi-agent LLM system for pharmaceutical test generation with GAMP-5 compliance.

## High-Level Architecture

```mermaid
graph TD
    URS[URS Document] --> CAT[GAMP-5 Categorization Agent]
    CAT --> CTX[Context Provider Agent]
    CAT --> RES[Research Agent]
    CAT --> SME[SME Agent]
    CTX --> OQ[OQ Generator Agent]
    RES --> OQ
    SME --> OQ
    OQ --> TS[Test Suite]
    TS --> LF[LangFuse Cloud Tracing]
```

## Core Agents

### GAMP-5 Categorization Agent

Determines software category per ISPE GAMP-5 guidelines:

```python
# main/src/agents/categorization/agent.py
class GAMPCategorizationWorkflow(Workflow):
    @step
    @observe(name="gamp_categorization")
    async def categorize(self, ctx: Context, ev: StartEvent) -> StopEvent:
        indicators = self._extract_gamp_indicators(ev.urs_content)
        response = await self.llm.astructured_predict(
            output_cls=GAMPCategoryOutput,
            prompt=self._build_categorization_prompt(indicators),
            temperature=0.1
        )

        # NO FALLBACKS - explicit failure on low confidence
        if response.confidence < 0.8:
            raise HumanConsultationRequiredEvent(
                reason=f"Low confidence: {response.confidence}",
                suggested_category=response.category
            )
        return StopEvent(result=response)
```

### Context Provider (ChromaDB RAG)

Retrieves regulatory context from 26 indexed pharmaceutical documents:

```python
# main/src/agents/parallel/context_provider.py
class ContextProviderAgent:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_collection("pharmaceutical_regulations")

    async def get_regulatory_context(
        self, urs_content: str, gamp_category: GAMPCategory
    ) -> RegulatoryContext:
        query_embedding = self.embed_model.get_text_embedding(urs_content)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={"category": gamp_category.value}
        )
        return RegulatoryContext(
            gamp_requirements=self._extract_gamp_requirements(results),
            cfr_requirements=self._extract_cfr_requirements(results),
            alcoa_principles=self._map_alcoa_principles(results)
        )
```

### OQ Test Generator

Generates test suites using DeepSeek V3 via OpenRouter:

```python
# main/src/agents/oq_generator/generator.py
class OQTestGenerator:
    def __init__(self, llm: LLM):
        self.llm = llm  # DeepSeek V3 via OpenRouter
        self.yaml_parser = EnhancedYAMLParser()

    @observe(name="oq_test_generation")
    async def generate_oq_test_suite(
        self, gamp_category: GAMPCategory,
        urs_content: str, context_data: Dict, config: OQGenerationConfig
    ) -> OQTestSuite:
        prompt = self._build_generation_prompt(
            urs_content=urs_content,
            gamp_category=gamp_category,
            regulatory_context=context_data.get("regulatory_context"),
            target_count=config.target_test_count
        )
        response = await self.llm.acomplete(prompt, temperature=0.1, max_tokens=30000)
        test_suite = self.yaml_parser.parse_and_validate(response.text)
        self._validate_alcoa_compliance(test_suite)
        return test_suite
```

---

## Compliance Implementation

### ALCOA+ Validation

```python
# main/src/validation/alcoa_validator.py
class ALCOAPlusValidator:
    PRINCIPLES = {
        "Attributable": self._validate_attribution,
        "Legible": self._validate_legibility,
        "Contemporaneous": self._validate_contemporaneous,
        "Original": self._validate_originality,
        "Accurate": self._validate_accuracy,
        "Complete": self._validate_completeness,
        "Consistent": self._validate_consistency,
        "Enduring": self._validate_enduring,
        "Available": self._validate_availability
    }

    @observe(name="alcoa_validation")
    def validate_test_suite(self, suite: OQTestSuite) -> ValidationResult:
        for principle, validator in self.PRINCIPLES.items():
            result = validator(suite)
            if not result.passed:
                raise ALCOAViolationError(principle=principle, details=result.details)
        return ValidationResult(passed=True, principles=results)
```

### Traceability Matrix

```python
# main/src/validation/traceability.py
class TraceabilityMatrix:
    def build_matrix(
        self, urs_requirements: List[Requirement], test_cases: List[OQTestCase]
    ) -> pd.DataFrame:
        matrix = pd.DataFrame(
            index=[req.id for req in urs_requirements],
            columns=[test.test_id for test in test_cases]
        )
        for req in urs_requirements:
            for test in test_cases:
                similarity = self._calculate_similarity(req.description, test.objective)
                if similarity > 0.85:
                    matrix.loc[req.id, test.test_id] = 1
        return matrix
```

---

## Security Implementation

### OWASP LLM Top 10 Validation

```python
# main/src/security/owasp_validator.py
class OWASPLLMValidator:
    def validate_generated_tests(self, test_suite: OQTestSuite) -> SecurityReport:
        vulnerabilities = []

        # LLM01: Prompt Injection Prevention
        if self._detect_prompt_injection(test_suite):
            vulnerabilities.append(VulnerabilityReport(risk="LLM01", severity="HIGH"))

        # LLM06: Insecure Output Handling
        for test in test_suite.test_cases:
            insecure_patterns = self._scan_insecure_patterns(test.test_steps)
            if insecure_patterns:
                vulnerabilities.append(VulnerabilityReport(risk="LLM06", severity="MEDIUM"))

        return SecurityReport(vulnerabilities=vulnerabilities)
```

---

## LangFuse Observability

### Automatic Tracing

```python
# main/api/observability.py
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

langfuse_client = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

@observe(name="unified_workflow_execution")
async def execute_unified_workflow(urs_content: str, job_id: str):
    langfuse_context.update_current_trace(
        name="pharmaceutical_test_generation",
        user_id=job_id,
        tags=["pharmaceutical", "gamp5", "oq_generation"],
        metadata={"framework": "GAMP-5", "regulatory_standard": "21 CFR Part 11"}
    )
    workflow = UnifiedTestGenerationWorkflow()
    return await workflow.run(urs_content=urs_content)
```

### Audit Trail Generation

```python
# main/src/compliance/audit_trail.py
@observe(name="audit_trail_generation")
def generate_alcoa_audit_trail(job_id: str, workflow_result: dict) -> dict:
    return {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "trace_id": langfuse_context.get_current_trace_id(),
        "compliance_metadata": {
            "gamp_category": workflow_result.get("gamp_category"),
            "alcoa_validated": True,
            "cfr_part11_compliant": True
        }
    }
```

---

## Docker Stack

5-service Docker Compose architecture:

| Service | Purpose | Technology |
|---------|---------|------------|
| **postgres** | Job queue metadata | PostgreSQL 15 + pgvector |
| **localstack** | AWS SQS emulation | LocalStack 3.9.0 |
| **api** | REST API endpoints | FastAPI + uvicorn |
| **worker** | Async workflow executor | Python asyncio |
| **frontend** | Job submission UI | Next.js 14 |

```yaml
# docker-compose.dev.yml (key services)
services:
  postgres:
    image: ankane/pgvector:v0.8.1
    environment:
      POSTGRES_DB: pharma_tests
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]

  api:
    build:
      dockerfile: Dockerfile.api
    ports:
      - "8080:8080"
    environment:
      LANGFUSE_HOST: https://cloud.langfuse.com
      LLM_MODEL: deepseek/deepseek-chat
    depends_on:
      postgres:
        condition: service_healthy

  worker:
    build:
      dockerfile: Dockerfile.api
    command: python main/api/worker.py
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
```

**Job Queue Flow:**
```
API → PostgreSQL → SQS → Worker → LangFuse traces
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| LLM (Production) | DeepSeek V3.1 via OpenRouter |
| LLM (Development) | Gemini 2.5 Flash Lite |
| Observability | LangFuse Cloud (EU) |
| Vector Store | ChromaDB |
| Authentication | Clerk |
| Backend | FastAPI |
| Frontend | Next.js 14 (Pages Router) |
| Queue | AWS SQS (LocalStack for dev) |
| Database | PostgreSQL + pgvector |
| IaC | Terraform |

---

## Environment Configuration

```bash
# .env.local
# LLM
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=deepseek/deepseek-chat
EMBEDDING_MODEL=text-embedding-3-small

# LangFuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Clerk
CLERK_SECRET_KEY=sk_test_...
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/pharma_tests

# RAG
RAG_VECTOR_STORE_PATH=/app/chroma_db
RAG_COLLECTION_NAME=pharmaceutical_regulations
```

---

## Code Structure

```
thesis_project/
├── main/
│   ├── src/
│   │   ├── core/unified_workflow.py      # Master orchestrator
│   │   ├── agents/
│   │   │   ├── categorization/           # GAMP-5 categorizer
│   │   │   ├── oq_generator/             # Test generator
│   │   │   └── parallel/                 # Context, Research, SME
│   │   ├── validation/
│   │   │   ├── alcoa_validator.py        # ALCOA+ implementation
│   │   │   └── traceability.py           # Requirements mapping
│   │   └── security/owasp_validator.py   # Security controls
│   ├── api/
│   │   ├── app.py                        # FastAPI application
│   │   └── worker.py                     # Background job processor
│   └── tests/
├── frontend/                             # Next.js dashboard
├── aws/terraform/                        # AWS infrastructure
└── docker-compose.dev.yml
```
