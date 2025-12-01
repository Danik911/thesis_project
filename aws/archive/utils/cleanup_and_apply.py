#!/usr/bin/env python3
"""Clean up failed resources and re-apply Terraform."""

import subprocess
import platform

def is_windows():
    return platform.system() == "Windows" and "microsoft" not in platform.uname().release.lower()

def main():
    cleanup_cmd = '''
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project/aws/terraform
export PATH=$HOME/bin:$PATH

echo "=== Removing Failed Resources from State ==="
# Remove SQS scaling policy if partially created
terraform state rm 'module.ecs_worker.aws_appautoscaling_policy.sqs[0]' 2>&1 || echo "SQS policy not in state"
terraform state rm 'module.ecs_worker.aws_appautoscaling_target.this[0]' 2>&1 || echo "Scaling target not in state"

# Remove partially created HTTPS listeners
terraform state rm 'module.alb_api.aws_lb_listener.https[0]' 2>&1 || echo "api https listener not in state"
terraform state rm 'module.alb_frontend.aws_lb_listener.https[0]' 2>&1 || echo "frontend https listener not in state"

# Remove API and frontend services to recreate properly
terraform state rm 'module.ecs_api.aws_ecs_service.this' 2>&1 || echo "api service not in state"
terraform state rm 'module.ecs_frontend.aws_ecs_service.this' 2>&1 || echo "frontend service not in state"

echo "=== Running Terraform Plan and Apply ==="
terraform plan -var-file=environments/staging.tfvars -out=tfplan
terraform apply -auto-approve tfplan
'''

    if is_windows():
        cmd = ["wsl", "-e", "bash", "-c", cleanup_cmd]
    else:
        cmd = cleanup_cmd

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
