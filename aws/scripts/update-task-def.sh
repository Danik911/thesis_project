#!/bin/bash
set -e

NEW_IMAGE="275333454012.dkr.ecr.eu-west-2.amazonaws.com/pharma-test-gen-api:staging-20251206105702"
REGION="eu-west-2"

echo "Getting current task definition..."
aws ecs describe-task-definition --task-definition pharma-test-gen-api --region $REGION --query 'taskDefinition' > /tmp/current-task-def.json

echo "Updating image to: $NEW_IMAGE"
jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)' /tmp/current-task-def.json | \
jq --arg img "$NEW_IMAGE" '.containerDefinitions[0].image = $img' > /tmp/new-task-def.json

echo "Registering new task definition..."
REVISION=$(aws ecs register-task-definition --cli-input-json file:///tmp/new-task-def.json --region $REGION --query 'taskDefinition.revision' --output text)

echo "Registered revision: $REVISION"

echo "Forcing new deployment..."
aws ecs update-service --cluster pharma-test-gen-cluster --service pharma-test-gen-api --task-definition pharma-test-gen-api:$REVISION --force-new-deployment --region $REGION --query 'service.deployments[0].status' --output text

echo "Done! Service is deploying."
