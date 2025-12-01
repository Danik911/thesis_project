#!/usr/bin/env python3
"""
Generate Strong Destroy Warning for AWS Resources

Generates a formatted warning message with cost breakdown to encourage
users to destroy prototype resources after testing.

Usage:
    python generate_destroy_warning.py
    python generate_destroy_warning.py --hourly-cost 0.15
"""

import argparse
from datetime import datetime
from typing import Optional


def generate_destroy_warning(
    hourly_cost: float = 0.14,
    resources: Optional[dict] = None
) -> str:
    """
    Generate a strong warning message about ongoing AWS costs.

    Args:
        hourly_cost: Estimated hourly cost of running resources
        resources: Optional dict of resource names and counts

    Returns:
        Formatted markdown warning message
    """

    # Default resources if not provided
    if resources is None:
        resources = {
            "ECS Cluster": 1,
            "ECS Services": 3,
            "ECS Tasks": 3,
            "Application Load Balancers": 2,
            "SQS Queues": 1,
            "CloudWatch Log Groups": 3,
            "S3 Buckets": 2,
            "ECR Repositories": 3,
        }

    # Calculate costs for different timeframes
    daily_cost = hourly_cost * 24
    weekly_cost = daily_cost * 7
    monthly_cost = daily_cost * 30

    # Calculate waste scenarios
    overnight_waste = hourly_cost * 16  # 16 hours overnight
    weekend_waste = hourly_cost * 48    # 48 hours weekend
    forgot_week_waste = weekly_cost

    warning = f"""
## IMPORTANT: Resource Cleanup Decision

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

Your AWS resources are now **LIVE** and **INCURRING CHARGES**.

### Resources Created

| Resource Type | Count |
|--------------|-------|
"""

    for resource, count in resources.items():
        warning += f"| {resource} | {count} |\n"

    warning += f"""
### Ongoing Cost Breakdown

| Timeframe | Cost | If You Forget... |
|-----------|------|------------------|
| Per HOUR | **${hourly_cost:.2f}** | Coffee money |
| Per DAY | **${daily_cost:.2f}** | Nice lunch |
| Per WEEK | **${weekly_cost:.2f}** | Dinner out |
| Per MONTH | **${monthly_cost:.2f}** | Monthly subscription |

### Cost of Common Mistakes

| Scenario | Wasted Money |
|----------|--------------|
| Left running overnight (16 hrs) | **${overnight_waste:.2f}** |
| Forgot over weekend (48 hrs) | **${weekend_waste:.2f}** |
| Forgot for a week | **${forgot_week_waste:.2f}** |
| Forgot for a month | **${monthly_cost:.2f}** |

---

## My Strong Recommendation

**For a prototype/learning/portfolio project:**

### DESTROY THESE RESOURCES NOW

You can redeploy anytime in ~15 minutes with:
```bash
python aws/scripts/deploy.py
```

The only "cost" of destroying is ~15 minutes to redeploy.
The cost of forgetting is **real money** charged to your card.

---

## Your Options

### Option 1: DESTROY NOW (Recommended)

```bash
python aws/scripts/destroy.py
```

**What happens:**
- All ECS tasks stop immediately
- Load balancers deleted
- SQS queues deleted
- CloudWatch logs preserved (for debugging)
- ECR images preserved (for quick redeploy)
- S3 buckets emptied and deleted

**Cost after destroy:** ~$0.10/month (Terraform state only)

### Option 2: KEEP RUNNING

If you choose to keep resources running:

- Set a calendar reminder to destroy
- Understand you're paying ~${daily_cost:.2f}/day
- Consider: Is this worth the cost?

**Destroy command for later:**
```bash
python aws/scripts/destroy.py
```

---

## Quick Cost Check

Before keeping resources running, ask yourself:

1. Do I need this running 24/7? -> Probably not
2. Can I redeploy when needed? -> Yes, ~15 minutes
3. Am I willing to pay ${monthly_cost:.2f}/month? -> Your call
4. Will I remember to destroy later? -> Be honest...

---

## What Gets Preserved After Destroy

| Resource | Kept | Monthly Cost |
|----------|------|--------------|
| Terraform state (S3) | Yes | ~$0.02 |
| ECR images | Yes (optional delete) | ~$0.10 |
| CloudWatch logs | Yes (30-day retention) | ~$0.00 |
| **Total after destroy** | | **~$0.12** |

You can safely destroy and redeploy without losing your work.
"""

    return warning


def main():
    parser = argparse.ArgumentParser(description="Generate AWS Destroy Warning")
    parser.add_argument(
        "--hourly-cost", type=float, default=0.14,
        help="Estimated hourly cost (default: 0.14)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file path (default: stdout)"
    )
    args = parser.parse_args()

    warning = generate_destroy_warning(hourly_cost=args.hourly_cost)

    if args.output:
        with open(args.output, "w") as f:
            f.write(warning)
        print(f"Warning written to: {args.output}")
    else:
        print(warning)


if __name__ == "__main__":
    main()
