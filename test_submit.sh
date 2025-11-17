#!/bin/bash

# Generate fresh Clerk JWT token
TOKEN=$(python scripts/get_clerk_token.py --user-id user_35KgiAcvIC0tdtFvJUN1vDkrNYc --env-file .env.local)

echo "Token generated: ${TOKEN:0:20}..."

# Submit URS workflow
echo "Submitting URS-001.md to API..."
RESPONSE=$(curl -X POST http://localhost:8080/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "urs_file=@./datasets/urs_corpus/category_3/URS-001.md" \
  2>&1)

echo "Response: $RESPONSE"

# Extract job ID if submission successful
JOB_ID=$(echo "$RESPONSE" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$JOB_ID" ]; then
  echo "✅ Job submitted successfully!"
  echo "Job ID: $JOB_ID"
  echo ""
  echo "Monitor with:"
  echo "curl http://localhost:8080/jobs/$JOB_ID -H \"Authorization: Bearer \$TOKEN\""
else
  echo "❌ Job submission failed"
  echo "Full response: $RESPONSE"
fi
