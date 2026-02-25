# Pre-Flight Check: MES Agentic BI for PPRS PoC

**Date:** 2026-02-25
**PRP:** `PRPs/data-copilot-poc.md`
**Branch:** `feature/mes-agentic-bi`
**Analyzed by:** task-analyzer agent

---

**Setup Intensity: MODERATE-HEAVY**
Est. 45 minutes manual work + 0-24 hour wait for Bedrock model access approval

---

## Blocking Items (Read First)

1. AWS credentials are completely absent from `.env.local`. boto3 will fail immediately without them.
2. The Bedrock first-time-use form for Anthropic models must be submitted once per AWS account before any Claude model can be invoked. This is usually approved instantly to within a few minutes, but can take up to 24 hours.
3. The correct model ID to use is the US inference profile `us.anthropic.claude-sonnet-4-6`, NOT the base model ID `anthropic.claude-sonnet-4-6`. The base model ID may not be directly invocable — the inference profile is the recommended path.

---

## Current State Assessment

### What is already installed (no action needed)

| Dependency | Status | Evidence |
|---|---|---|
| `boto3>=1.40.61` | Already in `pyproject.toml` | Line 73 |
| `pandas>=2.0.0` | Already in `pyproject.toml` | Line 38 |
| `openpyxl>=3.1.0` | Already in `pyproject.toml` | Line 80 |
| LangFuse keys | Already in `.env.local` | Lines 58-60 (backend), `main/frontend/.env.local` lines 8-10 |
| Clerk keys | Already in `.env.local` | Not needed for PoC (auth disabled) |

### What is missing (action required)

| Dependency | Missing | Action |
|---|---|---|
| `fpdf2>=2.7.0` | NOT in `pyproject.toml` | Add to pyproject.toml + `uv sync` |
| `@tanstack/react-table` | NOT in `package.json` | `npm install` in `main/frontend/` |
| `@tanstack/react-virtual` | NOT in `package.json` | `npm install` in `main/frontend/` |
| `AWS_ACCESS_KEY_ID` | NOT in `.env.local` | Create IAM user, configure `~/.aws/credentials` |
| `AWS_SECRET_ACCESS_KEY` | NOT in `.env.local` | Create IAM user, configure `~/.aws/credentials` |
| `BI_BEDROCK_REGION` | NOT in `.env.local` | Add `BI_BEDROCK_REGION=us-east-1` |
| `BI_BEDROCK_MODEL_ID` | NOT in `.env.local` | Add `BI_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6` |
| Bedrock model access | Unknown — may need first-time-use form | Submit via Bedrock console |

---

## Manual Prerequisites

### Step 1: Create AWS IAM User for Bedrock Access
**Time estimate:** 15 minutes
**Lead time:** None (immediate)

1. Log into the AWS Management Console (the account that owns the AWS infrastructure for this project).
2. Navigate to: IAM -> Users -> Create user.
3. Username: `bedrock-local-dev` (or similar). No console access needed — programmatic only.
4. Attach policy: `AmazonBedrockLimitedAccess` (managed policy). This grants `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, and the required AWS Marketplace subscription permissions.
5. After user creation, go to: Security credentials tab -> Access keys -> Create access key.
6. Select "Local code" as use case.
7. Copy both values immediately — the secret access key is shown only once:
   - `AWS_ACCESS_KEY_ID=AKIA______________`
   - `AWS_SECRET_ACCESS_KEY=____________________________`

**Important:** Do NOT paste these into `.env.local` directly. Use the `~/.aws/credentials` file (see Step 2). The `.env.local` approach risks accidental git commits.

### Step 2: Configure AWS Credentials in ~/.aws/credentials
**Time estimate:** 5 minutes
**Lead time:** None (immediate)

On the WSL Ubuntu environment (since Docker runs in WSL), configure boto3 credentials:

```bash
# Run in WSL terminal
mkdir -p ~/.aws
cat >> ~/.aws/credentials << 'EOF'
[bedrock-dev]
aws_access_key_id = AKIA______________
aws_secret_access_key = ____________________________
EOF

cat >> ~/.aws/config << 'EOF'
[profile bedrock-dev]
region = us-east-1
EOF

# Restrict permissions
chmod 600 ~/.aws/credentials
chmod 600 ~/.aws/config
```

Then add to `.env.local` (NOT the keys themselves — just the profile reference and region):

```bash
# .env.local additions for BI feature
BI_BEDROCK_REGION=us-east-1
BI_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
AWS_PROFILE=bedrock-dev
AWS_DEFAULT_REGION=us-east-1
```

Alternatively, for Docker Compose compatibility, export from the credentials file by adding to `.env.local`:

```bash
AWS_ACCESS_KEY_ID=AKIA______________
AWS_SECRET_ACCESS_KEY=____________________________
AWS_DEFAULT_REGION=us-east-1
```

**Note:** The `docker-compose.bi.yml` will need to pass `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` into the API container as environment variables (same pattern as LIMS compose file passes `LIMS_*` vars).

### Step 3: Enable Bedrock Model Access (First-Time-Use Form for Anthropic)
**Time estimate:** 5 minutes to submit
**Lead time:** Usually instant to 24 hours

1. Log into AWS Console.
2. Navigate to: Amazon Bedrock -> Model access (left sidebar).
3. Look for Anthropic Claude models. If the account has never used Anthropic models on Bedrock, a first-time-use form will appear asking for:
   - Company name
   - Website
   - Intended users
   - Industry category
   - Use case description
4. Submit the form. Access is usually granted immediately or within minutes.
5. Verify the model is accessible by checking: Bedrock -> Model access -> confirm `Claude Sonnet 4.6` shows "Access granted".

**Model ID note:** The PRP specifies `anthropic.claude-sonnet-4-6` as the model ID. Based on research, the US inference profile `us.anthropic.claude-sonnet-4-6` is the recommended approach for us-east-1 in February 2026. The `copilot.py` implementation should use the inference profile ID. The `BI_BEDROCK_MODEL_ID` env var in the PRP should be updated to `us.anthropic.claude-sonnet-4-6`.

### Step 4: Verify Bedrock Connectivity
**Time estimate:** 2 minutes
**Lead time:** After Steps 1-3 complete

Run this quick test in WSL after configuring credentials:

```bash
cd /path/to/thesis_project
uv run python -c "
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
response = client.converse(
    modelId='us.anthropic.claude-sonnet-4-6',
    messages=[{'role': 'user', 'content': [{'text': 'Say hello'}]}]
)
print('SUCCESS:', response['output']['message']['content'][0]['text'])
"
```

If this succeeds, Day 3 copilot integration is unblocked.

### Step 5: Install Missing Python Package
**Time estimate:** 2 minutes
**Lead time:** None

Add `fpdf2>=2.7.0` to `pyproject.toml` under `dependencies`, then run:

```bash
# In WSL, in the project root
uv sync
```

`pyproject.toml` line to add (after the `openpyxl` line, e.g. after line 80):

```toml
"fpdf2>=2.7.0",
```

### Step 6: Install Missing npm Packages
**Time estimate:** 3 minutes
**Lead time:** None

```bash
# In WSL, in the frontend directory
cd main/frontend
npm install @tanstack/react-table @tanstack/react-virtual
```

These are the TanStack Table v8 and react-virtual packages required for the data grid.

### Step 7: Prepare a Sample Data File
**Time estimate:** Variable (depends on what data you have)
**Lead time:** Before Day 1 development starts

The PRP specifies testing with ~15K rows of XLSX/CSV data. Ideally a Snowflake export or any tabular dataset with at least 10-15 columns and 10,000+ rows. A public dataset (e.g., world population statistics, pharmaceutical manufacturing records) works fine for PoC validation.

Store the file somewhere accessible, e.g. `main/src/bi/test_data/sample_data.xlsx`.

### Step 8: Add BI Environment Variables to .env.local
**Time estimate:** 2 minutes

Add the following block to `.env.local` (as specified in PRP Section 8, with one correction to the model ID):

```bash
# -----------------------------------------------------------------------------
# MES Agentic BI PoC (BI_* prefixed)
# -----------------------------------------------------------------------------
BI_BEDROCK_REGION=us-east-1
# CORRECTED: Use inference profile ID, not base model ID
BI_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
BI_MAX_UPLOAD_SIZE_MB=50
BI_MAX_ROWS=100000
BI_SESSION_TTL_SECONDS=3600
BI_MAX_SESSIONS=20

# AWS credentials for Bedrock (add if not using ~/.aws/credentials profile)
AWS_ACCESS_KEY_ID=AKIA______________
AWS_SECRET_ACCESS_KEY=____________________________
AWS_DEFAULT_REGION=us-east-1
```

Note: LangFuse keys (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) are already present in `.env.local` — no action needed for observability.

---

## Model ID Correction

The PRP (Section 8 and throughout) specifies:
```
BI_BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-6
```

Research confirms this base model ID may not be directly invocable in us-east-1. The correct ID to use is the US cross-region inference profile:
```
BI_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
```

The `copilot.py` implementation must use `us.anthropic.claude-sonnet-4-6` when calling `client.converse(modelId=...)`.

The PRP's Kill Criterion on Day 3 remains valid: if Bedrock model access is not available, fall back to OpenRouter (same tool definitions, different client — OpenRouter keys are already in `.env.local`).

---

## IAM Policy Note (Least Privilege)

If the account administrator prefers not to use the `AmazonBedrockLimitedAccess` managed policy, a minimal custom inline policy granting only what is needed:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-6",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6"
      ]
    },
    {
      "Sid": "MarketplaceSubscribe",
      "Effect": "Allow",
      "Action": [
        "aws-marketplace:Subscribe",
        "aws-marketplace:Unsubscribe",
        "aws-marketplace:ViewSubscriptions"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## No New Third-Party Services Required

| Service | Status |
|---|---|
| LangFuse | Already configured in `.env.local` (lines 58-60 backend, `main/frontend/.env.local` lines 8-10) |
| OpenRouter | Already configured — available as fallback if Bedrock blocked |
| Clerk | Not needed (auth disabled: `NEXT_PUBLIC_AUTH_ENABLED=false`) |
| LlamaCloud | Already configured (LIMS PoC) — not needed for BI PoC |

---

## Setup Sequence

1. Now (15 min): Create IAM user in AWS Console -> generate access key -> copy credentials.
2. Now (5 min): Configure `~/.aws/credentials` in WSL with the new key pair.
3. Now (5 min): Submit Bedrock first-time-use form for Anthropic (if not already done for this account).
4. Now (2 min): Add BI env vars block to `.env.local`.
5. Now (2 min): Add `fpdf2>=2.7.0` to `pyproject.toml` -> run `uv sync` in WSL.
6. Now (3 min): `cd main/frontend && npm install @tanstack/react-table @tanstack/react-virtual`.
7. Wait (0-24 hours): Bedrock Anthropic model access approval (usually instant).
8. Verify (2 min): Run the boto3 connectivity test script above.
9. Prepare: Source a sample XLSX/CSV file with ~15K rows for testing.
10. Ready: Execute Day 1 implementation (`/prp B1.1` or equivalent).

---

## Total Prep Time

| Category | Time |
|---|---|
| IAM user creation + credentials config | 20 minutes |
| Bedrock model access form | 5 minutes |
| Env var updates | 5 minutes |
| Python package install (fpdf2) | 2 minutes |
| npm package install (TanStack) | 3 minutes |
| Connectivity verification | 2 minutes |
| Waiting for Bedrock approval | 0-24 hours (usually instant) |
| Sample data preparation | Variable |
| **Total manual work** | **~37 minutes** |
| **Total potential wait** | **0-24 hours** |

---

## Quick Reference: What to Add to .env.local

```bash
# --- ADD THESE LINES TO .env.local ---

# MES Agentic BI PoC
BI_BEDROCK_REGION=us-east-1
BI_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
BI_MAX_UPLOAD_SIZE_MB=50
BI_MAX_ROWS=100000
BI_SESSION_TTL_SECONDS=3600
BI_MAX_SESSIONS=20

# AWS Bedrock credentials (IAM user: bedrock-local-dev)
AWS_ACCESS_KEY_ID=____________
AWS_SECRET_ACCESS_KEY=____________
AWS_DEFAULT_REGION=us-east-1
```

---

**When all steps are complete, begin Day 1 implementation per the PRP delivery structure.**
