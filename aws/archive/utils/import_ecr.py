#!/usr/bin/env python3
"""Import existing ECR repositories into Terraform state."""

import subprocess
import sys
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def run_terraform_import(resource_address, ecr_repo_name):
    """Run a terraform import command."""
    print(f"Importing {ecr_repo_name} as {resource_address}")

    terraform_cmd = f'cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform && export PATH=$HOME/bin:$PATH && terraform import -var-file=environments/staging.tfvars "{resource_address}" {ecr_repo_name}'

    if is_windows():
        cmd = ["wsl", "-e", "bash", "-c", terraform_cmd]
    else:
        cmd = terraform_cmd

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=not is_windows(),
            timeout=120
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    imports = [
        ('module.ecr.aws_ecr_repository.this[\\"api\\"]', 'pharma-test-gen-api'),
        ('module.ecr.aws_ecr_repository.this[\\"worker\\"]', 'pharma-test-gen-worker'),
        ('module.ecr.aws_ecr_repository.this[\\"frontend\\"]', 'pharma-test-gen-frontend'),
    ]

    for resource_address, ecr_repo_name in imports:
        success = run_terraform_import(resource_address, ecr_repo_name)
        if not success:
            print(f"Warning: Import may have failed for {ecr_repo_name}")

    print("ECR import complete!")

if __name__ == "__main__":
    main()
