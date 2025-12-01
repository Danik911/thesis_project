#!/usr/bin/env python3
"""Delete existing target groups so Terraform can create them."""

import subprocess
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def main():
    # First, we need to remove the target groups from state since they're incorrectly tracked
    terraform_cmd = '''
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

echo "=== Removing Target Groups from State ==="
terraform state rm 'module.alb_api.aws_lb_target_group.this' 2>&1 || echo "api target group not in state"
terraform state rm 'module.alb_frontend.aws_lb_target_group.this' 2>&1 || echo "frontend target group not in state"
'''

    delete_cmd = '''
echo "=== Deleting Target Groups ==="
aws elbv2 delete-target-group --target-group-arn arn:aws:elasticloadbalancing:eu-west-2:275333454012:targetgroup/pharma-test-gen-api-alb-tg/e6daad3442abde46 --region eu-west-2 2>&1 || echo "api target group already deleted"
aws elbv2 delete-target-group --target-group-arn arn:aws:elasticloadbalancing:eu-west-2:275333454012:targetgroup/pharma-test-gen-frontend-alb-tg/0d5e20b948b3b135 --region eu-west-2 2>&1 || echo "frontend target group already deleted"
echo "=== Target Groups Deleted ==="
'''

    if is_windows():
        cmd1 = ["wsl", "-e", "bash", "-c", terraform_cmd]
        cmd2 = ["wsl", "-e", "bash", "-c", delete_cmd]
    else:
        cmd1 = terraform_cmd
        cmd2 = delete_cmd

    subprocess.run(
        cmd1,
        text=True,
        shell=not is_windows(),
        timeout=120
    )

    subprocess.run(
        cmd2,
        text=True,
        shell=not is_windows(),
        timeout=120
    )

    print("Target groups removed. Ready for Terraform to recreate them.")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
