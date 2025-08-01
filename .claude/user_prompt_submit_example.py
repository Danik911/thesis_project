#!/usr/bin/env uv run python
"""
Example: UserPromptSubmit Hook with additionalContext in Advanced JSON
Demonstrates the new Claude Code capability to add rich context to user prompts
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
LOG_FILE = Path(__file__).parent / "prompt_context_hooks.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def handle_user_prompt_submit(hook_data: dict[str, Any]) -> dict[str, Any]:
    """
    Handle UserPromptSubmit events with enhanced additionalContext
    
    The new feature allows adding rich context to user prompts through
    advanced JSON output with additionalContext field
    """

    try:
        user_prompt = hook_data.get("user_prompt", "")
        conversation_context = hook_data.get("conversation_context", {})

        logger.info(f"Processing user prompt: {user_prompt[:100]}...")

        # Generate comprehensive additional context
        additional_context = generate_additional_context(user_prompt, conversation_context)

        # Determine if prompt should be enhanced, blocked, or passed through
        action = determine_prompt_action(user_prompt, additional_context)

        if action == "block":
            return {
                "decision": "block",
                "message": "❌ Prompt blocked by context analysis",
                "reason": additional_context.get("block_reason", "Content policy violation"),
                "additionalContext": additional_context
            }

        if action == "enhance":
            return {
                "decision": "continue",
                "message": "✨ Prompt enhanced with project context",
                "additionalContext": additional_context
            }

        # pass through
        return {
            "decision": "continue",
            "message": "📝 Prompt processed with basic context",
            "additionalContext": {
                "enhancement_applied": False,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"UserPromptSubmit error: {e}")
        return {
            "decision": "continue",
            "message": f"⚠️ Context processing error: {e!s}",
            "additionalContext": {
                "error": str(e),
                "fallback_mode": True
            }
        }

def generate_additional_context(user_prompt: str, conversation_context: dict) -> dict[str, Any]:
    """Generate rich additional context for the user prompt"""

    context = {
        "timestamp": datetime.now().isoformat(),
        "prompt_analysis": analyze_prompt_intent(user_prompt),
        "project_state": get_current_project_state(),
        "environment_info": get_environment_context(),
        "conversation_metadata": process_conversation_context(conversation_context),
        "suggestions": generate_context_suggestions(user_prompt),
        "security_analysis": perform_security_analysis(user_prompt),
        "resource_recommendations": get_resource_recommendations(user_prompt)
    }

    # Add conditional context based on prompt content
    if is_coding_request(user_prompt):
        context["coding_context"] = get_coding_context()

    if is_git_related(user_prompt):
        context["git_context"] = get_git_context()

    if is_file_operation(user_prompt):
        context["file_context"] = get_file_operation_context(user_prompt)

    if is_research_request(user_prompt):
        context["research_context"] = get_research_context()

    return context

def analyze_prompt_intent(prompt: str) -> dict[str, Any]:
    """Analyze the intent and complexity of the user prompt"""

    intent_patterns = {
        "code_creation": ["create", "implement", "build", "develop", "write code"],
        "debugging": ["fix", "debug", "error", "not working", "issue"],
        "explanation": ["explain", "how does", "what is", "why"],
        "file_operation": ["read", "write", "edit", "delete", "move"],
        "research": ["search", "find", "lookup", "investigate"],
        "planning": ["plan", "design", "architecture", "structure"],
        "testing": ["test", "verify", "check", "validate"]
    }

    detected_intents = []
    prompt_lower = prompt.lower()

    for intent, patterns in intent_patterns.items():
        if any(pattern in prompt_lower for pattern in patterns):
            detected_intents.append(intent)

    complexity_score = calculate_complexity_score(prompt)

    return {
        "detected_intents": detected_intents,
        "primary_intent": detected_intents[0] if detected_intents else "general",
        "complexity_score": complexity_score,
        "word_count": len(prompt.split()),
        "has_code_snippets": "```" in prompt or "`" in prompt,
        "has_file_paths": "/" in prompt or "\\" in prompt,
        "has_urls": "http" in prompt.lower()
    }

def get_current_project_state() -> dict[str, Any]:
    """Get comprehensive current project state"""

    try:
        project_root = Path("/home/anteb/thesis_project")

        # Git information
        git_info = {}
        try:
            git_info = {
                "current_branch": subprocess.check_output(
                    ["git", "branch", "--show-current"],
                    cwd=project_root, text=True
                ).strip(),
                "has_uncommitted": len(subprocess.check_output(
                    ["git", "status", "--porcelain"],
                    cwd=project_root, text=True
                ).strip()) > 0,
                "last_commit": subprocess.check_output(
                    ["git", "log", "-1", "--oneline"],
                    cwd=project_root, text=True
                ).strip()
            }
        except:
            git_info = {"status": "not_available"}

        # Project structure
        structure_info = {
            "has_claude_config": (project_root / ".claude").exists(),
            "has_prp_directory": (project_root / "PRPs").exists(),
            "has_src_directory": (project_root / "src").exists(),
            "has_tests": (project_root / "tests").exists(),
            "total_files": len(list(project_root.rglob("*"))) if project_root.exists() else 0
        }

        # Recent activity
        recent_files = get_recently_modified_files(project_root)

        return {
            "git_info": git_info,
            "structure_info": structure_info,
            "recent_activity": {
                "recently_modified_files": recent_files,
                "active_areas": identify_active_project_areas(recent_files)
            },
            "project_type": "thesis_project_with_prp_framework"
        }

    except Exception as e:
        return {"error": str(e), "fallback": True}

def get_environment_context() -> dict[str, Any]:
    """Get current environment and system context"""

    return {
        "working_directory": os.getcwd(),
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "user": os.getenv("USER", "unknown"),
        "claude_code_session": os.getenv("CLAUDE_CODE_SESSION_ID", "unknown"),
        "available_tools": get_available_tools(),
        "shell": os.getenv("SHELL", "unknown"),
        "terminal_type": os.getenv("TERM", "unknown")
    }

def get_coding_context() -> dict[str, Any]:
    """Get context specific to coding requests"""

    try:
        project_root = Path("/home/anteb/thesis_project")

        # Language detection
        languages = detect_project_languages(project_root)

        # Framework detection
        frameworks = detect_frameworks(project_root)

        # Code quality tools
        quality_tools = detect_quality_tools(project_root)

        return {
            "languages": languages,
            "frameworks": frameworks,
            "quality_tools": quality_tools,
            "coding_standards": get_coding_standards(),
            "recommended_patterns": get_recommended_patterns()
        }

    except Exception as e:
        return {"error": str(e)}

def get_git_context() -> dict[str, Any]:
    """Get Git-specific context"""

    try:
        project_root = Path("/home/anteb/thesis_project")

        return {
            "current_branch": subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=project_root, text=True
            ).strip(),
            "remote_branches": subprocess.check_output(
                ["git", "branch", "-r"],
                cwd=project_root, text=True
            ).strip().split("\n"),
            "staged_files": subprocess.check_output(
                ["git", "diff", "--cached", "--name-only"],
                cwd=project_root, text=True
            ).strip().split("\n") if subprocess.check_output(
                ["git", "diff", "--cached", "--name-only"],
                cwd=project_root, text=True
            ).strip() else [],
            "modified_files": subprocess.check_output(
                ["git", "diff", "--name-only"],
                cwd=project_root, text=True
            ).strip().split("\n") if subprocess.check_output(
                ["git", "diff", "--name-only"],
                cwd=project_root, text=True
            ).strip() else []
        }

    except Exception as e:
        return {"error": str(e)}

def determine_prompt_action(prompt: str, context: dict[str, Any]) -> str:
    """Determine what action to take with the prompt"""

    # Security checks
    security_analysis = context.get("security_analysis", {})
    if security_analysis.get("risk_level") == "high":
        return "block"

    # Enhancement checks
    if should_enhance_prompt(prompt, context):
        return "enhance"

    return "continue"

def should_enhance_prompt(prompt: str, context: dict[str, Any]) -> bool:
    """Determine if prompt should be enhanced with additional context"""

    enhancement_triggers = [
        lambda: context.get("prompt_analysis", {}).get("complexity_score", 0) > 7,
        lambda: "implement" in prompt.lower() and context.get("coding_context"),
        lambda: "git" in prompt.lower() and context.get("git_context"),
        lambda: len(prompt.split()) > 50,  # Long prompts benefit from context
        lambda: context.get("project_state", {}).get("git_info", {}).get("has_uncommitted", False)
    ]

    return any(trigger() for trigger in enhancement_triggers)

def perform_security_analysis(prompt: str) -> dict[str, Any]:
    """Perform security analysis on the prompt"""

    risk_patterns = {
        "high": [
            "rm -rf", "sudo rm", "format", "delete everything",
            "drop table", "truncate", ">/dev/null"
        ],
        "medium": [
            "sudo", "chmod 777", "password", "token", "secret",
            "api_key", "private_key"
        ],
        "low": [
            "install", "download", "curl", "wget"
        ]
    }

    prompt_lower = prompt.lower()
    risk_level = "none"
    detected_patterns = []

    for level, patterns in risk_patterns.items():
        for pattern in patterns:
            if pattern in prompt_lower:
                detected_patterns.append(pattern)
                if level == "high":
                    risk_level = "high"
                elif level == "medium" and risk_level != "high":
                    risk_level = "medium"
                elif level == "low" and risk_level == "none":
                    risk_level = "low"

    return {
        "risk_level": risk_level,
        "detected_patterns": detected_patterns,
        "recommendation": get_security_recommendation(risk_level)
    }

# Helper functions (simplified for brevity)
def calculate_complexity_score(prompt: str) -> int:
    """Calculate complexity score 1-10"""
    factors = [
        len(prompt.split()) / 10,  # Word count factor
        prompt.count("\n"),  # Multi-line factor
        prompt.count("```") * 2,  # Code block factor
        len([w for w in prompt.split() if w.startswith("/")]) * 0.5,  # File path factor
    ]
    return min(10, int(sum(factors)))

def get_recently_modified_files(project_root: Path) -> list[str]:
    """Get recently modified files"""
    try:
        return subprocess.check_output(
            ["find", str(project_root), "-type", "f", "-mtime", "-1"],
            text=True
        ).strip().split("\n")[:10]
    except:
        return []

def identify_active_project_areas(recent_files: list[str]) -> list[str]:
    """Identify active project areas from recent files"""
    areas = set()
    for file_path in recent_files:
        if file_path:
            path_parts = Path(file_path).parts
            if len(path_parts) > 2:
                areas.add(path_parts[-2])  # Parent directory
    return list(areas)[:5]

def detect_project_languages(project_root: Path) -> list[str]:
    """Detect programming languages in project"""
    extensions = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                 ".md": "Markdown", ".json": "JSON", ".sh": "Shell"}
    found_languages = set()

    try:
        for ext, lang in extensions.items():
            if list(project_root.rglob(f"*{ext}")):
                found_languages.add(lang)
    except:
        pass

    return list(found_languages)

def detect_frameworks(project_root: Path) -> list[str]:
    """Detect frameworks in project"""
    framework_indicators = {
        "package.json": ["Node.js"],
        "requirements.txt": ["Python"],
        "pyproject.toml": ["Python", "Modern Python"],
        "Dockerfile": ["Docker"],
        ".github": ["GitHub Actions"]
    }

    found_frameworks = set()
    try:
        for indicator, frameworks in framework_indicators.items():
            if (project_root / indicator).exists():
                found_frameworks.update(frameworks)
    except:
        pass

    return list(found_frameworks)

def detect_quality_tools(project_root: Path) -> list[str]:
    """Detect code quality tools"""
    tools = []
    try:
        if (project_root / ".pre-commit-config.yaml").exists():
            tools.append("pre-commit")
        if (project_root / "pyproject.toml").exists():
            tools.append("modern Python tooling")
    except:
        pass
    return tools

def get_coding_standards() -> dict[str, str]:
    """Get project coding standards"""
    return {
        "python": "PEP 8, type hints required",
        "javascript": "ES6+, modern syntax",
        "general": "Keep files under 500 lines, comprehensive documentation"
    }

def get_recommended_patterns() -> list[str]:
    """Get recommended coding patterns for this project"""
    return [
        "Use PRP methodology for complex features",
        "Implement validation gates for all code",
        "Follow iterative development approach",
        "Include comprehensive documentation"
    ]

def get_available_tools() -> list[str]:
    """Get list of available Claude Code tools"""
    return [
        "Bash", "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep",
        "TodoWrite", "WebFetch", "mcp__filesystem__*", "mcp__perplexity-mcp__*"
    ]

def generate_context_suggestions(prompt: str) -> list[str]:
    """Generate contextual suggestions based on prompt"""
    suggestions = []
    prompt_lower = prompt.lower()

    if "implement" in prompt_lower:
        suggestions.append("Consider using /create-base-prp for complex implementations")

    if "git" in prompt_lower:
        suggestions.append("Check current branch and uncommitted changes first")

    if "test" in prompt_lower:
        suggestions.append("Run existing tests before making changes")

    return suggestions

def get_resource_recommendations(prompt: str) -> list[str]:
    """Get resource recommendations based on prompt"""
    recommendations = []
    prompt_lower = prompt.lower()

    if any(lang in prompt_lower for lang in ["python", "javascript", "typescript"]):
        recommendations.append("Use context7 tool for up-to-date documentation")

    if "api" in prompt_lower:
        recommendations.append("Check existing API documentation in project")

    return recommendations

def get_security_recommendation(risk_level: str) -> str:
    """Get security recommendation based on risk level"""
    recommendations = {
        "high": "⚠️ High risk operation - manual review required",
        "medium": "⚠️ Medium risk - verify operation before execution",
        "low": "ℹ️ Low risk - standard precautions apply",
        "none": "✅ No security concerns detected"
    }
    return recommendations.get(risk_level, "Unknown risk level")

def process_conversation_context(context: dict) -> dict[str, Any]:
    """Process conversation context metadata"""
    return {
        "message_count": context.get("message_count", 0),
        "conversation_duration": context.get("duration", "unknown"),
        "topics_discussed": context.get("topics", []),
        "tools_used": context.get("tools_used", [])
    }

def get_research_context() -> dict[str, Any]:
    """Get context for research requests"""
    return {
        "available_research_tools": ["mcp__perplexity-mcp__search", "WebFetch", "context7"],
        "research_guidelines": "Use multiple sources, verify information",
        "preferred_sources": ["official documentation", "recent articles", "authoritative sources"]
    }

def get_file_operation_context(prompt: str) -> dict[str, Any]:
    """Get context for file operations"""
    return {
        "current_directory": os.getcwd(),
        "write_permissions": os.access(".", os.W_OK),
        "file_safety_check": "Always read files before editing",
        "backup_recommendation": "Consider backing up important files"
    }

def is_coding_request(prompt: str) -> bool:
    """Check if prompt is coding-related"""
    coding_keywords = ["code", "implement", "function", "class", "debug", "fix", "program"]
    return any(keyword in prompt.lower() for keyword in coding_keywords)

def is_git_related(prompt: str) -> bool:
    """Check if prompt is git-related"""
    git_keywords = ["git", "commit", "push", "pull", "branch", "merge", "repository"]
    return any(keyword in prompt.lower() for keyword in git_keywords)

def is_file_operation(prompt: str) -> bool:
    """Check if prompt involves file operations"""
    file_keywords = ["file", "read", "write", "edit", "create", "delete", "move"]
    return any(keyword in prompt.lower() for keyword in file_keywords)

def is_research_request(prompt: str) -> bool:
    """Check if prompt is a research request"""
    research_keywords = ["search", "find", "lookup", "research", "investigate", "documentation"]
    return any(keyword in prompt.lower() for keyword in research_keywords)

def main():
    """Main entry point for UserPromptSubmit hook"""
    try:
        if len(sys.argv) > 1:
            # Test mode
            test_data = {
                "hook_event_name": "UserPromptSubmit",
                "user_prompt": " ".join(sys.argv[1:]),
                "conversation_context": {"message_count": 1, "tools_used": []}
            }
            result = handle_user_prompt_submit(test_data)
            print(json.dumps(result, indent=2))
        else:
            # Real hook execution
            hook_data = json.loads(sys.stdin.read())
            result = handle_user_prompt_submit(hook_data)
            print(json.dumps(result))

    except Exception as e:
        logger.error(f"Main error: {e}")
        print(json.dumps({
            "decision": "continue",
            "message": f"Context processing error: {e!s}",
            "additionalContext": {"error": str(e)}
        }))

if __name__ == "__main__":
    main()
