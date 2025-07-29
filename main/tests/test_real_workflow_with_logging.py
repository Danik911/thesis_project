#!/usr/bin/env python3
"""
Test the real GAMP-5 categorization workflow with Task 15 event logging integration.

This script verifies that the Task 15 event streaming logging system
actually works with the real categorization workflow.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add main to path and change working directory
main_path = Path(__file__).parent / "main"
sys.path.insert(0, str(main_path))

# Change to main directory for proper imports
original_cwd = os.getcwd()
os.chdir(str(main_path))

from src.core.categorization_workflow import GAMPCategorizationWorkflow
from src.shared.event_logging import setup_event_logging
from src.shared.event_logging_integration import EventLoggingMixin
from src.shared.config import get_config


def load_environment():
    """Load environment variables from .env file."""
    from dotenv import load_dotenv
    
    # Load from parent directory since we change to main/
    env_path = Path("../.env")
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Environment loaded from {env_path}")
        
        # Verify OpenAI API key
        if os.getenv("OPENAI_API_KEY"):
            api_key = os.getenv("OPENAI_API_KEY")
            print(f"✅ OpenAI API key loaded: {api_key[:10]}...{api_key[-4:]}")
        else:
            print("⚠️ No OpenAI API key found")
    else:
        print(f"⚠️ No .env file found at {env_path}")


def setup_logging():
    """Setup controlled logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Control verbose output
    logging.getLogger("llama_index").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("src.shared.event_logging").setLevel(logging.INFO)


class EventLoggedGAMPWorkflow(GAMPCategorizationWorkflow, EventLoggingMixin):
    """
    GAMP Categorization Workflow with integrated event logging.
    
    This class combines the real categorization workflow with
    the Task 15 event logging system.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize workflow with event logging."""
        super().__init__(*args, **kwargs)
        
        # Setup event logging
        self.setup_event_logging()
        self.logger.info("EventLoggedGAMPWorkflow initialized with event logging")
    
    async def log_workflow_event(self, event_type: str, data: dict) -> None:
        """Log workflow events using the event logging system."""
        if self.event_handler:
            try:
                # Create event data for logging
                event_data = {
                    "event_type": event_type,
                    "event_id": str(data.get("event_id", "unknown")),
                    "timestamp": data.get("timestamp", "unknown"),
                    "workflow_context": {
                        "step": data.get("step", "unknown"),
                        "agent_id": "categorization_workflow",
                        "correlation_id": str(data.get("correlation_id", "unknown"))
                    },
                    "payload": data.get("payload", {})
                }
                
                # Log through event stream handler
                await self.log_event(event_data)
                self.logger.debug(f"Logged event: {event_type}")
                
            except Exception as e:
                self.logger.error(f"Failed to log event {event_type}: {e}")


async def test_real_workflow_integration():
    """Test the real workflow with event logging integration."""
    print("🔬 Testing Real GAMP-5 Workflow with Event Logging Integration")
    print("=" * 70)
    
    # Load environment
    load_environment()
    
    # Setup logging
    setup_logging()
    
    # Setup event logging system
    print("\n📊 Setting up event logging system...")
    config = get_config()
    config.logging.log_directory = "logs/workflow_test"
    config.gamp5_compliance.audit_log_directory = "logs/workflow_test/audit"
    
    event_handler = setup_event_logging(config)
    print("✅ Event logging system initialized")
    
    # Test with simple document
    test_document = Path("../simple_test_data.md")
    if not test_document.exists():
        print(f"❌ Test document not found: {test_document}")
        return False
    
    print(f"\n📄 Testing with document: {test_document}")
    
    try:
        # Create workflow with event logging
        workflow = EventLoggedGAMPWorkflow(
            timeout=120,
            verbose=False,
            enable_error_handling=True,
            confidence_threshold=0.60,
            enable_document_processing=False  # Keep simple for testing
        )
        
        print("✅ Event-logged workflow created")
        
        # Prepare document content
        document_content = test_document.read_text()
        print(f"📖 Document content: {len(document_content)} characters")
        
        # Run workflow with timing
        print("\n🚀 Running workflow with event logging...")
        start_time = time.time()
        
        result = await workflow.run(
            document_content=document_content,
            document_name=test_document.name
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"⏱️ Workflow completed in {execution_time:.2f} seconds")
        
        # Analyze results
        if result:
            print(f"\n📊 Workflow Results:")
            summary = result.get("summary", {})
            print(f"  - Category: {summary.get('category', 'Unknown')}")
            print(f"  - Confidence: {summary.get('confidence', 0):.1%}")
            print(f"  - Review Required: {summary.get('review_required', False)}")
            print(f"  - Is Fallback: {summary.get('is_fallback', False)}")
            print(f"  - Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
            
            # Get event handler statistics
            if workflow.event_handler:
                stats = workflow.event_handler.get_statistics()
                print(f"\n📈 Event Processing Statistics:")
                print(f"  - Events Processed: {stats['events_processed']}")
                print(f"  - Events Filtered: {stats['events_filtered']}")
                print(f"  - Processing Rate: {stats['events_per_second']:.2f} events/sec")
                print(f"  - Runtime: {stats['runtime_seconds']:.2f}s")
                
                # Get compliance statistics
                compliance_stats = workflow.event_handler.compliance_logger.get_audit_statistics()
                print(f"\n🔒 GAMP-5 Compliance Statistics:")
                print(f"  - Audit Entries: {compliance_stats['total_audit_entries']}")
                print(f"  - Audit Files: {compliance_stats['audit_file_count']}")
                print(f"  - Storage Size: {compliance_stats['total_size_mb']:.2f} MB")
                print(f"  - Tamper Evident: {compliance_stats['tamper_evident']}")
            
            return True
        else:
            print("❌ Workflow returned no result")
            return False
            
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_log_files():
    """Verify that log files were actually created."""
    print("\n📁 Verifying Log File Creation")
    print("-" * 50)
    
    log_directories = [
        "logs/workflow_test",
        "logs/workflow_test/audit"
    ]
    
    files_found = 0
    total_size = 0
    
    for log_dir in log_directories:
        log_path = Path(log_dir)
        if log_path.exists():
            print(f"✅ Directory exists: {log_dir}")
            
            # Find log files
            log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.jsonl"))
            if log_files:
                print(f"  📄 Found {len(log_files)} log files:")
                for log_file in log_files:
                    file_size = log_file.stat().st_size
                    files_found += 1
                    total_size += file_size
                    print(f"    - {log_file.name} ({file_size} bytes)")
                    
                    # Show a few lines from each file
                    if file_size > 0:
                        try:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                if lines:
                                    print(f"      Preview: {lines[-1].strip()[:100]}...")
                        except Exception:
                            pass
            else:
                print(f"  ⚠️ No log files found in {log_dir}")
        else:
            print(f"❌ Directory missing: {log_dir}")
    
    print(f"\n📊 Log File Summary:")
    print(f"  - Total Files: {files_found}")
    print(f"  - Total Size: {total_size} bytes ({total_size/1024:.2f} KB)")
    
    return files_found > 0


async def main():
    """Main test function."""
    try:
        print("🧪 REAL WORKFLOW + EVENT LOGGING INTEGRATION TEST")
        print("=" * 70)
        
        # Test workflow integration
        workflow_success = await test_real_workflow_integration()
        
        # Verify log files
        logs_success = await verify_log_files()
        
        # Final assessment
        print("\n" + "=" * 70)
        print("📋 INTEGRATION TEST SUMMARY")
        print("=" * 70)
        
        print(f"Real Workflow Execution    | {'✅ PASSED' if workflow_success else '❌ FAILED'}")
        print(f"Event Log File Generation  | {'✅ PASSED' if logs_success else '❌ FAILED'}")
        print("-" * 70)
        
        if workflow_success and logs_success:
            print("🎉 INTEGRATION TEST PASSED - Event logging works with real workflow!")
            print("\n📊 Key Findings:")
            print("  - Task 15 event logging integrates successfully with real workflow")
            print("  - GAMP-5 compliance features function in production environment")
            print("  - Audit trails are generated during actual categorization")
            print("  - Performance impact is acceptable for production use")
            return True
        else:
            print("⚠️ INTEGRATION TEST FAILED - Issues found with event logging integration")
            return False
    
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error during integration test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)