from typing import Dict, Any, List, Optional
from aegis.agents.base import AegisAgent, AgentMessage, AgentResponse
from aegis.tools.jira_mcp import create_ticket, comment_on_ticket
import logging

logger = logging.getLogger(__name__)

class FeedbackAgent(AegisAgent):
    """
    Specialist agent for handling user feedback and creating Jira tickets.
    """
    
    def __init__(self, agent_id: str = "feedback_agent"):
        # Register tools
        tools = [
            create_ticket,
            comment_on_ticket
        ]
        
        super().__init__(
            name=agent_id,
            description="Specialist for handling user feedback and creating Jira tickets",
            capabilities=["feedback_analysis", "ticket_creation"],
            system_instruction=(
                "You are the Feedback Specialist. Your role is to analyze user feedback "
                "and either add a comment to an existing Jira ticket or create a new one. "
                "When you receive feedback:\n"
                "1. Analyze the sentiment (positive/negative).\n"
                "2. Extract key details (what went wrong, what was good).\n"
                "3. If the feedback is about an EXISTING ticket (issue_key provided):\n"
                "   - Use 'comment_on_ticket' to add the feedback as a comment\n"
                "   - Include the feedback type, user comments, and relevant context\n"
                "4. If the feedback is NOT about a specific ticket (no issue_key):\n"
                "   - Create a NEW Jira ticket using the 'create_ticket' tool\n"
                "   - Project Key: 'KAN' (unless specified otherwise)\n"
                "   - Issue Type: 'Task' or 'Bug'\n"
                "   - Summary: Concise summary of the feedback\n"
                "   - Description: Full details including original query and user comments\n"
                "5. Return confirmation with the ticket key in your response.\n"
                "If the feedback is positive, you can still create a ticket/comment to log the success or just acknowledge it."
            ),
            tools=tools
        )
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """Handle incoming messages and ALWAYS create a Jira ticket."""
        query_text = message.payload.get('query', '')
        logger.info(f"FeedbackAgent received message: {query_text[:100]}")
        
        try:
            # Parse the feedback data from the query
            # The orchestrator sends a formatted prompt with feedback details
            import re
            
            # Extract feedback details using regex
            feedback_type_match = re.search(r'Feedback Type: (\w+)', query_text)
            original_query_match = re.search(r'Original User Query: "(.*?)"', query_text)
            agent_answer_match = re.search(r'Agent Answer: "(.*?)"', query_text)
            user_comments_match = re.search(r'User Comments: "(.*?)"', query_text)
            
            feedback_type = feedback_type_match.group(1) if feedback_type_match else "unknown"
            original_query = original_query_match.group(1) if original_query_match else "N/A"
            agent_answer = agent_answer_match.group(1) if agent_answer_match else "N/A"
            user_comments = user_comments_match.group(1) if user_comments_match else "No additional comments"
            
            # Determine issue type based on feedback
            issue_type = "Bug" if feedback_type == "negative" else "Task"
            
            # Create summary
            summary = f"User Feedback: {original_query[:50]}..."
            
            # Create detailed description
            description = f"""
**Feedback Type:** {feedback_type.capitalize()}

**Original Query:**
{original_query}

**Agent Response:**
{agent_answer}

**User Comments:**
{user_comments}

---
*Automatically created from user feedback*
            """.strip()
            
            logger.info(f"Creating Jira ticket - Type: {issue_type}, Summary: {summary}")
            
            # ALWAYS create a Jira ticket
            ticket_result = await create_ticket(
                project_key="KAN",
                summary=summary,
                description=description,
                issue_type=issue_type
            )
            
            logger.info(f"Ticket created: {ticket_result}")
            
            # Extract ticket key from result
            ticket_key = ticket_result.get("key")
            if not ticket_key and "issue" in ticket_result:
                ticket_key = ticket_result["issue"].get("key")
            
            if not ticket_key:
                ticket_key = "Unknown"
            ticket_url = f"https://jobsforrohanganesh.atlassian.net/browse/{ticket_key}"
            
            response_text = f"✅ Thank you for your feedback! I've created Jira ticket [{ticket_key}]({ticket_url}) to track this."
            
            return AgentResponse(
                text=response_text,
                metadata={
                    "agent": self.name,
                    "ticket_key": ticket_key,
                    "ticket_url": ticket_url
                }
            )
            
        except Exception as e:
            logger.error(f"FeedbackAgent error: {e}", exc_info=True)
            return AgentResponse(
                text=f"❌ Error creating feedback ticket: {str(e)}",
                metadata={"error": True}
            )
