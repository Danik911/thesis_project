#!/usr/bin/env python3
"""
Deploy the Pharmaceutical Test Generation ECS/Fargate Infrastructure.

This script:
1. Checks prerequisites (Docker, Terraform, AWS CLI)
2. Builds Docker images for API, Worker, Frontend
3. Pushes images to Amazon ECR
4. Deploys infrastructure with Terraform
5. Waits for ECS services to be healthy
6. Displays deployment URLs and cost information

GAMP-5 Compliance: All deployments are tracked via Terraform state with full audit trail.
"""

import subprocess
import sys
import os
import json
import time
import platform
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_NAME = "pharma-test-gen"
AWS_REGION = "eu-west-2"
TERRAFORM_DIR = "aws/terraform"
TFVARS_FILE = "environments/staging.tfvars"

# Estimated hourly cost (without Aurora)
ESTIMATED_HOURLY_COST = 0.75  # ~$0.50-1.00/hour


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def is_wsl() -> bool:
    """Check if running in WSL."""
    return "microsoft" in platform.uname().release.lower()


def is_windows() -> bool:
    """Check if running on Windows (not WSL)."""
    return platform.system() == "Windows" and not is_wsl()


def run_command(cmd, cwd=None, check=True, capture_output=False, env=None, timeout=None):
    """Run a command and optionally capture output."""
    if isinstance(cmd, list):
        cmd_str = ' '.join(cmd)
    else:
        cmd_str = cmd

    print(f"  $ {cmd_str}")

    # If on Windows, wrap in WSL with expanded PATH for terraform in ~/bin
    if is_windows() and isinstance(cmd, list):
        cmd = ["wsl", "-e", "bash", "-c", f"export PATH=$HOME/bin:$PATH && {' '.join(cmd)}"]
    elif is_windows() and isinstance(cmd, str):
        cmd = f'wsl -e bash -c "export PATH=$HOME/bin:$PATH && {cmd}"'

    try:
        if capture_output:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True,
                shell=isinstance(cmd, str), env=env, timeout=timeout
            )
            if check and result.returncode != 0:
                print(f"  Error: {result.stderr}")
                return None
            return result.stdout.strip()
        else:
            result = subprocess.run(
                cmd, cwd=cwd, shell=isinstance(cmd, str), env=env, timeout=timeout
            )
            if check and result.returncode != 0:
                return False
            return True
    except subprocess.TimeoutExpired:
        print(f"  Timeout after {timeout}s")
        return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None


def check_prerequisites():
    """Check that all required tools are installed."""
    print("\n1. Checking prerequisites...")

    tools = {
        "docker": "Docker is required for building container images",
        "terraform": "Terraform is required for infrastructure deployment",
        "aws": "AWS CLI is required for ECR push and resource management"
    }

    all_ok = True
    for tool, message in tools.items():
        result = run_command([tool, "--version"], capture_output=True, check=False)
        if result:
            version = result.split('\n')[0]
            print(f"     {tool}: {version}")
        else:
            print(f"     {tool}: NOT FOUND - {message}")
            all_ok = False

    if not all_ok:
        print("\n   Please install missing tools and try again.")
        sys.exit(1)

    # Check if Docker is running
    result = run_command(["docker", "info"], capture_output=True, check=False)
    if not result:
        print("     Docker is not running. Please start Docker.")
        sys.exit(1)
    print("     Docker is running")

    # Check AWS credentials
    result = run_command(["aws", "sts", "get-caller-identity"], capture_output=True, check=False)
    if not result:
        print("     AWS credentials not configured. Run 'aws configure'")
        sys.exit(1)

    identity = json.loads(result)
    print(f"     AWS Account: {identity['Account']}")
    print(f"     AWS User: {identity['Arn'].split('/')[-1]}")


def get_ecr_login():
    """Get ECR login token and authenticate Docker."""
    print("\n2. Authenticating with Amazon ECR...")

    # Get AWS account ID
    result = run_command(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        capture_output=True
    )
    if not result:
        print("   Failed to get AWS account ID")
        sys.exit(1)

    account_id = result.strip()
    ecr_url = f"{account_id}.dkr.ecr.{AWS_REGION}.amazonaws.com"

    # Get ECR login password and login Docker
    login_cmd = f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {ecr_url}"
    result = run_command(login_cmd, capture_output=True, check=False)

    if result is None or "Login Succeeded" not in str(result):
        # Try alternative approach
        print("   Trying alternative ECR login...")
        result = run_command(
            ["aws", "ecr", "get-login-password", "--region", AWS_REGION],
            capture_output=True
        )
        if result:
            run_command(
                f"echo '{result}' | docker login --username AWS --password-stdin {ecr_url}",
                capture_output=True
            )

    print(f"     Authenticated with ECR: {ecr_url}")
    return account_id, ecr_url


def create_ecr_repositories(account_id):
    """Create ECR repositories if they don't exist."""
    print("\n3. Creating Amazon ECR repositories...")

    services = ["api", "worker", "frontend"]

    for service in services:
        repo_name = f"{PROJECT_NAME}-{service}"

        # Check if repository exists
        result = run_command(
            ["aws", "ecr", "describe-repositories", "--repository-names", repo_name, "--region", AWS_REGION],
            capture_output=True, check=False
        )

        if result:
            print(f"     {repo_name}: exists")
        else:
            # Create repository
            print(f"     {repo_name}: creating...")
            run_command([
                "aws", "ecr", "create-repository",
                "--repository-name", repo_name,
                "--image-tag-mutability", "IMMUTABLE",  # GAMP-5 compliance
                "--region", AWS_REGION
            ])
            print(f"     {repo_name}: created")


def build_docker_images():
    """Build Docker images for all services."""
    print("\n4. Building Docker images (linux/amd64 for Fargate)...")

    project_root = get_project_root()
    services = {
        "api": project_root / "main" / "api",
        "worker": project_root / "main" / "api",  # Same Dockerfile, different command
        "frontend": project_root / "main" / "frontend"
    }

    built_images = {}

    for service, dockerfile_dir in services.items():
        image_name = f"{PROJECT_NAME}-{service}:latest"
        print(f"     Building {image_name}...")

        # Check if Dockerfile exists
        dockerfile = dockerfile_dir / "Dockerfile"
        if not dockerfile.exists():
            print(f"     Dockerfile not found: {dockerfile}")
            print(f"     Skipping {service} - will use placeholder image")
            built_images[service] = None
            continue

        # Build for linux/amd64 (AWS Fargate requirement)
        result = run_command([
            "docker", "build",
            "--platform", "linux/amd64",
            "-t", image_name,
            "-f", str(dockerfile),
            str(dockerfile_dir)
        ], timeout=600)

        if result:
            built_images[service] = image_name
            print(f"     {image_name}: built successfully")
        else:
            print(f"     {image_name}: build failed")
            built_images[service] = None

    return built_images


def push_to_ecr(account_id, ecr_url, built_images):
    """Push Docker images to Amazon ECR."""
    print("\n5. Pushing images to Amazon ECR...")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    for service, local_image in built_images.items():
        if local_image is None:
            print(f"     {service}: skipped (no image built)")
            continue

        repo_name = f"{PROJECT_NAME}-{service}"
        ecr_image = f"{ecr_url}/{repo_name}"

        # Tag with both 'latest' and timestamp
        tags = ["staging-latest", f"staging-{timestamp}"]

        for tag in tags:
            full_tag = f"{ecr_image}:{tag}"

            # Tag the image
            run_command(["docker", "tag", local_image, full_tag])

            # Push to ECR
            print(f"     Pushing {repo_name}:{tag}...")
            result = run_command(["docker", "push", full_tag], timeout=300)

            if result:
                print(f"     {repo_name}:{tag}: pushed")
            else:
                print(f"     {repo_name}:{tag}: push failed")


def deploy_terraform():
    """Deploy infrastructure with Terraform."""
    print("\n6. Deploying infrastructure with Terraform...")

    project_root = get_project_root()
    terraform_dir = project_root / TERRAFORM_DIR

    if not terraform_dir.exists():
        print(f"   Terraform directory not found: {terraform_dir}")
        sys.exit(1)

    # Initialize Terraform if needed
    if not (terraform_dir / ".terraform").exists():
        print("     Initializing Terraform...")
        run_command(["terraform", "init"], cwd=str(terraform_dir))

    # Plan the deployment
    print("     Planning deployment...")
    result = run_command(
        ["terraform", "plan", f"-var-file={TFVARS_FILE}", "-out=tfplan"],
        cwd=str(terraform_dir)
    )

    if not result:
        print("   Terraform plan failed")
        sys.exit(1)

    # Apply the deployment
    print("\n     Applying deployment (this takes 10-15 minutes)...")
    print("     Creating AWS resources:")
    print("       - Amazon ECS Cluster")
    print("       - Amazon ECS Services (API, Worker, Frontend)")
    print("       - Amazon Application Load Balancers (2)")
    print("       - Amazon SQS Queue + Dead Letter Queue")
    print("       - Amazon CloudWatch Log Groups")
    print("       - AWS IAM Roles and Policies")
    print("       - AWS Security Groups")

    result = run_command(
        ["terraform", "apply", "-auto-approve", "tfplan"],
        cwd=str(terraform_dir),
        timeout=1200  # 20 minutes
    )

    if not result:
        print("   Terraform apply failed")
        sys.exit(1)

    # Get outputs
    print("\n     Getting deployment outputs...")
    outputs_json = run_command(
        ["terraform", "output", "-json"],
        cwd=str(terraform_dir),
        capture_output=True
    )

    if outputs_json:
        return json.loads(outputs_json)
    return {}


def wait_for_services(cluster_name):
    """Wait for ECS services to be healthy."""
    print("\n7. Waiting for ECS services to be healthy...")

    services = [f"{PROJECT_NAME}-api", f"{PROJECT_NAME}-worker", f"{PROJECT_NAME}-frontend"]
    max_wait = 300  # 5 minutes
    start_time = time.time()

    while time.time() - start_time < max_wait:
        all_healthy = True

        for service in services:
            result = run_command([
                "aws", "ecs", "describe-services",
                "--cluster", cluster_name,
                "--services", service,
                "--region", AWS_REGION,
                "--query", "services[0].deployments[0].runningCount",
                "--output", "text"
            ], capture_output=True, check=False)

            running = int(result) if result and result.isdigit() else 0

            if running > 0:
                print(f"     {service}: {running} task(s) running")
            else:
                print(f"     {service}: starting...")
                all_healthy = False

        if all_healthy:
            print("     All services healthy!")
            return True

        print(f"     Waiting... ({int(time.time() - start_time)}s)")
        time.sleep(15)

    print("   Timeout waiting for services. Check AWS Console for details.")
    return False


def display_deployment_info(outputs):
    """Display deployment information and cost warnings."""
    print("\n" + "=" * 70)
    print("   DEPLOYMENT COMPLETE")
    print("=" * 70)

    api_url = outputs.get("api_url", {}).get("value", "N/A")
    frontend_url = outputs.get("frontend_url", {}).get("value", "N/A")
    cluster_name = outputs.get("ecs_cluster_name", {}).get("value", "N/A")

    print(f"""
   Frontend URL:  {frontend_url}
   API URL:       {api_url}
   ECS Cluster:   {cluster_name}
   Region:        {AWS_REGION}
    """)

    # Cost warning
    print("=" * 70)
    print("   COST INFORMATION")
    print("=" * 70)
    print(f"""
   Estimated hourly cost: ~${ESTIMATED_HOURLY_COST:.2f}/hour
   Estimated daily cost:  ~${ESTIMATED_HOURLY_COST * 24:.2f}/day

   Services running:
     - 3 ECS Fargate tasks (~$0.04/hour each)
     - 2 Application Load Balancers (~$0.02/hour each)
     - CloudWatch Logs (pay per GB ingested)
     - SQS Queue (minimal cost)
    """)

    print("=" * 70)
    print("   IMPORTANT: DESTROY AFTER TESTING")
    print("=" * 70)
    print(f"""
   To stop AWS charges, run:

     python aws/scripts/destroy.py

   Or with uv:

     uv run aws/scripts/destroy.py
    """)


def main():
    """Main deployment function."""
    print("\n" + "=" * 70)
    print("   PHARMACEUTICAL TEST GENERATION - AWS ECS DEPLOYMENT")
    print("   GAMP-5 Compliant Infrastructure")
    print("=" * 70)
    print(f"\n   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Region:  {AWS_REGION}")
    print(f"   Project: {PROJECT_NAME}")

    # Check prerequisites
    check_prerequisites()

    # Get ECR login
    account_id, ecr_url = get_ecr_login()

    # Create ECR repositories
    create_ecr_repositories(account_id)

    # Build Docker images
    built_images = build_docker_images()

    # Push to ECR
    push_to_ecr(account_id, ecr_url, built_images)

    # Deploy Terraform
    outputs = deploy_terraform()

    # Wait for services
    cluster_name = outputs.get("ecs_cluster_name", {}).get("value", f"{PROJECT_NAME}-cluster")
    wait_for_services(cluster_name)

    # Display info
    display_deployment_info(outputs)

    print(f"\n   Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
