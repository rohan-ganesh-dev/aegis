"""
Orchestrator Agent - Routes queries to specialized agents.

This agent classifies incoming queries and routes them to the appropriate
specialized agent (OnboardingAgent or QueryResolutionAgent).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from aegis.agents.base import AgentMessage, AgentResponse, BaseAgent, AgentTransport
from aegis.agents.feedback_mixin import FeedbackHandlerMixin
from aegis.agents.onboarding_agent import OnboardingAgent
from aegis.agents.query_resolution_agent import QueryResolutionAgent


class OrchestratorAgent(BaseAgent, FeedbackHandlerMixin):
    """
    Orchestrator agent that routes queries to specialized agents.
    
    Routing Logic:
    - Classifies query as "onboarding" or "general"
    - Routes to OnboardingAgent for onboarding-related queries
    - Routes to QueryResolutionAgent for general support queries
    - Tracks which agent handled each query
    """
    
    # Keywords for onboarding classification
    ONBOARDING_KEYWORDS = [
        'registration', 'register', 'signup', 'sign up',  'getting started',
        'initial setup', 'onboard', 'welcome', 'new account', 'create account',
        'first time', 'begin', 'start using', 'how do i start', 'setup guide',
        'installation', 'configure initially', 'new customer', 'new user'
    ]
    
    # Keywords for query resolution (supplementary - most queries default here)
    GENERAL_KEYWORDS = [
        'billing', 'subscription', 'invoice', 'payment', 'charge',
        'configuration', 'troubleshoot', 'error', 'issue', 'problem',
        'how to use', 'how does', 'difference between', 'explain',
        'integration', 'api', 'webhook', 'customize', 'modify'
    ]
    
    def __init__(
        self,
        agent_id: str = "orchestrator_agent",
        transport: Optional[AgentTransport] = None,
        feedback_project_key: str = "KAN"
    ) -> None:
        super().__init__(agent_id=agent_id, transport=transport)
        self.feedback_project_key = feedback_project_key
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # Initialize specialized agents
        self.onboarding_agent = OnboardingAgent(
            agent_id="onboarding_agent",
            transport=transport,
            feedback_project_key=feedback_project_key
        )
        self.query_agent = QueryResolutionAgent(
            agent_id="query_resolution_agent",
            transport=transport,
            feedback_project_key=feedback_project_key
        )
        
        # A2A capabilities - orchestrator can handle any query by delegation
        self.capabilities = [
            "orchestration",
            "routing",
            "query_classification"
        ]
    
    async def start(self) -> None:
        """Start orchestrator and all specialized agents."""
        await super().start()
        await self.onboarding_agent.start()
        await self.query_agent.start()
        self.logger.info("All specialized agents started")
    
    async def stop(self) -> None:
        """Stop orchestrator and all specialized agents."""
        await self.onboarding_agent.stop()
        await self.query_agent.stop()
        await super().stop()
        self.logger.info("All specialized agents stopped")
    
    def _classify_query(self, query: str) -> str:
        """
        Classify query as 'onboarding' or 'general'.
        
        Args:
            query: User query to classify
            
        Returns:
            'onboarding' or 'general'
        """
        query_lower = query.lower()
        
        # Check for onboarding keywords
        onboarding_score = sum(
            1 for keyword in self.ONBOARDING_KEYWORDS
            if keyword in query_lower
        )
        
        # Check for general keywords
        general_score = sum(
            1 for keyword in self.GENERAL_KEYWORDS
            if keyword in query_lower
        )
        
        # Decision logic
        if onboarding_score > general_score:
            return "onboarding"
        elif onboarding_score > 0 and general_score == 0:
            return "onboarding"
        else:
            # Default to general/query resolution for most queries
            return "general"
    
    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        """Route message to appropriate specialized agent."""
        self.logger.info("Orchestrator received message")
        
        payload = message.payload or {}
        query = payload.get("query", "")
        
        # Classify the query
        classification = self._classify_query(query)
        
        self.logger.info(f"Query classified as: {classification}")
        self.logger.info(f"Query: {query[:100]}...")
        
        # Route to appropriate agent
        if classification == "onboarding":
            self.logger.info("Routing to OnboardingAgent")
            response = await self.onboarding_agent.handle_message(message)
            routed_to = "OnboardingAgent"
        else:
            self.logger.info("Routing to QueryResolutionAgent")
            response = await self.query_agent.handle_message(message)
            routed_to = "QueryResolutionAgent"
        
        # Add orchestrator metadata
        if response.metadata is None:
            response.metadata = {}
        
        response.metadata["orchestrator"] = {
            "agent_id": self.agent_id,
            "classification": classification,
            "routed_to": routed_to,
        }
        
        return response
