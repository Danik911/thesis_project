#!/usr/bin/env python3
"""
Test script for new Claude Code hooks features
Tests both PermissionDecision and UserPromptSubmit with additionalContext
"""

import json
import subprocess
import sys
from pathlib import Path

def test_permission_decision():
    """Test PermissionDecision hook with various scenarios"""
    print("🧪 Testing PermissionDecision Hook")
    print("=" * 50)
    
    test_cases = [
        ("Safe Read Operation", ["Read", "test.txt"]),
        ("Dangerous Delete", ["Bash", "rm -rf /tmp/test"]),
        ("Git Push with Context", ["Bash", "git push origin main"]),
        ("Sudo Command", ["Bash", "sudo apt update"]),
        ("Todo Update", ["TodoWrite", "update tasks"]),
    ]
    
    script_path = Path(__file__).parent / "permission_decision_example.py"
    
    for test_name, args in test_cases:
        print(f"\n📋 Test: {test_name}")
        print(f"   Command: {' '.join(args)}")
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)] + args,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                decision = response.get("decision", "unknown")
                message = response.get("message", "No message")
                
                print(f"   ✅ Decision: {decision}")
                print(f"   📝 Message: {message}")
                
                if "additionalContext" in response:
                    context = response["additionalContext"]
                    print(f"   🔍 Context keys: {list(context.keys())}")
            else:
                print(f"   ❌ Error: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 50)

def test_user_prompt_submit():
    """Test UserPromptSubmit hook with additionalContext"""
    print("\n🧪 Testing UserPromptSubmit Hook")
    print("=" * 50)
    
    test_prompts = [
        ("Simple Question", "What is the current time?"),
        ("Code Implementation", "implement a user authentication system with JWT tokens"),
        ("File Operation", "read the configuration file and update the database settings"),
        ("Git Operation", "commit these changes and push to the main branch"),
        ("Research Request", "search for the latest Python async programming best practices"),
        ("Dangerous Command", "delete all files in the temp directory using rm -rf"),
        ("Complex Multi-step", "analyze the codebase, identify performance bottlenecks, implement optimizations, and run comprehensive tests to verify improvements"),
    ]
    
    script_path = Path(__file__).parent / "user_prompt_submit_example.py"
    
    for test_name, prompt in test_prompts:
        print(f"\n📋 Test: {test_name}")
        print(f"   Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path), prompt],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                decision = response.get("decision", "unknown")
                message = response.get("message", "No message")
                
                print(f"   ✅ Decision: {decision}")
                print(f"   📝 Message: {message}")
                
                if "additionalContext" in response:
                    context = response["additionalContext"]
                    print(f"   🔍 Context Analysis:")
                    
                    # Show key context information
                    if "prompt_analysis" in context:
                        analysis = context["prompt_analysis"]
                        print(f"      - Complexity Score: {analysis.get('complexity_score', 'N/A')}")
                        print(f"      - Detected Intents: {analysis.get('detected_intents', [])}")
                    
                    if "security_analysis" in context:
                        security = context["security_analysis"]
                        print(f"      - Security Risk: {security.get('risk_level', 'N/A')}")
                        if security.get("detected_patterns"):
                            print(f"      - Risk Patterns: {security['detected_patterns']}")
                    
                    if "suggestions" in context:
                        suggestions = context["suggestions"]
                        if suggestions:
                            print(f"      - Suggestions: {suggestions[:2]}")  # Show first 2
                            
            else:
                print(f"   ❌ Error: {result.stderr}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 50)

def test_integration():
    """Test integration scenarios"""
    print("\n🧪 Testing Integration Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Coding Request with File Operations",
            "description": "Test how both hooks work together for coding tasks",
            "prompt": "create a new Python module for user management and write tests",
            "expected_permission": "Write operation will be requested",
            "expected_context": "Coding context with project standards"
        },
        {
            "name": "Git Workflow Integration", 
            "description": "Test git operations with project context",
            "prompt": "commit all changes and push to remote repository",
            "expected_permission": "Git operations may require confirmation",
            "expected_context": "Git status and branch information"
        },
        {
            "name": "Security-Sensitive Operation",
            "description": "Test security analysis and permission flow",
            "prompt": "delete temporary files using sudo rm -rf /tmp/*",
            "expected_permission": "High-risk operation will be blocked or require explicit approval",
            "expected_context": "Security analysis with risk patterns"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Prompt: {scenario['prompt']}")
        print(f"   Expected Permission: {scenario['expected_permission']}")
        print(f"   Expected Context: {scenario['expected_context']}")
        
        # Test UserPromptSubmit first
        prompt_script = Path(__file__).parent / "user_prompt_submit_example.py"
        try:
            result = subprocess.run(
                [sys.executable, str(prompt_script), scenario['prompt']],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                print(f"   📤 Prompt Processing: {response.get('decision', 'unknown')}")
                
                context = response.get("additionalContext", {})
                if "security_analysis" in context:
                    risk = context["security_analysis"].get("risk_level", "none")
                    print(f"   🔒 Security Risk: {risk}")
                
        except Exception as e:
            print(f"   ❌ Prompt test failed: {e}")
    
    print("\n" + "=" * 50)

def show_configuration_example():
    """Show how to configure the new hooks"""
    print("\n⚙️  Configuration Example")
    print("=" * 50)
    
    config = {
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
            # Keep existing hooks
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
    
    print("Add this to your .claude/settings.local.json:")
    print(json.dumps(config, indent=2))
    print("\n📝 Note: This preserves your existing audio hooks while adding the new functionality.")

def main():
    """Run all tests"""
    print("🚀 Claude Code New Hooks Features Test Suite")
    print("=" * 60)
    
    # Check if example files exist
    base_dir = Path(__file__).parent
    permission_script = base_dir / "permission_decision_example.py"
    prompt_script = base_dir / "user_prompt_submit_example.py"
    
    missing_files = []
    if not permission_script.exists():
        missing_files.append(str(permission_script))
    if not prompt_script.exists():
        missing_files.append(str(prompt_script))
    
    if missing_files:
        print(f"❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease run the examples creation first.")
        return
    
    try:
        # Run tests
        test_permission_decision()
        test_user_prompt_submit()
        test_integration()
        show_configuration_example()
        
        print(f"\n✅ Test suite completed!")
        print(f"📊 View detailed logs at:")
        print(f"   - Permission logs: {base_dir}/permission_hooks.log")
        print(f"   - Prompt context logs: {base_dir}/prompt_context_hooks.log")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")

if __name__ == "__main__":
    main()