# Template: Research/Exploration Task

Use this template for tasks that involve investigating, analyzing, or gathering information.

---

## Template

```markdown
# Research Task: [TOPIC]

## Objective
[Clear statement of what to research/discover/analyze]

## Context

### Why This Research
[Explain the purpose and how results will be used]
- Decision to make: [What decision this informs]
- Constraints: [Technical, business, or compliance constraints]
- Timeline: [When the decision needs to be made]

### Current Knowledge
[What we already know - prevents redundant research]
- [Known fact 1]
- [Known fact 2]
- [Assumption to verify or challenge]

### Scope Boundaries
- IN SCOPE: [What to research]
- OUT OF SCOPE: [What to ignore]

## Research Questions

### Primary Questions (Must Answer)
1. [Critical question 1]
2. [Critical question 2]
3. [Critical question 3]

### Secondary Questions (If Time Permits)
1. [Nice-to-have question]
2. [Nice-to-have question]

## Sources to Consult

### Required Sources
- [Source 1: URL or file path]
- [Source 2: URL or file path]
- [Documentation: specific docs to check]

### Suggested Sources
- [Optional source 1]
- [Optional source 2]

## Evaluation Criteria
[How to assess the options/findings]

| Criterion | Weight | Description |
|-----------|--------|-------------|
| [Criterion 1] | High | [What makes it good/bad] |
| [Criterion 2] | Medium | [What makes it good/bad] |
| [Criterion 3] | Low | [What makes it good/bad] |

## Output

### Required Sections
1. **Executive Summary** (max 100 words)
2. **Options Evaluated** (structured comparison)
3. **Recommendation** (with rationale)
4. **Risks** (identified concerns)
5. **Open Questions** (things needing clarification)

### Format
```markdown
# Research Report: [Topic]

## Executive Summary
[Key findings and recommendation in 2-3 sentences]

## Options Evaluated

### Option 1: [Name]
- **Description**: [What it is]
- **Pros**: [Benefits]
- **Cons**: [Drawbacks]
- **Fit Score**: HIGH / MEDIUM / LOW

### Option 2: [Name]
[Same structure]

## Comparison Matrix
| Criterion | Option 1 | Option 2 | Option 3 |
|-----------|----------|----------|----------|
| ... | ... | ... | ... |

## Recommendation
**Selected**: [Option]
**Rationale**: [Why this option]
**Confidence**: HIGH / MEDIUM / LOW

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ... | ... | ... | ... |

## Open Questions
- [Question needing answer]

## References
- [Source 1]
- [Source 2]
```

### Delivery
Save to: `[specified location]`

### Constraints
- Maximum length: [word count]
- Focus on actionable insights
- Include specific examples where possible
```

---

## Filled Example

```markdown
# Research Task: Vector Database Selection for Production

## Objective
Evaluate vector database options for the pharmaceutical test generation
system's production deployment, recommending the best fit for our
requirements.

## Context

### Why This Research
- Decision to make: Which vector database to use in AWS production
- Constraints: EU data residency (eu-west-2), GAMP-5 compliance
- Timeline: Decision needed by end of Week 2

### Current Knowledge
- ChromaDB works well locally but doesn't scale
- Need 1536-dimension embeddings (OpenAI text-embedding-3-small)
- Query latency requirement: <100ms for 1000 vectors
- Assumption: AWS-native services preferred (verify this)

### Scope Boundaries
- IN SCOPE: AWS-native options, major managed services
- OUT OF SCOPE: Self-hosted open source (ops burden too high)

## Research Questions

### Primary Questions (Must Answer)
1. Which vector databases support EU data residency?
2. What are the cost implications at our scale (10M vectors)?
3. How do options compare on query latency?
4. Which options integrate best with our existing AWS stack?

### Secondary Questions (If Time Permits)
1. What are the migration paths from ChromaDB?
2. What monitoring/observability is available?

## Sources to Consult

### Required Sources
- AWS S3 Vectors documentation
- Pinecone pricing and regions page
- OpenSearch Serverless vector search docs
- examples/alex/backend/ - production patterns

### Suggested Sources
- AWS re:Invent 2024 vector search sessions
- Hacker News discussions on vector DB performance

## Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| EU Data Residency | High | Must support eu-west-2 |
| Cost at Scale | High | <$500/month for 10M vectors |
| Query Latency | High | P95 <100ms |
| AWS Integration | Medium | Native integration preferred |
| Ease of Migration | Medium | Simple path from ChromaDB |
| GAMP-5 Compatibility | High | Audit logging, access controls |

## Output

### Required Sections
1. Executive Summary (max 100 words)
2. Options Evaluated (3-5 options)
3. Recommendation with rationale
4. Risks and mitigations
5. Open questions

### Format
[Use standard research report format]

### Delivery
Save to: `.claude/state/results/context-collector-{YYYYMMDD-HHMMSS}.md`

### Constraints
- Maximum length: 800 words (excluding tables)
- Focus on decision-relevant information
- Include specific numbers (costs, latencies) where available
```

---

## Checklist Before Sending

- [ ] Objective clearly states what to discover
- [ ] Context explains WHY this research matters
- [ ] Current knowledge prevents redundant work
- [ ] Scope boundaries are explicit (IN/OUT)
- [ ] Primary questions are specific and answerable
- [ ] Sources include both required and suggested
- [ ] Evaluation criteria have weights
- [ ] Output format is fully specified
- [ ] Length constraints prevent excessive output
