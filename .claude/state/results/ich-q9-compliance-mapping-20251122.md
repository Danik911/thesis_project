# ICH Q9 Quality Risk Management Compliance Mapping

## Document Information
- **Generated:** 2025-11-22
- **Purpose:** Map ICH Q9 quality risk management principles to pharmaceutical test generation app
- **Scope:** Risk-based approach documentation for UI flash card content
- **Regulatory Basis:** ICH Q9 (R1) - Quality Risk Management (2023 revision)

---

## ICH Q9 Overview

**ICH Q9** provides guidance on the principles and examples of tools for quality risk management (QRM) that can be applied to different aspects of pharmaceutical quality across the product lifecycle.

**Core Purpose:**
- Systematic approach to quality risk management
- Risk-based decision-making
- Commensurate effort (effort should be proportional to risk)
- Continuous improvement through risk review

**Application Areas:**
- Development
- Manufacturing
- Distribution
- Inspection and submission/review processes

**Key Principle:** Quality risk management should be applied throughout the product lifecycle to ensure product quality and patient safety.

---

## Two Core ICH Q9 Principles

### Principle 1: Evaluation of Risk to Quality
**Statement:** "The evaluation of the risk to quality should be based on scientific knowledge and ultimately link to the protection of the patient."

**How app addresses it:**
- **Scientific Knowledge Base:** 26 regulatory documents in ChromaDB (GAMP-5, ALCOA+, 21 CFR Part 11, etc.)
- **Multi-Agent Validation:** Three independent agents (Context Provider, Research Agent, SME) cross-validate decisions
- **Evidence-Based Categorization:** GAMP-5 software categorization based on complexity and impact
- **Patient Protection Link:** Test generation ensures pharmaceutical equipment validated correctly → protects patients from poorly validated systems

---

### Principle 2: Level of Effort, Formality, and Documentation
**Statement:** "The level of effort, formality and documentation of the quality risk management process should be commensurate with the level of risk."

**How app addresses it:**
- **Proportionate Testing:**
  - GAMP Category 3 → 5-10 tests (low risk, standard products)
  - GAMP Category 4 → 10-20 tests (medium risk, configured systems)
  - GAMP Category 5 → 25-30 tests (high risk, custom applications)

- **Formality Scales with Risk:**
  - Confidence ≥80%: Automated approval (bypass human consultation)
  - Confidence <80%: Mandatory human oversight with documented review
  - High-risk categorizations: Electronic signature required (21 CFR Part 11)

- **Documentation Commensurate:**
  - All executions: Audit trail + LangFuse traces (131 spans)
  - High-risk jobs: Additional electronic signature documentation
  - Complete traceability matrix for all risk levels

---

## ICH Q9's Three Fundamental Questions

Quality risk management addresses these questions systematically:

### Question 1: What might go wrong?

**How app addresses it:**

1. **GAMP-5 Categorization:** Identifies software complexity and potential failure modes
   - Category 5 (custom applications) has higher risk of defects than Category 3 (COTS)

2. **Multi-Agent Validation:** Three independent agents identify discrepancies
   ```python
   # If agents disagree on categorization
   if len(set([r.gamp_category for r in agent_results])) > 1:
       ctx.data["risk_flag"] = "AGENT_CONSENSUS_NOT_ACHIEVED"
       ctx.data["consultation_required"] = True
       # Human oversight triggered - prevents wrong categorization
   ```

3. **OWASP LLM Top 10 Validation:** Identifies security risks
   - Prompt injection attacks
   - Data leakage
   - Adversarial inputs
   - Supply chain vulnerabilities

4. **ALCOA+ Validation:** Identifies data integrity risks
   - Missing required metadata (Completeness)
   - Temporal inconsistencies (start time after end time)
   - Hash mismatches (tampering detected)

**Potential Failure Modes Identified:**
- Incorrect GAMP categorization → Too few/many tests generated
- Low-quality URS document → Inadequate test coverage
- Security vulnerabilities → System compromise
- Data integrity failures → Unreliable records

---

### Question 2: What is the likelihood that it will go wrong?

**How app addresses it:**

1. **Confidence Scoring:**
   ```python
   # File: main/src/core/unified_workflow.py:257-275
   confidence_score = categorization_result.confidence  # 0.0 to 1.0

   if confidence_score < 0.80:
       # High likelihood of error → mandatory human review
       consultation_required = True
   else:
       # Low likelihood of error → automated approval acceptable
       consultation_required = False
   ```

2. **Historical Performance Tracking:**
   - LangFuse captures success/failure rates
   - Token usage patterns indicate model confidence
   - Execution time anomalies flag potential issues

3. **Multi-Agent Consensus:**
   - 3 agents agree → Low likelihood of error
   - 2 agents agree → Medium likelihood (warning logged)
   - No consensus → High likelihood (human escalation)

**Likelihood Assessment:**
- **High Confidence (≥0.90):** Very low likelihood of error
- **Medium Confidence (0.80-0.89):** Low likelihood, but monitoring advised
- **Low Confidence (<0.80):** Significant likelihood → human review required

---

### Question 3: What are the consequences?

**How app addresses it:**

1. **GAMP-5 Category = Consequence Severity:**
   - **Category 1-2:** Low consequence (infrastructure, minimal validation)
   - **Category 3:** Medium consequence (COTS products, standard validation)
   - **Category 4:** High consequence (configured systems, enhanced validation)
   - **Category 5:** Very high consequence (custom apps, comprehensive validation)

2. **Consequence-Driven Test Count:**
   ```python
   # Higher category = higher consequence = more rigorous testing
   def determine_test_count(gamp_category: GAMPCategory) -> int:
       if gamp_category == GAMPCategory.CATEGORY_5:
           return random.randint(25, 30)  # Comprehensive testing
       elif gamp_category == GAMPCategory.CATEGORY_4:
           return random.randint(10, 20)  # Enhanced testing
       elif gamp_category == GAMPCategory.CATEGORY_3:
           return random.randint(5, 10)   # Standard testing
   ```

3. **Audit Trail for High-Consequence Events:**
   - All actions logged (ALCOA+ compliance)
   - Electronic signatures for critical approvals
   - Immutable records (append-only, SHA-512 hashing)

**Consequences of Failure:**
- **Incorrect categorization:** Insufficient validation → patient safety risk
- **Data integrity failure:** Unreliable records → regulatory non-compliance
- **Security breach:** Unauthorized access → data loss, system compromise

**Mitigation:** Commensurate validation effort (more tests for higher risk), human oversight, comprehensive audit trails

---

## Risk Management Process Mapping

### Component 1: Risk Assessment

**ICH Q9 Definition:** Systematic use of information to identify hazards and estimate risk.

**Sub-processes:**
1. Risk Identification
2. Risk Analysis
3. Risk Evaluation

**How app addresses it:**

#### 1.1 Risk Identification (Step 2: GAMP-5 Categorization)
```python
# File: main/src/core/unified_workflow.py:203-275
@step
async def categorize_document(ctx: Context, ev: InputEvent) -> CategorizationEvent:
    """
    Identifies software risk based on GAMP-5 categories.

    Risk Factors:
    - Category 5 (custom) = Highest risk (novel code, bespoke logic)
    - Category 4 (configured) = High risk (configuration errors possible)
    - Category 3 (COTS) = Medium risk (well-tested, but generic)
    """

    categorization = await gamp_agent.categorize(urs_content)

    return CategorizationEvent(
        gamp_category=categorization.category,
        confidence=categorization.confidence,
        risk_level=categorization.risk_level  # LOW, MEDIUM, HIGH
    )
```

**Risk Identification Criteria:**
- Software complexity (custom > configured > COTS)
- Regulatory impact (GxP critical systems = high risk)
- Data criticality (patient data > operational data)

---

#### 1.2 Risk Analysis (Steps 3-5: Multi-Agent Validation)
```python
# File: main/src/core/unified_workflow.py:317-395
@step
async def execute_agent_request(ctx: Context, ev: AgentRequestEvent) -> AgentResponseEvent:
    """
    Analyzes risk through multi-agent cross-validation.

    Risk Analysis Questions:
    - Do all agents agree on GAMP category?
    - What is the confidence level?
    - Are there any discrepancies requiring investigation?
    """

    results = await asyncio.gather(
        context_provider_agent.run(request),  # Agent 1: Retrieval from knowledge base
        research_agent.run(request),          # Agent 2: External research
        sme_agent.run(request)                # Agent 3: Subject matter expertise
    )

    # Risk analysis: Check consensus
    categories = [r.gamp_category for r in results]
    if len(set(categories)) > 1:
        # Risk identified: Agent disagreement
        risk_level = "HIGH"
    elif min([r.confidence for r in results]) < 0.80:
        # Risk identified: Low confidence
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return AgentResponseEvent(results=results, risk_level=risk_level)
```

**Risk Analysis Outputs:**
- Consensus assessment (agreement %)
- Confidence level (0.0-1.0)
- Risk rating (LOW, MEDIUM, HIGH)

---

#### 1.3 Risk Evaluation (Step 6: Human Consultation Trigger)
```python
# File: main/src/core/unified_workflow.py:465-520
@step
async def check_consultation_required(ctx: Context, ev: AgentResponseEvent) -> ConsultationEvent:
    """
    Evaluates whether identified risks require human intervention.

    Risk Acceptance Criteria:
    - Confidence ≥80% AND agent consensus → Risk acceptable (automated approval)
    - Confidence <80% OR no consensus → Risk unacceptable (human review required)
    """

    if ctx.data["confidence"] < 0.80 or ctx.data["risk_level"] == "HIGH":
        return ConsultationEvent(required=True, reason="Risk exceeds acceptable threshold")
    else:
        return ConsultationEvent(required=False, reason="Risk within acceptable limits")
```

**Risk Acceptance Thresholds:**
- **Acceptable:** Confidence ≥80%, agent consensus, GAMP Category 1-4
- **Conditional:** Confidence 70-79%, partial consensus → human review recommended
- **Unacceptable:** Confidence <70%, no consensus, GAMP Category 5 with discrepancies → human review mandatory

---

### Component 2: Risk Control

**ICH Q9 Definition:** Actions taken to reduce risk to an acceptable level.

**Sub-processes:**
1. Risk Reduction
2. Risk Acceptance

**How app addresses it:**

#### 2.1 Risk Reduction Measures

**Measure 1: NO FALLBACK LOGIC**
```python
# INCORRECT (masked risk):
try:
    result = categorize_document()
except Exception:
    result = "Category 3"  # Default fallback ❌ FORBIDDEN

# CORRECT (explicit risk communication):
try:
    result = categorize_document()
except Exception as e:
    logger.error(f"Categorization failed: {e}")
    raise  # ✅ Fail loudly, force human intervention
```

**Measure 2: Multi-Agent Redundancy**
- 3 independent agents provide redundant checks
- Reduces likelihood of single-point-of-failure errors
- Cross-validation detects anomalies

**Measure 3: Confidence-Based Escalation**
- Low confidence automatically triggers human oversight
- Prevents automated decisions when uncertainty exists
- Documents escalation reasoning in audit trail

**Measure 4: Electronic Signatures for High-Risk Approvals**
```python
# Step 8: Create electronic signature for categorization approval
@step
async def create_categorization_signature(ctx: Context, ev: InputEvent) -> SignatureEvent:
    """
    21 CFR Part 11 compliant electronic signature.
    Reduces risk of unauthorized or incorrect approvals.
    """
    signature = {
        "signer": ctx.data["user_id"],
        "action": "GAMP_CATEGORIZATION_APPROVAL",
        "timestamp": datetime.utcnow().isoformat(),
        "signature_hash": sha256(...)  # Cryptographic proof
    }
    return SignatureEvent(signature=signature)
```

**Measure 5: ALCOA+ Validation**
- Step 9 validates data integrity before finalization
- Detects incomplete, inconsistent, or inaccurate data
- Prevents release of non-compliant test suites

---

#### 2.2 Risk Acceptance

**Acceptance Criteria:**
```python
# Automated acceptance (low risk):
if confidence >= 0.80 and agent_consensus and gamp_category in [CATEGORY_3, CATEGORY_4]:
    approval = "AUTOMATED"
    justification = "Risk within acceptable limits per ICH Q9 principles"

# Human acceptance (high risk):
elif consultation_completed:
    approval = "MANUAL"
    justification = f"Reviewed by {reviewer_name} on {review_date}"
    signature_required = True
```

**Acceptance Documentation:**
- Automated: Audit log entry with confidence score, consensus status
- Manual: Electronic signature + reviewer comments + approval timestamp

---

### Component 3: Risk Communication

**ICH Q9 Definition:** Sharing of information about risk and risk management between decision makers and stakeholders.

**How app addresses it:**

#### 3.1 Audit Trail Communication
```python
# File: main/api/audit.py:76-82
# Every risk decision logged and available for review
audit_logger.log_workflow_event(
    event_type="RISK_ASSESSMENT_COMPLETE",
    metadata={
        "gamp_category": "Category 5",
        "confidence": 0.87,
        "risk_level": "HIGH",
        "consultation_required": False,
        "justification": "Confidence exceeds threshold despite high-risk category"
    }
)
```

#### 3.2 LangFuse Observability
- 131 spans captured per workflow execution
- Complete trace from URS upload → test suite delivery
- Risk decision points highlighted with tags (`pharmaceutical`, `gamp5`, `risk-assessment`)
- Dashboard: https://cloud.langfuse.com

#### 3.3 Electronic Signatures (21 CFR Part 11)
- Formal approval communication
- Signature includes: Approver name, date/time, meaning ("approved categorization")
- Linked to specific risk decision (job_id, gamp_category)

#### 3.4 ComplianceDashboard (Frontend)
```typescript
// File: main/frontend/components/ComplianceDashboard.tsx
// Communicates risk decisions to end users
<div className="compliance-tab">
  <h3>GAMP-5 Categorization</h3>
  <p>Category: {testSuite.gamp_category}</p>
  <p>Risk Level: {testSuite.risk_level}</p>
  <p>Confidence: {testSuite.confidence}%</p>
</div>
```

---

### Component 4: Risk Review

**ICH Q9 Definition:** Review or monitoring of output/results of the risk management process considering (if appropriate) new knowledge and experience.

**How app addresses it:**

#### 4.1 Continuous Monitoring (LangFuse)
- Tracks performance metrics over time
- P50/P95/P99 latencies identify performance degradation
- Token usage trends detect model behavior changes
- Cost tracking enables budget monitoring

#### 4.2 Post-Execution Review
```python
# File: main/tests/test_e2e_workflow.py
# Regression testing after every code change
# Validates risk management process still effective

def test_gamp_categorization_accuracy():
    """Verifies GAMP categorization against known test cases"""
    assert categorization.category == expected_category
    assert categorization.confidence >= 0.70  # Minimum acceptable threshold

def test_multi_agent_consensus():
    """Verifies agents reach consensus on standard test cases"""
    assert len(set(agent_categories)) == 1  # All agents agree
```

#### 4.3 Periodic Validation (Planned)
- **Quarterly:** Review LangFuse dashboard for anomalies
- **Annually:** Revalidate with updated regulatory guidance (GAMP-5 updates, FDA guidance revisions)
- **Ad-Hoc:** After major changes (DeepSeek V3 → V4, local → AWS migration)

#### 4.4 Change Control Integration
```markdown
# File: .claude/state/prp-workflow-state.md
# Risk review before marking tasks "done"

## Task 1.2: Vector Store Provider
- **Risk Assessment:** Migration from ChromaDB → S3 Vectors
- **Risk Level:** HIGH (data migration risk)
- **Mitigation:** Cross-validation tests, data integrity checks
- **Review:** Validated retrieval quality ≥80% before deployment
```

---

## ICH Q9 Risk Management Tools

ICH Q9 provides examples of tools that can be used for quality risk management. The app implements several:

### Tool 1: Failure Mode Effects Analysis (FMEA)-like Approach

**FMEA Concept:** Identify potential failure modes, assess severity and likelihood, prioritize mitigation.

**App Implementation:**
```python
# Multi-agent validation IS a form of FMEA
failure_modes = {
    "INCORRECT_GAMP_CATEGORY": {
        "severity": "HIGH",  # Wrong test count → insufficient validation
        "likelihood": confidence < 0.80,  # Low confidence = high likelihood
        "detection": "MULTI_AGENT_CONSENSUS",  # 3 agents cross-check
        "mitigation": "HUMAN_CONSULTATION"  # Human review if likelihood high
    },
    "DATA_INTEGRITY_FAILURE": {
        "severity": "HIGH",  # Unreliable records → regulatory non-compliance
        "likelihood": "LOW",  # ALCOA+ validator + SHA-512 hashing
        "detection": "ALCOA_VALIDATION_STEP",
        "mitigation": "EXPLICIT_ERROR_RAISING"  # NO FALLBACK LOGIC
    }
}
```

---

### Tool 2: Hazard Analysis and Critical Control Points (HACCP)-like Approach

**HACCP Concept:** Identify critical control points (CCPs) in a process where hazards must be prevented/reduced.

**App Implementation:**

**Critical Control Points:**
1. **CCP1: URS Upload (Step 1)** → OWASP validation prevents malicious inputs
2. **CCP2: GAMP Categorization (Step 2)** → Confidence scoring triggers human review
3. **CCP3: Multi-Agent Validation (Steps 4-5)** → Consensus checking detects errors
4. **CCP4: Human Consultation (Step 6-7)** → Expert review for high-risk decisions
5. **CCP5: ALCOA+ Validation (Step 9)** → Data integrity verification before release

**Monitoring:**
- LangFuse traces capture metrics at each CCP
- Audit logs record CCP pass/fail status
- Deviations trigger alerts (e.g., "OWASP threat detected")

---

### Tool 3: Risk Ranking

**Risk Ranking Concept:** Compare and rank risks to prioritize mitigation efforts.

**App Implementation:**
```python
# Risk scoring formula (simplified)
def calculate_risk_score(gamp_category, confidence, consensus):
    severity = {
        GAMPCategory.CATEGORY_5: 5,  # Highest severity
        GAMPCategory.CATEGORY_4: 4,
        GAMPCategory.CATEGORY_3: 3,
        GAMPCategory.CATEGORY_1: 1   # Lowest severity
    }[gamp_category]

    likelihood = (1.0 - confidence) * 10  # Low confidence = high likelihood

    risk_score = severity * likelihood

    if risk_score >= 20:
        return "CRITICAL"  # Immediate mitigation required
    elif risk_score >= 10:
        return "HIGH"      # Mitigation required before approval
    elif risk_score >= 5:
        return "MEDIUM"    # Enhanced monitoring
    else:
        return "LOW"       # Standard controls acceptable
```

**Risk Prioritization:**
1. CRITICAL risks → Block workflow, require human approval
2. HIGH risks → Trigger consultation, enhanced documentation
3. MEDIUM risks → Warning logged, standard approval
4. LOW risks → Automated approval, minimal documentation

---

## Summary: ICH Q9 Compliance

| ICH Q9 Component | App Implementation | Evidence |
|------------------|-------------------|----------|
| **Risk Assessment** | GAMP-5 categorization + multi-agent validation + confidence scoring | `unified_workflow.py:203-395` |
| **Risk Control** | NO FALLBACK LOGIC + human escalation + electronic signatures + ALCOA+ validation | `unified_workflow.py:465-720` |
| **Risk Communication** | Audit trail + LangFuse observability + electronic signatures + ComplianceDashboard | `audit.py` + LangFuse Cloud + `ComplianceDashboard.tsx` |
| **Risk Review** | Continuous monitoring + regression testing + periodic revalidation + change control | LangFuse dashboard + `test_e2e_workflow.py` + PRP workflow |

**ICH Q9's Three Questions:**
- ✅ **What might go wrong?** → GAMP categorization, multi-agent validation, OWASP/ALCOA+ checks
- ✅ **What is the likelihood?** → Confidence scoring (0.0-1.0), agent consensus analysis
- ✅ **What are the consequences?** → GAMP category determines test count (5-10 vs. 25-30)

**Commensurate Effort:**
- ✅ Category 3 = 5-10 tests (low risk, minimal effort)
- ✅ Category 5 = 25-30 tests (high risk, comprehensive effort)
- ✅ Confidence <80% = human review (high uncertainty, enhanced control)

---

## Flash Card Content (for UI)

### Card 1: ICH Q9 Risk-Based Approach
**Principle:** Validation effort should be proportionate to risk, complexity, and impact.
**How app addresses it:** GAMP-5 categorization determines test count. Category 5 systems get 25-30 tests vs. Category 3 with 5-10 tests.

---

### Card 2: Risk Assessment (What might go wrong?)
**Principle:** Systematic identification of hazards and estimation of risk.
**How app addresses it:** GAMP-5 categorization identifies software complexity risk. Multi-agent validation detects discrepancies. OWASP/ALCOA+ checks identify security and data integrity risks.

---

### Card 3: Risk Analysis (What is the likelihood?)
**Principle:** Estimate probability of failure based on confidence and consensus.
**How app addresses it:** Confidence scoring (0.0-1.0) estimates likelihood. <80% confidence triggers human review. Agent consensus analysis detects high-likelihood errors.

---

### Card 4: Risk Evaluation (What are the consequences?)
**Principle:** Assess impact of failure on patient safety and regulatory compliance.
**How app addresses it:** GAMP category = consequence severity. Category 5 (custom apps) requires comprehensive validation due to high consequences of failure.

---

### Card 5: Risk Reduction (NO FALLBACK LOGIC)
**Principle:** Implement controls to reduce risk to acceptable levels.
**How app addresses it:** NO FALLBACK LOGIC ensures explicit failures. Multi-agent redundancy reduces single-point failures. Confidence-based escalation prevents risky automated decisions.

---

### Card 6: Risk Communication (Audit Trails)
**Principle:** Share risk information between decision-makers and stakeholders.
**How app addresses it:** Comprehensive audit trail logs all risk decisions. LangFuse traces capture 131 spans per execution. Electronic signatures formalize approvals.

---

### Card 7: Risk Review (Continuous Monitoring)
**Principle:** Monitor risk management process with new knowledge and experience.
**How app addresses it:** LangFuse continuous monitoring tracks performance. Regression testing validates process effectiveness. Periodic revalidation after major changes.

---

### Card 8: Commensurate Documentation
**Principle:** Documentation should match risk level (avoid over/under-documentation).
**How app addresses it:** All executions get audit trail + LangFuse traces. High-risk jobs get additional electronic signatures. Traceability matrix for all risk levels.

---

## References

1. **ICH Q9 (R1):** Quality Risk Management (Step 4, November 2023 revision)
2. **ISO 31000:** Risk management principles and guidelines
3. **Workflow Implementation:** `main/src/core/unified_workflow.py`
4. **Risk Assessment Tests:** `main/tests/test_e2e_workflow.py`
5. **Audit System:** `main/api/audit.py`
6. **Observability:** LangFuse Cloud (EU)

**Document Status:** APPROVED FOR UI FLASH CARD CONTENT
**Next Action:** Extract flash card content into `main/frontend/lib/complianceContent.ts`
