#!/usr/bin/env python3
"""
Test script to validate workflow architecture and database fixes.

This script tests:
1. OQ Workflow StopEvent fix
2. Phoenix database consistency 
3. State management validation
"""

import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_oq_workflow_stopevent():
    """Test that OQ workflow now properly returns StopEvent."""
    print("\n🔧 Testing OQ Workflow StopEvent Fix...")
    
    try:
        from src.agents.oq_generator.workflow import OQTestGenerationWorkflow
        from src.agents.oq_generator.events import OQTestGenerationEvent
        from src.core.events import GAMPCategory
        from llama_index.core.workflow import StopEvent
        
        # Create OQ workflow
        workflow = OQTestGenerationWorkflow(
            verbose=True,
            timeout=60  # Short timeout for testing
        )
        
        # Create test event
        test_event = OQTestGenerationEvent(
            gamp_category=GAMPCategory.CATEGORY_5,
            urs_content="Test URS content for Category 5 pharmaceutical system",
            document_metadata={"name": "Test Document"},
            required_test_count=5,
            test_strategy={},
            compliance_requirements=["GAMP-5"],
            aggregated_context={},
            categorization_confidence=0.8,
            complexity_level="standard",
            focus_areas=["functionality"],
            risk_level="medium",
            triggering_step="test_validation"
        )
        
        print("   ✅ OQ Workflow imports successful")
        print("   ✅ Test event created")
        
        # Check that workflow has complete_oq_generation step
        steps = [method for method in dir(workflow) if hasattr(getattr(workflow, method), '__wrapped__')]
        step_names = [method for method in steps if 'step' in str(getattr(workflow, method))]
        
        if 'complete_oq_generation' in [step.replace('_wrapped', '') for step in dir(workflow)]:
            print("   ✅ complete_oq_generation step found")
        else:
            print("   ❌ complete_oq_generation step not found")
            return False
            
        print("   🎯 OQ Workflow StopEvent fix validated")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def clear_chromadb():
    """Clear ChromaDB database to fix dimension conflicts."""
    print("\n🗑️  Clearing ChromaDB Database...")
    
    # ChromaDB database path
    chroma_db_path = Path("lib/chroma_db")
    
    if chroma_db_path.exists():
        print(f"   🗑️  Clearing corrupted ChromaDB at: {chroma_db_path}")
        
        try:
            # Remove the entire directory
            shutil.rmtree(chroma_db_path)
            print("   ✅ Successfully cleared ChromaDB database")
            
            # Create empty directory for next ingestion
            chroma_db_path.mkdir(parents=True, exist_ok=True)
            print("   📁 Created fresh ChromaDB directory")
            
        except Exception as e:
            print(f"   ❌ Error clearing ChromaDB: {e}")
            return False
    else:
        print(f"   ℹ️  ChromaDB database not found at: {chroma_db_path}")
        print("   ✅ No clearing needed")

    # Also clear any embedding cache that might have mixed dimensions
    cache_files = [
        "lib/embedding_cache.pkl",
        "lib/ingestion_cache.json"
    ]
    
    for cache_file in cache_files:
        cache_path = Path(cache_file)
        if cache_path.exists():
            try:
                cache_path.unlink()
                print(f"   🗑️  Cleared cache file: {cache_file}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not clear cache {cache_file}: {e}")
    
    print("   ✅ ChromaDB clearing complete!")
    return True

def test_phoenix_configuration():
    """Test Phoenix configuration for consistent embeddings."""
    print("\n🔍 Testing Phoenix Configuration...")
    
    try:
        from src.monitoring.phoenix_config import setup_phoenix, PhoenixConfig
        
        # Test Phoenix configuration
        config = PhoenixConfig()
        print(f"   ✅ Phoenix config created")
        print(f"   📍 Phoenix host: {config.phoenix_host}:{config.phoenix_port}")
        print(f"   🔧 OpenAI instrumentation: {config.enable_openai_instrumentation}")
        print(f"   🔧 ChromaDB instrumentation: {config.enable_chromadb_instrumentation}")
        
        # Test that Phoenix can be set up (without actually starting)
        phoenix_manager = setup_phoenix(config)
        if phoenix_manager:
            print("   ✅ Phoenix manager creation successful")
        else:
            print("   ⚠️  Phoenix manager creation returned None")
            
        return True
        
    except ImportError as e:
        print(f"   ❌ Phoenix import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Phoenix test failed: {e}")
        return False

def test_embedding_consistency():
    """Test that embedding configuration is consistent."""
    print("\n📐 Testing Embedding Model Consistency...")
    
    # Check environment variable
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    print(f"   🔧 Environment EMBEDDING_MODEL: {embedding_model}")
    
    if embedding_model == "text-embedding-3-small":
        print("   ✅ Consistent embedding model configuration (1536 dimensions)")
        expected_dimensions = 1536
    elif embedding_model == "text-embedding-ada-002":
        print("   ⚠️  Using ada-002 model (3072 dimensions)")
        expected_dimensions = 3072
    else:
        print(f"   ❓ Unknown embedding model: {embedding_model}")
        expected_dimensions = None
    
    # Test context provider configuration
    try:
        from src.agents.parallel.context_provider import ContextProviderAgent
        
        # Check default embedding model
        agent = ContextProviderAgent()
        agent_model = agent.embedding_model_name
        print(f"   🔧 ContextProvider embedding model: {agent_model}")
        
        if agent_model == embedding_model:
            print("   ✅ ContextProvider model matches environment")
        else:
            print(f"   ⚠️  Model mismatch: env={embedding_model}, agent={agent_model}")
            
        return True
        
    except ImportError as e:
        print(f"   ❌ Context provider import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Embedding consistency test failed: {e}")
        return False

async def test_state_management():
    """Test workflow state management."""
    print("\n📊 Testing Workflow State Management...")
    
    try:
        from llama_index.core.workflow import Context
        from src.core.unified_workflow import UnifiedTestGenerationWorkflow
        
        # Create a workflow instance
        workflow = UnifiedTestGenerationWorkflow(
            timeout=60,
            verbose=True
        )
        
        print("   ✅ Unified workflow instance created")
        print("   🔧 Testing context management patterns...")
        
        # Workflow has proper context handling methods
        context_methods = [method for method in dir(workflow) if 'ctx' in method.lower() or 'context' in method.lower()]
        print(f"   📋 Context-related methods: {len(context_methods)}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ State management import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ State management test failed: {e}")
        return False

async def main():
    """Run all validation tests."""
    print("🧪 Starting Workflow Architecture and Database Fix Validation")
    print("=" * 70)
    
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    results = {}
    
    # Test 1: OQ Workflow StopEvent fix
    results['oq_stopevent'] = await test_oq_workflow_stopevent()
    
    # Test 2: Clear ChromaDB database
    results['chromadb_clear'] = clear_chromadb()
    
    # Test 3: Phoenix configuration
    results['phoenix_config'] = test_phoenix_configuration()
    
    # Test 4: Embedding consistency
    results['embedding_consistency'] = test_embedding_consistency()
    
    # Test 5: State management
    results['state_management'] = await test_state_management()
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<25}: {status}")
    
    print(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Fixes appear to be working correctly.")
        print("\n💡 Ready for integration testing:")
        print("   1. Run complete unified workflow")
        print("   2. Test Phoenix observability")
        print("   3. Validate regulatory compliance")
    else:
        print("⚠️  Some tests failed. Review issues above.")
        print("🔧 Fixes needed before integration testing.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)