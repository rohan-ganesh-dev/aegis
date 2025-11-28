"""A2A Protocol module for agent discoverability."""

from aegis.protocols.a2a_protocol import (
    A2ARegistry,
    AgentCapability,
    AgentRegistration,
    discover_agents,
    get_registry,
    register_agent,
)

__all__ = [
    "A2ARegistry",
    "AgentCapability",
    "AgentRegistration",
    "get_registry",
    "register_agent",
    "discover_agents",
]
