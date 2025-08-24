"""
Parallel Agent Execution System

This module implements the parallel agent execution system for pharmaceutical
test generation, providing Context Provider, SME, and Research agents that
work together with the coordination infrastructure.

The agents follow LlamaIndex FunctionAgent patterns and integrate with the
existing event-driven workflow orchestration system.
"""

from .agent_factory import create_agent_registry, create_agents_for_coordination
from .context_provider import ContextProviderAgent, create_context_provider_agent
from .research_agent import ResearchAgent, create_research_agent
from .sme_agent import SMEAgent, create_sme_agent

__all__ = [
    "ContextProviderAgent",
    "ResearchAgent",
    "SMEAgent",
    "create_agent_registry",
    "create_agents_for_coordination",
    "create_context_provider_agent",
    "create_research_agent",
    "create_sme_agent",
]
