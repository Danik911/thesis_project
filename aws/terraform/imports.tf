# Import blocks for existing ECR repositories
import {
  to = module.ecr.aws_ecr_repository.this["api"]
  id = "pharma-test-gen-api"
}

import {
  to = module.ecr.aws_ecr_repository.this["worker"]
  id = "pharma-test-gen-worker"
}

import {
  to = module.ecr.aws_ecr_repository.this["frontend"]
  id = "pharma-test-gen-frontend"
}
