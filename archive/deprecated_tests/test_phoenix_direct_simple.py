"""
Simple test of Phoenix direct client access without Unicode.
"""

import logging

import phoenix as px
from phoenix.client import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_access():
    """Test direct Phoenix client access."""
    logger.info("Testing Phoenix direct client access...")

    try:
        # Method 1: Using phoenix.client
        logger.info("Method 1: Using phoenix.client.Client")
        client = Client(base_url="http://localhost:6006")

        # Try to access projects
        try:
            projects = client.projects
            logger.info(f"  Client initialized, projects attribute exists: {hasattr(client, 'projects')}")
        except Exception as e:
            logger.error(f"  Failed to access projects: {e}")

    except Exception as e:
        logger.error(f"Method 1 failed: {e}")

    try:
        # Method 2: Using phoenix.Client
        logger.info("\nMethod 2: Using phoenix.Client")
        px_client = px.Client()
        logger.info(f"  Phoenix client initialized: {px_client}")

        # Try to get spans DataFrame
        try:
            # This is the documented method for Phoenix
            spans_df = px_client.query_spans()
            logger.info(f"  Retrieved {len(spans_df)} spans")

            if len(spans_df) > 0:
                logger.info("  SUCCESS: Can access trace data via direct client!")
                logger.info(f"  Sample span columns: {list(spans_df.columns[:5])}")
                return True
        except Exception as e:
            logger.error(f"  Failed to query spans: {e}")

    except Exception as e:
        logger.error(f"Method 2 failed: {e}")

    try:
        # Method 3: Using launch_app
        logger.info("\nMethod 3: Testing local Phoenix access")
        session = px.launch_app()
        logger.info(f"  Phoenix session: {session}")

        # Get DataFrame from session
        try:
            df = session.query_spans()
            logger.info(f"  Retrieved {len(df)} spans from session")
            return True
        except Exception as e:
            logger.error(f"  Failed to query from session: {e}")

    except Exception as e:
        logger.error(f"Method 3 failed: {e}")

    return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PHOENIX DIRECT CLIENT TEST")
    logger.info("=" * 60)

    success = test_direct_access()

    if success:
        logger.info("\nSUCCESS: Found working method to access Phoenix data!")
    else:
        logger.info("\nFAILED: Could not access Phoenix data via direct client")

    logger.info("=" * 60)
