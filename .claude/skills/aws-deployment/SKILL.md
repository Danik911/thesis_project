---
name: aws-deployment
description: Deploys AWS infrastructure with research-first approach. ALWAYS searches AWS documentation before writing code, explains services and abbreviations, considers alternatives, maintains organized aws/ folder, and CRITICALLY offers to destroy resources after testing. Use PROACTIVELY for any AWS deployment, Terraform, ECS, Fargate, Lambda, S3, RDS, or cloud infrastructure tasks. MUST BE USED for prototype/learning projects to avoid unexpected costs.
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "WebSearch", "WebFetch", "AskUserQuestion", "mcp__one-search-mcp__one_search"]
---

# AWS Deployment Skill

## Overview

This skill enforces a **research-first, education-focused** approach to AWS deployments.
It is designed for **prototype/learning/portfolio** projects where understanding is as
important as deployment, and where avoiding unexpected costs is critical.

### Core Philosophy

1. **Research Before Code**: ALWAYS search AWS documentation before writing Terraform
2. **Explain Everything**: Never assume the user knows AWS services - explain as you deploy
3. **Prototype Mode**: Optimize for learning and cost savings, not production readiness
4. **Mandatory Cleanup**: ALWAYS offer to destroy resources after testing

### Current Date Context

You are working in **December 2025**. When searching for AWS documentation:
- Check for 2025 service updates and pricing changes
- Note any deprecated features or new alternatives
- AWS pricing and features change frequently - always verify

---

## When to Use This Skill

**Activate this skill when the user mentions:**
- AWS, Amazon Web Services, cloud deployment
- Terraform, infrastructure as code, IaC
- ECS, Fargate, Lambda, EC2, containers
- S3, RDS, Aurora, DynamoDB, databases
- ALB, load balancer, networking
- ECR, container registry, Docker push
- SQS, SNS, queues, messaging
- IAM, permissions, policies
- CloudWatch, logging, monitoring
- Any request to "deploy to AWS" or "set up infrastructure"

---

## Critical Rules (MUST FOLLOW)

### Rule 1: Research First
```
BEFORE writing ANY Terraform or AWS code:
1. Search docs.aws.amazon.com for the specific service
2. Verify current pricing (December 2025)
3. Check for deprecations or new alternatives
4. Document findings in aws/docs/research-{service}.md
```

### Rule 2: Explain Every Service
```
WHEN deploying any AWS service, FIRST explain:
1. Full service name (expand abbreviations)
2. What it does (1-2 sentences, simple terms)
3. Why it's needed in THIS specific application
4. 2-3 alternatives and why you chose this one
5. Prototype vs production cost implications
```

### Rule 3: Mandatory Destroy Offer
```
AFTER ANY deployment completes, you MUST:
1. Present a summary of all created resources
2. Calculate ongoing costs (hourly, daily, monthly)
3. STRONGLY RECOMMEND destroying to avoid charges
4. Ask user explicitly: "Destroy now or keep running?"
5. If keeping: Warn about ongoing costs and set reminder

THIS PHASE CANNOT BE SKIPPED. EVER.
```

---

## 6-Phase Workflow

### Phase 1: Research & Discovery (10-15 min)

**Objective:** Gather current AWS documentation before writing any code

**Steps:**
1. Identify all AWS services needed for the deployment
2. For EACH service, use WebSearch with query: `site:docs.aws.amazon.com {service} pricing 2025`
3. Check for December 2025 updates/changes
4. Search for known issues or deprecations
5. Create research notes file

**Create file:** `aws/docs/research-{timestamp}.md`
```markdown
# AWS Research Notes - {Date}

## Services Researched

### {Service 1 Name}
- **Full Name:** {Expand abbreviation}
- **Pricing (Dec 2025):** {Current pricing}
- **Key Features:** {Relevant features}
- **Known Issues:** {Any deprecations or problems}
- **Source:** {URL}

### {Service 2 Name}
...
```

**Quality Gate:** Research file created with at least one citation per service

### Phase 2: Service Selection & Explanation (5-10 min)

**Objective:** Explain services to user, present alternatives, get decisions

**For each AWS service needed, present:**
```markdown
## Deploying {Service Name}

**What is {Abbreviation}?**
{Full name} is {1-2 sentence explanation in simple terms}.

**Why we need it:**
{Specific role in THIS application - not generic description}

**Alternatives considered:**
| Option | Pros | Cons | Cost |
|--------|------|------|------|
| {Service 1} | ... | ... | ~$/hr |
| {Service 2} | ... | ... | ~$/hr |
| {Service 3} | ... | ... | ~$/hr |

**Recommendation for prototype:** {Choice} because {reason}
**For production you'd want:** {Different choice if applicable}
```

**After explaining all services, ask user:**
- Do you agree with these service selections?
- Any preferences for alternatives?
- Any cost constraints to consider?

**Quality Gate:** User confirmed service selections

### Phase 3: Cost & Security Planning (5-10 min)

**Objective:** Estimate costs, identify security requirements for prototype

**Read reference file:** `reference/cost-security-tradeoffs.md`

**Generate cost estimate using:** `scripts/estimate_costs.py`

**Present to user:**
```markdown
## Cost Estimate for Prototype Deployment

| Service | Config | Hourly | Daily | Monthly |
|---------|--------|--------|-------|---------|
| ECS Fargate | 2 tasks, 0.5 vCPU | $0.04 | $0.96 | $28.80 |
| ALB | 1 load balancer | $0.02 | $0.48 | $14.40 |
| ... | ... | ... | ... | ... |
| **TOTAL** | | **$X.XX** | **$XX.XX** | **$XXX.XX** |

### Assumptions
- {Running 24/7 vs business hours only}
- {Data transfer estimates}
- {Storage estimates}

### Prototype vs Production
- Prototype config: ~$X/month
- Production config would be: ~$Y/month
- Savings from prototype mode: $Z/month
```

**Quality Gate:** User accepted cost estimate

### Phase 4: Infrastructure Deployment (15-45 min)

**Objective:** Deploy infrastructure using existing scripts and Terraform

**Use existing scripts in:** `aws/scripts/`
- `deploy.py` - Main deployment orchestrator
- `destroy.py` - Teardown orchestrator

**Steps:**
1. Verify prerequisites (Docker, Terraform, AWS CLI)
2. Update Terraform variables if needed
3. Run deployment:
   ```bash
   python aws/scripts/deploy.py
   ```
4. Capture outputs (URLs, ARNs, etc.)
5. Update `aws/scripts/README.md` with new resources

**On deployment failure:**
- Check CloudWatch logs
- Review ECS service events
- Fix issue and retry

**Quality Gate:** Deployment successful, all services healthy

### Phase 5: Validation & Testing (10-20 min)

**Objective:** Verify deployment works

**Tests to run:**
1. Health endpoint check: `curl {ALB_URL}/health`
2. API connectivity: Test main endpoints
3. Worker connectivity: Submit test job
4. Log verification: Check CloudWatch for errors

**Document results:**
```markdown
## Deployment Validation - {Date}

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| API health | 200 OK | ... | PASS/FAIL |
| Frontend loads | 200 OK | ... | PASS/FAIL |
| Worker processes | Job completes | ... | PASS/FAIL |
| Logs clean | No errors | ... | PASS/FAIL |
```

**Quality Gate:** All critical tests passing

### Phase 6: Cleanup Offer (MANDATORY)

**THIS PHASE CANNOT BE SKIPPED**

**Objective:** Offer to destroy resources to avoid ongoing charges

**Run:** `python .claude/skills/aws-deployment/scripts/generate_destroy_warning.py`

**Present to user:**
```markdown
## IMPORTANT: Resource Cleanup Decision

Your AWS resources are now running and **incurring charges**.

### Resources Created
- ECS Cluster: pharma-test-gen-cluster
- ECS Services: 3 (API, Worker, Frontend)
- ALB: 2 (API, Frontend)
- SQS Queue: 1
- CloudWatch Log Groups: 3
- S3 Buckets: 2

### Ongoing Costs
| Timeframe | Cost |
|-----------|------|
| Per HOUR | ~$0.50 |
| Per DAY | ~$12.00 |
| Per WEEK | ~$84.00 |
| Per MONTH | ~$360.00 |

### My Recommendation

**For a prototype/learning project, I STRONGLY RECOMMEND destroying
these resources now.** You can redeploy anytime with a single command.

Keeping resources running for a weekend = ~$24 wasted
Keeping resources running for a week = ~$84 wasted
Keeping resources running for a month = ~$360 wasted

### Your Options

1. **DESTROY NOW** (Recommended)
   - Run: `python aws/scripts/destroy.py`
   - All resources removed
   - No ongoing charges
   - ~5 minutes to redeploy later

2. **KEEP RUNNING**
   - Resources stay active
   - Charges continue accumulating
   - Set a reminder to destroy later
```

**Ask user explicitly:**
```
Do you want to destroy these resources now?
- Yes: I'll run destroy.py to clean everything up
- No: I understand I'll incur ongoing charges of ~$X/day
```

**If user chooses NO:**
```markdown
### Reminder Set

You chose to keep resources running. Remember:
- Current burn rate: ~$X/day
- Destroy command: `python aws/scripts/destroy.py`
- Check AWS Cost Explorer: https://console.aws.amazon.com/cost-management/

I'll remind you about these costs next time you start a conversation.
```

**Quality Gate:** User explicitly chose to keep or destroy

---

## AWS Service Explanations (Dynamic)

When deploying ANY AWS service, use this template:

```markdown
## Creating {Service Name}

**What is {ABBREVIATION}?**
{Full Name} - {Simple 1-sentence explanation}

**Why we need it in this project:**
{Specific role - not generic description}

**Alternatives considered:**
- {Alt 1}: {Why not chosen}
- {Alt 2}: {Why not chosen}

**Cost for prototype:** ~${X}/hour (Dec 2025 pricing)
```

**Always verify pricing with WebSearch before stating costs.**

---

## Folder Organization

Keep the `aws/` folder organized:

```
aws/
├── scripts/           # Active Python scripts only
│   ├── deploy.py     # Main deployment
│   ├── destroy.py    # Teardown
│   └── README.md     # Usage documentation
├── terraform/         # Infrastructure as Code
├── iam-policies/      # IAM policy JSON files
├── docs/              # Research notes, architecture docs
└── archive/           # Old/unused files
    ├── legacy/       # Old shell scripts
    └── utils/        # One-time utility scripts
```

**After any deployment:**
1. Move completed research notes to `aws/docs/`
2. Archive any one-time scripts to `aws/archive/utils/`
3. Update `aws/scripts/README.md` with current state

---

## Integration with Existing Scripts

This skill wraps the existing deployment infrastructure:

| Script | Location | Purpose |
|--------|----------|---------|
| deploy.py | aws/scripts/ | Full deployment orchestration |
| destroy.py | aws/scripts/ | Clean teardown |
| run_local.py | aws/scripts/ | Local Docker development |

**Do not duplicate functionality** - use existing scripts.

---

## Success Criteria

A deployment is successful when:

1. [ ] Research completed with documentation
2. [ ] All services explained to user
3. [ ] Cost estimate presented and accepted
4. [ ] Terraform apply successful
5. [ ] Health checks passing
6. [ ] **User explicitly chose to destroy or keep resources**

The final checkbox is MANDATORY - deployment is not complete until
the user has made a conscious decision about cleanup.

---

## Reference Files

For detailed guidance, see:
- `reference/cost-security-tradeoffs.md` - Prototype vs production decisions
- `reference/common-architectures.md` - Cost estimates for common patterns
