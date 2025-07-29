"""
Agent Factory for Parallel Agent Coordination

This module provides factory functions for creating and configuring the parallel
agents used in pharmaceutical test generation. It ensures consistent agent
configuration and provides a centralized interface for agent instantiation.

Key Features:
- Standardized agent creation with LLM and tool configuration
- GAMP-5 compliance configuration for all agents
- Phoenix AI instrumentation integration
- Consistent error handling and timeout configuration
"""

from typing import Any

from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI

from .context_provider import ContextProviderAgent, create_context_provider_agent
from .research_agent import ResearchAgent, create_research_agent
from .sme_agent import SMEAgent, create_sme_agent


class AgentRegistry:
    """Registry for managing parallel agent instances."""

    def __init__(self, llm: LLM | None = None, verbose: bool = False):
        """
        Initialize the agent registry.
        
        Args:
            llm: Language model for agent intelligence
            verbose: Enable verbose logging
        """
        self.llm = llm or OpenAI(model="gpt-4.1-mini-2025-04-14")
        self.verbose = verbose

        # Agent instances
        self._context_provider: ContextProviderAgent | None = None
        self._sme_agent: SMEAgent | None = None
        self._research_agent: ResearchAgent | None = None

    def get_context_provider_agent(self) -> ContextProviderAgent:
        """Get or create Context Provider Agent."""
        if self._context_provider is None:
            self._context_provider = create_context_provider_agent(
                llm=self.llm,
                verbose=self.verbose
            )
        return self._context_provider

    def get_sme_agent(self, specialty: str = "pharmaceutical_validation") -> SMEAgent:
        """Get or create SME Agent with specified specialty."""
        if self._sme_agent is None:
            self._sme_agent = create_sme_agent(
                specialty=specialty,
                llm=self.llm,
                verbose=self.verbose
            )
        return self._sme_agent

    def get_research_agent(self) -> ResearchAgent:
        """Get or create Research Agent."""
        if self._research_agent is None:
            self._research_agent = create_research_agent(
                llm=self.llm,
                verbose=self.verbose
            )
        return self._research_agent

    def get_agent_by_type(self, agent_type: str, **kwargs) -> Any:
        """
        Get agent by type string.
        
        Args:
            agent_type: Agent type identifier
            **kwargs: Additional agent configuration
            
        Returns:
            Agent instance
        """
        if agent_type == "context_provider":
            return self.get_context_provider_agent()
        if agent_type == "sme_agent":
            specialty = kwargs.get("specialty", "pharmaceutical_validation")
            return self.get_sme_agent(specialty=specialty)
        if agent_type == "research_agent":
            return self.get_research_agent()
        raise ValueError(f"Unknown agent type: {agent_type}")


def create_agents_for_coordination(
    llm: LLM | None = None,
    verbose: bool = False,
    enable_phoenix: bool = True
) -> dict[str, Any]:
    """
    Create all agents needed for parallel coordination.
    
    Args:
        llm: Language model for all agents
        verbose: Enable verbose logging
        enable_phoenix: Enable Phoenix AI instrumentation
        
    Returns:
        Dictionary mapping agent types to agent instances
    """
    if llm is None:
        llm = OpenAI(model="gpt-4.1-mini-2025-04-14")

    agents = {
        "context_provider": create_context_provider_agent(
            llm=llm,
            verbose=verbose,
            enable_phoenix=enable_phoenix
        ),
        "sme_agent": create_sme_agent(
            specialty="pharmaceutical_validation",
            llm=llm,
            verbose=verbose,
            enable_phoenix=enable_phoenix
        ),
        "research_agent": create_research_agent(
            llm=llm,
            verbose=verbose,
            enable_phoenix=enable_phoenix
        )
    }

    return agents


def create_agent_registry(
    llm: LLM | None = None,
    verbose: bool = False
) -> AgentRegistry:
    """
    Create agent registry for managing agent instances.
    
    Args:
        llm: Language model for agents
        verbose: Enable verbose logging
        
    Returns:
        Configured AgentRegistry instance
    """
    return AgentRegistry(llm=llm, verbose=verbose)
