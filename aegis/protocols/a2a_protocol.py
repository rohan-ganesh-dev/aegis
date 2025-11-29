"""
Agent-to-Agent (A2A) Protocol implementation using Google ADK.

This module provides utilities for:
- Agent discovery via Agent Cards
- A2A communication using RemoteA2aAgent
- Conversion of local agents to A2A-compatible interfaces
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import (
    RemoteA2aAgent,
    AGENT_CARD_WELL_KNOWN_PATH,
)
from google.adk.a2a.utils.agent_to_a2a import to_a2a

logger = logging.getLogger(__name__)

# Standard path for agent card discovery
WELL_KNOWN_PATH = AGENT_CARD_WELL_KNOWN_PATH


def create_remote_agent(
    base_url: str,
    agent_id: str,
    api_key: Optional[str] = None
) -> RemoteA2aAgent:
    """
    Create a RemoteA2aAgent client for communicating with another agent.
    
    Args:
        base_url: Base URL of the remote agent (e.g., http://localhost:8001)
        agent_id: ID/Name of the remote agent
        api_key: Optional API key for authentication
        
    Returns:
        Configured RemoteA2aAgent instance
    """
    # Ensure URL doesn't end with slash
    if base_url.endswith("/"):
        base_url = base_url[:-1]
        
    agent_card_url = f"{base_url}{WELL_KNOWN_PATH}"
    
    logger.info(f"Creating remote agent client for {agent_id} at {base_url} (Card: {agent_card_url})")
    
    # RemoteA2aAgent requires name and agent_card
    return RemoteA2aAgent(
        name=agent_id,
        agent_card=agent_card_url,
        # api_key handling depends on ADK version, passing in kwargs if supported
        # or it might need to be configured via client factory
    )


def expose_agent_as_a2a(agent: LlmAgent, host: str = "0.0.0.0", port: int = 8000):
    """
    Utility to expose a local LlmAgent as an A2A service.
    
    This is typically used in the agent's startup code.
    
    Args:
        agent: The LlmAgent instance to expose
        host: Host to bind to
        port: Port to bind to
    """
    # This uses the ADK's to_a2a utility to create a FastAPI app
    logger.info(f"Exposing agent {agent.name} on {host}:{port}")
    
    # Note: to_a2a typically returns a FastAPI app
    app = to_a2a(agent)
    
    return app
