"""
Query Resolution Agent implementation using Google ADK.

Handles general queries and RAG-based documentation retrieval.
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


class QueryResolutionAgent(AegisAgent):
    """
    General purpose query resolution agent.
    
    Uses RAG tools to answer questions that don't fit other specialists.
    """
    
    def __init__(self, agent_id: str = "query_resolution_agent"):
        """Initialize the query resolution agent."""
        
        # Tools for general knowledge/docs and ticket management
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
            description="General query resolution agent with documentation access",
            capabilities=["general_query", "documentation_search"],
            tools=tools,
            system_instruction=(
                "You are the Query Resolution Specialist. "
                "Your job is to answer general questions about the platform "
                "and provide information from the documentation. "
                "\n"
                "CRITICAL TOOL USAGE RULES:\n"
                "1. When a user asks about a Jira ticket (e.g., 'What is the status of KAN-7?', 'Show me KAN-19'), "
                "you MUST use get_ticket_details to get comprehensive information including status, description, and comments. "
                "NEVER create a new ticket for these queries.\n"
                "2. ONLY use create_ticket when the user EXPLICITLY asks to create a ticket "
                "(e.g., 'Create a ticket for bug X', 'I want to report an issue'). Do NOT create tickets for status queries.\n"
                "3. If the user asks about Chargebee, you MUST use query_chargebee_docs or query_chargebee_code tools. "
                "DO NOT use your internal knowledge base for Chargebee information.\n"
                "4. If you cannot find the answer in the tools, state that you cannot find it.\n"
                "5. Decline questions unrelated to Chargebee or Jira.\n"
                "\n"
                "RESPONSE FORMATTING:\n"
                "When presenting ticket information, be CONCISE and HUMAN-READABLE:\n"
                "- Status: Current ticket status\n"
                "- Description: Brief 1-2 sentence summary (if available)\n"
                "- Comments: Short summary of the most recent or important comment (if available)\n"
                "\n"
                "CRITICAL FORMATTING RULES:\n"
                "1. NEVER output raw JSON or Python dictionaries (e.g., {'name': 'To Do'...}).\n"
                "2. ALWAYS parse the tool output and present it as clean text.\n"
                "3. Do NOT dump all fields. Filter for relevance.\n"
                "4. Keep responses brief and actionable.\n"
                "If you cannot find the answer, politely say so."
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
            logger.error(f"Error in QueryResolutionAgent: {e}", exc_info=True)
            return AgentResponse(
                text=f"I encountered an error: {str(e)}",
                metadata={"error": True}
            )
