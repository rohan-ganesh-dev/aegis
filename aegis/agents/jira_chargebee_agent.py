"""
Single agent that:
- Reads Jira ticket details via MCP
- Queries Chargebee documentation (via MCP-backed client)
- Posts its findings back to the Jira ticket
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable, Optional

from aegis.agents.base import AgentMessage, AgentResponse, BaseAgent, AgentTransport
from aegis.tools.jira_mcp import comment_on_ticket, get_ticket_details, create_ticket
from aegis.tools.chargebee_ops_mcp_tool import query_chargebee_docs



class JiraChargebeeAgent(BaseAgent):
    """
    Minimal ADK-based agent that connects Jira tickets to Chargebee docs.

    Flow:
    - Read Jira issue (summary/description)
    - Use that as a query into Chargebee documentation (via MCP-backed client)
    - Post a summarized explanation back to the Jira ticket as a comment
    """

    def __init__(
        self,
        agent_id: str,
        transport: Optional[AgentTransport] = None,
        feedback_project_key: str = "KAN"
    ) -> None:
        super().__init__(agent_id=agent_id, transport=transport)
        # Default to the shared Chargebee MCP docs client if none is provided.
        self.docs_client = query_chargebee_docs
        self.feedback_project_key = feedback_project_key
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        self.logger.info("Entering handle_message")
        payload = message.payload or {}
        issue_key = payload.get("issue_key")
        query = payload.get("query")
        dry_run = bool(payload.get("dry_run", False))

        self.logger.info("Processing Jira ticket %s via Chargebee docs", issue_key)
        
        # If there's an issue key, get the ticket details and build query from it
        if issue_key is not None:
            issue = await get_ticket_details(issue_key)
            query = self._build_query(issue)
        
        # Query Chargebee docs
        docs_answer = await self.docs_client(query)
        
        # Prepare comment body only if we have an issue key
        comment_body = None
        if issue_key is not None:
            comment_body = self._compose_comment(
                issue,
                query,
                docs_answer,
                payload.get("comment_prefix"),
            )

        metadata = {
            "issue_key": issue_key,
            "query": query,
            "dry_run": dry_run,
        }

        if dry_run:
            if issue_key is not None:
                text = f"[DRY RUN] Would comment on {issue_key} with Chargebee docs findings."
                attachments = [
                    {
                        "preview_comment": comment_body,
                        "docs_answer": docs_answer,
                    }
                ]
            else:
                # Pure documentation query
                text = f"Here's what I found in the Chargebee documentation:"
                attachments = [{"docs_answer": docs_answer}]
        else:
            if issue_key is not None:
                comment_result = await comment_on_ticket(issue_key, comment_body)
                metadata["comment_id"] = comment_result.get("id")
                text = f"Posted Chargebee docs context comment to {issue_key}."
                attachments = [{"docs_answer": docs_answer}]
            else:
                # Pure documentation query
                text = docs_answer
                attachments = [{"docs_answer": docs_answer}]

        return AgentResponse(
            text=text,
            metadata=metadata,
            attachments=attachments,
        )

    def _build_query(self, issue: dict) -> str:
        summary = issue.get("summary") or ""
        description = issue.get("description") or ""
        print("query asked is is ",summary)
        return f"{summary}\\n\\n{description}".strip()

    def _compose_comment(
        self,
        issue: dict,
        query: str,
        docs_answer: str,
        prefix: Optional[str],
    ) -> str:
        intro = prefix or "Automated Chargebee docs context from Aegis Agent:"
        summary = issue.get("summary", "")
        status = issue.get("status", {}).get("name", "Unknown")
        lines = [
            intro,
            "",
            f"*Issue:* {issue.get('key')} — {summary}",
            f"*Status:* {status}",
            "",
            "*Search Query (from Jira):*",
            query,
            "",
            "*Chargebee Documentation Findings:*",
            docs_answer or "No relevant documentation was found in Chargebee.",
        ]
        return "\n".join(lines)

    async def handle_feedback(
        self,
        query: str,
        docs_answer: str,
        feedback_type: str,
        additional_feedback: Optional[str] = None,
        issue_key: Optional[str] = None,
    ) -> AgentResponse:
        """
        Process user feedback on a documentation query.
        
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
        self.logger.info(f"Processing {feedback_type} feedback for query: {query}, issue_key: {issue_key}")
        
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
                self.logger.info(f"Added feedback comment to ticket: {issue_key}")
                
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
                self.logger.error(f"Failed to add comment to ticket: {e}", exc_info=True)
                return AgentResponse(
                    text=f"Thank you for your feedback. Unfortunately, I encountered an error adding the comment: {str(e)}",
                    metadata={
                        "feedback_type": "negative",
                        "query": query,
                        "error": str(e),
                    },
                )
        else:
            # Create new feedback ticket (original behavior for documentation queries)
            summary = f"Documentation query needs improvement: {query[:80]}"
            if len(query) > 80:
                summary += "..."
            
            description_lines = [
                "# User Feedback: Documentation Answer Unsatisfactory",
                "",
                "## Original Query",
                query,
                "",
                "## Documentation Answer Provided",
                docs_answer or "No answer was provided.",
                "",
            ]
            
            if additional_feedback:
                description_lines.extend([
                    "## User Feedback",
                    additional_feedback,
                    "",
                ])
            
            description_lines.extend([
                "---",
                "*This ticket was automatically created by the Aegis Agent based on user feedback.*",
            ])
            
            description = "\n".join(description_lines)
            
            try:
                ticket = await create_ticket(
                    project_key=self.feedback_project_key,
                    summary=summary,
                    description=description,
                    issue_type="Task",
                )
                
                # Debug: log the full ticket response to understand its structure
                self.logger.info(f"Ticket response: {ticket}")
                
                # Extract key from nested structure: ticket['issue']['key']
                issue_data = ticket.get('issue', {})
                ticket_key = issue_data.get('key') or ticket.get('key') or ticket.get('id', 'Unknown')
                self.logger.info(f"Created feedback ticket: {ticket_key}")
                
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
                self.logger.error(f"Failed to create feedback ticket: {e}", exc_info=True)
                return AgentResponse(
                    text=f"Thank you for your feedback. Unfortunately, I encountered an error creating the ticket: {str(e)}",
                    metadata={
                        "feedback_type": "negative",
                        "query": query,
                        "error": str(e),
                    },
                )

