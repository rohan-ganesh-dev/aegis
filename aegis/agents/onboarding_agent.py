"""
Onboarding Agent - Specialized for customer onboarding and registration queries.

This agent handles queries related to:
- Customer registration and account setup
- Initial configuration procedures
- Onboarding best practices
- Getting started guides
"""

from __future__ import annotations

import logging
from typing import Optional

from aegis.agents.base import AgentMessage, AgentResponse, BaseAgent, AgentTransport
from aegis.agents.feedback_mixin import FeedbackHandlerMixin
from aegis.tools.jira_mcp import comment_on_ticket, get_ticket_details
from aegis.tools.chargebee_ops_mcp_tool import query_chargebee_docs


class OnboardingAgent(BaseAgent, FeedbackHandlerMixin):
    """
    Specialized agent for onboarding and registration support.
    
    Capabilities:
    - Customer registration and account setup
    - Initial configuration procedures
    - Onboarding best practices
    - Getting started guides
    
    The agent uses specialized prompts to provide step-by-step guidance
    for new users getting started with Chargebee.
    """
    
    # Specialized system prompt for onboarding
    SYSTEM_PROMPT = """You are an Onboarding Specialist for Chargebee, focused on helping new customers get started successfully.

Your expertise includes:
- Customer registration and account setup
- Initial configuration and setup procedures
- Onboarding best practices and workflows
- Getting started guides and tutorials
- First-time user guidance

Communication Style:
- Be warm, welcoming, and encouraging
- Provide step-by-step guidance
- Use simple, clear language
- Include helpful tips for new users
- Anticipate common beginner questions

When answering:
1. Start with a clear, concise answer
2. Provide step-by-step instructions when applicable
3. Highlight important first steps
4. Mention common pitfalls to avoid
5. Encourage users and build their confidence
"""
    
    def __init__(
        self,
        agent_id: str = "onboarding_agent",
        transport: Optional[AgentTransport] = None,
        feedback_project_key: str = "KAN"
    ) -> None:
        super().__init__(agent_id=agent_id, transport=transport)
        self.docs_client = query_chargebee_docs
        self.feedback_project_key = feedback_project_key
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # A2A capabilities registration
        self.capabilities = [
            "onboarding",
            "registration",
            "setup",
            "getting_started",
            "customer_creation",
            "account_setup"
        ]
    
    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        """Handle onboarding-related queries."""
        self.logger.info("Entering handle_message")
        payload = message.payload or {}
        issue_key = payload.get("issue_key")
        query = payload.get("query")
        dry_run = bool(payload.get("dry_run", False))
        
        self.logger.info(f"Processing onboarding query - issue: {issue_key}")
        
        # If there's an issue key, get the ticket details and build query from it
        if issue_key is not None:
            issue = await get_ticket_details(issue_key)
            query = self._build_query(issue)
        
        # Enhance query with onboarding context
        enhanced_query = self._enhance_query_with_context(query)
        
        # Query Chargebee docs with onboarding focus
        docs_answer = await self.docs_client(enhanced_query)
        
        # Post-process answer with onboarding-specific guidance
        formatted_answer = self._format_onboarding_answer(docs_answer, query)
        
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
            "agent_type": "onboarding",
            "capabilities": self.capabilities,
        }
        
        if dry_run:
            if issue_key is not None:
                text = f"[ONBOARDING AGENT - DRY RUN] Would comment on {issue_key}"
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
                text = f"[Onboarding Agent] Posted guidance to {issue_key}."
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
        """Add onboarding-specific context to the query."""
        return f"{query}\n\nContext: This is for a new customer just getting started with Chargebee. Please provide beginner-friendly, step-by-step guidance."
    
    def _format_onboarding_answer(self, docs_answer: str, original_query: str) -> str:
        """Format the answer with onboarding-friendly introduction."""
        intro = "🌟 **Welcome to Chargebee!** Here's how to get started:\n\n"
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
        """Compose Jira comment with onboarding context."""
        intro = prefix or "🌟 Onboarding Guidance from Aegis Onboarding Agent:"
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
            "*Onboarding Guidance:*",
            docs_answer or "No relevant documentation was found.",
        ]
        return "\n".join(lines)
