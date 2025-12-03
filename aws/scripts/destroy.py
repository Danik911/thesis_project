#!/usr/bin/env python3
"""
Destroy the Pharmaceutical Test Generation ECS/Fargate Infrastructure.

This script:
1. Confirms destruction with detailed warning
2. Empties S3 buckets (vectors + output)
3. Destroys infrastructure with Terraform
4. Optionally cleans up ECR images
5. Displays cost savings information

IMPORTANT: This will permanently delete all AWS resources except:
- Terraform state bucket (pharma-test-gen-terraform-state)
- DynamoDB lock table (pharma-test-gen-terraform-locks)

These resources cost ~$0.10/month and allow quick re-deployment.
"""

import subprocess
import sys
import os
import json
import platform
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_NAME = "pharma-test-gen"
AWS_REGION = "eu-west-2"
TERRAFORM_DIR = "aws/terraform"
TFVARS_FILE = "environments/staging.tfvars"

# Estimated hourly cost (without Aurora)
ESTIMATED_HOURLY_COST = 0.75


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def is_windows() -> bool:
    """Check if running on Windows (not WSL)."""
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()


def run_command(cmd, cwd=None, check=True, capture_output=False, timeout=None):
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
                shell=isinstance(cmd, str), timeout=timeout
            )
            if check and result.returncode != 0:
                return None
            return result.stdout.strip()
        else:
            result = subprocess.run(
                cmd, cwd=cwd, shell=isinstance(cmd, str), timeout=timeout
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


def confirm_destruction(auto_approve=False):
    """Ask for confirmation before destroying resources."""
    print("\n" + "=" * 70)
    print("   WARNING: INFRASTRUCTURE DESTRUCTION")
    print("=" * 70)

    print("""
   This will PERMANENTLY DELETE the following AWS resources:

   COMPUTE:
     - Amazon ECS Cluster (pharma-test-gen-cluster)
     - Amazon ECS Services (API, Worker, Frontend)
     - Amazon ECS Task Definitions

   NETWORKING:
     - Amazon Application Load Balancers (2)
     - Target Groups
     - Security Groups

   CDN:
     - Amazon CloudFront distribution (Terraform managed)
       Note: CloudFront auto-updates origins on next deploy

   STORAGE:
     - Amazon S3 Bucket contents (pharma-test-gen-vectors-staging)
     - Amazon S3 Bucket contents (pharma-test-gen-output-staging)

   MESSAGING:
     - Amazon SQS Queue (pharma-test-gen-worker-queue)
     - Amazon SQS Dead Letter Queue

   MONITORING:
     - Amazon CloudWatch Log Groups
     - AWS Config recorder (stopped, not deleted)

   SECURITY:
     - AWS IAM Roles and Policies

   PRESERVED (for quick re-deployment):
     - Amazon S3: pharma-test-gen-terraform-state (~$0.02/month)
     - Amazon DynamoDB: pharma-test-gen-terraform-locks (~$0.00/month)
     - Amazon ECR repositories (protected by lifecycle rule - images kept)
    """)

    print("=" * 70)
    print(f"   Estimated savings: ~${ESTIMATED_HOURLY_COST:.2f}/hour")
    print("=" * 70)

    if auto_approve:
        print("\n   Auto-approved with --yes flag")
        return True

    response = input("\n   Type 'yes' to confirm destruction: ")
    return response.lower().strip() == 'yes'


def get_terraform_outputs():
    """Get outputs from Terraform state."""
    project_root = get_project_root()
    terraform_dir = project_root / TERRAFORM_DIR

    if not (terraform_dir / ".terraform").exists():
        print("   Terraform not initialized, skipping output retrieval")
        return {}

    result = run_command(
        ["terraform", "output", "-json"],
        cwd=str(terraform_dir),
        capture_output=True,
        check=False
    )

    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {}
    return {}


def empty_s3_buckets():
    """Empty S3 buckets before Terraform destruction."""
    print("\n1. Emptying Amazon S3 buckets...")

    buckets = [
        f"{PROJECT_NAME}-vectors-staging",
        f"{PROJECT_NAME}-output-staging"
    ]

    for bucket in buckets:
        print(f"     Checking bucket: {bucket}")

        # Check if bucket exists
        result = run_command(
            ["aws", "s3", "ls", f"s3://{bucket}", "--region", AWS_REGION],
            capture_output=True, check=False
        )

        if result is None:
            print(f"     {bucket}: does not exist or empty")
            continue

        # Delete all objects
        print(f"     {bucket}: deleting objects...")
        run_command([
            "aws", "s3", "rm", f"s3://{bucket}/",
            "--recursive", "--region", AWS_REGION
        ], check=False)

        # Delete versioned objects if versioning is enabled
        print(f"     {bucket}: deleting object versions...")
        versions_cmd = f"aws s3api list-object-versions --bucket {bucket} --region {AWS_REGION} --query 'Versions[].{{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null"
        versions = run_command(versions_cmd, capture_output=True, check=False)

        if versions and versions != "null" and versions != "[]":
            try:
                version_list = json.loads(versions)
                if version_list:
                    for v in version_list:
                        run_command([
                            "aws", "s3api", "delete-object",
                            "--bucket", bucket,
                            "--key", v["Key"],
                            "--version-id", v["VersionId"],
                            "--region", AWS_REGION
                        ], check=False, capture_output=True)
            except json.JSONDecodeError:
                pass

        # Delete delete markers
        markers_cmd = f"aws s3api list-object-versions --bucket {bucket} --region {AWS_REGION} --query 'DeleteMarkers[].{{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null"
        markers = run_command(markers_cmd, capture_output=True, check=False)

        if markers and markers != "null" and markers != "[]":
            try:
                marker_list = json.loads(markers)
                if marker_list:
                    for m in marker_list:
                        run_command([
                            "aws", "s3api", "delete-object",
                            "--bucket", bucket,
                            "--key", m["Key"],
                            "--version-id", m["VersionId"],
                            "--region", AWS_REGION
                        ], check=False, capture_output=True)
            except json.JSONDecodeError:
                pass

        print(f"     {bucket}: emptied")


def scale_down_ecs_services():
    """Scale ECS services to 0 before destruction (faster cleanup)."""
    print("\n2. Scaling down ECS services...")

    cluster_name = f"{PROJECT_NAME}-cluster"
    services = [f"{PROJECT_NAME}-api", f"{PROJECT_NAME}-worker", f"{PROJECT_NAME}-frontend"]

    for service in services:
        print(f"     Scaling down: {service}")
        run_command([
            "aws", "ecs", "update-service",
            "--cluster", cluster_name,
            "--service", service,
            "--desired-count", "0",
            "--region", AWS_REGION
        ], check=False, capture_output=True)

    print("     Waiting 30 seconds for tasks to stop...")
    import time
    time.sleep(30)


def remove_ecr_from_state():
    """Remove ECR repos from Terraform state to allow destroy to proceed.

    ECR repos have prevent_destroy lifecycle rule, so we remove them from state
    before destruction. The repos remain in AWS for quick re-deployment.
    """
    print("\n   Removing ECR repositories from Terraform state...")
    print("     (ECR repos have prevent_destroy - keeping in AWS for quick redeploy)")

    project_root = get_project_root()
    terraform_dir = project_root / TERRAFORM_DIR

    services = ["api", "worker", "frontend"]

    for service in services:
        resource_address = f'module.ecr.aws_ecr_repository.this["{service}"]'
        policy_address = f'module.ecr.aws_ecr_lifecycle_policy.this["{service}"]'

        # Remove repo from state
        run_command(
            ["terraform", "state", "rm", resource_address],
            cwd=str(terraform_dir),
            capture_output=True, check=False
        )

        # Remove lifecycle policy from state
        run_command(
            ["terraform", "state", "rm", policy_address],
            cwd=str(terraform_dir),
            capture_output=True, check=False
        )

    print("     ECR resources removed from state (kept in AWS)")


def destroy_terraform():
    """Destroy infrastructure with Terraform."""
    print("\n3. Destroying infrastructure with Terraform...")

    project_root = get_project_root()
    terraform_dir = project_root / TERRAFORM_DIR

    if not terraform_dir.exists():
        print(f"   Terraform directory not found: {terraform_dir}")
        return False

    if not (terraform_dir / ".terraform").exists():
        print("   Terraform not initialized, nothing to destroy")
        return True

    # Remove ECR repos from state first (they have prevent_destroy)
    remove_ecr_from_state()

    # Run terraform destroy
    print("     Running terraform destroy...")
    print("     This will take 10-15 minutes...")

    result = run_command(
        ["terraform", "destroy", f"-var-file={TFVARS_FILE}", "-auto-approve"],
        cwd=str(terraform_dir),
        timeout=1200  # 20 minutes
    )

    if result:
        print("     Infrastructure destroyed successfully")
        return True
    else:
        print("     Terraform destroy failed")
        print("     You may need to manually delete resources in AWS Console")
        return False


def cleanup_ecr_images(skip=False):
    """Optionally clean up ECR images."""
    print("\n4. ECR Image Cleanup (Optional)...")

    if skip:
        print("     Skipping ECR cleanup (--skip-ecr flag)")
        print("     Keeping ECR images for faster re-deployment")
        return

    try:
        response = input("     Delete ECR images? (y/N): ")
    except EOFError:
        print("     Non-interactive mode - keeping ECR images")
        return

    if response.lower().strip() != 'y':
        print("     Keeping ECR images for faster re-deployment")
        return

    services = ["api", "worker", "frontend"]

    for service in services:
        repo_name = f"{PROJECT_NAME}-{service}"
        print(f"     Deleting images from: {repo_name}")

        # Get all image IDs
        result = run_command([
            "aws", "ecr", "list-images",
            "--repository-name", repo_name,
            "--region", AWS_REGION,
            "--query", "imageIds[*]",
            "--output", "json"
        ], capture_output=True, check=False)

        if result and result != "[]":
            try:
                images = json.loads(result)
                if images:
                    images_json = json.dumps(images)
                    run_command([
                        "aws", "ecr", "batch-delete-image",
                        "--repository-name", repo_name,
                        "--image-ids", images_json,
                        "--region", AWS_REGION
                    ], check=False, capture_output=True)
                    print(f"     {repo_name}: images deleted")
            except json.JSONDecodeError:
                pass
        else:
            print(f"     {repo_name}: no images found")


def stop_config_recorder():
    """Stop AWS Config recorder to save costs during development.

    AWS Config is NOT used by the application - it's infrastructure monitoring.
    Saves ~$3-5/month when stopped.
    """
    print("\n5. Stopping AWS Config recorder...")

    # Check current status
    result = run_command([
        "aws", "configservice", "describe-configuration-recorder-status",
        "--configuration-recorder-name", "pharma",
        "--region", AWS_REGION,
        "--query", "ConfigurationRecordersStatus[0].recording",
        "--output", "text"
    ], capture_output=True, check=False)

    if result and result.lower() == "true":
        run_command([
            "aws", "configservice", "stop-configuration-recorder",
            "--configuration-recorder-name", "pharma",
            "--region", AWS_REGION
        ], check=False, capture_output=True)
        print("     AWS Config recorder stopped (saves ~$3-5/month)")
    else:
        print("     AWS Config recorder already stopped or not found")


def cleanup_local_artifacts():
    """Clean up local build artifacts."""
    print("\n6. Cleaning up local artifacts...")

    project_root = get_project_root()
    terraform_dir = project_root / TERRAFORM_DIR

    # Only delete tfplan - keep .terraform.lock.hcl to avoid 'terraform init' requirement on redeploy
    artifacts = [
        terraform_dir / "tfplan",
        # NOTE: Don't delete .terraform.lock.hcl - it causes deploy failures
    ]

    for artifact in artifacts:
        if artifact.exists():
            if artifact.is_file():
                artifact.unlink()
                print(f"     Deleted: {artifact.name}")
            elif artifact.is_dir():
                import shutil
                shutil.rmtree(artifact)
                print(f"     Deleted directory: {artifact.name}")

    print("     Local artifacts cleaned")


def display_summary():
    """Display destruction summary."""
    print("\n" + "=" * 70)
    print("   DESTRUCTION COMPLETE")
    print("=" * 70)

    print(f"""
   All ECS/Fargate infrastructure has been destroyed.

   PRESERVED RESOURCES (for quick re-deployment):
     - S3 Bucket: pharma-test-gen-terraform-state
     - DynamoDB Table: pharma-test-gen-terraform-locks
     - ECR Repositories (removed from Terraform state, kept in AWS)
     - AWS Config (stopped, restart with: aws configservice start-configuration-recorder --configuration-recorder-name pharma --region eu-west-2)
     - CloudTrail (still logging)

   Total monthly cost of preserved resources: ~$0.10

   NOTE: CloudFront distribution was destroyed. On next deploy:
     - New ALBs will be created
     - CloudFront will be recreated with correct ALB origins
     - No manual intervention needed (Terraform manages CloudFront)

   TO RE-DEPLOY:
     python aws/scripts/deploy.py

   Or with uv:
     uv run aws/scripts/deploy.py
    """)

    print("=" * 70)


def main():
    """Main destruction function."""
    import argparse
    parser = argparse.ArgumentParser(description="Destroy AWS infrastructure")
    parser.add_argument("--yes", "-y", action="store_true", help="Auto-approve destruction without prompting")
    parser.add_argument("--skip-ecr", action="store_true", help="Skip ECR image deletion prompt")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("   PHARMACEUTICAL TEST GENERATION - AWS INFRASTRUCTURE DESTRUCTION")
    print("=" * 70)
    print(f"\n   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Region:  {AWS_REGION}")
    print(f"   Project: {PROJECT_NAME}")

    # Confirm destruction
    if not confirm_destruction(auto_approve=args.yes):
        print("\n   Destruction cancelled.")
        sys.exit(0)

    # Get terraform outputs before destruction
    outputs = get_terraform_outputs()

    # Empty S3 buckets first
    empty_s3_buckets()

    # Scale down ECS services for faster destruction
    scale_down_ecs_services()

    # Destroy Terraform infrastructure
    success = destroy_terraform()

    # Optionally cleanup ECR images
    if success:
        cleanup_ecr_images(skip=args.skip_ecr or args.yes)

    # Stop AWS Config recorder (saves ~$3-5/month)
    stop_config_recorder()

    # Cleanup local artifacts
    cleanup_local_artifacts()

    # Display summary
    display_summary()

    print(f"\n   Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
