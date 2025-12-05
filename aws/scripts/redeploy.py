#!/usr/bin/env python3
"""
Simple ECS Redeploy Script

Registers golden task definitions and forces redeployment of ECS services.
No Terraform, no Docker builds - just task definition updates and service restart.

Use this when:
- Secrets were lost after Terraform apply
- Configuration changed in task definition JSON files
- Need quick recovery without full infrastructure rebuild

Usage:
    python aws/scripts/redeploy.py              # Redeploy all services
    python aws/scripts/redeploy.py --api        # Redeploy API only
    python aws/scripts/redeploy.py --worker     # Redeploy Worker only
    python aws/scripts/redeploy.py --frontend   # Redeploy Frontend only
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


# Configuration
REGION = "eu-west-2"
CLUSTER = "pharma-test-gen-cluster"

# Golden task definition files (source of truth for secrets)
TASK_DEFINITIONS = {
    "api": {
        "file": "aws/terraform/task-definition-api-v19.json",
        "service": "pharma-test-gen-api",
        "family": "pharma-test-gen-api",
    },
    "worker": {
        "file": "aws/terraform/task-definition-worker-v21.json",
        "service": "pharma-test-gen-worker",
        "family": "pharma-test-gen-worker",
    },
    "frontend": {
        "file": "aws/terraform/task-definition-frontend-v13.json",
        "service": "pharma-test-gen-frontend",
        "family": "pharma-test-gen-frontend",
    },
}


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run AWS CLI command and return success status."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    print(f"$ {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"SUCCESS")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {e.stderr}")
        return False, e.stderr


def register_task_definition(name: str, config: dict) -> bool:
    """Register a task definition from JSON file."""
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    task_def_path = project_root / config["file"]

    if not task_def_path.exists():
        print(f"ERROR: Task definition file not found: {task_def_path}")
        return False

    cmd = [
        "aws", "ecs", "register-task-definition",
        "--cli-input-json", f"file://{task_def_path}",
        "--region", REGION,
    ]

    success, output = run_command(cmd, f"Registering {name} task definition")

    if success:
        # Parse revision number
        try:
            data = json.loads(output)
            revision = data["taskDefinition"]["revision"]
            print(f"  Registered revision: {revision}")
        except (json.JSONDecodeError, KeyError):
            pass

    return success


def update_service(name: str, config: dict) -> bool:
    """Force new deployment of ECS service."""
    cmd = [
        "aws", "ecs", "update-service",
        "--cluster", CLUSTER,
        "--service", config["service"],
        "--task-definition", config["family"],
        "--force-new-deployment",
        "--region", REGION,
    ]

    success, _ = run_command(cmd, f"Forcing redeployment of {name} service")
    return success


def check_service_status(name: str, config: dict) -> None:
    """Print current service status."""
    cmd = [
        "aws", "ecs", "describe-services",
        "--cluster", CLUSTER,
        "--services", config["service"],
        "--region", REGION,
        "--query", "services[0].[serviceName,status,runningCount,desiredCount]",
        "--output", "text",
    ]

    success, output = run_command(cmd, f"Checking {name} service status")
    if success and output.strip():
        parts = output.strip().split()
        if len(parts) >= 4:
            print(f"  Service: {parts[0]}, Status: {parts[1]}, Running: {parts[2]}/{parts[3]}")


def main():
    parser = argparse.ArgumentParser(
        description="Register golden task definitions and redeploy ECS services"
    )
    parser.add_argument("--api", action="store_true", help="Redeploy API service only")
    parser.add_argument("--worker", action="store_true", help="Redeploy Worker service only")
    parser.add_argument("--frontend", action="store_true", help="Redeploy Frontend service only")
    parser.add_argument("--skip-register", action="store_true", help="Skip task definition registration")
    parser.add_argument("--status-only", action="store_true", help="Only check service status")

    args = parser.parse_args()

    # Determine which services to redeploy
    if args.api or args.worker or args.frontend:
        services = []
        if args.api:
            services.append("api")
        if args.worker:
            services.append("worker")
        if args.frontend:
            services.append("frontend")
    else:
        # Default: all services
        services = ["api", "worker", "frontend"]

    print("\n" + "="*60)
    print("  ECS REDEPLOY SCRIPT")
    print("="*60)
    print(f"Region:   {REGION}")
    print(f"Cluster:  {CLUSTER}")
    print(f"Services: {', '.join(services)}")

    # Status only mode
    if args.status_only:
        print("\nChecking service status...")
        for name in services:
            check_service_status(name, TASK_DEFINITIONS[name])
        return

    errors = []

    # Register task definitions
    if not args.skip_register:
        print("\n" + "-"*60)
        print("  PHASE 1: Register Task Definitions")
        print("-"*60)

        for name in services:
            if not register_task_definition(name, TASK_DEFINITIONS[name]):
                errors.append(f"Failed to register {name} task definition")

    # Force redeployment
    print("\n" + "-"*60)
    print("  PHASE 2: Force Redeployment")
    print("-"*60)

    for name in services:
        if not update_service(name, TASK_DEFINITIONS[name]):
            errors.append(f"Failed to update {name} service")

    # Check final status
    print("\n" + "-"*60)
    print("  PHASE 3: Check Status")
    print("-"*60)

    for name in services:
        check_service_status(name, TASK_DEFINITIONS[name])

    # Summary
    print("\n" + "="*60)
    if errors:
        print("  COMPLETED WITH ERRORS")
        print("="*60)
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("  REDEPLOY COMPLETE")
        print("="*60)
        print("\nServices are updating. New tasks will be running in 2-5 minutes.")
        print("Monitor with: aws ecs wait services-stable --cluster pharma-test-gen-cluster --services " + " ".join([TASK_DEFINITIONS[s]["service"] for s in services]) + f" --region {REGION}")


if __name__ == "__main__":
    main()
