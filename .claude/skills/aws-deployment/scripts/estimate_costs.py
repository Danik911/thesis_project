#!/usr/bin/env python3
"""
AWS Cost Estimator for Prototype Deployments

Calculates per-service cost breakdown with hourly, daily, and monthly estimates.
Uses December 2025 pricing for eu-west-2 (London) region.

Usage:
    python estimate_costs.py
    python estimate_costs.py --config custom_config.json
"""

import json
import argparse
from dataclasses import dataclass
from typing import Optional


# December 2025 Pricing - eu-west-2 (London)
# Source: AWS Pricing Calculator / docs.aws.amazon.com
PRICING = {
    "fargate": {
        "vcpu_per_hour": 0.04048,  # per vCPU-hour
        "memory_per_gb_hour": 0.004445,  # per GB-hour
    },
    "alb": {
        "per_hour": 0.0225,  # per ALB-hour
        "lcu_per_hour": 0.008,  # per LCU-hour (usually ~1 LCU for prototype)
    },
    "rds": {
        "t3_micro_per_hour": 0.018,
        "t3_small_per_hour": 0.036,
        "t3_medium_per_hour": 0.072,
        "storage_per_gb_month": 0.115,  # gp2
    },
    "aurora_serverless": {
        "acu_per_hour": 0.12,  # per ACU-hour
        "min_acu": 0.5,
        "storage_per_gb_month": 0.10,
    },
    "s3": {
        "storage_per_gb_month": 0.023,  # Standard
        "put_per_1000": 0.005,
        "get_per_1000": 0.0004,
    },
    "sqs": {
        "per_million_requests": 0.40,  # Standard queue
    },
    "ecr": {
        "storage_per_gb_month": 0.10,
    },
    "cloudwatch": {
        "log_ingestion_per_gb": 0.57,
        "log_storage_per_gb_month": 0.03,
        "metrics_per_month": 0.30,  # Custom metrics
    },
    "data_transfer": {
        "out_per_gb": 0.09,  # To internet
        "in_per_gb": 0.00,  # Free
    },
}


@dataclass
class ServiceCost:
    """Cost breakdown for a single AWS service."""

    name: str
    config: str
    hourly: float
    assumptions: str

    @property
    def daily(self) -> float:
        return self.hourly * 24

    @property
    def monthly(self) -> float:
        return self.hourly * 24 * 30

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "config": self.config,
            "hourly": round(self.hourly, 4),
            "daily": round(self.daily, 2),
            "monthly": round(self.monthly, 2),
            "assumptions": self.assumptions,
        }


def calculate_fargate_cost(
    vcpu: float = 0.5,
    memory_gb: float = 1.0,
    task_count: int = 1,
    service_name: str = "ECS Fargate"
) -> ServiceCost:
    """Calculate ECS Fargate cost."""
    vcpu_cost = vcpu * PRICING["fargate"]["vcpu_per_hour"]
    memory_cost = memory_gb * PRICING["fargate"]["memory_per_gb_hour"]
    hourly = (vcpu_cost + memory_cost) * task_count

    return ServiceCost(
        name=service_name,
        config=f"{task_count}x {vcpu} vCPU, {memory_gb} GB",
        hourly=hourly,
        assumptions=f"Running 24/7, {task_count} task(s)"
    )


def calculate_alb_cost(
    count: int = 1,
    lcu: float = 1.0
) -> ServiceCost:
    """Calculate Application Load Balancer cost."""
    hourly = (PRICING["alb"]["per_hour"] + PRICING["alb"]["lcu_per_hour"] * lcu) * count

    return ServiceCost(
        name="Application Load Balancer",
        config=f"{count} ALB(s), ~{lcu} LCU avg",
        hourly=hourly,
        assumptions="Running 24/7, light traffic"
    )


def calculate_rds_cost(
    instance_type: str = "t3.micro",
    storage_gb: int = 20,
    multi_az: bool = False
) -> ServiceCost:
    """Calculate RDS cost."""
    type_key = f"{instance_type.replace('.', '_')}_per_hour"
    hourly_rate = PRICING["rds"].get(type_key, 0.018)

    if multi_az:
        hourly_rate *= 2

    storage_hourly = (storage_gb * PRICING["rds"]["storage_per_gb_month"]) / (24 * 30)
    hourly = hourly_rate + storage_hourly

    return ServiceCost(
        name="RDS PostgreSQL",
        config=f"{instance_type}, {storage_gb} GB, {'Multi-AZ' if multi_az else 'Single-AZ'}",
        hourly=hourly,
        assumptions="Running 24/7"
    )


def calculate_s3_cost(
    storage_gb: float = 10.0,
    puts_per_month: int = 10000,
    gets_per_month: int = 100000
) -> ServiceCost:
    """Calculate S3 cost."""
    storage_monthly = storage_gb * PRICING["s3"]["storage_per_gb_month"]
    puts_monthly = (puts_per_month / 1000) * PRICING["s3"]["put_per_1000"]
    gets_monthly = (gets_per_month / 1000) * PRICING["s3"]["get_per_1000"]

    monthly = storage_monthly + puts_monthly + gets_monthly
    hourly = monthly / (24 * 30)

    return ServiceCost(
        name="S3 Storage",
        config=f"{storage_gb} GB, {puts_per_month:,} PUTs, {gets_per_month:,} GETs",
        hourly=hourly,
        assumptions="Standard storage class"
    )


def calculate_sqs_cost(
    requests_per_month: int = 100000
) -> ServiceCost:
    """Calculate SQS cost."""
    monthly = (requests_per_month / 1_000_000) * PRICING["sqs"]["per_million_requests"]
    hourly = monthly / (24 * 30)

    return ServiceCost(
        name="SQS Queue",
        config=f"{requests_per_month:,} requests/month",
        hourly=hourly,
        assumptions="Standard queue"
    )


def calculate_cloudwatch_cost(
    log_gb_per_month: float = 1.0,
    custom_metrics: int = 5
) -> ServiceCost:
    """Calculate CloudWatch cost."""
    ingestion = log_gb_per_month * PRICING["cloudwatch"]["log_ingestion_per_gb"]
    storage = log_gb_per_month * PRICING["cloudwatch"]["log_storage_per_gb_month"]
    metrics = custom_metrics * PRICING["cloudwatch"]["metrics_per_month"]

    monthly = ingestion + storage + metrics
    hourly = monthly / (24 * 30)

    return ServiceCost(
        name="CloudWatch",
        config=f"{log_gb_per_month} GB logs, {custom_metrics} metrics",
        hourly=hourly,
        assumptions="Basic monitoring"
    )


def calculate_ecr_cost(
    storage_gb: float = 2.0,
    repos: int = 3
) -> ServiceCost:
    """Calculate ECR cost."""
    monthly = storage_gb * repos * PRICING["ecr"]["storage_per_gb_month"]
    hourly = monthly / (24 * 30)

    return ServiceCost(
        name="ECR Registry",
        config=f"{repos} repos, ~{storage_gb} GB each",
        hourly=hourly,
        assumptions="Image storage only"
    )


def calculate_prototype_costs() -> list[ServiceCost]:
    """Calculate costs for a typical prototype deployment."""
    costs = [
        # API Service
        calculate_fargate_cost(
            vcpu=0.5, memory_gb=1.0, task_count=1,
            service_name="ECS Fargate (API)"
        ),
        # Worker Service
        calculate_fargate_cost(
            vcpu=1.0, memory_gb=2.0, task_count=1,
            service_name="ECS Fargate (Worker)"
        ),
        # Frontend Service
        calculate_fargate_cost(
            vcpu=0.25, memory_gb=0.5, task_count=1,
            service_name="ECS Fargate (Frontend)"
        ),
        # Load Balancers
        calculate_alb_cost(count=2, lcu=0.5),
        # Database
        calculate_rds_cost(instance_type="t3.micro", storage_gb=20, multi_az=False),
        # Storage
        calculate_s3_cost(storage_gb=5.0, puts_per_month=5000, gets_per_month=50000),
        # Queue
        calculate_sqs_cost(requests_per_month=50000),
        # Observability
        calculate_cloudwatch_cost(log_gb_per_month=0.5, custom_metrics=3),
        # Registry
        calculate_ecr_cost(storage_gb=1.0, repos=3),
    ]

    return costs


def format_cost_table(costs: list[ServiceCost]) -> str:
    """Format costs as a markdown table."""
    lines = [
        "| Service | Configuration | Hourly | Daily | Monthly |",
        "|---------|--------------|--------|-------|---------|",
    ]

    total_hourly = 0.0
    for cost in costs:
        total_hourly += cost.hourly
        lines.append(
            f"| {cost.name} | {cost.config} | "
            f"${cost.hourly:.4f} | ${cost.daily:.2f} | ${cost.monthly:.2f} |"
        )

    # Add total row
    total_daily = total_hourly * 24
    total_monthly = total_hourly * 24 * 30
    lines.append(
        f"| **TOTAL** | | **${total_hourly:.4f}** | "
        f"**${total_daily:.2f}** | **${total_monthly:.2f}** |"
    )

    return "\n".join(lines)


def format_assumptions(costs: list[ServiceCost]) -> str:
    """Format assumptions as a list."""
    lines = ["### Assumptions", ""]
    for cost in costs:
        lines.append(f"- **{cost.name}:** {cost.assumptions}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AWS Cost Estimator")
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown",
        help="Output format"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Custom configuration JSON file"
    )
    args = parser.parse_args()

    # Calculate costs
    costs = calculate_prototype_costs()

    if args.format == "json":
        output = {
            "costs": [c.to_dict() for c in costs],
            "total": {
                "hourly": sum(c.hourly for c in costs),
                "daily": sum(c.daily for c in costs),
                "monthly": sum(c.monthly for c in costs),
            },
            "pricing_date": "December 2025",
            "region": "eu-west-2 (London)",
        }
        print(json.dumps(output, indent=2))
    else:
        print("## AWS Cost Estimate - Prototype Deployment")
        print()
        print(f"**Region:** eu-west-2 (London)")
        print(f"**Pricing Date:** December 2025")
        print()
        print(format_cost_table(costs))
        print()
        print(format_assumptions(costs))
        print()
        print("### Cost Saving Tips")
        print()
        print("1. **Destroy when not using:** Run `destroy.py` overnight to save ~70%")
        print("2. **Run 8 hours/day:** Reduces cost from ~$100/month to ~$33/month")
        print("3. **Weekend shutdown:** Save additional ~30%")


if __name__ == "__main__":
    main()
