# Product Overview

## Project Purpose

LLM-Driven Test Generation for Computerised System Validation (CSV) in pharmaceutical/life sciences domain. This system automates the generation of Operational Qualification (OQ) test scripts from User Requirements Specifications (URS) while maintaining strict regulatory compliance with GAMP-5, 21 CFR Part 11, and ALCOA+ principles.

**Research Title**: *Evaluating Efficiency Gains and Security of LLM-Driven Test Generation for Computerised System Validation: A Compliance-Focused Analysis of Life Sciences Testing Processes*

## Value Proposition

- **91% cost reduction** achieved ($1.35 vs $15 per 1M tokens) using DeepSeek V3 via OpenRouter
- **76.7% success rate** with 316 valid OQ tests generated across 30 documents
- **91.3% GAMP-5 categorization accuracy** with Cohen's Kappa = 0.817 (almost perfect agreement)
- **100% regulatory compliance** for all generated tests (GAMP-5, 21 CFR Part 11, ALCOA+)
- **Zero fallback policy** - explicit error handling prevents silent failures

## Key Features

### Multi-Agent System Architecture
- **GAMP-5 Categorization Agent**: Determines software category (3, 4, 5) per ISPE GAMP-5 guidelines
- **Context Provider Agent**: Retrieves regulatory context from ChromaDB (26 indexed documents)
- **Research Agent**: Augments context with external regulatory sources
- **SME Agent**: Performs technical and compliance sanity checks on planned tests
- **OQ Generator Agent**: Produces compliant OQ test suites using DeepSeek V3 (671B MoE)

### Compliance & Security
- **OWASP LLM Top 10 Mitigations**: StruQ structured queries, isolated training, Llama Guard integration
- **ALCOA+ Validator**: Ensures data integrity principles (Attributable, Legible, Contemporaneous, Original, Accurate)
- **Traceability Matrix**: Bidirectional mapping between requirements and test cases
- **Audit Trail**: Complete workflow traces with LangFuse Cloud observability

### Production Infrastructure
- **Docker Compose Stack**: 5-service architecture (postgres, localstack, api, worker, frontend)
- **FastAPI Backend**: RESTful API with Clerk JWT authentication
- **Next.js Frontend**: Web UI for URS upload, job tracking, test suite download
- **LangFuse Cloud**: EU-compliant observability with automatic trace capture via @observe decorators
- **ChromaDB**: Vector store for regulatory document retrieval (GAMP-5, ICH Q9, FDA Part 11)

## Target Users

### Primary Users
- **Pharmaceutical QA Engineers**: Generate OQ test scripts from URS documents
- **Validation Specialists**: Ensure computerised system compliance with regulatory standards
- **Quality Assurance Teams**: Automate CSV workflows while maintaining audit trails

### Secondary Users
- **Regulatory Affairs**: Review compliance documentation and traceability matrices
- **Software Developers**: Integrate test generation into CI/CD pipelines
- **Academic Researchers**: Study LLM efficiency in regulated industries

## Use Cases

### 1. Automated OQ Test Generation
**Input**: User Requirements Specification (URS) document (Markdown, PDF, or text)
**Process**: 
1. Upload URS via frontend or API
2. GAMP-5 categorization (Category 3, 4, or 5)
3. Parallel agent execution (Context, Research, SME)
4. OQ test suite generation with DeepSeek V3
5. ALCOA+ validation and traceability matrix creation
**Output**: YAML test suite with 13.7 tests average per document

### 2. Regulatory Compliance Validation
**Input**: Generated test suite
**Process**: 
1. ALCOA+ validator checks data integrity principles
2. OWASP LLM scanner detects security risks
3. Traceability matrix validates requirement coverage
**Output**: Compliance report with pass/fail status

### 3. Cross-Validation Analysis
**Input**: 30 diverse URS documents across 3 corpora
**Process**: 
1. Stratified sampling with category distribution
2. Statistical analysis (Cohen's Kappa, confidence intervals)
3. Performance benchmarking (cost, time, accuracy)
**Output**: Thesis evidence package with 517 traces and visualizations

### 4. Human-in-the-Loop Consultation
**Input**: Ambiguous URS or low-confidence categorization
**Process**: 
1. System detects ambiguity (confidence < 0.4)
2. Prompts user for clarification via frontend
3. User provides guidance or approves categorization
**Output**: Refined categorization with audit trail

## Validated Performance Metrics

| Metric | Target | Achieved |
|--------|---------|----------|
| Cost Reduction | 70% | **91%** ✅ |
| Generation Time | <10 min | **7.7 min avg** ✅ |
| Success Rate | ≥85% | **76.7%** (23/30) ⚠️ |
| Categorization Accuracy | ≥80% | **91.3%** ✅ |
| Tests Generated | 250-300 | **316 total** ✅ |
| Cohen's Kappa | >0.8 | **0.817** ✅ |
| False Positive Rate | <5% | **0%** ✅ |
| ALCOA+ Compliance | 100% | **100%** ✅ |

## Research Contributions

1. **First quantitative evaluation** of LLM efficiency in pharmaceutical CSV
2. **Novel security framework** for LLM-generated validation artifacts
3. **Compliance-aware AI architecture** for regulated industries
4. **Open-source implementation** with reproducible benchmarks

## Deployment Status

- ✅ **Local Development**: Docker Compose stack fully operational
- ✅ **Observability**: LangFuse Cloud integration with EU data residency
- ✅ **Frontend**: Next.js UI with Clerk authentication
- ⏳ **AWS Deployment**: Terraform infrastructure ready (Phase 4 planned)
- ⏳ **CloudFront CDN**: Planned for production frontend delivery
