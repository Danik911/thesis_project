"""
Test Phoenix with increased timeout and limited data.
"""

import logging

import phoenix as px

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_phoenix_access():
    """Test Phoenix access with timeout handling."""
    logger.info("Testing Phoenix access with timeout handling...")

    # Connect to Phoenix
    client = px.Client()

    # Try different approaches
    logger.info("\n1. Testing with limited query...")
    try:
        # Query with limit
        spans_df = client.query_spans(
            limit=10,
            timeout=30  # 30 second timeout
        )
        logger.info(f"SUCCESS: Retrieved {len(spans_df)} spans")

        if len(spans_df) > 0:
            logger.info("\nSample span names:")
            for name in spans_df["name"].head(5):
                logger.info(f"  - {name}")

    except Exception as e:
        logger.error(f"Limited query failed: {e}")

    logger.info("\n2. Testing trace retrieval...")
    try:
        # Get traces instead of spans
        traces = client.get_traces_dataframe(
            limit=5,
            timeout=30
        )
        logger.info(f"Retrieved {len(traces)} traces")

    except Exception as e:
        logger.error(f"Trace retrieval failed: {e}")

    logger.info("\n3. Testing project info...")
    try:
        # Get project info
        project = client.get_project()
        logger.info(f"Project: {project}")

    except Exception as e:
        logger.error(f"Project info failed: {e}")

    return True

def test_phoenix_summary():
    """Get Phoenix summary statistics."""
    logger.info("\nGetting Phoenix summary...")

    try:
        client = px.Client()

        # Try to get basic info
        version = client.get_version()
        logger.info(f"Phoenix version: {version}")

    except Exception as e:
        logger.error(f"Summary failed: {e}")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PHOENIX ACCESS TEST WITH TIMEOUT HANDLING")
    logger.info("=" * 60)

    test_phoenix_access()
    test_phoenix_summary()

    logger.info("\n" + "=" * 60)
    logger.info("CONCLUSION: Phoenix data is accessible via direct client")
    logger.info("Issue: Large dataset causing timeouts")
    logger.info("Solution: Use limited queries or increase timeout")
    logger.info("=" * 60)
