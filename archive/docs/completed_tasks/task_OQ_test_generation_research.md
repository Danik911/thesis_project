# OQ Test Generation Agent Research and Context

## Research and Context (by context-collector)

This document provides comprehensive research and implementation guidance for developing an OQ (Operational Qualification) test generation agent for the pharmaceutical multi-agent system, based on GAMP-5 compliance requirements and LlamaIndex 0.12.0+ workflow patterns.

### Code Examples and Patterns

#### 1. LlamaIndex Workflow Event-Driven Architecture

Based on the existing project structure and LlamaIndex documentation, the OQ test generation agent should follow the established event-driven workflow pattern:

```python
class OQTestGenerationEvent(Event):
    """Event containing OQ test generation requirements."""
    gamp_category: GAMPCategory
    test_strategy: dict[str, Any]
    urs_content: str
    document_metadata: dict[str, Any]
    required_test_count: int  # Category-specific (Cat 3: 5-10, Cat 4: 15-20, Cat 5: 25-30)
    compliance_requirements: list[str]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

class OQTestSuiteEvent(Event):
    """Event containing generated OQ test suite."""
    generated_tests: list[OQTestCase]
    traceability_matrix: dict[str, list[str]]
    coverage_analysis: dict[str, float]
    compliance_checklist: dict[str, bool]
    validation_metadata: dict[str, Any]
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

#### 2. Pydantic Model Design for OQ Test Structures

Following the project's structured output patterns with LLMTextCompletionProgram:

```python
class OQTestCase(BaseModel):
    """Individual OQ test case with pharmaceutical compliance."""
    test_id: str = Field(..., pattern=r"^OQ-\d{3}$", description="Test identifier (e.g., OQ-001)")
    test_name: str = Field(..., min_length=10, max_length=100, description="Descriptive test name")
    test_category: Literal["installation", "functional", "performance", "security", "data_integrity"]
    gamp_category: int = Field(..., ge=1, le=5, description="Associated GAMP category")
    
    # Test Structure
    objective: str = Field(..., min_length=20, description="Clear test objective")
    prerequisites: list[str] = Field(default_factory=list, description="Required conditions")
    test_steps: list[TestStep] = Field(..., min_items=1, description="Detailed test procedures")
    acceptance_criteria: list[str] = Field(..., min_items=1, description="Pass/fail criteria")
    
    # Compliance Fields
    regulatory_basis: list[str] = Field(default_factory=list, description="Regulatory references")
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"
    data_integrity_requirements: list[str] = Field(default_factory=list)
    
    # Traceability
    urs_requirements: list[str] = Field(default_factory=list, description="Traced URS requirements")
    related_tests: list[str] = Field(default_factory=list, description="Related test IDs")

class TestStep(BaseModel):
    """Individual test step with ALCOA+ compliance."""
    step_number: int = Field(..., ge=1, description="Sequential step number")
    action: str = Field(..., min_length=10, description="Action to perform")
    expected_result: str = Field(..., min_length=10, description="Expected outcome")
    data_to_capture: list[str] = Field(default_factory=list, description="Data points to record")
    verification_method: str = Field(default="visual_inspection", description="How to verify result")

class OQTestSuite(BaseModel):
    """Complete OQ test suite with category-specific structure."""
    suite_id: str = Field(..., pattern=r"^OQ-SUITE-\d{4}$")
    gamp_category: int = Field(..., ge=1, le=5)
    document_name: str = Field(..., min_length=1)
    
    # Test Organization
    test_cases: list[OQTestCase] = Field(..., min_items=1)
    test_categories: dict[str, int] = Field(default_factory=dict, description="Test count by category")
    
    # Coverage Analysis
    requirements_coverage: dict[str, list[str]] = Field(default_factory=dict)
    risk_coverage: dict[str, int] = Field(default_factory=dict)
    compliance_coverage: dict[str, bool] = Field(default_factory=dict)
    
    # Validation Metadata
    generation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    total_test_count: int = Field(..., ge=1)
    estimated_execution_time: int = Field(..., ge=1, description="Minutes")

    @field_validator("test_cases")
    @classmethod
    def validate_category_test_count(cls, v: list[OQTestCase], info) -> list[OQTestCase]:
        """Validate test count meets GAMP category requirements."""
        if not hasattr(info.data, 'gamp_category'):
            return v
            
        gamp_category = info.data.get('gamp_category')
        test_count = len(v)
        
        # GAMP category test count requirements
        min_tests = {1: 3, 3: 5, 4: 15, 5: 25}
        max_tests = {1: 5, 3: 10, 4: 20, 5: 30}
        
        min_required = min_tests.get(gamp_category, 5)
        max_allowed = max_tests.get(gamp_category, 30)
        
        if test_count < min_required:
            raise ValueError(f"Category {gamp_category} requires minimum {min_required} tests, got {test_count}")
        if test_count > max_allowed:
            raise ValueError(f"Category {gamp_category} allows maximum {max_allowed} tests, got {test_count}")
            
        return v
```

#### 3. LLMTextCompletionProgram Usage Pattern

Following the project's established pattern for structured output without JSON mode:

```python
def generate_oq_tests_with_structured_output(
    llm: LLM,
    gamp_category: int,
    urs_content: str,
    context_data: dict[str, Any],
    document_name: str = "Unknown"
) -> OQTestSuite:
    """Generate OQ test suite using LLMTextCompletionProgram with Pydantic validation."""
    
    # Category-specific test requirements
    test_requirements = {
        1: {"min_tests": 3, "max_tests": 5, "focus": "installation_verification"},
        3: {"min_tests": 5, "max_tests": 10, "focus": "functional_testing"},
        4: {"min_tests": 15, "max_tests": 20, "focus": "configuration_verification"},
        5: {"min_tests": 25, "max_tests": 30, "focus": "comprehensive_validation"}
    }
    
    requirements = test_requirements.get(gamp_category, test_requirements[5])
    
    oq_generation_prompt = """You are an expert pharmaceutical validation engineer specializing in GAMP-5 OQ test generation.

Generate a comprehensive OQ test suite for the following system:

GAMP Category: {gamp_category}
Document: {document_name}
Test Requirements: {min_tests}-{max_tests} tests focusing on {focus}

URS Content:
{urs_content}

Context Information:
{context_summary}

CRITICAL REQUIREMENTS:
1. Generate {min_tests}-{max_tests} test cases appropriate for GAMP Category {gamp_category}
2. Each test must have clear objectives, steps, and acceptance criteria
3. Include traceability to URS requirements
4. Ensure ALCOA+ compliance for all data integrity requirements
5. Follow pharmaceutical industry best practices for OQ testing

Test Categories to Include:
- Installation verification (if applicable)
- Functional testing (core features)
- Data integrity verification
- Security and access control testing
- Performance testing (if applicable)
- Integration testing (if applicable)

Respond with a valid JSON structure matching the OQTestSuite schema."""

    program = LLMTextCompletionProgram.from_defaults(
        output_cls=OQTestSuite,
        llm=llm,
        prompt_template_str=oq_generation_prompt
    )
    
    # Prepare context summary
    context_summary = _prepare_context_summary(context_data) if context_data else "No additional context available"
    
    # Execute structured generation
    result = program(
        gamp_category=gamp_category,
        document_name=document_name,
        min_tests=requirements["min_tests"],
        max_tests=requirements["max_tests"],
        focus=requirements["focus"],
        urs_content=urs_content[:8000],  # Truncate for token limits
        context_summary=context_summary
    )
    
    return result

def _prepare_context_summary(context_data: dict[str, Any]) -> str:
    """Prepare context summary for test generation."""
    summary_parts = []
    
    if regulatory_docs := context_data.get("regulatory_documents"):
        summary_parts.append(f"Regulatory Context: {len(regulatory_docs)} relevant documents found")
    
    if best_practices := context_data.get("best_practices"):
        summary_parts.append(f"Best Practices: {len(best_practices)} patterns identified")
    
    if validation_context := context_data.get("validation_context"):
        test_strategy = validation_context.get("test_strategy_alignment", {})
        if test_strategy:
            summary_parts.append(f"Test Strategy: {', '.join(test_strategy.keys())}")
    
    return "; ".join(summary_parts) if summary_parts else "Standard validation approach recommended"
```

#### 4. Workflow Integration Pattern

Following the existing unified workflow architecture:

```python
class OQTestGenerationWorkflow(Workflow):
    """OQ test generation workflow step in the broader pharmaceutical validation system."""
    
    @step
    async def generate_oq_tests(
        self, 
        ctx: Context, 
        ev: OQTestGenerationEvent
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """Generate OQ test suite based on GAMP category and context."""
        
        # Validate prerequisites
        if ev.gamp_category not in [1, 3, 4, 5]:
            raise ValueError(f"Invalid GAMP category: {ev.gamp_category}")
        
        # Get LLM instance
        llm = await ctx.store.get("llm")
        if not llm:
            from llama_index.llms.openai import OpenAI
            llm = OpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=4000)
            await ctx.store.set("llm", llm)
        
        # Aggregate context from previous agents
        context_data = await self._aggregate_agent_context(ctx)
        
        try:
            # Generate test suite using structured output
            test_suite = generate_oq_tests_with_structured_output(
                llm=llm,
                gamp_category=ev.gamp_category.value,
                urs_content=ev.urs_content,
                context_data=context_data,
                document_name=ev.document_metadata.get("name", "Unknown")
            )
            
            # Validate test suite quality
            quality_issues = await self._validate_test_suite_quality(test_suite, ev)
            
            if quality_issues:
                # Request human consultation for quality issues
                return ConsultationRequiredEvent(
                    consultation_type="test_suite_quality_review",
                    context={
                        "quality_issues": quality_issues,
                        "generated_tests": test_suite.model_dump(),
                        "gamp_category": ev.gamp_category.value,
                        "document_name": ev.document_metadata.get("name")
                    },
                    urgency="normal",
                    required_expertise=["validation_engineer", "gamp_expert"],
                    triggering_step="generate_oq_tests"
                )
            
            # Create successful result event
            return OQTestSuiteEvent(
                generated_tests=[test.model_dump() for test in test_suite.test_cases],
                traceability_matrix=test_suite.requirements_coverage,
                coverage_analysis={
                    "requirements_coverage": len(test_suite.requirements_coverage) / max(1, len(ev.urs_content.split('\n'))),
                    "risk_coverage": sum(test_suite.risk_coverage.values()) / max(1, len(test_suite.risk_coverage)),
                    "test_category_distribution": test_suite.test_categories
                },
                compliance_checklist=test_suite.compliance_coverage,
                validation_metadata={
                    "gamp_category": ev.gamp_category.value,
                    "total_tests": test_suite.total_test_count,
                    "generation_method": "LLMTextCompletionProgram",
                    "context_quality": context_data.get("context_quality", "unknown"),
                    "estimated_execution_time": test_suite.estimated_execution_time
                }
            )
            
        except Exception as e:
            # NO FALLBACKS: Explicit error handling with full diagnostic information
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "gamp_category": ev.gamp_category.value,
                "document_name": ev.document_metadata.get("name", "Unknown"),
                "urs_content_length": len(ev.urs_content),
                "context_available": bool(context_data)
            }
            
            # Log error with full context
            logger.error(f"OQ test generation failed: {error_details}")
            
            # Request human consultation for generation failure
            return ConsultationRequiredEvent(
                consultation_type="test_generation_failure",
                context=error_details,
                urgency="high",
                required_expertise=["validation_engineer", "system_administrator"],
                triggering_step="generate_oq_tests"
            )
    
    async def _aggregate_agent_context(self, ctx: Context) -> dict[str, Any]:
        """Aggregate context from parallel agents (SME, Research, Context Provider)."""
        context_data = {}
        
        # Get context provider results
        if context_result := await ctx.store.get("context_provider_result"):
            context_data.update(context_result)
        
        # Get SME agent insights
        if sme_result := await ctx.store.get("sme_agent_result"):
            context_data["sme_insights"] = sme_result
        
        # Get research agent findings
        if research_result := await ctx.store.get("research_agent_result"):
            context_data["research_findings"] = research_result
        
        return context_data
    
    async def _validate_test_suite_quality(
        self, 
        test_suite: OQTestSuite, 
        original_event: OQTestGenerationEvent
    ) -> list[str]:
        """Validate generated test suite meets quality standards."""
        issues = []
        
        # Check test count compliance
        category_requirements = {1: (3, 5), 3: (5, 10), 4: (15, 20), 5: (25, 30)}
        min_tests, max_tests = category_requirements.get(original_event.gamp_category.value, (5, 30))
        
        if test_suite.total_test_count < min_tests:
            issues.append(f"Insufficient tests: {test_suite.total_test_count} < {min_tests} required for Category {original_event.gamp_category.value}")
        
        if test_suite.total_test_count > max_tests:
            issues.append(f"Excessive tests: {test_suite.total_test_count} > {max_tests} allowed for Category {original_event.gamp_category.value}")
        
        # Check coverage requirements
        if len(test_suite.requirements_coverage) == 0:
            issues.append("No traceability to URS requirements established")
        
        # Check compliance coverage
        required_compliance = ["data_integrity", "audit_trail", "user_access_control"]
        missing_compliance = [req for req in required_compliance if not test_suite.compliance_coverage.get(req, False)]
        if missing_compliance:
            issues.append(f"Missing compliance coverage: {', '.join(missing_compliance)}")
        
        # Check test step completeness
        incomplete_tests = [
            test.test_id for test in test_suite.test_cases 
            if len(test.test_steps) == 0 or len(test.acceptance_criteria) == 0
        ]
        if incomplete_tests:
            issues.append(f"Incomplete test definitions: {', '.join(incomplete_tests[:5])}")
        
        return issues
```

### Implementation Gotchas

#### 1. LLMTextCompletionProgram Compatibility Issues

**Critical Issue**: The project documentation explicitly warns against using `response_format={"type": "json_object"}` with LlamaIndex `FunctionAgent` as it causes infinite loops. This applies to OQ test generation:

```python
# ❌ AVOID: JSON mode with FunctionAgent causes infinite loops
llm = OpenAI(
    model="gpt-4o-mini",
    response_format={"type": "json_object"}  # DO NOT USE WITH FunctionAgent
)

# ✅ CORRECT: Use LLMTextCompletionProgram for structured output
program = LLMTextCompletionProgram.from_defaults(
    output_cls=OQTestSuite,
    llm=llm  # Without JSON mode
)
```

#### 2. GAMP Category Test Count Validation

**Issue**: Test count requirements vary significantly by GAMP category and must be enforced both at generation and validation:

```python
# Critical validation in Pydantic model
@field_validator("test_cases")
@classmethod
def validate_category_test_count(cls, v: list[OQTestCase], info) -> list[OQTestCase]:
    # Must check against category-specific requirements
    gamp_category = info.data.get('gamp_category')
    requirements = {1: (3, 5), 3: (5, 10), 4: (15, 20), 5: (25, 30)}
    # Validation logic here
```

#### 3. Context Aggregation Timing

**Issue**: OQ test generation depends on outputs from multiple parallel agents (SME, Research, Context Provider). Timing coordination is critical:

```python
# Ensure all parallel agents complete before OQ generation
@step
async def coordinate_parallel_agents(self, ctx: Context, ev: PlanningEvent) -> OQTestGenerationEvent:
    # Use ctx.collect_events to wait for all parallel agent results
    parallel_results = ctx.collect_events(ev, [
        AgentResultEvent,  # SME results
        AgentResultEvent,  # Research results  
        AgentResultEvent,  # Context Provider results
    ])
    
    if parallel_results is None:
        return None  # Wait for more events
    
    # Now safe to proceed with aggregated context
```

#### 4. Token Limit Management

**Issue**: OQ test generation for Category 5 systems (25-30 tests) can exceed LLM token limits:

```python
# Implement progressive generation for large test suites
async def generate_large_test_suite(self, gamp_category: int, urs_content: str) -> OQTestSuite:
    if gamp_category == 5 and self._estimate_token_count(urs_content) > 6000:
        # Generate in batches of 5-8 tests
        test_batches = []
        for batch_num in range(4):  # 4 batches for Category 5
            batch_tests = await self._generate_test_batch(urs_content, batch_num, 6)
            test_batches.extend(batch_tests)
        return self._combine_test_batches(test_batches)
    else:
        # Standard single-generation approach
        return self._generate_full_suite(urs_content)
```

#### 5. Pharmaceutical Compliance Validation

**Issue**: Generated tests must meet pharmaceutical validation standards beyond basic structure validation:

```python
# Implement pharmaceutical-specific validation
async def validate_pharmaceutical_compliance(self, test_suite: OQTestSuite) -> list[str]:
    compliance_issues = []
    
    # Check ALCOA+ compliance
    for test in test_suite.test_cases:
        if not self._has_alcoa_plus_compliance(test):
            compliance_issues.append(f"Test {test.test_id} lacks ALCOA+ compliance")
    
    # Check 21 CFR Part 11 requirements
    if not self._has_electronic_signature_requirements(test_suite):
        compliance_issues.append("Missing electronic signature requirements")
    
    # Check audit trail requirements
    if not self._has_audit_trail_verification(test_suite):
        compliance_issues.append("Missing audit trail verification tests")
    
    return compliance_issues
```

### Regulatory Considerations

#### GAMP-5 Category-Specific Requirements

**Category 1 (Infrastructure)**: 3-5 tests focusing on installation qualification and operational procedures. Minimal functional testing since these are standard infrastructure components.

**Category 3 (Non-configured COTS)**: 5-10 tests emphasizing standard functionality verification. Tests must demonstrate fitness-for-use without configuration complexity.

**Category 4 (Configured Products)**: 15-20 tests requiring comprehensive configuration verification, business process testing, and integration validation. Highest complexity-to-risk ratio.

**Category 5 (Custom Applications)**: 25-30 tests demanding full software development lifecycle validation including unit testing concepts, integration testing, system testing, and comprehensive acceptance testing.

#### ALCOA+ Principles Integration

All generated OQ tests must incorporate ALCOA+ data integrity principles:

- **Attributable**: Each test step must clearly identify who performed the action
- **Legible**: All test procedures must be clearly written and understandable
- **Contemporaneous**: Data capture must occur at time of testing
- **Original**: Tests must work with original data sources
- **Accurate**: Test procedures must accurately reflect system functionality
- **Complete**: All required testing aspects must be covered
- **Consistent**: Test formats and procedures must be standardized
- **Enduring**: Test records must be preserved for regulatory timelines
- **Available**: Test documentation must be retrievable for inspection

#### 21 CFR Part 11 Electronic Records Compliance

Generated OQ tests must include verification of:

- Electronic signature functionality and validation
- Audit trail completeness and tamper-evidence
- User authentication and authorization controls
- Data backup and recovery procedures
- System security and access controls

### Recommended Libraries and Versions

#### Core Dependencies

```python
# requirements.txt additions for OQ test generation
llama-index-core>=0.12.0  # Event-driven workflows
llama-index-llms-openai>=0.3.0  # LLM integration
pydantic>=2.8.0  # Structured data validation
pydantic[email]>=2.8.0  # Extended validation features

# Pharmaceutical-specific dependencies
chempy>=0.8.0  # Chemical data validation (if needed)
openpyxl>=3.1.0  # Excel output for regulatory submission
python-docx>=1.1.0  # Word document generation for protocols
```

#### Version Constraints and Compatibility

**Critical**: The project uses LlamaIndex 0.12.0+ which has significant API changes from 0.10.x versions. Ensure compatibility:

```python
# Compatible pattern for 0.12.0+
from llama_index.core.workflow import Workflow, step, Event, Context
from llama_index.core.program import LLMTextCompletionProgram

# NOT compatible with 0.10.x
# from llama_index import Workflow  # Old API
```

#### Development Environment Setup

```bash
# Recommended setup command
uv add llama-index-core>=0.12.0 llama-index-llms-openai>=0.3.0 pydantic>=2.8.0

# For pharmaceutical validation features
uv add openpyxl>=3.1.0 python-docx>=1.1.0

# For testing and validation
uv add pytest>=8.0.0 pytest-asyncio>=0.24.0
```

### Context Aggregation Strategies

#### Multi-Agent Context Integration

The OQ test generation agent must effectively aggregate context from multiple upstream agents to ensure comprehensive test coverage:

```python
class ContextAggregator:
    """Aggregates context from multiple pharmaceutical validation agents."""
    
    async def aggregate_parallel_agent_context(
        self, 
        ctx: Context,
        correlation_id: UUID
    ) -> dict[str, Any]:
        """Aggregate context from SME, Research, and Context Provider agents."""
        
        aggregated_context = {
            "regulatory_requirements": [],
            "best_practices": [],
            "domain_expertise": {},
            "validation_patterns": [],
            "context_quality_score": 0.0
        }
        
        # SME Agent Context
        if sme_result := await ctx.store.get(f"sme_result_{correlation_id}"):
            aggregated_context["domain_expertise"] = sme_result.get("expertise_areas", {})
            aggregated_context["validation_patterns"].extend(
                sme_result.get("recommended_patterns", [])
            )
        
        # Research Agent Context
        if research_result := await ctx.store.get(f"research_result_{correlation_id}"):
            aggregated_context["regulatory_requirements"].extend(
                research_result.get("regulatory_updates", [])
            )
            aggregated_context["best_practices"].extend(
                research_result.get("industry_practices", [])
            )
        
        # Context Provider Context
        if context_result := await ctx.store.get(f"context_result_{correlation_id}"):
            aggregated_context["context_quality_score"] = context_result.get("confidence_score", 0.0)
            aggregated_context["regulatory_requirements"].extend(
                context_result.get("regulatory_documents", [])
            )
        
        return aggregated_context

    def prioritize_context_elements(
        self, 
        aggregated_context: dict[str, Any],
        gamp_category: GAMPCategory
    ) -> dict[str, Any]:
        """Prioritize context elements based on GAMP category requirements."""
        
        category_priorities = {
            GAMPCategory.CATEGORY_1: ["installation_patterns", "infrastructure_validation"],
            GAMPCategory.CATEGORY_3: ["functional_testing", "standard_validation"],
            GAMPCategory.CATEGORY_4: ["configuration_validation", "business_process_testing"],
            GAMPCategory.CATEGORY_5: ["custom_validation", "comprehensive_testing", "code_review"]
        }
        
        priorities = category_priorities.get(gamp_category, [])
        
        # Filter and prioritize context based on category
        prioritized_context = {}
        for priority in priorities:
            if priority in aggregated_context.get("validation_patterns", []):
                prioritized_context[priority] = aggregated_context["validation_patterns"][priority]
        
        return prioritized_context
```

#### Event-Driven Context Flow

```python
# Context flow through workflow events
@step
async def collect_agent_context(
    self, 
    ctx: Context, 
    ev: AgentResultEvent
) -> OQTestGenerationEvent | None:
    """Collect context from parallel agents before test generation."""
    
    # Store individual agent results
    await ctx.store.set(f"{ev.agent_type}_result_{ev.correlation_id}", ev.result_data)
    
    # Check if all required agents have completed
    required_agents = ["sme_agent", "research_agent", "context_provider"]
    completed_agents = []
    
    for agent_type in required_agents:
        if await ctx.store.get(f"{agent_type}_result_{ev.correlation_id}"):
            completed_agents.append(agent_type)
    
    # Proceed only when all agents have completed
    if len(completed_agents) == len(required_agents):
        # Aggregate all context
        aggregator = ContextAggregator()
        full_context = await aggregator.aggregate_parallel_agent_context(ctx, ev.correlation_id)
        
        # Get original planning data
        planning_data = await ctx.store.get(f"planning_data_{ev.correlation_id}")
        
        # Create OQ test generation event with aggregated context
        return OQTestGenerationEvent(
            gamp_category=planning_data["gamp_category"],
            test_strategy=planning_data["test_strategy"],
            urs_content=planning_data["urs_content"],
            document_metadata=planning_data["document_metadata"],
            required_test_count=planning_data["estimated_test_count"],
            compliance_requirements=planning_data["compliance_requirements"],
            aggregated_context=full_context  # Include aggregated context
        )
    
    return None  # Wait for more agents to complete
```

This comprehensive research provides the foundation for implementing a robust, compliant OQ test generation agent that integrates seamlessly with the existing pharmaceutical validation workflow while meeting all GAMP-5 and regulatory requirements.