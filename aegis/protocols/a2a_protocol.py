"""
Agent-to-Agent (A2A) Protocol for agent discovery and communication.

This module provides a simple protocol for agents to register their
capabilities and discover other agents in the system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Describes an agent's capability."""
    name: str
    description: Optional[str] = None
    

@dataclass
class AgentRegistration:
    """Registration record for an A2A-enabled agent."""
    agent_id: str
    capabilities: List[str]
    description: str
    agent_instance: Optional[any] = None  # Reference to actual agent
    metadata: Dict[str, any] = field(default_factory=dict)


class A2ARegistry:
    """
    Central registry for A2A agent discovery.
    
    Agents register themselves with their capabilities,
    and other agents can discover them by capability.
    """
    
    def __init__(self):
        self._registrations: Dict[str, AgentRegistration] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> set of agent_ids
        self.logger = logging.getLogger(f"{__name__}.A2ARegistry")
    
    def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        description: str,
        agent_instance: Optional[any] = None,
        metadata: Optional[Dict[str, any]] = None
    ) -> None:
        """
        Register an agent with the A2A registry.
        
        Args:
            agent_id: Unique agent identifier
            capabilities: List of capability strings
            description: Human-readable agent description
            agent_instance: Optional reference to the agent instance
            metadata: Optional additional metadata
        """
        registration = AgentRegistration(
            agent_id=agent_id,
            capabilities=capabilities,
            description=description,
            agent_instance=agent_instance,
            metadata=metadata or {}
        )
        
        self._registrations[agent_id] = registration
        
        # Index by capabilities
        for capability in capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = set()
            self._capability_index[capability].add(agent_id)
        
        self.logger.info(f"Registered agent: {agent_id} with capabilities: {capabilities}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the registry."""
        if agent_id not in self._registrations:
            return
        
        registration = self._registrations[agent_id]
        
        # Remove from capability index
        for capability in registration.capabilities:
            if capability in self._capability_index:
                self._capability_index[capability].discard(agent_id)
                if not self._capability_index[capability]:
                    del self._capability_index[capability]
        
        del self._registrations[agent_id]
        self.logger.info(f"Unregistered agent: {agent_id}")
    
    def discover_by_capability(self, capability: str) -> List[AgentRegistration]:
        """
        Find all agents that have a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of AgentRegistration objects
        """
        agent_ids = self._capability_index.get(capability, set())
        return [self._registrations[aid] for aid in agent_ids]
    
    def discover_by_capabilities(self, capabilities: List[str], match_all: bool = False) -> List[AgentRegistration]:
        """
        Find agents that have one or more of the specified capabilities.
        
        Args:
            capabilities: List of capabilities to search for
            match_all: If True, only return agents that have ALL capabilities
            
        Returns:
            List of AgentRegistration objects
        """
        if match_all:
            # Find agents that have all specified capabilities
            agent_sets = [self._capability_index.get(cap, set()) for cap in capabilities]
            if not agent_sets:
                return []
            matching_ids = set.intersection(*agent_sets)
        else:
            # Find agents that have any of the specified capabilities
            matching_ids = set()
            for capability in capabilities:
                matching_ids.update(self._capability_index.get(capability, set()))
        
        return [self._registrations[aid] for aid in matching_ids]
    
    def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get registration for a specific agent."""
        return self._registrations.get(agent_id)
    
    def list_all_agents(self) -> List[AgentRegistration]:
        """List all registered agents."""
        return list(self._registrations.values())
    
    def list_all_capabilities(self) -> List[str]:
        """List all registered capabilities."""
        return list(self._capability_index.keys())


# Global registry instance
_global_registry = A2ARegistry()


def get_registry() -> A2ARegistry:
    """Get the global A2A registry instance."""
    return _global_registry


def register_agent(
    agent_id: str,
    capabilities: List[str],
    description: str,
    agent_instance: Optional[any] = None,
    metadata: Optional[Dict[str, any]] = None
) -> None:
    """Convenience function to register with global registry."""
    _global_registry.register_agent(agent_id, capabilities, description, agent_instance, metadata)


def discover_agents(capability: str) -> List[AgentRegistration]:
    """Convenience function to discover agents by capability."""
    return _global_registry.discover_by_capability(capability)
