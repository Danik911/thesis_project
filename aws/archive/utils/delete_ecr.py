#!/usr/bin/env python3
"""Delete existing ECR repositories so Terraform can create them."""

import subprocess
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def main():
    delete_cmd = '''
echo "=== Deleting ECR Repositories ==="
aws ecr delete-repository --repository-name pharma-test-gen-api --region eu-west-2 --force 2>&1 || echo "api already deleted"
aws ecr delete-repository --repository-name pharma-test-gen-worker --region eu-west-2 --force 2>&1 || echo "worker already deleted"
aws ecr delete-repository --repository-name pharma-test-gen-frontend --region eu-west-2 --force 2>&1 || echo "frontend already deleted"
echo "=== ECR Repositories Deleted ==="
'''

    if is_windows():
        cmd = ["wsl", "-e", "bash", "-c", delete_cmd]
    else:
        cmd = delete_cmd

    result = subprocess.run(
        cmd,
        text=True,
        shell=not is_windows(),
        timeout=120
    )
    print("ECR repositories deleted. Ready for Terraform to recreate them.")
    return result.returncode == 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
