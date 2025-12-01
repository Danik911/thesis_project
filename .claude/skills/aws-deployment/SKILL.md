---
name: aws-deployment
description: Deploys AWS infrastructure with research-first approach. Uses AWS MCP tools for documentation, regional availability, and resource management. ALWAYS searches AWS documentation before writing code, explains services and abbreviations, considers alternatives, maintains organized aws/ folder, and CRITICALLY offers to destroy resources after testing. Use PROACTIVELY for any AWS deployment, Terraform, ECS, Fargate, Lambda, S3, RDS, or cloud infrastructure tasks. MUST BE USED for prototype/learning projects to avoid unexpected costs.
allowed-tools: [
  "Bash", "Read", "Write", "Edit", "Grep", "Glob", "AskUserQuestion", "WebFetch",
  "mcp__aws-knowledge-mcp__aws___search_documentation",
  "mcp__aws-knowledge-mcp__aws___read_documentation",
  "mcp__aws-knowledge-mcp__aws___recommend",
  "mcp__aws-knowledge-mcp__aws___get_regional_availability",
  "mcp__aws-knowledge-mcp__aws___list_regions",
  "mcp__aws-api-mcp__suggest_aws_commands",
  "mcp__aws-api-mcp__call_aws",
  "mcp__aws-ccapi-mcp__check_environment_variables",
  "mcp__aws-ccapi-mcp__get_aws_session_info",
  "mcp__aws-ccapi-mcp__get_resource_schema_information",
  "mcp__aws-ccapi-mcp__list_resources",
  "mcp__aws-ccapi-mcp__get_resource",
  "mcp__aws-ccapi-mcp__generate_infrastructure_code",
  "mcp__aws-ccapi-mcp__explain",
  "mcp__aws-ccapi-mcp__run_checkov",
  "mcp__aws-ccapi-mcp__create_resource",
  "mcp__aws-ccapi-mcp__update_resource",
  "mcp__aws-ccapi-mcp__delete_resource",
  "mcp__aws-ccapi-mcp__get_aws_account_info"
]
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

## AWS MCP Tools Reference

This skill uses AWS MCP servers for authoritative documentation and resource management.

### Documentation Research (aws-knowledge-mcp)

| Tool | Use For |
|------|---------|
| `aws___search_documentation` | Search with topic filters |
| `aws___read_documentation` | Fetch full doc page |
| `aws___recommend` | Find related docs |
| `aws___get_regional_availability` | Check service availability |

**Search Topics:**
- `reference_documentation` - API/SDK/CLI references
- `current_awareness` - New features, announcements
- `troubleshooting` - Error messages, debugging
- `cloudformation` - CFN templates, SAM
- `cdk_docs` / `cdk_constructs` - CDK guidance
- `general` - Architecture, best practices, blogs

### AWS Operations (aws-api-mcp)

| Tool | Use For |
|------|---------|
| `suggest_aws_commands` | Natural language to CLI |
| `call_aws` | Execute AWS CLI commands |

### Resource Management (aws-ccapi-mcp)

| Tool | Use For |
|------|---------|
| `check_environment_variables` | Validate AWS env setup (ALWAYS FIRST) |
| `get_aws_session_info` | Confirm account/region (ALWAYS SECOND) |
| `list_resources` | List resources by type |
| `get_resource` | Get resource details |
| `run_checkov` | Security scanning |
| `generate_infrastructure_code` | Generate CloudFormation |
| `create_resource` / `update_resource` / `delete_resource` | Manage resources |

**CCAPI Workflow (mandatory order):**
1. `check_environment_variables()` → Get environment_token
2. `get_aws_session_info(environment_token)` → Get credentials_token
3. Use tokens for subsequent operations

### Fallback: WebFetch

Use `WebFetch` only when MCP search returns no results for:
- AWS Pricing Calculator pages
- Specific blog posts not indexed
- External comparison articles

---

## 6-Phase Workflow

### Phase 1: Research & Discovery (10-15 min)

**Objective:** Gather current AWS documentation using MCP tools

**Steps:**

1. **Identify AWS services** needed for the deployment

2. **Research each service** using AWS Knowledge MCP:
   ```
   # For service features and pricing
   mcp__aws-knowledge-mcp__aws___search_documentation(
     search_phrase="{service} pricing features eu-west-2",
     topics=["general", "reference_documentation"],
     limit=5
   )

   # For recent updates/changes
   mcp__aws-knowledge-mcp__aws___search_documentation(
     search_phrase="{service} new features 2025",
     topics=["current_awareness"],
     limit=3
   )
   ```

3. **Check regional availability** (eu-west-2):
   ```
   mcp__aws-knowledge-mcp__aws___get_regional_availability(
     region="eu-west-2",
     resource_type="product",
     filters=["Amazon ECS", "Amazon RDS", "Amazon S3"]
   )
   ```

4. **Read specific documentation** when needed:
   ```
   mcp__aws-knowledge-mcp__aws___read_documentation(
     url="https://docs.aws.amazon.com/...",
     max_length=5000
   )
   ```

5. **Create research notes file:** `aws/docs/research-{timestamp}.md`

**Research Notes Template:**
```markdown
# AWS Research Notes - {Date}

## MCP Search Results

### {Service 1 Name}
- **Full Name:** {Expand abbreviation}
- **Pricing (Dec 2025):** {From MCP search results}
- **Regional Availability:** {From get_regional_availability}
- **Key Features:** {Relevant features}
- **Known Issues:** {Any deprecations or problems}
- **Source URLs:** {From MCP results}

### {Service 2 Name}
...
```

**Quality Gate:** Research file created with MCP search results documented

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

**Objective:** Estimate costs, validate environment, identify security requirements

**Pre-Deployment Validation (MANDATORY):**
```
# Step 1: Check environment (ALWAYS FIRST)
mcp__aws-ccapi-mcp__check_environment_variables()
# Returns: environment_token, aws_region, readonly_mode

# Step 2: Get session info (ALWAYS SECOND)
mcp__aws-ccapi-mcp__get_aws_session_info(
  environment_token="env_xxx..."
)
# Returns: credentials_token, account_id, region
```

**Verify CloudFormation resource availability:**
```
mcp__aws-knowledge-mcp__aws___get_regional_availability(
  region="eu-west-2",
  resource_type="cfn",
  filters=["AWS::ECS::Service", "AWS::RDS::DBCluster", "AWS::SQS::Queue"]
)
```

**Read reference file:** `reference/cost-security-tradeoffs.md`

**Generate cost estimate using:** `scripts/estimate_costs.py`

**Verify pricing with MCP:**
```
mcp__aws-knowledge-mcp__aws___search_documentation(
  search_phrase="ECS Fargate pricing eu-west-2",
  topics=["general"],
  limit=3
)
```

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

**Objective:** Deploy infrastructure with security validation

**Use existing scripts in:** `aws/scripts/`
- `deploy.py` - Main deployment orchestrator
- `destroy.py` - Teardown orchestrator

**Pre-Deployment Security Scan (Recommended):**

When generating CloudFormation via CCAPI:
```
# 1. Generate infrastructure code
mcp__aws-ccapi-mcp__generate_infrastructure_code(
  resource_type="AWS::ECS::Service",
  properties={...},
  credentials_token="..."
)

# 2. Explain the generated code (MANDATORY - show to user)
mcp__aws-ccapi-mcp__explain(generated_code_token="...")

# 3. Run Checkov security scan
mcp__aws-ccapi-mcp__run_checkov(explained_token="...")
```

**Security Scan Results:**
- `scan_status='PASSED'`: Proceed with deployment
- `scan_status='FAILED'`: Present findings to user, ask how to proceed:
  - **Fix issues**: Address security findings first
  - **Proceed anyway**: User accepts risk (document in research notes)
  - **Cancel**: Abort deployment

**Steps:**
1. **Validate AWS credentials** via CLI:
   ```
   mcp__aws-api-mcp__call_aws(
     cli_command="aws sts get-caller-identity --region eu-west-2"
   )
   ```
2. Verify prerequisites (Docker, Terraform, AWS CLI)
3. Update Terraform variables if needed
4. Run deployment:
   ```bash
   python aws/scripts/deploy.py
   ```
5. Capture outputs (URLs, ARNs, etc.)
6. Update `aws/scripts/README.md` with new resources

**On deployment failure:**
- Check CloudWatch logs via CLI:
  ```
  mcp__aws-api-mcp__call_aws(
    cli_command="aws logs describe-log-groups --region eu-west-2"
  )
  ```
- Search troubleshooting docs:
  ```
  mcp__aws-knowledge-mcp__aws___search_documentation(
    search_phrase="{error message}",
    topics=["troubleshooting"],
    limit=5
  )
  ```
- Fix issue and retry

**Quality Gate:** Deployment successful, all services healthy

### Phase 5: Validation & Testing (10-20 min)

**Objective:** Verify deployment using MCP tools and manual tests

**Resource Verification via MCP:**
```
# List deployed ECS services
mcp__aws-ccapi-mcp__list_resources(
  resource_type="AWS::ECS::Service",
  region="eu-west-2"
)

# Get specific resource details with security analysis
mcp__aws-ccapi-mcp__get_resource(
  resource_type="AWS::ECS::Service",
  identifier="pharma-test-gen-api",
  region="eu-west-2",
  analyze_security=True
)

# List ALBs
mcp__aws-ccapi-mcp__list_resources(
  resource_type="AWS::ElasticLoadBalancingV2::LoadBalancer",
  region="eu-west-2"
)
```

**Health Checks via AWS CLI:**
```
# Check target group health
mcp__aws-api-mcp__call_aws(
  cli_command="aws elbv2 describe-target-health --target-group-arn {ARN} --region eu-west-2"
)

# Check ECS service status
mcp__aws-api-mcp__call_aws(
  cli_command="aws ecs describe-services --cluster {CLUSTER} --services {SERVICE} --region eu-west-2"
)
```

**Manual Tests:**
1. Health endpoint check: `curl {ALB_URL}/health`
2. API connectivity: Test main endpoints
3. Worker connectivity: Submit test job
4. Log verification: Check CloudWatch for errors

**Document results:**
```markdown
## Deployment Validation - {Date}

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| CCAPI list_resources | Resources found | ... | PASS/FAIL |
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

**Always verify pricing with MCP before stating costs:**
```
mcp__aws-knowledge-mcp__aws___search_documentation(
  search_phrase="{service} pricing eu-west-2",
  topics=["general"],
  limit=3
)
```

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
