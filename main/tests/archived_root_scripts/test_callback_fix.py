#!/usr/bin/env python3
"""
Test ChromaDB callback manager fix specifically.
Tests if context provider can now successfully create embeddings without callback errors.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the main directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from src.agents.parallel.context_provider import create_context_provider_agent
from src.config.llm_config import LLMConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_callback_fix():
    """Test that ChromaDB embedding works with callback manager fix."""
    logger.info("Testing ChromaDB callback manager fix...")

    try:
        # Initialize context provider
        llm = LLMConfig.get_llm()
        context_provider = create_context_provider_agent(
            llm=llm,
            verbose=True,
            enable_phoenix=False
        )

        logger.info("✅ Context provider agent created successfully")

        # Test embedding creation through a query (this was failing before)
        from src.agents.parallel.models import ContextProviderRequest

        test_request = ContextProviderRequest(
            gamp_category="5",
            test_strategy="comprehensive",
            document_sections=["functional_requirements", "validation_requirements"],
            search_scope={}
        )

        logger.info(f"Testing context search for GAMP Category {test_request.gamp_category}")

        query_embedding = await asyncio.to_thread(
            context_provider.embedding_model.get_text_embedding,
            test_query
        )

        logger.info("✅ Embedding created successfully")
        logger.info(f"  Embedding dimension: {len(query_embedding) if query_embedding else 'None'}")

        return True

    except Exception as e:
        logger.error(f"❌ ChromaDB callback test failed: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return False

async def main():
    """Main test execution."""
    logger.info("🧪 TESTING CHROMADB CALLBACK MANAGER FIX")
    logger.info("=" * 50)

    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY not found - cannot test embeddings")
        return

    success = await test_callback_fix()

    if success:
        logger.info("🎉 CALLBACK FIX TEST PASSED!")
        logger.info("✅ ChromaDB embeddings working without callback errors")
    else:
        logger.error("❌ CALLBACK FIX TEST FAILED!")
        logger.error("🔧 ChromaDB callback issue still exists")

if __name__ == "__main__":
    asyncio.run(main())
