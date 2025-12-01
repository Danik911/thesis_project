#!/usr/bin/env python3
"""Import all existing resources into Terraform state."""

import subprocess
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def main():
    terraform_cmd = '''
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

echo "=== Importing ECR Repositories ==="
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["api"]' pharma-test-gen-api 2>&1 || true
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["worker"]' pharma-test-gen-worker 2>&1 || true
terraform import -var-file=environments/staging.tfvars 'module.ecr.aws_ecr_repository.this["frontend"]' pharma-test-gen-frontend 2>&1 || true

echo "=== Importing Target Groups ==="
terraform import -var-file=environments/staging.tfvars 'module.alb_api.aws_lb_target_group.this' arn:aws:elasticloadbalancing:eu-west-2:275333454012:targetgroup/pharma-test-gen-api-alb-tg/e6daad3442abde46 2>&1 || true
terraform import -var-file=environments/staging.tfvars 'module.alb_frontend.aws_lb_target_group.this' arn:aws:elasticloadbalancing:eu-west-2:275333454012:targetgroup/pharma-test-gen-frontend-alb-tg/0d5e20b948b3b135 2>&1 || true

echo "=== Import Complete ==="
'''

    if is_windows():
        cmd = ["wsl", "-e", "bash", "-c", terraform_cmd]
    else:
        cmd = terraform_cmd

    result = subprocess.run(
        cmd,
        text=True,
        shell=not is_windows(),
        timeout=300
    )
    return result.returncode == 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
