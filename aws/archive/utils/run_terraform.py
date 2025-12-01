#!/usr/bin/env python3
"""Run Terraform plan and apply."""

import subprocess
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def main():
    terraform_cmd = '''
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

echo "=== Terraform Plan ==="
terraform plan -var-file=environments/staging.tfvars -out=tfplan

echo "=== Terraform Apply ==="
terraform apply -auto-approve tfplan
'''

    if is_windows():
        cmd = ["wsl", "-e", "bash", "-c", terraform_cmd]
    else:
        cmd = terraform_cmd

    result = subprocess.run(
        cmd,
        text=True,
        shell=not is_windows(),
        timeout=1200  # 20 minutes
    )
    return result.returncode == 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
