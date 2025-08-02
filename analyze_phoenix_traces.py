"""
Analyze Phoenix traces to verify our pharmaceutical workflow data.
"""

import logging
import phoenix as px
import pandas as pd
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_traces():
    """Analyze Phoenix traces for pharmaceutical workflows."""
    logger.info("Connecting to Phoenix...")
    
    # Connect to Phoenix
    client = px.Client()
    
    # Query spans
    logger.info("Querying spans...")
    spans_df = client.query_spans()
    
    logger.info(f"\nTotal spans found: {len(spans_df)}")
    
    # Analyze span types
    if 'name' in spans_df.columns:
        span_types = spans_df['name'].value_counts().head(10)
        logger.info("\nTop 10 span types:")
        for name, count in span_types.items():
            logger.info(f"  {name}: {count}")
    
    # Look for pharmaceutical workflow traces
    if 'attributes' in spans_df.columns:
        # Filter for workflow spans
        workflow_spans = spans_df[spans_df['name'].str.contains('workflow', case=False, na=False)]
        logger.info(f"\nWorkflow spans found: {len(workflow_spans)}")
        
        # Look for GAMP categorization
        gamp_spans = spans_df[spans_df['name'].str.contains('gamp|categorization', case=False, na=False)]
        logger.info(f"GAMP/Categorization spans found: {len(gamp_spans)}")
        
        # Look for test workflow spans
        test_spans = spans_df[spans_df['name'].str.contains('test', case=False, na=False)]
        logger.info(f"Test spans found: {len(test_spans)}")
    
    # Time analysis
    if 'start_time' in spans_df.columns:
        spans_df['start_time'] = pd.to_datetime(spans_df['start_time'])
        latest_span = spans_df['start_time'].max()
        earliest_span = spans_df['start_time'].min()
        
        logger.info(f"\nTime range:")
        logger.info(f"  Earliest span: {earliest_span}")
        logger.info(f"  Latest span: {latest_span}")
        logger.info(f"  Time span: {latest_span - earliest_span}")
        
        # Recent activity
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_spans = spans_df[spans_df['start_time'] > one_hour_ago]
        logger.info(f"\nSpans in last hour: {len(recent_spans)}")
    
    # Look for our test traces
    if len(spans_df) > 0:
        # Check for our test workflow traces
        test_workflow_spans = spans_df[spans_df['name'].str.contains('test-workflow', na=False)]
        if len(test_workflow_spans) > 0:
            logger.info(f"\nOur test workflow spans found: {len(test_workflow_spans)}")
            logger.info("SUCCESS: Our test traces are visible in Phoenix!")
        
    # Export sample data
    if len(spans_df) > 0:
        sample = spans_df.head(5)
        logger.info("\nSample span data:")
        for col in ['name', 'span_kind', 'start_time']:
            if col in sample.columns:
                logger.info(f"\n{col}:")
                for val in sample[col]:
                    logger.info(f"  {val}")
    
    return spans_df

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PHOENIX TRACE ANALYSIS")
    logger.info("=" * 60)
    
    try:
        df = analyze_traces()
        logger.info("\nAnalysis complete!")
        logger.info(f"Data accessible: YES")
        logger.info(f"Total spans available: {len(df)}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        
    logger.info("=" * 60)