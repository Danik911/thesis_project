# AWS ECR/ECS Troubleshooting Guide

Complete troubleshooting reference for AWS container services (ECR, ECS) when used with Docker.

---

## ECR Authentication Issues

### Error: "no basic auth credentials"

**Symptom:**
```
Error response from daemon: pull access denied for <account>.dkr.ecr.<region>.amazonaws.com/<repo>
no basic auth credentials
```

**Cause:** ECR login token expired (tokens valid for 12 hours)

**Solution:**
```bash
# Get fresh ECR login token and authenticate
aws ecr get-login-password --region eu-west-2 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.eu-west-2.amazonaws.com

# Verify authentication
docker pull <account-id>.dkr.ecr.eu-west-2.amazonaws.com/<repo>:<tag>
```

**Using AWS MCP:**
```
Tool: mcp__aws-api-mcp__call_aws
Command: aws ecr get-login-password --region eu-west-2
```

### Error: "denied: Your authorization token has expired"

**Cause:** Same as above - token expiration

**Prevention:** Script ECR login before docker operations:
```bash
#!/bin/bash
# ecr-login.sh
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-eu-west-2}

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
```

---

## ECS Pull Failures

### Error: "CannotPullContainerError"

**Symptom:** ECS task fails to start with image pull error

**Diagnosis Checklist:**

1. **IAM Permissions** - Task execution role needs ECR access
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "ecr:GetAuthorizationToken",
       "ecr:BatchCheckLayerAvailability",
       "ecr:GetDownloadUrlForLayer",
       "ecr:BatchGetImage"
     ],
     "Resource": "*"
   }
   ```

2. **Network Configuration** - Private subnets need NAT Gateway
   - Check: VPC has NAT Gateway in public subnet
   - Check: Private subnet route table has 0.0.0.0/0 -> NAT Gateway

3. **Image Existence** - Verify image tag exists
   ```bash
   aws ecr describe-images --repository-name <repo> \
     --image-ids imageTag=<tag> --region eu-west-2
   ```

**Using AWS MCP:**
```
Tool: mcp__aws-ccapi-mcp__list_resources
Resource Type: AWS::ECS::TaskDefinition
```

### Error: "ResourceInitializationError: unable to pull secrets"

**Cause:** Task execution role missing Secrets Manager permissions

**Solution:** Add to task execution role:
```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": "arn:aws:secretsmanager:<region>:<account>:secret:<secret-name>*"
}
```

---

## Docker Hub Rate Limiting

### Error: "toomanyrequests: You have reached your pull rate limit"

**Symptom:** Docker Hub anonymous pull limit exceeded (100 pulls/6 hours)

**Solutions:**

1. **Use ECR Public Gallery** (preferred for AWS):
   ```dockerfile
   # Instead of: FROM python:3.12-slim
   FROM public.ecr.aws/docker/library/python:3.12-slim
   ```

2. **Authenticate to Docker Hub**:
   ```bash
   docker login --username <dockerhub-user>
   ```

3. **Use ECR Pull-Through Cache** (enterprise):
   - Configure ECR pull-through cache rule for Docker Hub
   - Images cached in your ECR, no rate limits

---

## Common ECS Debugging Commands

```bash
# List failed tasks
aws ecs list-tasks --cluster <cluster> --desired-status STOPPED

# Get task failure reason
aws ecs describe-tasks --cluster <cluster> --tasks <task-arn> \
  --query 'tasks[0].stoppedReason'

# View task logs (if CloudWatch configured)
aws logs get-log-events --log-group-name /ecs/<service> \
  --log-stream-name ecs/<container>/<task-id>

# Check service events for deployment issues
aws ecs describe-services --cluster <cluster> --services <service> \
  --query 'services[0].events[:5]'
```

---

## AWS MCP Tools Reference

| Tool | Purpose | Example Use |
|------|---------|-------------|
| `mcp__aws-api-mcp__call_aws` | Execute AWS CLI | ECR login, describe tasks |
| `mcp__aws-knowledge-mcp__aws___search_documentation` | Search AWS docs | Find ECS troubleshooting guides |
| `mcp__aws-ccapi-mcp__list_resources` | List resources | View ECS tasks, ECR repos |
| `mcp__aws-ccapi-mcp__get_resource` | Get resource details | Inspect task definition |

---

## Quick Diagnosis Flowchart

```
Image pull failure?
├── Local Docker → Check ECR authentication (12hr token)
├── ECS Task → Check:
│   ├── Task execution role (ECR permissions)
│   ├── VPC networking (NAT Gateway for private subnets)
│   └── Image tag exists in ECR
└── Rate limited → Use ECR Public or authenticate
```
