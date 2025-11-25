"""Agents package initialization."""

from aegis.agents.base import AgentMessage, AgentResponse, BaseAgent, CustomerContext
from aegis.agents.growth import GrowthAgent
from aegis.agents.integration import IntegrationAgent
from aegis.agents.onboarding import OnboardingAgent
from aegis.agents.proactive import ProactiveAgent
from aegis.agents.supervisor import SupervisorAgent

__all__ = [
    "BaseAgent",
    "AgentMessage",
    "AgentResponse",
    "CustomerContext",
    "SupervisorAgent",
    "OnboardingAgent",
    "IntegrationAgent",
    "ProactiveAgent",
    "GrowthAgent",
]
