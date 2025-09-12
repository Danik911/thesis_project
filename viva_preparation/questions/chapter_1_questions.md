# Chapter 1 Viva Examination Questions - Introduction

**Thesis**: "Evaluating Efficiency Gains and Security of LLM-Driven Test Generation for Computerised System Validation"  
**Candidate**: Daniil Vladimirov  
**Target Discussion Time**: 60-90 minutes

---

## 1. Opening Questions (Foundation) - 4 questions

### Q1.1: Research Overview and Positioning
"Can you provide a 3-minute summary of your research, explaining how it addresses the fundamental tension between regulatory certainty and development flexibility in pharmaceutical validation?"

**Context**: Tests candidate's ability to articulate the core problem and position their work within the broader industry challenge. Look for clear articulation of the CSV burden and LLM solution paradigm.

**Follow-up probes**:
- What makes this tension particularly acute in pharmaceutical settings compared to other regulated industries?
- How does your approach differ from conventional automation strategies?

### Q1.2: Market Opportunity Validation
"You cite impressive market figures - $3.92B growing to $14.02B by 2037 with 10.3% CAGR. How did you validate these figures, and what assumptions underpin your cost reduction projections?"

**Context**: Probes the robustness of market analysis and economic foundations. Tests understanding of industry economics and validation methodology.

**Follow-up probes**:
- How sensitive are these projections to adoption rates?
- What market research informed your 91% cost reduction claim?

### Q1.3: Research Gap Identification
"You identify three key gaps in empirical evidence. Walk me through how you systematically identified these gaps and why they represent the most critical research priorities."

**Context**: Assesses systematic literature review approach and critical thinking about research priorities.

**Follow-up probes**:
- How did you ensure you weren't missing existing work in adjacent fields?
- Which gap proved most challenging to address empirically?

### Q1.4: Scope Definition and Delimitations
"Your focus is exclusively on the OQ phase, using synthetic URS datasets. How do you justify these scope limitations, and what are the implications for generalizability?"

**Context**: Tests understanding of research boundaries and their impact on validity. Critical for assessing practical applicability.

**Follow-up probes**:
- How representative are synthetic URS datasets of real-world complexity?
- Why exclude IQ and PQ phases entirely rather than include limited analysis?

---

## 2. Research Problem & Gap (Analytical) - 6 questions

### Q2.1: CSV Market Analysis and Validation Burden
"You state that 66% of validation teams report increased workload and 25% spend >10% of budgets on validation. How did you verify these statistics, and what methodology underlies these industry surveys?"

**Context**: Probes data validation and source credibility. Tests ability to critically assess industry data.

**Follow-up probes**:
- How do you account for potential survey bias in these figures?
- What correlation exists between validation burden and company size/therapeutic area?

### Q2.2: LLM Suitability for CSV Applications
"You argue that LLMs are 'uniquely applicable to CSV problems' due to their ability to interpret unstructured documents and regulatory intent. What empirical evidence supports this claim?"

**Context**: Challenges the fundamental premise with request for evidence-based justification.

**Follow-up probes**:
- How do you quantify 'regulatory intent interpretation'?
- What validation exists for LLM understanding of pharmaceutical context?

### Q2.3: Risk Assessment - Compliance Jeopardy
"You state that implementing LLMs without evidence-based models creates 'a risk that no pharmaceutical company can afford to take.' How did you systematically assess this risk landscape?"

**Context**: Tests risk analysis methodology and understanding of pharmaceutical risk tolerance.

**Follow-up probes**:
- What specific compliance failures could result from LLM implementation?
- How do you balance innovation pressure against regulatory risk?

### Q2.4: Security-Compliance Integration Gap
"Your second research gap focuses on the intersection of security and compliance requirements. Why hasn't this been adequately addressed in existing literature?"

**Context**: Assesses understanding of interdisciplinary research challenges and field maturity.

**Follow-up probes**:
- How do ALCOA+ principle violations specifically relate to security vulnerabilities?
- What makes pharmaceutical AI security requirements unique?

### Q2.5: Measurable Indicators Development
"You identify the lack of 'measurable indicators to assess LLM-generated validation artifacts.' What existing software quality metrics did you consider adapting?"

**Context**: Tests knowledge of software engineering measurement and adaptation to pharmaceutical context.

**Follow-up probes**:
- How do traditional software metrics map to GxP requirements?
- Why develop new metrics rather than adapt existing ones?

### Q2.6: FDA CSA Guidance Limitations
"You note that FDA CSA guidance doesn't cover 'unique problems of comparing AI-generated test scripts to regulatory requirements.' What specific gaps did you identify?"

**Context**: Assesses detailed understanding of regulatory landscape and guidance limitations.

**Follow-up probes**:
- How might future FDA guidance address these gaps?
- What regulatory precedents exist for AI validation in other domains?

---

## 3. Objectives & Contributions (Critical) - 6 questions

### Q3.1: Target Threshold Justification
"Your design goals include ≥90% requirements coverage and <5% false positive/negative rates. How did you establish these specific thresholds?"

**Context**: Critical examination of success criteria and their basis in industry practice or regulatory requirements.

**Follow-up probes**:
- What industry benchmarks informed these targets?
- How do these thresholds compare to manual validation performance?

### Q3.2: Open-Source Model Strategy
"You specify using open-source models 'to ensure reproducibility and transparency.' How does this decision impact your security assessment and commercial viability?"

**Context**: Tests understanding of trade-offs between transparency and security/performance.

**Follow-up probes**:
- How do open-source model capabilities compare to proprietary alternatives?
- What additional security considerations arise from open-source usage?

### Q3.3: OWASP LLM Top 10 Focus Areas
"You prioritize three specific OWASP risks: LLM02, LLM06, and LLM01. What analysis led to this prioritization?"

**Context**: Assesses systematic risk prioritization and pharmaceutical context adaptation.

**Follow-up probes**:
- How did you map OWASP risks to pharmaceutical validation contexts?
- What mitigation strategies proved most effective?

### Q3.4: 100% 21 CFR Part 11 Compliance Target
"You target 100% compliance with 21 CFR Part 11. Is this realistic given the complexity of electronic records requirements?"

**Context**: Challenges ambitious compliance target and tests understanding of regulatory complexity.

**Follow-up probes**:
- Which Part 11 requirements pose the greatest challenges for LLM systems?
- How do you validate audit trail completeness programmatically?

### Q3.5: Efficiency Gains Measurement Methodology
"Your efficiency measurement includes 'time reduction aligned with industry benchmarks showing 20-50% gains.' How will you isolate LLM contribution from other automation factors?"

**Context**: Tests experimental design rigor and confounding variable control.

**Follow-up probes**:
- What baseline timing protocols will you use?
- How do you account for learning curve effects?

### Q3.6: Compliance-Aware AI Engineering Paradigm
"You introduce 'Compliance-Aware AI Engineering' as a theoretical contribution. How does this differ from existing responsible AI frameworks?"

**Context**: Assesses theoretical innovation and differentiation from existing work.

**Follow-up probes**:
- What design principles distinguish compliance-aware from safety-aware AI?
- How do you operationalize regulatory requirements as system constraints?

---

## 4. Methodology Overview (Analytical) - 5 questions

### Q4.1: Design Science Research Application
"You employ DSR methodology for constructing and evaluating your prototype. How does DSR specifically address the pharmaceutical validation domain requirements?"

**Context**: Tests appropriateness of methodology choice and domain-specific adaptations.

**Follow-up probes**:
- What DSR evaluation criteria are most relevant to regulatory contexts?
- How do you handle the tension between innovation and validation rigor?

### Q4.2: Five-Fold Cross-Validation Strategy
"Your evaluation uses 5-fold cross-validation on 10-15 synthetic URS datasets. How did you determine this sample size and validation approach?"

**Context**: Assesses statistical methodology and sample size justification.

**Follow-up probes**:
- What power analysis supported the 10-15 dataset decision?
- How do you ensure representative sampling across pharmaceutical domains?

### Q4.3: Synthetic Dataset Representativeness
"You acknowledge that synthetic URS datasets 'may not capture all proprietary format variations.' How significant is this limitation?"

**Context**: Critical assessment of external validity and generalizability constraints.

**Follow-up probes**:
- What validation exists for synthetic dataset fidelity?
- How do proprietary formats typically differ from standardized ones?

### Q4.4: Human-in-the-Loop Integration
"Your primary research question asks about 'level of human-in-the-loop review required.' How will you systematically determine optimal human oversight?"

**Context**: Tests understanding of human-AI collaboration design and measurement.

**Follow-up probes**:
- What metrics will indicate insufficient vs. excessive human oversight?
- How do you account for individual reviewer variation?

### Q4.5: Ethical Considerations and Data Protection
"You state compliance with institutional ethics guidelines using synthetic datasets. What additional ethical considerations arise from pharmaceutical AI research?"

**Context**: Assesses broader ethical awareness beyond data protection.

**Follow-up probes**:
- How do you address potential bias in AI-generated validation scripts?
- What ethical frameworks guide pharmaceutical AI research?

---

## 5. Scope & Limitations (Critical) - 5 questions

### Q5.1: OQ Phase Limitation Impact
"You limit focus to OQ phase only, stating IQ and PQ 'require separate investigation.' How does this limitation affect the practical utility of your findings?"

**Context**: Critical assessment of scope limitations and practical implementation barriers.

**Follow-up probes**:
- What fundamental differences make IQ/PQ phases unsuitable for similar approaches?
- How do pharmaceutical companies typically integrate validation across phases?

### Q5.2: Security Testing Simulation vs. Reality
"You acknowledge that security testing 'simulates threat models without live penetration testing.' What critical vulnerabilities might this approach miss?"

**Context**: Probes security assessment limitations and potential blind spots.

**Follow-up probes**:
- What ethical and practical constraints prevent live penetration testing?
- How do simulated threats compare to real-world attack patterns?

### Q5.3: Regulatory Jurisdiction Generalizability
"Findings 'may not generalize to all therapeutic areas or regulatory jurisdictions.' How significant are these variations?"

**Context**: Assesses international applicability and regulatory heterogeneity.

**Follow-up probes**:
- Which regulatory jurisdictions present the greatest validation differences?
- How do therapeutic area requirements vary (biologics vs. small molecules)?

### Q5.4: LLM Version Dependencies
"You note that 'LLM version dependencies require careful management for reproducibility.' How will you address model evolution?"

**Context**: Tests understanding of technology stability and long-term viability.

**Follow-up probes**:
- What happens to your system when underlying models are deprecated?
- How do you ensure consistent performance across model updates?

### Q5.5: NO-FALLBACKS Policy Justification
"Your implementation uses a 'NO-FALLBACKS policy.' How does this conservative approach affect your success rate claims?"

**Context**: Critical examination of design choices and their impact on reported performance.

**Follow-up probes**:
- How would success rates change with fallback mechanisms enabled?
- What drove the decision to exclude fallbacks entirely?

---

## 6. Closing Integration Questions - 3 questions

### Q6.1: Research Questions Alignment Assessment
"Looking at your four research questions, RQ4 focuses on human oversight requirements. Why is this data 'missing' from your current work?"

**Context**: Direct challenge about incomplete research question coverage and thesis completeness.

**Follow-up probes**:
- How do you defend submitting a thesis with incomplete RQ coverage?
- What timeline exists for completing RQ4 analysis?

### Q6.2: Industry Adoption Readiness
"Given your findings - 76.7% success rate, n=30 sample, OQ-only focus - how ready is this technology for pharmaceutical industry adoption?"

**Context**: Synthesis question requiring integration of limitations with practical implications.

**Follow-up probes**:
- What would constitute 'production-ready' performance levels?
- Which pharmaceutical companies are most likely early adopters?

### Q6.3: Future Research Priority Ranking
"If you could only pursue three follow-up studies, what would they be and why?"

**Context**: Tests strategic thinking about research program development and priority assessment.

**Follow-up probes**:
- Which limitations pose the greatest barriers to adoption?
- How do you balance theoretical advancement with practical needs?

---

## Key Vulnerability Areas for Intensive Probing

1. **Statistical Validity**: n=30 sample size, 76.7% success rate below 90% target
2. **Scope Limitations**: OQ-only focus, synthetic datasets, missing RQ4 data
3. **Economic Claims**: 91% cost reduction, $14.02B market projections
4. **Security Assessment**: Simulated vs. real threats, NO-FALLBACKS policy impact
5. **Regulatory Generalization**: Single-jurisdiction focus, therapeutic area variations
6. **Technology Dependency**: LLM version management, open-source model evolution

## Expected Defense Strategies

- **Temporal Improvement Emphasis**: 64.7% → 87.5% → 100% progression
- **Conservative Design Justification**: NO-FALLBACKS as safety-first approach
- **Resource Constraint Acknowledgment**: MSc-level scope and time limitations
- **Proof-of-Concept Positioning**: Foundational work enabling future studies
- **Industry Validation Needs**: Emphasis on evidence-based adoption requirements

---

*Generated for Daniil Vladimirov's viva preparation - Chapter 1 focus*