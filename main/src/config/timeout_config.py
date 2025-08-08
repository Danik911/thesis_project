"""
Centralized timeout configuration for all agents and services.

This module provides configurable timeouts for pharmaceutical multi-agent system
components, ensuring proper timeout hierarchy and environmental overrides.

CRITICAL: NO FALLBACKS - All timeouts are explicit and configurable.
"""

import os
from typing import Dict, Any
from datetime import datetime


class TimeoutConfig:
    """Centralized timeout configuration for all agents and services."""
    
    # Default timeouts (in seconds) - optimized for OSS model performance
    DEFAULT_TIMEOUTS = {
        "openrouter_api": 300,      # Increased from 120s to 5 minutes for OSS models
        "sme_agent": 360,           # 6 minutes (buffer over API timeout)
        "oq_generator": 480,        # 8 minutes for complex pharmaceutical generation
        "context_provider": 180,    # 3 minutes for context aggregation
        "research_agent": 240,      # 4 minutes for research tasks
        "categorization": 120,      # 2 minutes for GAMP categorization
        "unified_workflow": 1800,   # 30 minutes total workflow timeout
    }
    
    @classmethod
    def get_timeout(cls, service: str) -> int:
        """
        Get timeout for specific service with environment override.
        
        Args:
            service: Service name from DEFAULT_TIMEOUTS keys
            
        Returns:
            Timeout value in seconds
            
        Raises:
            ValueError: If service name is invalid
        """
        if service not in cls.DEFAULT_TIMEOUTS:
            available_services = list(cls.DEFAULT_TIMEOUTS.keys())
            raise ValueError(
                f"Invalid service '{service}'. Available services: {available_services}"
            )
        
        env_key = f"{service.upper()}_TIMEOUT"
        default_timeout = cls.DEFAULT_TIMEOUTS[service]
        
        try:
            return int(os.getenv(env_key, default_timeout))
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid timeout value in environment variable {env_key}. "
                f"Must be integer seconds. Using default: {default_timeout}"
            ) from e
    
    @classmethod
    def get_all_timeouts(cls) -> Dict[str, int]:
        """Get all configured timeouts with environment overrides applied."""
        return {
            service: cls.get_timeout(service) 
            for service in cls.DEFAULT_TIMEOUTS.keys()
        }
    
    @classmethod
    def validate_timeouts(cls) -> Dict[str, Any]:
        """
        Validate timeout configuration for consistency and pharmaceutical compliance.
        
        Returns:
            Dictionary with validation results including issues and recommendations
        """
        timeouts = cls.get_all_timeouts()
        issues = []
        warnings = []
        recommendations = []
        
        # Critical validation: API timeout should be less than agent timeouts
        api_timeout = timeouts["openrouter_api"]
        
        if api_timeout >= timeouts["sme_agent"]:
            issues.append(
                f"OpenRouter API timeout ({api_timeout}s) should be less than "
                f"SME agent timeout ({timeouts['sme_agent']}s) to prevent API timeouts "
                f"before agent timeout handling"
            )
        
        if api_timeout >= timeouts["oq_generator"]:
            issues.append(
                f"OpenRouter API timeout ({api_timeout}s) should be less than "
                f"OQ generator timeout ({timeouts['oq_generator']}s) to prevent API timeouts "
                f"before generator timeout handling"
            )
        
        # Pharmaceutical compliance checks
        if timeouts["unified_workflow"] < 900:  # 15 minutes minimum
            warnings.append(
                f"Unified workflow timeout ({timeouts['unified_workflow']}s) is less than "
                f"recommended 15 minutes for pharmaceutical validation processes"
            )
        
        # Performance recommendations
        if api_timeout < 180:  # 3 minutes minimum for OSS models
            recommendations.append(
                f"Consider increasing OpenRouter API timeout ({api_timeout}s) to at least "
                f"180 seconds for better OSS model performance"
            )
        
        if timeouts["oq_generator"] < 300:  # 5 minutes for complex generation
            recommendations.append(
                f"Consider increasing OQ generator timeout ({timeouts['oq_generator']}s) "
                f"to at least 300 seconds for complex pharmaceutical test generation"
            )
        
        # Buffer analysis
        buffers = {}
        for agent in ["sme_agent", "oq_generator"]:
            buffer = timeouts[agent] - api_timeout
            buffers[agent] = buffer
            if buffer < 60:  # Minimum 1 minute buffer
                warnings.append(
                    f"Small timeout buffer for {agent}: {buffer}s. "
                    f"Consider increasing to at least 60s for reliable error handling"
                )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "timeouts": timeouts,
            "buffers": buffers,
            "validation_timestamp": datetime.now().isoformat()
        }
    
    @classmethod
    def get_environment_variables_help(cls) -> Dict[str, str]:
        """Get help documentation for timeout environment variables."""
        return {
            f"{service.upper()}_TIMEOUT": f"Timeout for {service} in seconds (default: {timeout}s)"
            for service, timeout in cls.DEFAULT_TIMEOUTS.items()
        }
    
    @classmethod
    def log_configuration(cls, logger) -> None:
        """Log current timeout configuration for debugging."""
        timeouts = cls.get_all_timeouts()
        validation = cls.validate_timeouts()
        
        logger.info("=== Timeout Configuration ===")
        for service, timeout in timeouts.items():
            env_var = f"{service.upper()}_TIMEOUT"
            is_overridden = env_var in os.environ
            override_marker = " (ENV)" if is_overridden else ""
            logger.info(f"  {service}: {timeout}s{override_marker}")
        
        if validation["issues"]:
            logger.error("Timeout validation issues:")
            for issue in validation["issues"]:
                logger.error(f"  - {issue}")
        
        if validation["warnings"]:
            logger.warning("Timeout validation warnings:")
            for warning in validation["warnings"]:
                logger.warning(f"  - {warning}")
        
        if validation["recommendations"]:
            logger.info("Timeout recommendations:")
            for rec in validation["recommendations"]:
                logger.info(f"  - {rec}")


# Convenience functions for common timeout operations
def get_api_timeout() -> int:
    """Get OpenRouter API timeout."""
    return TimeoutConfig.get_timeout("openrouter_api")


def get_agent_timeout(agent_type: str) -> int:
    """Get timeout for specific agent type."""
    agent_mapping = {
        "sme": "sme_agent",
        "oq": "oq_generator",
        "context": "context_provider",
        "research": "research_agent",
        "categorization": "categorization"
    }
    
    service = agent_mapping.get(agent_type, agent_type)
    return TimeoutConfig.get_timeout(service)


def validate_system_timeouts() -> bool:
    """Validate system timeout configuration and log results."""
    import logging
    logger = logging.getLogger(__name__)
    
    validation = TimeoutConfig.validate_timeouts()
    
    if validation["issues"]:
        logger.error("CRITICAL: Timeout configuration issues detected:")
        for issue in validation["issues"]:
            logger.error(f"  {issue}")
        return False
    
    if validation["warnings"]:
        logger.warning("Timeout configuration warnings:")
        for warning in validation["warnings"]:
            logger.warning(f"  {warning}")
    
    return True