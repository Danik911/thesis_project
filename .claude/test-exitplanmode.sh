#!/bin/bash
# Test script to verify ExitPlanMode pattern detection

echo "Testing ExitPlanMode pattern detection..."
echo ""

# Test various ExitPlanMode outputs
test_patterns=(
    "Do you want to allow Claude to use the tool ExitPlanMode?"
    "ExitPlanMode permission requested"
    "Ready to exit plan mode"
    "User has approved your plan. You can now start coding."
    "Claude wants to exit plan mode"
    "[y/N]: Allow ExitPlanMode?"
)

for pattern in "${test_patterns[@]}"; do
    echo "Testing: $pattern"
    echo "$pattern" | /home/anteb/thesis_project/.claude/claude-audio-wrapper.sh cat
    echo "---"
    sleep 1
done

echo "Test complete. You should have heard audio for each pattern."