#!/usr/bin/env python3
"""Check Terraform state for ECR repositories."""

import subprocess
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def main():
    terraform_cmd = '''
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH
terraform state list | grep ecr
'''

    if is_windows():
        cmd = ["wsl", "-e", "bash", "-c", terraform_cmd]
    else:
        cmd = terraform_cmd

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=not is_windows(),
        timeout=60
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

if __name__ == "__main__":
    main()
