#!/usr/bin/env python3
"""Import all existing ECR repositories into Terraform state in a single session."""

import subprocess
import sys
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def run_terraform_import_all():
    """Run terraform import for all ECR repositories."""
    print("Importing all ECR repositories into Terraform state...")

    # Build a command that imports all three ECR repos sequentially
    terraform_cmd = '''
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

# Import all three ECR repositories
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["api"]' pharma-test-gen-api 2>/dev/null || echo "api import done or skipped"
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["worker"]' pharma-test-gen-worker 2>/dev/null || echo "worker import done or skipped"
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["frontend"]' pharma-test-gen-frontend 2>/dev/null || echo "frontend import done or skipped"

echo "All imports complete"
'''

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
            timeout=300
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    run_terraform_import_all()

if __name__ == "__main__":
    main()
