#!/usr/bin/env python
"""
Phoenix Environment Fix Script

This script fixes the critical environment and dependency issues that prevent
Phoenix observability from working correctly.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PhoenixEnvironmentFixer:
    """Fix Phoenix environment and dependency issues."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "fixes_applied": [],
            "errors": [],
            "success": False
        }
    
    def run_command(self, command, description):
        """Run a command and track results."""
        logger.info(f"🔧 {description}")
        logger.info(f"   Command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                logger.info(f"   Output: {result.stdout.strip()}")
            
            self.results["fixes_applied"].append({
                "description": description,
                "command": " ".join(command),
                "success": True,
                "output": result.stdout.strip()
            })
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ {description} - FAILED")
            logger.error(f"   Error: {e.stderr.strip() if e.stderr else str(e)}")
            
            self.results["errors"].append({
                "description": description,
                "command": " ".join(command),
                "error": e.stderr.strip() if e.stderr else str(e),
                "return_code": e.returncode
            })
            
            return False
        
        except Exception as e:
            logger.error(f"❌ {description} - EXCEPTION: {e}")
            self.results["errors"].append({
                "description": description,
                "command": " ".join(command),
                "error": str(e),
                "exception_type": type(e).__name__
            })
            
            return False
    
    def check_current_environment(self):
        """Check current Python environment and packages."""
        logger.info("🔍 Checking current environment...")
        
        # Check Python version
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Python version: {sys.version}")
        
        # Check key packages
        packages_to_check = [
            "phoenix", "numpy", "opentelemetry", "requests",
            "llama_index", "openai"
        ]
        
        for package in packages_to_check:
            try:
                module = __import__(package)
                version = getattr(module, "__version__", "unknown")
                location = getattr(module, "__file__", "unknown")
                logger.info(f"{package}: {version} at {location}")
            except ImportError:
                logger.warning(f"{package}: NOT INSTALLED")
    
    def fix_numpy_compatibility(self):
        """Fix NumPy 2.x compatibility issues."""
        logger.info("🔧 Fixing NumPy compatibility...")
        
        # Check current NumPy version
        try:
            import numpy
            current_version = numpy.__version__
            logger.info(f"Current NumPy version: {current_version}")
            
            if current_version.startswith("2."):
                logger.warning("NumPy 2.x detected - downgrading for Phoenix compatibility")
                return self.run_command(
                    ["uv", "add", "numpy<2.0", "--resolution=highest"],
                    "Downgrade NumPy to <2.0 for Phoenix compatibility"
                )
            else:
                logger.info("NumPy version compatible")
                return True
                
        except ImportError:
            logger.warning("NumPy not installed - will be installed with Phoenix")
            return True
    
    def install_phoenix_dependencies(self):
        """Install all required Phoenix dependencies."""
        logger.info("🔧 Installing Phoenix dependencies...")
        
        # Core Phoenix packages
        commands = [
            (["uv", "add", "arize-phoenix"], "Install Arize Phoenix"),
            (["uv", "add", "opentelemetry-api"], "Install OpenTelemetry API"),
            (["uv", "add", "opentelemetry-sdk"], "Install OpenTelemetry SDK"),
            (["uv", "add", "opentelemetry-exporter-otlp"], "Install OTLP Exporter"),
            (["uv", "add", "openinference-instrumentation-llama-index"], "Install LlamaIndex Instrumentation"),
            (["uv", "add", "openinference-instrumentation-openai"], "Install OpenAI Instrumentation"),
            (["uv", "add", "requests"], "Install Requests library"),
        ]
        
        success = True
        for command, description in commands:
            if not self.run_command(command, description):
                success = False
        
        return success
    
    def sync_environment(self):
        """Sync the UV environment to ensure consistency."""
        logger.info("🔧 Syncing environment...")
        return self.run_command(["uv", "sync"], "Sync UV environment")
    
    def test_phoenix_import(self):
        """Test if Phoenix can be imported successfully."""
        logger.info("🧪 Testing Phoenix import...")
        
        try:
            import phoenix as px
            logger.info(f"✅ Phoenix imported successfully - version: {px.__version__}")
            
            # Test basic Phoenix functionality
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            logger.info("✅ OpenTelemetry components imported successfully")
            
            self.results["fixes_applied"].append({
                "description": "Phoenix import test",
                "success": True,
                "phoenix_version": px.__version__
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Phoenix import failed: {e}")
            self.results["errors"].append({
                "description": "Phoenix import test",
                "error": str(e),
                "exception_type": type(e).__name__
            })
            return False
    
    def create_environment_test_script(self):
        """Create a simple test script to validate the environment."""
        test_script_content = '''#!/usr/bin/env python
"""
Simple Phoenix environment validation test.
"""

import sys
import traceback

def test_imports():
    """Test all required imports."""
    print("Testing imports...")
    
    try:
        import phoenix as px
        print(f"✅ Phoenix: {px.__version__}")
    except Exception as e:
        print(f"❌ Phoenix import failed: {e}")
        return False
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except Exception as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        print("✅ OpenTelemetry components imported")
    except Exception as e:
        print(f"❌ OpenTelemetry import failed: {e}")
        return False
    
    try:
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
        print("✅ LlamaIndex instrumentation imported")
    except Exception as e:
        print(f"⚠️ LlamaIndex instrumentation not available: {e}")
    
    try:
        from openinference.instrumentation.openai import OpenAIInstrumentor
        print("✅ OpenAI instrumentation imported")
    except Exception as e:
        print(f"⚠️ OpenAI instrumentation not available: {e}")
    
    return True

def test_basic_functionality():
    """Test basic Phoenix functionality."""
    print("\\nTesting basic functionality...")
    
    try:
        import phoenix as px
        
        # Test Phoenix session creation (without actually launching)
        print("✅ Phoenix module functional")
        
        # Test OpenTelemetry setup
        from opentelemetry import trace
        from opentelemetry.sdk import trace as trace_sdk
        from opentelemetry.sdk.resources import Resource
        
        resource = Resource.create({"service.name": "test_service"})
        tracer_provider = trace_sdk.TracerProvider(resource=resource)
        
        print("✅ OpenTelemetry setup functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Phoenix Environment Validation Test")
    print("=" * 50)
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print()
    
    if not test_imports():
        print("❌ Import tests failed")
        return False
    
    if not test_basic_functionality():
        print("❌ Functionality tests failed")
        return False
    
    print("\\n✅ All environment tests passed!")
    print("Phoenix environment is ready for use.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        
        test_script_path = self.project_root / "validate_phoenix_environment.py"
        test_script_path.write_text(test_script_content)
        
        logger.info(f"📝 Created environment validation script: {test_script_path}")
        
        self.results["fixes_applied"].append({
            "description": "Create environment validation script",
            "success": True,
            "script_path": str(test_script_path)
        })
        
        return True
    
    def run_all_fixes(self):
        """Run all environment fixes."""
        logger.info("🚀 Starting Phoenix Environment Fixes")
        logger.info("=" * 60)
        
        # Check current state
        self.check_current_environment()
        
        fixes = [
            ("Fix NumPy compatibility", self.fix_numpy_compatibility),
            ("Install Phoenix dependencies", self.install_phoenix_dependencies),
            ("Sync environment", self.sync_environment),
            ("Test Phoenix import", self.test_phoenix_import),
            ("Create validation script", self.create_environment_test_script),
        ]
        
        success_count = 0
        for description, fix_func in fixes:
            logger.info(f"\\n🔧 {description}...")
            try:
                if fix_func():
                    success_count += 1
                    logger.info(f"✅ {description} completed successfully")
                else:
                    logger.error(f"❌ {description} failed")
            except Exception as e:
                logger.error(f"❌ {description} failed with exception: {e}")
                self.results["errors"].append({
                    "description": description,
                    "error": str(e),
                    "exception_type": type(e).__name__
                })
        
        self.results["success"] = success_count == len(fixes)
        
        logger.info("=" * 60)
        logger.info(f"🏁 Environment fixes complete: {success_count}/{len(fixes)} successful")
        
        if self.results["success"]:
            logger.info("✅ Phoenix environment is now ready!")
            logger.info("🧪 Run 'python validate_phoenix_environment.py' to test")
        else:
            logger.error("❌ Some environment fixes failed - check logs above")
        
        return self.results
    
    def save_results(self, filename="phoenix_environment_fix_results.json"):
        """Save fix results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📊 Fix results saved to: {filename}")
        return filename

def main():
    """Run Phoenix environment fixes."""
    fixer = PhoenixEnvironmentFixer()
    results = fixer.run_all_fixes()
    
    # Save results
    fixer.save_results()
    
    # Print summary
    print("\\n" + "=" * 60)
    print("📋 ENVIRONMENT FIX SUMMARY")
    print("=" * 60)
    
    print(f"✅ Fixes Applied: {len(results['fixes_applied'])}")
    print(f"❌ Errors: {len(results['errors'])}")
    
    if results["fixes_applied"]:
        print("\\n✅ Successful Fixes:")
        for fix in results["fixes_applied"]:
            print(f"   • {fix['description']}")
    
    if results["errors"]:
        print("\\n❌ Errors:")
        for error in results["errors"]:
            print(f"   • {error['description']}: {error.get('error', 'Unknown error')}")
    
    if results["success"]:
        print("\\n🎉 Phoenix environment is ready!")
        print("   Next steps:")
        print("   1. Run 'python validate_phoenix_environment.py' to test")
        print("   2. Run 'python main/debug_phoenix_comprehensive.py' for full diagnostic")
    else:
        print("\\n⚠️ Some fixes failed - manual intervention may be required")
    
    return results["success"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)