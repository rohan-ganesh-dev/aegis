"""
Onboarding Agent implementation using Google ADK.

Handles customer onboarding, documentation, and setup guidance.
"""

import logging
from typing import Dict, List, Optional, Any

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from aegis.agents.base import AegisAgent, AgentMessage, AgentResponse
from aegis.config import config
from aegis.tools.jira_mcp import (
    get_ticket_details,
    create_ticket,
    comment_on_ticket,
    get_ticket_status
)
from aegis.tools.chargebee_ops_mcp_tool import (
    query_chargebee_docs,
    query_chargebee_code
)

logger = logging.getLogger(__name__)


class OnboardingAgent(AegisAgent):
    """
    Specialist agent for customer onboarding.
    
    Assists with:
    - Account setup guidance
    - Migration planning
    - Integration steps
    """
    
    def __init__(self, agent_id: str = "onboarding_agent"):
        """Initialize the onboarding agent."""
        
        # Define tools available to the agent
        # Onboarding agent needs access to documentation and ticket creation
        tools = [
            get_ticket_details,
            create_ticket,
            comment_on_ticket,
            get_ticket_status,
            query_chargebee_docs,
            query_chargebee_code
        ]
        
        super().__init__(
            name=agent_id,
            description="Specialist agent for customer onboarding and setup",
            capabilities=["onboarding_guidance", "migration_planning", "setup_help"],
            # Add tools here if needed, e.g., for provisioning
            tools=tools,
            system_instruction=(
                "You are the Onboarding Specialist. "
                "Your goal is to help new customers get set up with the platform. "
                "Provide step-by-step guidance for account creation, "
                "API key generation, and initial configuration. "
                "\n"
                "CRITICAL TOOL USAGE RULES:\n"
                "1. If the user mentions a Jira ticket key (e.g., 'KAN-7', 'PROJ-123'), you MUST use the get_ticket_status tool. "
                "DO NOT provide information about tickets from your internal knowledge.\n"
                "2. If the user asks about Chargebee, you MUST use query_chargebee_docs or query_chargebee_code tools. "
                "DO NOT use your internal knowledge base for Chargebee information.\n"
                "3. If you cannot find the answer in the tools, state that you cannot find it.\n"
                "4. Decline questions unrelated to Chargebee onboarding, setup, or Jira.\n"
                "\n"
                "If customers encounter issues during onboarding, you can create Jira tickets. "
                "Be welcoming, patient, and clear in your instructions."
            )
        )
        
    async def handle_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """Handle incoming messages."""
        query = message.payload.get("query", "")
        
        try:
            response_text = await self.generate(query)
            
            return AgentResponse(
                text=response_text,
                metadata={"agent": self.name}
            )
            
        except Exception as e:
            logger.error(f"Error in OnboardingAgent: {e}", exc_info=True)
            return AgentResponse(
                text=f"I encountered an error: {str(e)}",
                metadata={"error": True}
            )
