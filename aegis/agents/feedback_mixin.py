"""
Feedback handling mixin for agents.

Provides common feedback functionality for creating tickets
and adding comments based on user satisfaction.
"""

from typing import Optional
from aegis.agents.base import AgentResponse
from aegis.tools.jira_mcp import create_ticket, comment_on_ticket
import logging


class FeedbackHandlerMixin:
    """
    Mixin providing feedback handling capabilities to agents.
    
    Agents using this mixin must have:
    - self.logger: logging.Logger
    - self.feedback_project_key: str
    """
    
    async def handle_feedback(
        self,
        query: str,
        docs_answer: str,
        feedback_type: str,
        additional_feedback: Optional[str] = None,
        issue_key: Optional[str] = None,
    ) -> AgentResponse:
        """
        Process user feedback on a query response.
        
        If issue_key is provided (query was about a ticket), adds a comment to that ticket.
        Otherwise, creates a new feedback ticket.
        
        Args:
            query: The original user query
            docs_answer: The documentation answer that was provided
            feedback_type: Either "positive" or "negative"
            additional_feedback: Optional additional context from the user
            issue_key: Optional ticket key if query was about an existing ticket
            
        Returns:
            AgentResponse with the result of feedback processing
        """
        logger = getattr(self, 'logger', logging.getLogger(__name__))
        logger.info(f"Processing {feedback_type} feedback for query: {query}, issue_key: {issue_key}")
        
        if feedback_type == "positive":
            return AgentResponse(
                text="Thank you for your positive feedback! 👍",
                metadata={
                    "feedback_type": "positive",
                    "query": query,
                },
            )
        
        # Handle negative feedback
        # If there's an issue_key, add a comment to that ticket
        # Otherwise, create a new feedback ticket
        
        if issue_key:
            # Add comment to existing ticket
            comment_lines = [
                "h2. User Feedback: Not Satisfied with Response",
                "",
                "*Original Query:*",
                query,
                "",
            ]
            
            if additional_feedback:
                comment_lines.extend([
                    "*User Feedback:*",
                    additional_feedback,
                    "",
                ])
            
            comment_lines.extend([
                "---",
                "_User provided negative feedback on the agent's response._",
            ])
            
            comment = "\n".join(comment_lines)
            
            try:
                await comment_on_ticket(issue_key, comment)
                logger.info(f"Added feedback comment to ticket: {issue_key}")
                
                return AgentResponse(
                    text=f"Thank you for your feedback. I've added your comments to ticket {issue_key}.",
                    metadata={
                        "feedback_type": "negative",
                        "query": query,
                        "ticket_key": issue_key,
                        "action": "comment_added",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to add comment to ticket: {e}", exc_info=True)
                return AgentResponse(
                    text=f"Thank you for your feedback. Unfortunately, I encountered an error adding the comment: {str(e)}",
                    metadata={
                        "feedback_type": "negative",
                        "query": query,
                        "error": str(e),
                    },
                )
        else:
            # Create new feedback ticket
            feedback_project_key = getattr(self, 'feedback_project_key', 'KAN')
            agent_name = getattr(self, 'agent_id', 'agent')
            
            summary = f"[{agent_name}] Documentation query needs improvement: {query[:60]}"
            if len(query) > 60:
                summary += "..."
            
            description_lines = [
                f"h1. User Feedback: Documentation Answer Unsatisfactory",
                "",
                f"h2. Agent: {agent_name}",
                "",
                "h2. Original Query",
                query,
                "",
                "h2. Documentation Answer Provided",
                docs_answer or "No answer was provided.",
                "",
            ]
            
            if additional_feedback:
                description_lines.extend([
                    "h2. User Feedback",
                    additional_feedback,
                    "",
                ])
            
            description_lines.extend([
                "---",
                "_This ticket was automatically created by the Aegis Agent based on user feedback._",
            ])
            
            description = "\n".join(description_lines)
            
            try:
                ticket = await create_ticket(
                    project_key=feedback_project_key,
                    summary=summary,
                    description=description,
                    issue_type="Task",
                )
                
                # Extract key from nested structure: ticket['issue']['key']
                issue_data = ticket.get('issue', {})
                ticket_key = issue_data.get('key') or ticket.get('key') or ticket.get('id', 'Unknown')
                logger.info(f"Created feedback ticket: {ticket_key}")
                
                return AgentResponse(
                    text=f"Thank you for your feedback. I've created ticket [{ticket_key}] to improve this documentation answer.",
                    metadata={
                        "feedback_type": "negative",
                        "query": query,
                        "ticket_key": ticket_key,
                        "ticket": ticket,
                        "action": "ticket_created",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to create feedback ticket: {e}", exc_info=True)
                return AgentResponse(
                    text=f"Thank you for your feedback. Unfortunately, I encountered an error creating the ticket: {str(e)}",
                    metadata={
                        "feedback_type": "negative",
                        "query": query,
                        "error": str(e),
                    },
                )
