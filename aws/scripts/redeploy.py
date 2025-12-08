#!/usr/bin/env python3
"""
Simple ECS Redeploy Script

Registers golden task definitions and forces redeployment of ECS services.
With --rebuild flag, also builds fresh Docker images before redeploying.

Use this when:
- Secrets were lost after Terraform apply
- Configuration changed in task definition JSON files
- Need quick recovery without full infrastructure rebuild
- Code changes need to be deployed (use --rebuild flag)

Usage:
    python aws/scripts/redeploy.py                   # Redeploy all (no rebuild)
    python aws/scripts/redeploy.py --rebuild         # Rebuild & redeploy all
    python aws/scripts/redeploy.py --rebuild --api   # Rebuild & redeploy API only
    python aws/scripts/redeploy.py --frontend        # Redeploy Frontend only (no rebuild)
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# Configuration
REGION = "eu-west-2"
CLUSTER = "pharma-test-gen-cluster"
PROJECT_NAME = "pharma-test-gen"
CLOUDFRONT_DISTRIBUTION_ID = "E1DTSJYZQGK50L"  # d861au413p5o2.cloudfront.net
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Dockerfile mapping
DOCKERFILES = {
    "api": "Dockerfile.api.pip",
    "worker": "Dockerfile.worker.pip",
    "frontend": "Dockerfile.frontend",
}

# Clerk key for frontend build
CLERK_PUBLISHABLE_KEY = os.environ.get(
    "CLERK_PUBLISHABLE_KEY",
    "pk_test_aGVscGVkLXN0dXJnZW9uLTE5LmNsZXJrLmFjY291bnRzLmRldiQ"
)


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


def invalidate_cloudfront_cache(distribution_id: str = CLOUDFRONT_DISTRIBUTION_ID) -> bool:
    """Invalidate CloudFront cache after deployment.

    This ensures users get fresh content after frontend redeployment,
    preventing 404 errors caused by build ID mismatches.
    """
    cmd = [
        "aws", "cloudfront", "create-invalidation",
        "--distribution-id", distribution_id,
        "--paths", "/*",
        "--region", "us-east-1",  # CloudFront is global, always us-east-1
    ]

    success, output = run_command(cmd, f"Invalidating CloudFront cache ({distribution_id})")

    if success:
        try:
            data = json.loads(output)
            invalidation_id = data["Invalidation"]["Id"]
            print(f"  Invalidation ID: {invalidation_id}")
            print(f"  Status: {data['Invalidation']['Status']}")
            print("  Note: Invalidation takes 1-2 minutes to propagate")
        except (json.JSONDecodeError, KeyError):
            pass

    return success


def get_ecr_url() -> str:
    """Get the ECR repository URL from AWS account."""
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text", "--region", REGION],
        capture_output=True,
        text=True
    )
    account_id = result.stdout.strip()
    return f"{account_id}.dkr.ecr.{REGION}.amazonaws.com"


def ecr_login() -> bool:
    """Login to ECR registry."""
    print("\n" + "="*60)
    print("  Logging in to ECR")
    print("="*60)

    ecr_url = get_ecr_url()

    # Get ECR password
    result = subprocess.run(
        ["aws", "ecr", "get-login-password", "--region", REGION],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"FAILED to get ECR password: {result.stderr}")
        return False

    password = result.stdout.strip()

    # Login to Docker
    login_result = subprocess.run(
        ["docker", "login", "--username", "AWS", "--password-stdin", ecr_url],
        input=password,
        capture_output=True,
        text=True
    )

    if login_result.returncode != 0:
        print(f"FAILED to login: {login_result.stderr}")
        return False

    print("SUCCESS - Logged in to ECR")
    return True


def build_and_push_image(service: str, no_cache: bool = False) -> bool:
    """Build and push Docker image for a service to ECR.

    Builds image with docker buildx, tags as staging-latest, and pushes to ECR.

    Args:
        service: Service name (api, worker, frontend)
        no_cache: If True, force full rebuild without Docker cache
    """
    dockerfile = DOCKERFILES.get(service)
    if not dockerfile:
        print(f"ERROR: No Dockerfile configured for {service}")
        return False

    dockerfile_path = PROJECT_ROOT / dockerfile
    if not dockerfile_path.exists():
        print(f"ERROR: Dockerfile not found: {dockerfile_path}")
        return False

    ecr_url = get_ecr_url()
    ecr_repo = f"{ecr_url}/{PROJECT_NAME}-{service}"
    local_image = f"{PROJECT_NAME}-{service}:rebuild"

    print(f"\n{'='*60}")
    print(f"  Building {service} image")
    print(f"{'='*60}")
    print(f"  Dockerfile: {dockerfile}")
    print(f"  ECR Repo: {ecr_repo}")
    if no_cache:
        print("  Mode: NO CACHE (full rebuild)")

    # Build command - different for frontend vs backend
    if service == "frontend":
        build_cmd = [
            "docker", "buildx", "build",
            "--platform", "linux/amd64",
            "--build-arg", "NEXT_PUBLIC_API_BASE_URL=",
            "--build-arg", f"NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY={CLERK_PUBLISHABLE_KEY}",
            "-t", local_image,
            "-f", str(dockerfile_path),
            "--load",
            str(PROJECT_ROOT)
        ]
    else:
        build_cmd = [
            "docker", "buildx", "build",
            "--platform", "linux/amd64",
            "-t", local_image,
            "-f", str(dockerfile_path),
            "--load",
            str(PROJECT_ROOT)
        ]

    # Add --no-cache flag if requested
    if no_cache:
        build_cmd.insert(3, "--no-cache")

    print(f"$ {' '.join(build_cmd)}")

    # Longer timeout for --no-cache builds (25 min vs 15 min)
    build_timeout = 1500 if no_cache else 900
    timeout_mins = build_timeout // 60
    try:
        result = subprocess.run(build_cmd, check=True, timeout=build_timeout)
    except subprocess.TimeoutExpired:
        print(f"FAILED: Build timed out after {timeout_mins} minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"FAILED: Build error: {e}")
        return False

    print("SUCCESS - Image built")

    # Tag and push staging-latest
    ecr_image = f"{ecr_repo}:staging-latest"

    print(f"\n  Tagging as: {ecr_image}")
    tag_result = subprocess.run(["docker", "tag", local_image, ecr_image])
    if tag_result.returncode != 0:
        print("FAILED: Could not tag image")
        return False

    print(f"  Pushing to ECR...")
    try:
        push_result = subprocess.run(
            ["docker", "push", ecr_image],
            check=True,
            timeout=300
        )
    except subprocess.TimeoutExpired:
        print("FAILED: Push timed out after 5 minutes")
        return False
    except subprocess.CalledProcessError as e:
        print(f"FAILED: Push error: {e}")
        return False

    print(f"SUCCESS - Pushed {service}:staging-latest to ECR")
    return True


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
    parser.add_argument("--skip-invalidate", action="store_true", help="Skip CloudFront cache invalidation")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild and push Docker images before redeploying")
    parser.add_argument("--no-cache", action="store_true", help="Force full rebuild without Docker cache (use with --rebuild)")

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
    if args.rebuild:
        if args.no_cache:
            print("Mode:     REBUILD + NO-CACHE (full rebuild, no Docker cache)")
        else:
            print("Mode:     REBUILD (will build and push new Docker images)")

    # Status only mode
    if args.status_only:
        print("\nChecking service status...")
        for name in services:
            check_service_status(name, TASK_DEFINITIONS[name])
        return

    errors = []

    # Rebuild images if requested
    if args.rebuild:
        print("\n" + "-"*60)
        print("  PHASE 0: Rebuild and Push Docker Images")
        print("-"*60)

        # Login to ECR first
        if not ecr_login():
            print("FATAL: Cannot proceed without ECR login")
            sys.exit(1)

        # Build and push each service
        for name in services:
            if not build_and_push_image(name, no_cache=args.no_cache):
                errors.append(f"Failed to build/push {name} image")
                # Don't continue if build fails - it's critical
                print(f"\nFATAL: Build failed for {name}. Stopping.")
                sys.exit(1)

        print("\n  All images rebuilt and pushed to ECR")

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

    # Invalidate CloudFront cache (important when frontend is redeployed)
    if "frontend" in services and not args.skip_invalidate:
        print("\n" + "-"*60)
        print("  PHASE 5: Invalidate CloudFront Cache")
        print("-"*60)
        if not invalidate_cloudfront_cache():
            errors.append("Failed to invalidate CloudFront cache")

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
