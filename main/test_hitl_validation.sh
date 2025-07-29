#!/bin/bash

echo "🧪 Testing HITL Fix Implementation"
echo "=================================="

cd /home/anteb/thesis_project/main

echo "📋 Running validation test..."
python3 test_hitl_fix.py

echo ""
echo "🔍 Testing actual workflow execution (manual test required)..."
echo "Run this command manually and provide input when prompted:"
echo "python3 main.py test_urs_hitl.txt --verbose"
echo ""
echo "Expected prompts:"
echo "1. HUMAN CONSULTATION REQUIRED dialog"
echo "2. Enter GAMP category (1, 3, 4, 5): "
echo "3. Enter decision rationale: "
echo "4. Enter confidence level (0.0-1.0) [default: 0.8]: "
echo "5. Enter your user ID [default: cli_user]: "
echo "6. Enter your role [default: validation_engineer]: "
echo ""
echo "✅ If workflow continues after human input, the fix is successful!"