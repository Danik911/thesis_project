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
import glob
import json
import subprocess
import sys
import time
from pathlib import Path


# Configuration
REGION = "eu-west-2"
CLUSTER = "pharma-test-gen-cluster"
PROJECT_ROOT = Path(__file__).parent.parent.parent


def find_latest_task_definition(service: str) -> str | None:
    """Find the latest task definition file for a service.

    Looks for files matching pattern: task-definition-{service}-v*.json
    Returns the one with highest version number.
    """
    terraform_dir = PROJECT_ROOT / "aws" / "terraform"
    pattern = f"task-definition-{service}-v*.json"
    files = list(terraform_dir.glob(pattern))

    if not files:
        return None

    # Sort by version number (extract vN from filename)
    def get_version(path: Path) -> int:
        name = path.stem  # task-definition-api-v19
        parts = name.split("-v")
        if len(parts) >= 2:
            try:
                return int(parts[-1])
            except ValueError:
                return 0
        return 0

    files.sort(key=get_version, reverse=True)
    return str(files[0].relative_to(PROJECT_ROOT))


def get_task_definitions() -> dict:
    """Get task definition config, dynamically finding latest versions."""
    services = ["api", "worker", "frontend"]
    result = {}

    for service in services:
        task_def_file = find_latest_task_definition(service)
        if task_def_file:
            result[service] = {
                "file": task_def_file,
                "service": f"pharma-test-gen-{service}",
                "family": f"pharma-test-gen-{service}",
            }
        else:
            # Fallback: use family name only (uses latest registered in AWS)
            result[service] = {
                "file": None,
                "service": f"pharma-test-gen-{service}",
                "family": f"pharma-test-gen-{service}",
            }

    return result


# Task definitions loaded dynamically
TASK_DEFINITIONS = get_task_definitions()


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


def wait_for_services_healthy(services: list[str], timeout: int = 300) -> bool:
    """Wait until all services show running tasks matching desired count.

    Args:
        services: List of service names to wait for
        timeout: Maximum seconds to wait (default 5 minutes)

    Returns:
        True if all services healthy, False if timeout reached
    """
    print(f"\nWaiting for services to be healthy (timeout: {timeout}s)...")

    start_time = time.time()
    poll_interval = 15

    while time.time() - start_time < timeout:
        all_healthy = True
        status_lines = []

        for name in services:
            config = TASK_DEFINITIONS[name]
            cmd = [
                "aws", "ecs", "describe-services",
                "--cluster", CLUSTER,
                "--services", config["service"],
                "--region", REGION,
                "--query", "services[0].[runningCount,desiredCount]",
                "--output", "text",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    running = int(parts[0])
                    desired = int(parts[1])
                    status = "✓" if running >= desired and desired > 0 else "..."
                    status_lines.append(f"  {name}: {running}/{desired} {status}")
                    if running < desired or desired == 0:
                        all_healthy = False
                else:
                    status_lines.append(f"  {name}: unknown")
                    all_healthy = False
            else:
                status_lines.append(f"  {name}: error")
                all_healthy = False

        # Print status update
        elapsed = int(time.time() - start_time)
        print(f"\n[{elapsed}s] Service status:")
        for line in status_lines:
            print(line)

        if all_healthy:
            print("\n✓ All services healthy!")
            return True

        time.sleep(poll_interval)

    print(f"\n✗ Timeout after {timeout}s - some services not healthy")
    return False


def register_task_definition(name: str, config: dict) -> bool:
    """Register a task definition from JSON file."""
    if config["file"] is None:
        print(f"  No task definition file for {name} - using AWS-registered version")
        return True

    task_def_path = PROJECT_ROOT / config["file"]

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
    parser.add_argument("--wait", action="store_true", help="Wait for services to be healthy after redeployment")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds for --wait (default: 300)")

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

    # Wait for services if requested
    if args.wait:
        print("\n" + "-"*60)
        print("  PHASE 4: Wait for Healthy Services")
        print("-"*60)
        healthy = wait_for_services_healthy(services, timeout=args.timeout)
        if not healthy:
            errors.append("Services did not become healthy within timeout")

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
        if not args.wait:
            print("\nServices are updating. New tasks will be running in 2-5 minutes.")
            print("Use --wait flag to wait for services to be healthy.")
            print("Monitor with: aws ecs wait services-stable --cluster pharma-test-gen-cluster --services " + " ".join([TASK_DEFINITIONS[s]["service"] for s in services]) + f" --region {REGION}")


if __name__ == "__main__":
    main()
