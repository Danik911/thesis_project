"""
Planner Agent Package - Test Generation Orchestrator

This package implements the Test Generation Orchestrator Agent that serves as the central
coordinator for pharmaceutical test generation workflows. It creates planning context,
determines required test types based on GAMP-5 category, and orchestrates parallel 
execution of specialized agents.

Key Components:
- PlannerAgent: Core orchestration agent with test strategy generation
- PlannerAgentWorkflow: LlamaIndex workflow for event-driven coordination
- GAMPStrategyGenerator: GAMP-category-specific test strategy logic
- AgentCoordinator: Parallel agent execution coordination

The planner agent follows established patterns from the categorization agent while
extending functionality for complex test planning and multi-agent coordination.
"""

from .agent import PlannerAgent, create_planner_agent
from .coordination import AgentCoordinator
from .gamp_strategies import (
    GAMP_CATEGORY_STRATEGIES,
    determine_compliance_requirements,
    determine_sme_requirements,
    get_category_strategy,
)
from .strategy_generator import GAMPStrategyGenerator
from .workflow import PlannerAgentWorkflow

__all__ = [
    "GAMP_CATEGORY_STRATEGIES",
    "AgentCoordinator",
    "GAMPStrategyGenerator",
    "PlannerAgent",
    "PlannerAgentWorkflow",
    "create_planner_agent",
    "determine_compliance_requirements",
    "determine_sme_requirements",
    "get_category_strategy"
]
