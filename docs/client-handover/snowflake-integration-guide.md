# Snowflake Integration Guide for MES Agentic BI

> **Last updated**: February 2026
> **Applies to**: MES Agentic BI v1.x deployed on AWS ECS/Fargate
> **Package versions**: `snowflake-connector-python[pandas] >= 3.6.0` (tested with 4.3.0)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Snowflake-Side Setup](#3-snowflake-side-setup)
4. [Authentication Methods](#4-authentication-methods)
5. [AWS Secrets Manager](#5-aws-secrets-manager)
6. [ECS Task Role Configuration](#6-ecs-task-role-configuration)
7. [Network Security](#7-network-security)
8. [Application Configuration](#8-application-configuration)
9. [S3 External Stages (Optional)](#9-s3-external-stages-optional)
10. [Testing and Verification](#10-testing-and-verification)
11. [Performance Tuning](#11-performance-tuning)
12. [Troubleshooting](#12-troubleshooting)
13. [Official Documentation Links](#13-official-documentation-links)

---

## 1. Architecture Overview

The MES Agentic BI application connects to Snowflake **directly at runtime** to query tables and load reports into in-memory pandas DataFrames for analysis, filtering, and AI-assisted insights.

```
                                        Snowflake Cloud
                                        +-----------------------+
                                        |  Warehouse            |
                                        |  Database / Schema    |
                                        |  Tables / Views       |
                                        |  Named Stages (files) |
                                        +----------+------------+
                                                   |
                                          HTTPS/443 (TLS 1.2+)
                                                   |
                              Option A: NAT GW     |    Option B: PrivateLink
                              (public internet) ---+--- (private VPC endpoint)
                                                   |
+--------------------------------------------------+----------------------------+
|  AWS VPC (e.g. eu-west-2)                                                      |
|                                                                                |
|  +--Private Subnet-------------------------------------------+                 |
|  |                                                           |                 |
|  |  ECS Fargate Task                                         |                 |
|  |  +-----------------------------------------------------+ |                 |
|  |  |  MES Agentic BI API (FastAPI)                        | |                 |
|  |  |                                                      | |                 |
|  |  |  snowflake_connector.py                              | |                 |
|  |  |    -> snowflake.connector.connect()                  | |                 |
|  |  |    -> cur.fetch_pandas_all()                         | |                 |
|  |  |    -> DataFrame loaded into session                  | |                 |
|  |  +-----------------------------------------------------+ |                 |
|  |       |                                                   |                 |
|  |       | boto3 (IAM Task Role)                             |                 |
|  |       v                                                   |                 |
|  |  AWS Secrets Manager                                      |                 |
|  |  (Snowflake credentials)                                  |                 |
|  +-----------------------------------------------------------+                 |
+--------------------------------------------------------------------------------+
```

### Data Flow

1. User opens the Agentic BI app and selects **Snowflake** as the data source
2. User enters connection details (or defaults from env vars are used)
3. App calls `POST /bi/snowflake/tables` to list available tables
4. User selects a table/view to load
5. App calls `POST /bi/snowflake/load/table` which executes `SELECT * FROM table LIMIT {max_rows}`
6. Result is loaded via `fetch_pandas_all()` into a pandas DataFrame
7. DataFrame is stored in an in-memory session (TTL: 1 hour default)
8. User can filter, chat with copilot, and export (Excel/PDF) as usual

### Existing Integration Code

| File | Purpose |
|------|---------|
| `mes-agentic-bi/src/bi/snowflake_connector.py` | Connection management, table/stage queries, DataFrame loading |
| `mes-agentic-bi/src/bi/config.py` | `BI_SF_*` environment variable loading |
| `mes-agentic-bi/api/bi_router.py` | REST endpoints: `/bi/snowflake/tables`, `/bi/snowflake/load/table`, etc. |
| `mes-agentic-bi/frontend/components/bi/SnowflakeBrowser.tsx` | Frontend table/stage browser UI |

---

## 2. Prerequisites

### Snowflake

- [ ] Active Snowflake account ([sign up](https://signup.snowflake.com/))
- [ ] Account identifier (format: `<orgname>-<accountname>` or legacy `<account>.<region>`)
- [ ] A warehouse created and accessible to the service user
- [ ] A database and schema containing the report tables/views
- [ ] For PrivateLink: **Business Critical edition** or higher

### AWS

- [ ] VPC with private subnets (ECS tasks run here)
- [ ] NAT Gateway with Elastic IP (for Option A: IP allowlisting)
- [ ] ECS cluster and task definition for the API service
- [ ] AWS Secrets Manager accessible from the VPC
- [ ] IAM role for ECS tasks with Secrets Manager read access

### Application

- [ ] `snowflake-connector-python[pandas] >= 3.6.0` in `pyproject.toml` (already included)
- [ ] `boto3 >= 1.40.0` in `pyproject.toml` (already included)

---

## 3. Snowflake-Side Setup

Run these SQL commands in Snowflake as `ACCOUNTADMIN` (or a role with sufficient privileges). Replace placeholder values with your actual configuration.

### 3.1 Create a Dedicated Warehouse

```sql
-- A small warehouse for BI queries (auto-suspends after 5 minutes of inactivity)
CREATE WAREHOUSE IF NOT EXISTS MES_BI_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'MES Agentic BI application queries';
```

**Sizing guidance**:

| Size | Credits/Hour | Recommendation |
|------|-------------|----------------|
| X-Small | 1 | Start here. Suitable for most BI queries (<100K rows) |
| Small | 2 | If queries regularly spill to local disk |
| Medium | 4 | For complex joins or >500K row scans |

> Ref: [Warehouse considerations](https://docs.snowflake.com/en/user-guide/warehouses-considerations)

### 3.2 Create a Service User and Role

```sql
-- Create a dedicated role for the BI application
CREATE ROLE IF NOT EXISTS MES_BI_ROLE
  COMMENT = 'Role for MES Agentic BI application';

-- Create a service account user
CREATE USER IF NOT EXISTS SVC_MES_BI
  DEFAULT_WAREHOUSE = MES_BI_WH
  DEFAULT_ROLE = MES_BI_ROLE
  MUST_CHANGE_PASSWORD = FALSE
  COMMENT = 'Service account for MES Agentic BI';

-- Grant the role to the user
GRANT ROLE MES_BI_ROLE TO USER SVC_MES_BI;

-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE MES_BI_WH TO ROLE MES_BI_ROLE;
```

### 3.3 Grant Data Access

```sql
-- Replace YOUR_DATABASE and YOUR_SCHEMA with actual names

-- Database-level access
GRANT USAGE ON DATABASE YOUR_DATABASE TO ROLE MES_BI_ROLE;

-- Schema-level access
GRANT USAGE ON SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE MES_BI_ROLE;

-- Read-only access to all current and future tables/views in the schema
GRANT SELECT ON ALL TABLES IN SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE MES_BI_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE MES_BI_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE MES_BI_ROLE;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE MES_BI_ROLE;

-- (Optional) Stage access for file-based reports
GRANT USAGE ON ALL STAGES IN SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE MES_BI_ROLE;
GRANT READ ON ALL STAGES IN SCHEMA YOUR_DATABASE.YOUR_SCHEMA TO ROLE MES_BI_ROLE;
```

### 3.4 Network Policy (for IP Allowlisting)

If using Option A (NAT Gateway), create a network policy to restrict access:

```sql
-- Replace with your NAT Gateway Elastic IP(s)
CREATE NETWORK RULE IF NOT EXISTS MES_BI_ECS_RULE
  MODE = INGRESS
  TYPE = IPV4
  VALUE_LIST = ('203.0.113.10/32', '203.0.113.11/32');

CREATE NETWORK POLICY IF NOT EXISTS MES_BI_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('MES_BI_ECS_RULE')
  COMMENT = 'Restrict MES BI access to ECS NAT Gateway IPs';

-- Apply to the service user (not account-wide)
ALTER USER SVC_MES_BI SET NETWORK_POLICY = MES_BI_POLICY;
```

> Ref: [Network policies](https://docs.snowflake.com/en/user-guide/network-policies) | [Network rules](https://docs.snowflake.com/en/user-guide/network-rules)

---

## 4. Authentication Methods

### Option A: Key Pair Authentication (Recommended for Production)

Key pair authentication uses RSA key pairs — no passwords to rotate. The private key is stored in AWS Secrets Manager and the public key is registered with the Snowflake user.

**Step 1: Generate an RSA key pair**

```bash
# Generate encrypted private key (2048-bit RSA minimum, 4096-bit recommended)
openssl genrsa 4096 | openssl pkcs8 -topk8 -v2 aes-256-cbc -inform PEM -out rsa_key.p8
# Enter a passphrase when prompted (save this — you'll store it in Secrets Manager)

# Extract the public key
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

**Step 2: Register the public key with the Snowflake user**

```sql
-- Copy the public key content (without the BEGIN/END headers)
ALTER USER SVC_MES_BI SET RSA_PUBLIC_KEY = 'MIIBIjANBgkqhki...';

-- Verify
DESC USER SVC_MES_BI;
-- Check RSA_PUBLIC_KEY_FP is populated
```

**Step 3: Test the connection locally**

```python
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

with open("rsa_key.p8", "rb") as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=b"your_passphrase",
        backend=default_backend(),
    )

private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

conn = snowflake.connector.connect(
    account="<orgname>-<accountname>",
    user="SVC_MES_BI",
    private_key=private_key_bytes,
    warehouse="MES_BI_WH",
    database="YOUR_DATABASE",
    schema="YOUR_SCHEMA",
)

cur = conn.cursor()
cur.execute("SELECT CURRENT_TIMESTAMP()")
print(cur.fetchone())
conn.close()
```

**Key rotation**: Snowflake supports two public keys simultaneously (`RSA_PUBLIC_KEY` and `RSA_PUBLIC_KEY_2`) for zero-downtime rotation.

```sql
-- Set the new key as key 2
ALTER USER SVC_MES_BI SET RSA_PUBLIC_KEY_2 = 'MIIBIjANBgkqhki...NEW...';

-- After verifying the new key works, remove the old one
ALTER USER SVC_MES_BI UNSET RSA_PUBLIC_KEY;
-- Then promote key 2 to key 1 if desired
```

> Ref: [Key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)

### Option B: Username/Password (Simpler, for Dev/Staging)

Simpler setup, but requires periodic password rotation and is less secure.

```python
import snowflake.connector

conn = snowflake.connector.connect(
    account="<orgname>-<accountname>",
    user="SVC_MES_BI",
    password="your_secure_password",
    warehouse="MES_BI_WH",
    database="YOUR_DATABASE",
    schema="YOUR_SCHEMA",
)
```

Set a strong password and consider MFA:

```sql
ALTER USER SVC_MES_BI SET PASSWORD = 'YourStr0ng!P@ssw0rd';
```

> This is how the app works out of the box — credentials passed via `BI_SF_*` environment variables.

---

## 5. AWS Secrets Manager

Store Snowflake credentials in AWS Secrets Manager instead of plain environment variables.

### 5.1 Create the Secret

**For Key Pair auth:**

```bash
aws secretsmanager create-secret \
  --name "prod/mes-bi/snowflake" \
  --description "MES Agentic BI Snowflake credentials" \
  --secret-string '{
    "account": "<orgname>-<accountname>",
    "user": "SVC_MES_BI",
    "private_key_pem": "-----BEGIN ENCRYPTED PRIVATE KEY-----\nMIIE...\n-----END ENCRYPTED PRIVATE KEY-----",
    "private_key_passphrase": "your_passphrase",
    "warehouse": "MES_BI_WH",
    "database": "YOUR_DATABASE",
    "schema": "YOUR_SCHEMA",
    "role": "MES_BI_ROLE"
  }' \
  --region eu-west-2
```

**For Username/Password auth:**

```bash
aws secretsmanager create-secret \
  --name "prod/mes-bi/snowflake" \
  --description "MES Agentic BI Snowflake credentials" \
  --secret-string '{
    "account": "<orgname>-<accountname>",
    "user": "SVC_MES_BI",
    "password": "YourStr0ng!P@ssw0rd",
    "warehouse": "MES_BI_WH",
    "database": "YOUR_DATABASE",
    "schema": "YOUR_SCHEMA",
    "role": "MES_BI_ROLE"
  }' \
  --region eu-west-2
```

### 5.2 Retrieve Credentials in Python

```python
import json
import boto3

def get_snowflake_credentials(
    secret_name: str = "prod/mes-bi/snowflake",
    region: str = "eu-west-2",
) -> dict:
    """Retrieve Snowflake credentials from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])
```

### 5.3 Integration Pattern

There are **two approaches** to pass Snowflake credentials to the application:

**Approach A: ECS Task Definition `secrets` (Recommended)**

Use ECS native secret injection to populate `BI_SF_*` environment variables directly from Secrets Manager. No code changes required.

```json
{
  "containerDefinitions": [
    {
      "name": "mes-bi-api",
      "secrets": [
        {
          "name": "BI_SF_ACCOUNT",
          "valueFrom": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake:account::"
        },
        {
          "name": "BI_SF_USER",
          "valueFrom": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake:user::"
        },
        {
          "name": "BI_SF_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake:password::"
        },
        {
          "name": "BI_SF_WAREHOUSE",
          "valueFrom": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake:warehouse::"
        },
        {
          "name": "BI_SF_DATABASE",
          "valueFrom": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake:database::"
        },
        {
          "name": "BI_SF_SCHEMA",
          "valueFrom": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake:schema::"
        }
      ]
    }
  ]
}
```

> With this approach, the `BI_SF_*` env vars are populated at container start. The existing code in `config.py` reads them automatically. The frontend Snowflake browser will show them as pre-filled defaults.

**Approach B: Runtime boto3 retrieval**

Fetch the full secret at runtime via `boto3`. Requires a code enhancement to `snowflake_connector.py` (optional — see [Section 8.2](#82-optional-code-enhancement-secrets-manager-integration)).

> Ref: [Retrieve secrets in ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html) | [Secrets Manager Python SDK](https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets-python-sdk.html)

---

## 6. ECS Task Role Configuration

Two IAM roles are involved:

| Role | Used By | Purpose |
|------|---------|---------|
| **Task Execution Role** | ECS/Fargate agent | Pull container images from ECR, write CloudWatch logs, **read secrets at container startup** |
| **Task Role** | Application code (boto3) | Access AWS services at runtime (Secrets Manager, Bedrock, S3) |

### 6.1 Task Execution Role (for ECS secret injection)

The execution role needs `secretsmanager:GetSecretValue` to inject `BI_SF_*` vars from the secret:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake*"
    }
  ]
}
```

Attach this inline policy to the task execution role, or use the managed `AmazonECSTaskExecutionRolePolicy` plus the above.

### 6.2 Task Role (for runtime boto3 access)

If using Approach B (runtime retrieval) or if the app needs other AWS services:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SecretsManagerRead",
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:eu-west-2:123456789012:secret:prod/mes-bi/snowflake*"
    },
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.*"
    }
  ]
}
```

**Trust policy** (same for both roles):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

> Ref: [ECS task IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html) | [Task execution role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)

---

## 7. Network Security

The ECS Fargate tasks must be able to reach Snowflake on port 443. Two approaches:

### Option A: NAT Gateway + IP Allowlisting (Simpler)

**How it works**: ECS tasks in private subnets route outbound traffic through a NAT Gateway with a fixed Elastic IP. That IP is allowlisted in a Snowflake network policy.

**AWS side:**

1. Ensure your VPC has a **NAT Gateway** in a public subnet
2. Note the NAT Gateway's **Elastic IP** address (e.g., `203.0.113.10`)
3. Private subnets should have a route table entry: `0.0.0.0/0 -> nat-gateway-id`
4. Security group on ECS tasks: allow outbound HTTPS (port 443) to `0.0.0.0/0` (or Snowflake IP ranges)

**Snowflake side:** (see [Section 3.4](#34-network-policy-for-ip-allowlisting))

```sql
CREATE NETWORK RULE MES_BI_ECS_RULE
  MODE = INGRESS
  TYPE = IPV4
  VALUE_LIST = ('203.0.113.10/32');  -- Your NAT GW Elastic IP

CREATE NETWORK POLICY MES_BI_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('MES_BI_ECS_RULE');

ALTER USER SVC_MES_BI SET NETWORK_POLICY = MES_BI_POLICY;
```

**Pros**: Simple setup, works with any Snowflake edition.
**Cons**: Traffic traverses the public internet (encrypted via TLS 1.2+), NAT Gateway data processing costs ($0.045/GB).

### Option B: AWS PrivateLink (Most Secure)

**How it works**: Creates a VPC Interface Endpoint that connects directly to Snowflake's internal network. Traffic never leaves the AWS backbone.

**Requirements**: Snowflake **Business Critical edition** or higher.

**Step 1: Get the PrivateLink configuration from Snowflake**

```sql
-- Run as ACCOUNTADMIN in Snowflake
SELECT SYSTEM$GET_PRIVATELINK_CONFIG();
```

This returns JSON with:
- `privatelink-account-name` — Account name for PrivateLink connections
- `privatelink-vpce-id` — The VPC Endpoint Service name (e.g., `com.amazonaws.vpce.us-east-1.vpce-svc-...`)
- `privatelink-account-url` — URL to use for connections
- `privatelink-ocsp-url` — OCSP URL for certificate validation

**Step 2: Authorize PrivateLink in Snowflake**

```sql
-- Authorize your AWS account
SELECT SYSTEM$AUTHORIZE_PRIVATELINK(
  '<your_aws_account_id>',
  'com.amazonaws.vpce.<region>.vpce-svc-<id>'
);
```

**Step 3: Create VPC Interface Endpoint in AWS**

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0abc123def456 \
  --service-name com.amazonaws.vpce.<region>.vpce-svc-<id> \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0abc123 subnet-0def456 \
  --security-group-ids sg-0abc123 \
  --private-dns-enabled false \
  --region <your-aws-region>
```

Security group for the VPC endpoint must allow:
- **Inbound**: TCP 443 from ECS task security group
- **Inbound**: TCP 80 from ECS task security group (OCSP)

**Step 4: Configure DNS (Route 53 Private Hosted Zone)**

Create a private hosted zone for `privatelink.snowflakecomputing.com` and add CNAME records:

```
<account>.privatelink.snowflakecomputing.com  -> vpce-<id>.vpce-svc-<id>.<region>.vpce.amazonaws.com
```

**Step 5: Update the Snowflake account identifier**

When using PrivateLink, the account identifier changes. Update the `BI_SF_ACCOUNT` to use the PrivateLink-specific format:

```
<orgname>-<accountname>.privatelink
```

**Step 6: (Optional) Block public access**

```sql
CREATE NETWORK RULE MES_BI_PRIVATELINK_RULE
  MODE = INGRESS
  TYPE = AWSVPCEID
  VALUE_LIST = ('vpce-0abc123def456');

CREATE NETWORK POLICY MES_BI_PRIVATE_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('MES_BI_PRIVATELINK_RULE')
  BLOCKED_IP_LIST = ('0.0.0.0/0');

ALTER USER SVC_MES_BI SET NETWORK_POLICY = MES_BI_PRIVATE_POLICY;
```

**Pros**: Zero public internet exposure, lowest latency, meets strict compliance requirements.
**Cons**: Requires Business Critical edition, more complex DNS setup, PrivateLink endpoint costs (~$0.01/hr per AZ + $0.01/GB processed).

> Ref: [AWS PrivateLink and Snowflake](https://docs.snowflake.com/en/user-guide/admin-security-privatelink)

### Comparison

| Aspect | NAT Gateway + IP Allowlist | AWS PrivateLink |
|--------|---------------------------|-----------------|
| Snowflake edition | Any | Business Critical+ |
| Network path | Public internet (TLS encrypted) | AWS private backbone |
| Setup complexity | Low | Medium-High |
| Monthly cost | ~$32/month + $0.045/GB | ~$7/AZ/month + $0.01/GB |
| Compliance | Suitable for most | Required for strict regulatory |
| Latency | Low | Lowest (same-region) |

---

## 8. Application Configuration

### 8.1 Environment Variables

The app reads Snowflake defaults from these `BI_SF_*` environment variables (defined in `mes-agentic-bi/src/bi/config.py`):

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BI_SF_ACCOUNT` | Yes | Snowflake account identifier | `myorg-myaccount` |
| `BI_SF_USER` | Yes | Snowflake username | `SVC_MES_BI` |
| `BI_SF_PASSWORD` | Yes* | Snowflake password (*not needed for key pair auth) | `YourStr0ng!P@ss` |
| `BI_SF_WAREHOUSE` | Yes | Default warehouse | `MES_BI_WH` |
| `BI_SF_DATABASE` | Yes | Default database | `PROD_DB` |
| `BI_SF_SCHEMA` | Yes | Default schema | `PUBLIC` |
| `BI_MAX_ROWS` | No | Max rows to load (default: 100,000) | `100000` |
| `BI_MAX_UPLOAD_SIZE_MB` | No | Max file size for stage files (default: 50) | `50` |

When these are set, the Snowflake browser in the frontend pre-fills the connection form with these values. Users can override them per-session.

### 8.2 Optional Code Enhancement: Secrets Manager Integration

To add runtime Secrets Manager retrieval (Approach B), add this function to `snowflake_connector.py`:

```python
def _get_connection_from_secrets(
    secret_name: str = "prod/mes-bi/snowflake",
    region: str = "eu-west-2",
) -> Any:
    """Open a Snowflake connection using credentials from AWS Secrets Manager."""
    import json
    import boto3

    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    creds = json.loads(response["SecretString"])

    # If private_key_pem is present, use key pair auth
    if "private_key_pem" in creds:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = serialization.load_pem_private_key(
            creds["private_key_pem"].encode("utf-8"),
            password=creds.get("private_key_passphrase", "").encode("utf-8") or None,
            backend=default_backend(),
        )
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        import snowflake.connector
        return snowflake.connector.connect(
            account=creds["account"],
            user=creds["user"],
            private_key=private_key_bytes,
            warehouse=creds.get("warehouse", ""),
            database=creds.get("database", ""),
            schema=creds.get("schema", ""),
            role=creds.get("role", ""),
            client_session_keep_alive=False,
        )
    else:
        # Fall back to username/password
        return _get_connection(
            account=creds["account"],
            user=creds["user"],
            password=creds["password"],
            warehouse=creds.get("warehouse", ""),
            database=creds.get("database", ""),
            schema=creds.get("schema", ""),
        )
```

> This is optional. The recommended approach (5.3 Approach A) uses ECS secret injection and requires zero code changes.

### 8.3 Docker Compose (Local Development)

For local development, add Snowflake vars to `mes-agentic-bi/.env.local`:

```bash
# Snowflake connection defaults
BI_SF_ACCOUNT=myorg-myaccount
BI_SF_USER=SVC_MES_BI
BI_SF_PASSWORD=YourDevP@ssword
BI_SF_WAREHOUSE=MES_BI_WH
BI_SF_DATABASE=DEV_DB
BI_SF_SCHEMA=PUBLIC
```

Then start the stack:

```bash
cd mes-agentic-bi && docker compose up -d
```

---

## 9. S3 External Stages (Optional)

If reports are exported from Snowflake to S3 as CSV/Excel files (e.g., via a scheduled task), the app can load them via Snowflake's named stages.

### 9.1 Create a Storage Integration

```sql
-- Run as ACCOUNTADMIN
CREATE STORAGE INTEGRATION MES_BI_S3_INTEGRATION
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789012:role/snowflake-s3-access'
  STORAGE_ALLOWED_LOCATIONS = ('s3://your-reports-bucket/exports/');
```

### 9.2 Get the Snowflake IAM Info

```sql
DESC INTEGRATION MES_BI_S3_INTEGRATION;
-- Note: STORAGE_AWS_IAM_USER_ARN and STORAGE_AWS_EXTERNAL_ID
```

### 9.3 Configure AWS IAM Trust

Create an IAM role `snowflake-s3-access` with this trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "<STORAGE_AWS_IAM_USER_ARN from step 9.2>"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "<STORAGE_AWS_EXTERNAL_ID from step 9.2>"
        }
      }
    }
  ]
}
```

And attach a permission policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::your-reports-bucket",
        "arn:aws:s3:::your-reports-bucket/exports/*"
      ]
    }
  ]
}
```

### 9.4 Create the External Stage

```sql
CREATE STAGE MES_BI_REPORTS_STAGE
  STORAGE_INTEGRATION = MES_BI_S3_INTEGRATION
  URL = 's3://your-reports-bucket/exports/'
  FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);

-- Grant access to the BI role
GRANT USAGE ON STAGE YOUR_DATABASE.YOUR_SCHEMA.MES_BI_REPORTS_STAGE TO ROLE MES_BI_ROLE;
GRANT READ ON STAGE YOUR_DATABASE.YOUR_SCHEMA.MES_BI_REPORTS_STAGE TO ROLE MES_BI_ROLE;
```

Users can then browse and load stage files via the Snowflake browser in the app UI.

> Ref: [Configure S3 storage integration](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration) | [CREATE STAGE](https://docs.snowflake.com/en/sql-reference/sql/create-stage)

---

## 10. Testing and Verification

### 10.1 Local Connectivity Test

```python
# test_snowflake_connection.py
import snowflake.connector

conn = snowflake.connector.connect(
    account="<your-account>",
    user="SVC_MES_BI",
    password="<your-password>",
    warehouse="MES_BI_WH",
    database="YOUR_DATABASE",
    schema="YOUR_SCHEMA",
)

# 1. Verify connection
cur = conn.cursor()
cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()")
print("Connection OK:", cur.fetchone())

# 2. List tables
cur.execute(
    "SELECT TABLE_NAME, ROW_COUNT FROM INFORMATION_SCHEMA.TABLES "
    "WHERE TABLE_SCHEMA = 'YOUR_SCHEMA' ORDER BY TABLE_NAME"
)
for row in cur.fetchall():
    print(f"  Table: {row[0]}, Rows: {row[1]}")

# 3. Fetch sample data
cur.execute("SELECT * FROM YOUR_TABLE LIMIT 5")
df = cur.fetch_pandas_all()
print(f"\nSample data ({len(df)} rows, {len(df.columns)} cols):")
print(df.head())

conn.close()
```

### 10.2 API Endpoint Test

```bash
# List tables via the API
curl -X POST http://localhost:8080/bi/snowflake/tables \
  -H "Content-Type: application/json" \
  -d '{
    "account": "<your-account>",
    "user": "SVC_MES_BI",
    "password": "<your-password>",
    "warehouse": "MES_BI_WH",
    "database": "YOUR_DATABASE",
    "schema": "YOUR_SCHEMA"
  }'

# Load a table into a session
curl -X POST http://localhost:8080/bi/snowflake/load/table \
  -H "Content-Type: application/json" \
  -d '{
    "account": "<your-account>",
    "user": "SVC_MES_BI",
    "password": "<your-password>",
    "warehouse": "MES_BI_WH",
    "database": "YOUR_DATABASE",
    "schema": "YOUR_SCHEMA",
    "table_name": "YOUR_TABLE"
  }'
```

### 10.3 Verification Checklist

| # | Check | Pass |
|---|-------|------|
| 1 | Snowflake user `SVC_MES_BI` can authenticate | [ ] |
| 2 | Network policy allows connections from ECS NAT IP / PrivateLink endpoint | [ ] |
| 3 | `MES_BI_ROLE` can `USE WAREHOUSE MES_BI_WH` | [ ] |
| 4 | `MES_BI_ROLE` can `SELECT` from target tables | [ ] |
| 5 | API `/bi/snowflake/tables` returns table list | [ ] |
| 6 | API `/bi/snowflake/load/table` loads data into session | [ ] |
| 7 | Frontend Snowflake browser shows tables and loads data | [ ] |
| 8 | Copilot can analyze Snowflake-loaded data | [ ] |
| 9 | Excel/PDF export works on Snowflake-loaded data | [ ] |
| 10 | Secrets Manager credentials are not exposed in logs/UI | [ ] |

---

## 11. Performance Tuning

### Warehouse Sizing

Start with **X-Small** (`BI_SF_WAREHOUSE=MES_BI_WH`). Monitor with:

```sql
-- Check for query spillage (indicates warehouse is too small)
SELECT QUERY_ID, BYTES_SPILLED_TO_LOCAL_STORAGE, BYTES_SPILLED_TO_REMOTE_STORAGE
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE WAREHOUSE_NAME = 'MES_BI_WH'
  AND BYTES_SPILLED_TO_LOCAL_STORAGE > 0
ORDER BY START_TIME DESC
LIMIT 20;
```

If spillage is frequent, scale up one size.

### Result Caching

Snowflake has three cache layers:

| Layer | Duration | Cost | Action |
|-------|----------|------|--------|
| **Result cache** | 24 hours | Free (no warehouse) | Keep query text identical between calls |
| **Metadata cache** | Persistent | Free | Use `COUNT(*)`, `MIN()`, `MAX()` |
| **Warehouse cache** | While running | Normal credits | Set `AUTO_SUSPEND = 300` to keep cache warm |

> The app uses `SELECT * FROM table LIMIT N` — identical queries will hit result cache if data hasn't changed.

### Row Limits

The app enforces `BI_MAX_ROWS` (default: 100,000). For large tables, consider:

- Creating **views** in Snowflake that pre-filter/aggregate data
- Using `LIMIT` + `ORDER BY` to get the most recent records
- Scheduling Snowflake tasks to export summaries to stages

### Connection Timeouts

Add timeout parameters for production stability:

```python
conn = snowflake.connector.connect(
    # ... credentials ...
    login_timeout=30,        # seconds to establish connection
    network_timeout=60,      # seconds for network operations
    socket_timeout=120,      # seconds for socket operations
    client_session_keep_alive=False,
)
```

---

## 12. Troubleshooting

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `250001: Could not connect to Snowflake backend` | Account identifier wrong or network blocked | Verify `BI_SF_ACCOUNT` format. Check NAT GW / PrivateLink setup. |
| `250003: Failed to connect to DB` | Database/schema doesn't exist or no access | Run `SHOW GRANTS TO ROLE MES_BI_ROLE` |
| `251001: ... IP ... is not allowed to access Snowflake` | Network policy blocking | Add your ECS NAT IP to the network rule |
| `252004: Failed to ... warehouse` | Warehouse suspended or no access | Check `GRANT USAGE ON WAREHOUSE ... TO ROLE MES_BI_ROLE` |
| `Table ... returned no rows` | Empty table or wrong schema | Verify table exists: `SELECT COUNT(*) FROM your_table` |
| `exceeds BI_MAX_ROWS` | Table too large for in-memory session | Increase `BI_MAX_ROWS` or create a filtered view |
| `snowflake-connector-python is not installed` | Missing dependency | Run `uv sync` or `pip install "snowflake-connector-python[pandas]"` |
| `JWT token is invalid` (key pair auth) | Public key mismatch or key expired | Verify fingerprint: `DESC USER SVC_MES_BI` — check `RSA_PUBLIC_KEY_FP` |
| Connection timeout | Firewall, VPC routing, or Snowflake maintenance | Check security groups, route tables, and [status.snowflake.com](https://status.snowflake.com) |

### Diagnostic Queries

```sql
-- Check current user/role/warehouse
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();

-- Check grants on the BI role
SHOW GRANTS TO ROLE MES_BI_ROLE;

-- Check network policies applied to the user
SHOW PARAMETERS LIKE 'NETWORK_POLICY' FOR USER SVC_MES_BI;

-- Check recent failed login attempts
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE USER_NAME = 'SVC_MES_BI'
  AND IS_SUCCESS = 'NO'
ORDER BY EVENT_TIMESTAMP DESC
LIMIT 20;

-- Check query history for the BI warehouse
SELECT QUERY_TEXT, EXECUTION_STATUS, ERROR_MESSAGE, TOTAL_ELAPSED_TIME
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE WAREHOUSE_NAME = 'MES_BI_WH'
ORDER BY START_TIME DESC
LIMIT 20;
```

---

## 13. Official Documentation Links

### Snowflake

| Topic | URL |
|-------|-----|
| Python Connector Overview | https://docs.snowflake.com/en/developer-guide/python-connector/python-connector |
| Python Connector — Connecting | https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect |
| Python Connector — pandas Integration | https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-pandas |
| Python Connector — API Reference | https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api |
| Python Connector 2026 Release Notes | https://docs.snowflake.com/en/release-notes/clients-drivers/python-connector-2026 |
| Key-Pair Authentication | https://docs.snowflake.com/en/user-guide/key-pair-auth |
| Network Policies | https://docs.snowflake.com/en/user-guide/network-policies |
| Network Rules | https://docs.snowflake.com/en/user-guide/network-rules |
| AWS PrivateLink | https://docs.snowflake.com/en/user-guide/admin-security-privatelink |
| S3 Storage Integration | https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration |
| CREATE STAGE | https://docs.snowflake.com/en/sql-reference/sql/create-stage |
| Warehouse Sizing | https://docs.snowflake.com/en/user-guide/warehouses-considerations |
| Query Performance | https://docs.snowflake.com/en/user-guide/performance-query-warehouse |
| Result Caching | https://docs.snowflake.com/en/user-guide/performance-query-warehouse-cache |
| Account Identifiers | https://docs.snowflake.com/en/user-guide/admin-account-identifier |
| Snowflake Status Page | https://status.snowflake.com |

### AWS

| Topic | URL |
|-------|-----|
| ECS Task IAM Roles | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html |
| ECS Task Execution Role | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html |
| ECS Secrets from Secrets Manager | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html |
| Secrets Manager Python SDK | https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets-python-sdk.html |
| Secrets Manager — Snowflake Partner | https://docs.aws.amazon.com/secretsmanager/latest/userguide/mes-partner-Snowflake.html |
| VPC PrivateLink Concepts | https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html |
| Create VPC Interface Endpoint | https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html |
| ECS Networking Best Practices | https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/networking.html |
| IAM Roles for ECS Overview | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-ecs-iam-role-overview.html |

### Package Registry

| Package | Version (Feb 2026) | URL |
|---------|-------------------|-----|
| `snowflake-connector-python` | 4.3.0 | https://pypi.org/project/snowflake-connector-python/ |
| `snowflake-sqlalchemy` | 1.8.2 | https://pypi.org/project/snowflake-sqlalchemy/ |
| `boto3` | 1.36.x | https://pypi.org/project/boto3/ |

---

## Appendix: Quick Start Checklist

For the fastest path to a working Snowflake connection:

1. [ ] Run the SQL in [Section 3](#3-snowflake-side-setup) to create warehouse, user, role, and grants
2. [ ] Choose an auth method ([Section 4](#4-authentication-methods)) and set up credentials
3. [ ] Store credentials in Secrets Manager ([Section 5](#5-aws-secrets-manager))
4. [ ] Configure ECS task definition with `secrets` entries ([Section 5.3](#53-integration-pattern))
5. [ ] Add IAM permissions for Secrets Manager ([Section 6](#6-ecs-task-role-configuration))
6. [ ] Set up network access — NAT GW IP allowlist or PrivateLink ([Section 7](#7-network-security))
7. [ ] Deploy the updated ECS task and verify with the checklist ([Section 10.3](#103-verification-checklist))
