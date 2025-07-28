#!/usr/bin/env python3
"""
Example: PermissionDecision Hook with "ask" functionality
Demonstrates the new Claude Code hook capability to interact with permission decisions
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
LOG_FILE = Path(__file__).parent / "permission_hooks.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def handle_permission_decision(hook_data):
    """
    Handle PermissionDecision events with the new "ask" functionality
    
    This hook can:
    1. Intercept permission requests
    2. Make custom permission decisions
    3. Ask for user permission programmatically
    4. Provide custom permission logic
    """

    try:
        # Extract permission details from hook data
        tool_name = hook_data.get("tool_name", "")
        tool_input = hook_data.get("tool_input", {})
        permission_request = hook_data.get("permission_request", {})

        logger.info(f"Permission requested for tool: {tool_name}")

        # Example: Custom permission logic for dangerous operations
        if is_dangerous_operation(tool_name, tool_input):
            # Use the "ask" functionality to request explicit user permission
            response = {
                "decision": "ask",  # New "ask" option
                "message": f"⚠️  Dangerous operation detected: {tool_name}",
                "prompt": f"This operation involves {tool_name} with potentially risky parameters. Are you sure you want to proceed?",
                "sound": "warning",  # Custom sound for this permission type
                "additionalContext": {
                    "risk_level": "high",
                    "operation_type": "destructive",
                    "timestamp": datetime.now().isoformat(),
                    "suggested_alternatives": get_safer_alternatives(tool_name, tool_input)
                }
            }

        elif is_frequent_operation(tool_name):
            # Auto-allow frequent, safe operations
            response = {
                "decision": "allow",
                "message": f"✅ Auto-approved frequent operation: {tool_name}",
                "sound": "allow",
                "additionalContext": {
                    "auto_approved": True,
                    "reason": "frequent_safe_operation"
                }
            }

        elif requires_project_context(tool_name, tool_input):
            # Ask with project-specific context
            project_info = get_project_context()
            response = {
                "decision": "ask",
                "message": f"🔍 Project-sensitive operation: {tool_name}",
                "prompt": f"This operation will affect {project_info['type']} project. Proceed?",
                "additionalContext": {
                    "project_context": project_info,
                    "affected_files": get_affected_files(tool_input),
                    "risk_assessment": assess_project_risk(tool_name, tool_input)
                }
            }

        else:
            # Default behavior - use standard permission flow
            response = {
                "decision": "default",
                "message": f"📋 Standard permission check: {tool_name}"
            }

        logger.info(f"Permission decision: {response['decision']}")
        return response

    except Exception as e:
        logger.error(f"Permission decision error: {e}")
        return {
            "decision": "ask",  # Default to asking when in doubt
            "message": f"❌ Permission error - manual approval required: {e!s}"
        }

def is_dangerous_operation(tool_name, tool_input):
    """Check if operation is potentially dangerous"""
    dangerous_patterns = {
        "Bash": [
            "rm -rf", "sudo rm", ">/dev/", "format", "mkfs",
            "dd if=", "fdisk", "parted", "shutdown", "reboot"
        ],
        "Write": [
            "/.ssh/", "/etc/", "authorized_keys", "passwd", "shadow"
        ],
        "Edit": [
            "/.bashrc", "/.zshrc", "/etc/hosts", "crontab"
        ]
    }

    if tool_name in dangerous_patterns:
        patterns = dangerous_patterns[tool_name]
        content = str(tool_input).lower()
        return any(pattern.lower() in content for pattern in patterns)

    return False

def is_frequent_operation(tool_name):
    """Check if this is a frequent, safe operation"""
    frequent_safe_tools = {
        "Read", "LS", "Glob", "Grep", "TodoWrite",
        "mcp__filesystem__read_file", "mcp__filesystem__list_directory"
    }
    return tool_name in frequent_safe_tools

def requires_project_context(tool_name, tool_input):
    """Check if operation requires project context"""
    context_sensitive_operations = [
        "git commit", "git push", "npm publish", "docker build",
        "deployment", "production", "release"
    ]

    content = str(tool_input).lower()
    return any(op in content for op in context_sensitive_operations)

def get_project_context():
    """Get current project context"""
    return {
        "type": "thesis_project",
        "branch": "project_set_up",
        "has_uncommitted_changes": True,
        "framework": "PRP (Product Requirement Prompt)",
        "risk_level": "development"
    }

def get_affected_files(tool_input):
    """Extract affected file paths from tool input"""
    file_path = tool_input.get("file_path", "")
    if file_path:
        return [file_path]

    # Extract from bash commands
    command = tool_input.get("command", "")
    if command:
        # Simple extraction - could be enhanced
        words = command.split()
        files = [word for word in words if "/" in word or "." in word]
        return files[:5]  # Limit to 5 files

    return []

def assess_project_risk(tool_name, tool_input):
    """Assess risk level for project operations"""
    risk_factors = {
        "git push": "medium",
        "rm": "high",
        "sudo": "high",
        "production": "critical",
        "database": "high"
    }

    content = str(tool_input).lower()
    max_risk = "low"

    for factor, risk in risk_factors.items():
        if factor in content:
            if risk == "critical":
                max_risk = "critical"
                break
            if risk == "high" and max_risk != "critical":
                max_risk = "high"
            elif risk == "medium" and max_risk == "low":
                max_risk = "medium"

    return max_risk

def get_safer_alternatives(tool_name, tool_input):
    """Suggest safer alternatives for dangerous operations"""
    alternatives = {
        "rm -rf": "Use 'rm -i' for interactive deletion or move to trash first",
        "sudo": "Consider running without sudo first or use specific user permissions",
        "git push --force": "Use 'git push --force-with-lease' instead",
        ">/dev/null": "Consider using a log file instead for debugging"
    }

    content = str(tool_input).lower()
    suggestions = []

    for pattern, suggestion in alternatives.items():
        if pattern in content:
            suggestions.append(suggestion)

    return suggestions

def main():
    """Main entry point for PermissionDecision hook"""
    try:
        if len(sys.argv) > 1:
            # Test mode
            test_data = {
                "hook_event_name": "PermissionDecision",
                "tool_name": sys.argv[1],
                "tool_input": {"command": " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "test"},
                "permission_request": {"type": "tool_execution"}
            }
            result = handle_permission_decision(test_data)
            print(json.dumps(result, indent=2))
        else:
            # Real hook execution
            hook_data = json.loads(sys.stdin.read())
            result = handle_permission_decision(hook_data)
            print(json.dumps(result))

    except Exception as e:
        logger.error(f"Main error: {e}")
        print(json.dumps({
            "decision": "ask",
            "message": f"Hook error - manual approval required: {e!s}"
        }))

if __name__ == "__main__":
    main()
