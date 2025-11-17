#!/usr/bin/env python3
"""
Helper functions for Langfuse dashboard automation via Playwright MCP.

These functions generate MCP tool call instructions that Claude Code can execute.
"""

from datetime import datetime
from typing import Dict, List, Any


PROJECT_ID = "cmhuwhcfe006yad06cqfub107"
BASE_URL = f"https://cloud.langfuse.com/project/{PROJECT_ID}"


def capture_dashboard_screenshot(page: str = "traces", output_filename: str = None) -> List[Dict[str, Any]]:
    """
    Generate MCP workflow for capturing dashboard screenshot.

    Args:
        page: Dashboard page (traces, sessions, users, metrics)
        output_filename: Screenshot filename (auto-generated if None)

    Returns:
        List of MCP tool calls
    """
    if output_filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"langfuse_{page}_{timestamp}.png"

    return [
        {
            "tool": "mcp__playwright__browser_navigate",
            "url": f"{BASE_URL}/{page}"
        },
        {
            "tool": "mcp__playwright__browser_wait_for",
            "time": 5
        },
        {
            "tool": "mcp__playwright__browser_take_screenshot",
            "fullPage": True,
            "filename": output_filename
        }
    ]


def investigate_trace(trace_id: str, output_filename: str = None) -> List[Dict[str, Any]]:
    """
    Generate MCP workflow for investigating specific trace.

    Args:
        trace_id: Trace ID to investigate
        output_filename: Screenshot filename (auto-generated if None)

    Returns:
        List of MCP tool calls
    """
    if output_filename is None:
        output_filename = f"trace_{trace_id}_investigation.png"

    return [
        {
            "tool": "mcp__playwright__browser_navigate",
            "url": f"https://cloud.langfuse.com/trace/{trace_id}"
        },
        {
            "tool": "mcp__playwright__browser_wait_for",
            "time": 5
        },
        {
            "tool": "mcp__playwright__browser_take_screenshot",
            "fullPage": True,
            "filename": output_filename
        }
    ]


def extract_dashboard_metrics() -> List[Dict[str, Any]]:
    """
    Generate MCP workflow for extracting dashboard metrics.

    Returns:
        List of MCP tool calls
    """
    return [
        {
            "tool": "mcp__playwright__browser_navigate",
            "url": f"{BASE_URL}/metrics"
        },
        {
            "tool": "mcp__playwright__browser_wait_for",
            "time": 5
        },
        {
            "tool": "mcp__playwright__browser_snapshot"
        },
        {
            "tool": "mcp__playwright__browser_evaluate",
            "function": """
            () => {
                // Extract metrics from DOM
                // Note: Selectors may need adjustment based on actual Langfuse UI
                const getTextContent = (selector) => {
                    const elem = document.querySelector(selector);
                    return elem ? elem.textContent.trim() : 'N/A';
                };

                return {
                    total_traces: getTextContent('[data-testid="total-traces"]'),
                    total_cost: getTextContent('[data-testid="total-cost"]'),
                    avg_latency: getTextContent('[data-testid="avg-latency"]'),
                    timestamp: new Date().toISOString()
                };
            }
            """
        }
    ]


def navigate_and_filter(tags: List[str]) -> List[Dict[str, Any]]:
    """
    Generate MCP workflow for filtering traces by tags.

    Args:
        tags: List of tags to filter by (e.g., ["pharmaceutical", "gamp5"])

    Returns:
        List of MCP tool calls
    """
    workflow = [
        {
            "tool": "mcp__playwright__browser_navigate",
            "url": f"{BASE_URL}/traces"
        },
        {
            "tool": "mcp__playwright__browser_wait_for",
            "time": 5
        }
    ]

    # Note: Actual filter interaction depends on Langfuse UI
    # This is a placeholder pattern
    for tag in tags:
        workflow.append({
            "tool": "mcp__playwright__browser_click",
            "element": f"Tag filter: {tag}",
            "ref": f"[data-tag='{tag}']"
        })
        workflow.append({
            "tool": "mcp__playwright__browser_wait_for",
            "time": 2
        })

    workflow.append({
        "tool": "mcp__playwright__browser_take_screenshot",
        "fullPage": True,
        "filename": f"filtered_{'_'.join(tags)}.png"
    })

    return workflow


# Example usage
if __name__ == "__main__":
    print("Langfuse Dashboard Helper Functions")
    print("=" * 60)
    print()
    print("Available functions:")
    print("  - capture_dashboard_screenshot(page, output_filename)")
    print("  - investigate_trace(trace_id, output_filename)")
    print("  - extract_dashboard_metrics()")
    print("  - navigate_and_filter(tags)")
    print()
    print("Example:")
    print("  workflow = capture_dashboard_screenshot('traces')")
    print("  # Execute workflow using MCP tools in Claude Code")
