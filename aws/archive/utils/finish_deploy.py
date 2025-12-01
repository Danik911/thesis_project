#!/usr/bin/env python3
"""Finish deployment by importing existing autoscaling target."""

import subprocess
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def main():
    finish_cmd = '''
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

echo "=== Importing Existing Autoscaling Target ==="
terraform import -var-file=environments/staging.tfvars 'module.ecs_worker.aws_appautoscaling_target.this[0]' service/pharma-test-gen-cluster/pharma-test-gen-worker 2>&1 || echo "Already imported or not needed"

echo "=== Final Terraform Apply ==="
terraform apply -var-file=environments/staging.tfvars -auto-approve

echo "=== Getting Outputs ==="
terraform output -json
'''

    if is_windows():
        cmd = ["wsl", "-e", "bash", "-c", finish_cmd]
    else:
        cmd = finish_cmd

    result = subprocess.run(
        cmd,
        text=True,
        shell=not is_windows(),
        timeout=600  # 10 minutes
    )
    return result.returncode == 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
