# MCP Tool Selection Guide

Quick reference for selecting AWS MCP tools.

## Decision Table

| I need to... | Use this tool |
|--------------|---------------|
| Search AWS docs | `aws-knowledge-mcp__aws___search_documentation` |
| Read specific doc page | `aws-knowledge-mcp__aws___read_documentation` |
| Find related docs | `aws-knowledge-mcp__aws___recommend` |
| Check service availability | `aws-knowledge-mcp__aws___get_regional_availability` |
| Troubleshoot errors | `aws___search_documentation` (topic: `troubleshooting`) |
| Find new features | `aws___search_documentation` (topic: `current_awareness`) |
| Get CDK guidance | `aws___search_documentation` (topic: `cdk_docs`) |
| Run AWS CLI command | `aws-api-mcp__call_aws` |
| Figure out CLI syntax | `aws-api-mcp__suggest_aws_commands` |
| Validate AWS credentials | `aws-ccapi-mcp__check_environment_variables` |
| List deployed resources | `aws-ccapi-mcp__list_resources` |
| Get resource details | `aws-ccapi-mcp__get_resource` |
| Security scan | `aws-ccapi-mcp__run_checkov` |

## Search Topics

| Topic | Best For |
|-------|----------|
| `general` | Architecture, best practices, pricing |
| `reference_documentation` | API/SDK/CLI syntax |
| `troubleshooting` | Error messages, debugging |
| `current_awareness` | New features, announcements |
| `cloudformation` | CFN templates, SAM |
| `cdk_docs` | CDK concepts |
| `cdk_constructs` | CDK code examples |

## CCAPI Workflow (Mandatory Order)

```
# 1. ALWAYS FIRST
env = check_environment_variables()

# 2. ALWAYS SECOND
session = get_aws_session_info(environment_token=env.token)

# 3. Then use tokens for operations
list_resources(...), get_resource(...), etc.
```

## Fallback: WebFetch

Use only when MCP returns no results:
- AWS Pricing Calculator pages
- Specific blog posts
- External articles
