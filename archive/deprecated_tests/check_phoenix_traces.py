"""
Check Phoenix traces using GraphQL to verify data is accessible.
"""

import json
import logging

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_phoenix_traces():
    """Query Phoenix for trace data."""
    logger.info("Checking Phoenix traces...")

    # Query for recent traces
    query = """
    query RecentTraces {
        projects {
            edges {
                node {
                    name
                    traceCount
                    traces(first: 5) {
                        edges {
                            node {
                                traceId
                                startTime
                                latencyMs
                                rootSpan {
                                    name
                                    attributes
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    try:
        response = requests.post(
            "http://localhost:6006/graphql",
            json={"query": query},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
            else:
                # Parse results
                projects = data.get("data", {}).get("projects", {}).get("edges", [])

                for project in projects:
                    node = project.get("node", {})
                    logger.info(f"Project: {node.get('name')}")
                    logger.info(f"Total traces: {node.get('traceCount')}")

                    traces = node.get("traces", {}).get("edges", [])
                    logger.info(f"Recent traces retrieved: {len(traces)}")

                    for i, trace in enumerate(traces):
                        trace_node = trace.get("node", {})
                        logger.info(f"\nTrace {i+1}:")
                        logger.info(f"  ID: {trace_node.get('traceId')}")
                        logger.info(f"  Start: {trace_node.get('startTime')}")
                        logger.info(f"  Latency: {trace_node.get('latencyMs')}ms")

                        root_span = trace_node.get("rootSpan", {})
                        if root_span:
                            logger.info(f"  Root span: {root_span.get('name')}")
                            attrs = root_span.get("attributes", {})
                            if attrs:
                                logger.info(f"  Attributes: {json.dumps(attrs, indent=2)}")
        else:
            logger.error(f"GraphQL request failed: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to query Phoenix: {e}")

if __name__ == "__main__":
    check_phoenix_traces()
