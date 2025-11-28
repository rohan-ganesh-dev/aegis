"""
Aegis Agents

This module contains all agent implementations.
"""

from aegis.agents.base import AgentMessage, AgentResponse, BaseAgent

# Core agents
from aegis.agents.growth import GrowthAgent
from aegis.agents.integration import IntegrationAgent
from aegis.agents.proactive import ProactiveAgent
from aegis.agents.supervisor import SupervisorAgent

# Multi-agent architecture (NEW)
from aegis.agents.onboarding_agent import OnboardingAgent
from aegis.agents.orchestrator_agent import OrchestratorAgent
from aegis.agents.query_resolution_agent import QueryResolutionAgent

# Legacy agents (kept for backward compatibility)
from aegis.agents.jira_chargebee_agent import JiraChargebeeAgent
from aegis.agents.onboarding import OnboardingAgent as LegacyOnboardingAgent

__all__ = [
    # Base classes
    "AgentMessage",
    "AgentResponse",
    "BaseAgent",
    # Core agents
    "GrowthAgent",
    "IntegrationAgent",
    "ProactiveAgent",
    "SupervisorAgent",
    # Multi-agent architecture (recommended)
    "OnboardingAgent",
    "OrchestratorAgent",
    "QueryResolutionAgent",
    # Legacy (deprecated - use OrchestratorAgent instead)
    "JiraChargebeeAgent",
    "LegacyOnboardingAgent",
]
