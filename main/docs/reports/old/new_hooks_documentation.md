# Claude Code Hooks Documentation - Windows Migration & New Features

## Status: ⚠️ UNDER RESOLUTION
**Last Updated**: 2025-07-31  
**Issue Status**: Windows migration fixes implemented but NOT YET TESTED by user

---

## Windows Migration Issues & Fixes

### Original Problem
After migrating from Ubuntu to Windows, Claude Code hooks stopped working with error:
```
Stop [python3 /home/anteb/thesis_project/.claude/audio_hooks.py] 
failed with non-blocking status code 127: /usr/bin/bash: line 1:
python3: command not found
```

### Root Cause Analysis
1. **Linux paths in Windows environment**: Hook configuration still referenced `/home/anteb/thesis_project/` (Linux path)
2. **Wrong Python command**: Used `python3` instead of `python` (Windows standard)
3. **Bash shell assumption**: Hooks tried to execute via `/usr/bin/bash` which doesn't exist on Windows
4. **Configuration caching**: Claude Code may cache hook configuration requiring restart

### Research Findings

**Search Results Summary**:
- Windows Claude Code hooks require different command formats than Linux/WSL
- Status code 127 indicates "command not found" in shell environments
- Claude Code may need complete restart to pick up new hook configurations
- PowerShell execution is often more reliable than direct Python calls on Windows

**Key Issues Identified**:
- Direct `python3` calls fail on Windows (command not found)
- Windows paths require proper escaping and format
- Claude Code hooks system has caching behavior
- UTF-8 encoding issues with emoji characters in log files

### Implemented Fixes

#### 1. Updated Python Script for Windows Compatibility
**File**: `audio_hooks.py`
- Fixed UTF-8 encoding for log files: `logging.FileHandler(LOG_FILE, encoding='utf-8')`
- Updated PowerShell path: `"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"`
- Maintained Linux compatibility while adding Windows support

#### 2. Created Windows Hook Wrappers
**Files Created**:
- `hook_wrapper.bat` - Windows batch file wrapper
- `hook_wrapper.ps1` - PowerShell wrapper script (RECOMMENDED)

**PowerShell Wrapper** (`hook_wrapper.ps1`):
```powershell
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
try {
    $pythonPath = "python"
    $scriptPath = "C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.claude\audio_hooks.py"
    if ($Arguments) {
        & $pythonPath $scriptPath $Arguments
    } else {
        & $pythonPath $scriptPath
    }
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Error "Hook script failed with exit code: $exitCode"
        exit $exitCode
    }
} catch {
    Write-Error "PowerShell hook wrapper failed: $($_.Exception.Message)"
    exit 1
}
```

#### 3. Updated Hook Configuration
**File**: `.claude/settings.local.json`

**BEFORE** (Linux format):
```json
"command": "python3 /home/anteb/thesis_project/.claude/audio_hooks.py"
```

**AFTER** (Windows format):
```json
"command": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\.claude\\hook_wrapper.ps1\""
```

### Testing Results
✅ **PowerShell wrapper tested successfully**:
```bash
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.claude\hook_wrapper.ps1" Test
```
Output:
```json
{
  "allow": true,
  "message": "Hook processed (filtered): PreToolUse"
}
```

❌ **Claude Code still uses cached configuration** - requires restart to pick up changes

### Current Status: PENDING USER TEST

**What's Fixed**:
- ✅ Python script Windows compatibility 
- ✅ PowerShell wrapper working
- ✅ Updated hook configuration
- ✅ UTF-8 encoding issues resolved

**What Needs Testing**:
- ⏳ Complete Claude Code restart to clear configuration cache
- ⏳ Verification that hooks execute properly during Claude Code operations
- ⏳ Audio playback functionality on Windows

**Next Steps for User**:
1. **Completely restart Claude Code** (close IDE and reopen)
2. **Test hook execution** by triggering Stop or Notification events
3. **Verify audio playback** works with Windows PowerShell integration
4. **Report results** for final troubleshooting if needed

---

## New Claude Code Hooks Features Guide

This section documents the new Claude Code hooks features introduced in recent updates:

1. **PermissionDecision** exposed to hooks (including "ask")
2. **UserPromptSubmit** now supports `additionalContext` in advanced JSON output

⚠️ **Note**: These configurations show Linux paths. For Windows, use the PowerShell wrapper format documented above.

## Overview

These new features provide more granular control over Claude Code's behavior and enable richer context injection into conversations.

## 1. PermissionDecision Hook with "ask" Functionality

### What's New

The PermissionDecision hook can now:
- **Intercept permission requests** before they reach the user
- **Make custom permission decisions** based on context
- **Use "ask" decision** to request user permission with custom prompts
- **Provide rich context** for permission decisions

### Configuration

Add to your `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PermissionDecision": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/anteb/thesis_project/.claude/permission_decision_example.py"
          }
        ]
      }
    ]
  }
}
```

### Usage Examples

#### Example 1: Auto-Allow Safe Operations

```python
def handle_permission_decision(hook_data):
    tool_name = hook_data.get("tool_name", "")
    
    if tool_name in ["Read", "LS", "Glob", "TodoWrite"]:
        return {
            "decision": "allow",
            "message": f"✅ Auto-approved safe operation: {tool_name}",
            "additionalContext": {
                "auto_approved": True,
                "reason": "safe_operation"
            }
        }
```

#### Example 2: Ask for Dangerous Operations

```python
def handle_permission_decision(hook_data):
    tool_input = hook_data.get("tool_input", {})
    command = tool_input.get("command", "")
    
    if "rm -rf" in command:
        return {
            "decision": "ask",  # New "ask" functionality
            "message": "⚠️ Dangerous operation detected",
            "prompt": f"This will execute: {command}. Are you sure?",
            "additionalContext": {
                "risk_level": "high",
                "operation_type": "destructive",
                "safer_alternatives": ["Use rm -i for interactive deletion"]
            }
        }
```

#### Example 3: Context-Aware Decisions

```python
def handle_permission_decision(hook_data):
    project_context = get_current_project_state()
    
    if project_context.get("has_uncommitted_changes") and "git push" in str(hook_data):
        return {
            "decision": "ask",
            "message": "🔍 Git push with uncommitted changes",
            "prompt": "You have uncommitted changes. Push anyway?",
            "additionalContext": {
                "git_status": project_context["git_info"],
                "recommendation": "Consider committing changes first"
            }
        }
```

### Decision Types

- **`"allow"`**: Auto-approve the operation
- **`"deny"`**: Block the operation
- **`"ask"`**: Request user permission with custom prompt
- **`"default"`**: Use standard Claude Code permission flow

## 2. UserPromptSubmit with additionalContext

### What's New

UserPromptSubmit hooks can now provide rich additional context through advanced JSON output with the `additionalContext` field.

### Configuration

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/anteb/thesis_project/.claude/user_prompt_submit_example.py"
          }
        ]
      }
    ]
  }
}
```

### Usage Examples

#### Example 1: Project Context Injection

```python
def handle_user_prompt_submit(hook_data):
    user_prompt = hook_data.get("user_prompt", "")
    
    if "implement" in user_prompt.lower():
        return {
            "decision": "continue",
            "message": "✨ Enhanced with project context",
            "additionalContext": {
                "project_state": {
                    "current_branch": "project_set_up",
                    "framework": "PRP methodology",
                    "recent_changes": get_recent_files()
                },
                "coding_context": {
                    "languages": ["Python", "JavaScript"],
                    "standards": "PEP 8, under 500 lines per file",
                    "recommended_approach": "Use PRP for complex features"
                },
                "suggestions": [
                    "Consider using /create-base-prp for implementation",
                    "Run validation gates after implementation"
                ]
            }
        }
```

#### Example 2: Security Analysis

```python
def handle_user_prompt_submit(hook_data):
    user_prompt = hook_data.get("user_prompt", "")
    security_analysis = analyze_security_risk(user_prompt)
    
    if security_analysis["risk_level"] == "high":
        return {
            "decision": "block",
            "message": "❌ Security risk detected",
            "additionalContext": {
                "security_analysis": security_analysis,
                "detected_patterns": ["rm -rf", "sudo"],
                "recommendation": "Please rephrase without dangerous commands"
            }
        }
```

#### Example 3: Context-Aware Enhancement

```python
def handle_user_prompt_submit(hook_data):
    context = generate_comprehensive_context(hook_data)
    
    return {
        "decision": "continue",
        "additionalContext": {
            "timestamp": datetime.now().isoformat(),
            "prompt_analysis": {
                "complexity_score": 8,
                "detected_intents": ["code_creation", "testing"],
                "has_code_snippets": True
            },
            "environment_info": {
                "working_directory": "/home/anteb/thesis_project",
                "git_branch": "project_set_up",
                "available_tools": ["mcp__perplexity-mcp__search"]
            },
            "recommendations": {
                "research_tools": "Use context7 for documentation",
                "validation": "Run tests after implementation"
            }
        }
    }
```

## Integration with Your Current Setup

### Adding to Existing Hooks

Your current `audio_hooks.py` can be extended to support these new features:

```python
# In your existing ClaudeHooksHandler class
def handle_permission_decision(self, hook_data):
    """Handle new PermissionDecision events"""
    # Your permission logic here
    decision = self.make_permission_decision(hook_data)
    
    # Play appropriate sound based on decision
    if decision["decision"] == "ask":
        self.audio_manager.play_sound("permission_request")
    elif decision["decision"] == "allow":
        self.audio_manager.play_sound("permission_granted")
    
    return decision

def handle_user_prompt_enhanced(self, hook_data):
    """Handle UserPromptSubmit with additionalContext"""
    context = self.generate_context(hook_data)
    
    # Play context-aware sound
    if context.get("complexity_score", 0) > 7:
        self.audio_manager.play_sound("complex_request")
    
    return {
        "decision": "continue",
        "additionalContext": context
    }
```

## Testing the New Features

### Test PermissionDecision

```bash
# Test with dangerous command
python3 /home/anteb/thesis_project/.claude/permission_decision_example.py Bash "rm -rf /tmp/test"

# Test with safe command  
python3 /home/anteb/thesis_project/.claude/permission_decision_example.py Read "test.txt"
```

### Test UserPromptSubmit

```bash
# Test with coding request
python3 /home/anteb/thesis_project/.claude/user_prompt_submit_example.py "implement a new feature for user authentication"

# Test with research request
python3 /home/anteb/thesis_project/.claude/user_prompt_submit_example.py "search for the latest Python best practices"
```

## Real-World Use Cases

### 1. Smart Permission Management

- **Auto-approve** safe, frequent operations (Read, LS, TodoWrite)
- **Request confirmation** for destructive operations (rm, git push --force)
- **Block** operations that violate security policies
- **Provide alternatives** for risky commands

### 2. Context-Rich Conversations

- **Inject project state** into coding requests
- **Add environment information** for debugging help
- **Provide relevant documentation** links
- **Suggest appropriate tools** based on request type

### 3. Enhanced Workflows

- **PRP methodology integration**: Suggest using PRPs for complex features
- **Git workflow awareness**: Check branch status before operations
- **Quality assurance**: Remind about testing and validation
- **Security compliance**: Flag potential security issues

## Advanced Configuration

### Combined Hook Setup

#### Windows Configuration (CURRENT):
```json
{
  "hooks": {
    "PermissionDecision": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\.claude\\hook_wrapper.ps1\""
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "*", 
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\.claude\\hook_wrapper.ps1\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "powershell.exe -ExecutionPolicy Bypass -File \"C:\\Users\\anteb\\Desktop\\Courses\\Projects\\thesis_project\\.claude\\hook_wrapper.ps1\""
          }
        ]
      }
    ]
  }
}
```

#### Linux/WSL Configuration (LEGACY):
```json
{
  "hooks": {
    "PermissionDecision": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/anteb/thesis_project/.claude/permission_decision_example.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "*", 
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/anteb/thesis_project/.claude/user_prompt_submit_example.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/anteb/thesis_project/.claude/audio_hooks.py"
          }
        ]
      }
    ]
  }
}
```

### Conditional Processing

Both hooks support conditional processing based on:
- **Tool types** (Bash, Write, Edit, etc.)
- **Content analysis** (security patterns, complexity)
- **Project context** (git status, file types, recent activity)
- **User patterns** (frequent operations, preferences)

## Debugging and Logging

Both example implementations include comprehensive logging:

```bash
# View permission decision logs
tail -f /home/anteb/thesis_project/.claude/permission_hooks.log

# View prompt context logs  
tail -f /home/anteb/thesis_project/.claude/prompt_context_hooks.log

# View combined hook activity
tail -f /home/anteb/thesis_project/.claude/hooks.log
```

## Best Practices

1. **Security First**: Always validate input and sanitize dangerous operations
2. **Context Awareness**: Use project state to make intelligent decisions
3. **User Experience**: Provide clear messages and helpful suggestions
4. **Performance**: Keep hook processing fast to avoid delays
5. **Logging**: Maintain detailed logs for debugging and analysis
6. **Fallback Handling**: Always provide fallback behavior for errors

## Conclusion

These new Claude Code hooks features provide powerful capabilities for:
- **Intelligent permission management** with custom decision logic
- **Rich context injection** for enhanced AI conversations  
- **Improved security** through automated analysis and blocking
- **Better user experience** through smart automation and helpful prompts

The examples provided demonstrate practical implementations that can be adapted to your specific needs and workflows.