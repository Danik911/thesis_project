#!/bin/bash
# Test script to simulate Claude Code permission output

echo "Claude Code v1.0.0"
echo "Analyzing request..."
sleep 1
echo ""
echo "Claude needs your permission to execute the following command:"
echo "  rm -rf /tmp/test"
echo ""
echo "Do you want to allow this action? [y/N]: "
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Permission granted. Executing..."
    sleep 1
    echo "Command executed successfully."
else
    echo "Permission denied. Operation cancelled."
fi