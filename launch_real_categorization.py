#!/usr/bin/env python3
"""
Launch the real GAMP-5 categorization workflow.

This script launches the actual categorization workflow from main/src/core/categorization_workflow.py
with proper output controls to prevent terminal overflow.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add main to path and change working directory
main_path = Path(__file__).parent / "main"
sys.path.insert(0, str(main_path))

# Change to main directory to make relative imports work
original_cwd = os.getcwd()
os.chdir(str(main_path))

# Import the real workflow
from src.core.categorization_workflow import run_categorization_workflow


def setup_controlled_logging():
    """Setup logging with output controls to prevent terminal overflow."""
    # Configure root logger to WARNING level to prevent excessive output
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger("llama_index").setLevel(logging.WARNING)
    logging.getLogger("src").setLevel(logging.INFO)  # Our code - show info
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def load_environment():
    """Load environment variables from .env file."""
    from dotenv import load_dotenv
    
    # Load from parent directory since we change to main/
    env_path = Path("../.env")
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
    
    # Verify OpenAI API key is loaded
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OpenAI API key loaded: {openai_key[:8]}...{openai_key[-4:]}")
    else:
        print("❌ OpenAI API key not loaded!")
        return False
    return True


def truncate_output(text: str, max_length: int = 2000) -> str:
    """Truncate output to prevent overflow."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... [TRUNCATED - {len(text) - max_length} more characters]"


async def run_md_categorization():
    """Run categorization on the MD test data."""
    print("🚀 Starting GAMP-5 Categorization Workflow")
    print("=" * 50)
    
    # Read the simple test data first (adjust path since we're in main/ directory now)
    test_data_path = Path("../simple_test_data.md")
    if not test_data_path.exists():
        print(f"❌ Test data not found: {test_data_path}")
        return
    
    print(f"📄 Reading test data from: {test_data_path}")
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_content = f.read()
    
    print(f"📊 Content length: {len(test_content)} characters")
    
    # Configure workflow with longer timeout for real LLM processing
    workflow_config = {
        'timeout': 120,  # 2 minutes for real API calls
        'verbose': True,  # Enable verbose to see what's happening
        'enable_error_handling': True,
        'confidence_threshold': 0.60,
        'retry_attempts': 1,  # Reduce retries to avoid timeout
        'enable_document_processing': False  # Disable to reduce complexity for first test
    }
    
    print("\n🔧 Workflow Configuration:")
    for key, value in workflow_config.items():
        print(f"  {key}: {value}")
    
    print("\n🔄 Running categorization workflow...")
    
    try:
        # Run the real workflow
        result = await run_categorization_workflow(
            urs_content=test_content,
            document_name="simple_test_data.md",
            document_version="1.0",
            author="test_system",
            **workflow_config
        )
        
        print("\n✅ Workflow completed successfully!")
        print("=" * 50)
        
        # Extract and display results safely
        if result and 'result' in result:
            workflow_result = result['result']
            summary = workflow_result.get('summary', {})
            
            print("📋 CATEGORIZATION RESULTS:")
            print(f"  Category: {summary.get('category', 'Unknown')}")
            print(f"  Confidence: {summary.get('confidence', 0):.2%}")
            print(f"  Review Required: {summary.get('review_required', 'Unknown')}")
            print(f"  Is Fallback: {summary.get('is_fallback', 'Unknown')}")
            print(f"  Duration: {summary.get('workflow_duration_seconds', 0):.2f}s")
            
            # Show categorization event details (truncated)
            if 'categorization_event' in workflow_result:
                cat_event = workflow_result['categorization_event']
                print(f"\n📝 JUSTIFICATION:")
                justification = getattr(cat_event, 'justification', 'Not available')
                print(f"  {truncate_output(justification, 500)}")
                
                print(f"\n🎯 RISK ASSESSMENT:")
                risk_assessment = getattr(cat_event, 'risk_assessment', {})
                for key, value in risk_assessment.items():
                    if isinstance(value, str):
                        print(f"  {key}: {truncate_output(value, 200)}")
                    else:
                        print(f"  {key}: {value}")
            
            # Show consultation requirements if any
            if workflow_result.get('consultation_event'):
                print(f"\n⚠️  CONSULTATION REQUIRED:")
                consultation = workflow_result['consultation_event']
                print(f"  Type: {getattr(consultation, 'consultation_type', 'Unknown')}")
                print(f"  Urgency: {getattr(consultation, 'urgency', 'Unknown')}")
        
        print("\n🎉 Real workflow execution completed!")
        return result
        
    except Exception as e:
        print(f"\n❌ Workflow failed with error:")
        error_msg = str(e)
        print(f"  {truncate_output(error_msg, 500)}")
        print(f"\nError type: {type(e).__name__}")
        return None


async def main():
    """Main execution function."""
    # Setup controlled environment
    setup_controlled_logging()
    
    # Load environment variables first
    if not load_environment():
        print("\n❌ Environment setup failed. Cannot proceed without API key.")
        return None
    
    # Set environment variable to limit output
    os.environ['MAX_CONSOLE_OUTPUT'] = '100000'  # 100KB limit
    os.environ['LOG_LEVEL'] = 'WARNING'
    os.environ['VERBOSE_MODE'] = 'false'
    
    print("\n🌟 GAMP-5 Real Workflow Launch")
    print("Configured with output controls to prevent terminal overflow")
    print()
    
    # Run the categorization
    result = await run_md_categorization()
    
    if result:
        print("\n✅ Success! The real workflow executed successfully.")
        print("Ready to process PDF data next.")
    else:
        print("\n❌ Workflow execution failed. Check the error above.")
    
    return result


if __name__ == "__main__":
    # Run with asyncio
    asyncio.run(main())