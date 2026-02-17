#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
cd /mnt/c/Users/anteb/Desktop/Courses/Projects/thesis_project
uv run uvicorn main.api.app:app --host 0.0.0.0 --port 8080 --reload 2>&1 | tee /tmp/uvicorn.log &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
sleep 15
if curl -s http://localhost:8080/health; then
  echo ""
  echo "Server started OK"
else
  echo "Server failed. Last 20 lines:"
  tail -20 /tmp/uvicorn.log
fi
