"""
Query Resolution Agent - Specialized for general support and troubleshooting.

This agent handles queries related to:
- Billing and subscription management
- Feature explanations and usage
- Configuration and integration support
- Troubleshooting and debugging
"""

from __future__ import annotations

import logging
from typing import Optional

from aegis.agents.base import AgentMessage, AgentResponse, BaseAgent, AgentTransport
from aegis.agents.feedback_mixin import FeedbackHandlerMixin
from aegis.tools.jira_mcp import comment_on_ticket, get_ticket_details
from aegis.tools.chargebee_ops_mcp_tool import query_chargebee_docs


class QueryResolutionAgent(BaseAgent, FeedbackHandlerMixin):
    """
    Specialized agent for general query resolution and support.
    
    Capabilities:
    - Billing and subscription troubleshooting
    - Feature explanations and how-to guides  
    - Configuration and integration support
    - Debugging and error resolution
    - Best practices and optimization
    
    The agent uses specialized prompts to provide clear, actionable
    solutions for customer support issues.
    """
    
    # Specialized system prompt for query resolution
    SYSTEM_PROMPT = """You are a Support Specialist for Chargebee, focused on helping customers resolve issues and understand features.

Your expertise includes:
- Troubleshooting billing and subscription issues
- Explaining Chargebee features and functionality
- Configuration and integration support
- Best practices for using Chargebee effectively
- Debugging errors and resolving technical issues

Communication Style:
- Be clear, precise, and helpful
- Provide actionable solutions
- Include examples when helpful
- Explain the "why" behind recommendations
- Break down complex topics into understandable parts

When answering:
1. Directly address the specific issue or question
2. Provide clear, step-by-step solutions
3. Include relevant examples or code snippets
4. Explain potential causes of issues
5. Suggest preventive measures or best practices
6. Reference official documentation when appropriate
"""
    
    def __init__(
        self,
        agent_id: str = "query_resolution_agent",
        transport: Optional[AgentTransport] = None,
        feedback_project_key: str = "KAN"
    ) -> None:
        super().__init__(agent_id=agent_id, transport=transport)
        self.docs_client = query_chargebee_docs
        self.feedback_project_key = feedback_project_key
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # A2A capabilities registration
        self.capabilities = [
            "query_resolution",
            "troubleshooting",
            "billing_support",
            "subscription_management",
            "feature_explanation",
            "configuration",
            "integration_support",
            "debugging"
        ]
    
    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        """Handle general support queries."""
        self.logger.info("Entering handle_message")
        payload = message.payload or {}
        issue_key = payload.get("issue_key")
        query = payload.get("query")
        dry_run = bool(payload.get("dry_run", False))
        
        self.logger.info(f"Processing support query - issue: {issue_key}")
        
        # If there's an issue key, get the ticket details and build query from it
        if issue_key is not None:
            issue = await get_ticket_details(issue_key)
            query = self._build_query(issue)
        
        # Enhance query with support context
        enhanced_query = self._enhance_query_with_context(query)
        
        # Query Chargebee docs with support focus
        docs_answer = await self.docs_client(enhanced_query)
        
        # Post-process answer with support-specific formatting
        formatted_answer = self._format_support_answer(docs_answer, query)
        
        # Prepare comment body only if we have an issue key
        comment_body = None
        if issue_key is not None:
            comment_body = self._compose_comment(
                issue,
                query,
                formatted_answer,
                payload.get("comment_prefix"),
            )
        
        metadata = {
            "issue_key": issue_key,
            "query": query,
            "dry_run": dry_run,
            "agent_type": "query_resolution",
            "capabilities": self.capabilities,
        }
        
        if dry_run:
            if issue_key is not None:
                text = f"[QUERY RESOLUTION AGENT - DRY RUN] Would comment on {issue_key}"
                attachments = [
                    {
                        "preview_comment": comment_body,
                        "docs_answer": formatted_answer,
                    }
                ]
            else:
                text = formatted_answer
                attachments = [{"docs_answer": formatted_answer}]
        else:
            if issue_key is not None:
                comment_result = await comment_on_ticket(issue_key, comment_body)
                metadata["comment_id"] = comment_result.get("id")
                text = f"[Query Resolution Agent] Posted solution to {issue_key}."
                attachments = [{"docs_answer": formatted_answer}]
            else:
                text = formatted_answer
                attachments = [{"docs_answer": formatted_answer}]
        
        return AgentResponse(
            text=text,
            metadata=metadata,
            attachments=attachments,
        )
    
    def _enhance_query_with_context(self, query: str) -> str:
        """Add support-specific context to the query."""
        return f"{query}\n\nContext: This is a support query. Please provide a clear, actionable solution with examples if helpful."
    
    def _format_support_answer(self, docs_answer: str, original_query: str) -> str:
        """Format the answer with support-friendly introduction."""
        intro = "🔧 **Here's the solution:**\n\n"
        return f"{intro}{docs_answer}"
    
    def _build_query(self, issue: dict) -> str:
        """Build query from Jira issue."""
        summary = issue.get("summary") or ""
        description = issue.get("description") or ""
        return f"{summary}\n\n{description}".strip()
    
    def _compose_comment(
        self,
        issue: dict,
        query: str,
        docs_answer: str,
        prefix: Optional[str],
    ) -> str:
        """Compose Jira comment with support context."""
        intro = prefix or "🔧 Support Solution from Aegis Query Resolution Agent:"
        summary = issue.get("summary", "")
        status = issue.get("status", {}).get("name", "Unknown")
        lines = [
            intro,
            "",
            f"*Issue:* {issue.get('key')} — {summary}",
            f"*Status:* {status}",
            "",
            "*Query (from Jira):*",
            query,
            "",
            "*Solution:*",
            docs_answer or "No relevant documentation was found.",
        ]
        return "\n".join(lines)
