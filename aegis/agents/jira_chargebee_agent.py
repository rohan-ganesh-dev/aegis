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
from aegis.tools.jira_mcp import comment_on_ticket, get_ticket_details
from aegis.tools.chargebee_rag_tool import query_chargebee_docs



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
        transport: Optional[AgentTransport] = None
    ) -> None:
        super().__init__(agent_id=agent_id, transport=transport)
        # Default to the shared Chargebee MCP docs client if none is provided.
        self.docs_client =  query_chargebee_docs
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        payload = message.payload or {}
        issue_key = payload.get("issue_key")
        if not issue_key:
            raise ValueError("issue_key is required to process Jira tickets.")

        dry_run = bool(payload.get("dry_run", False))

        self.logger.info("Processing Jira ticket %s via Chargebee docs", issue_key)
        issue = await get_ticket_details(issue_key)
        query = payload.get("query") or self._build_query(issue)

        docs_answer = await self.docs_client(query)
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
            text = f"[DRY RUN] Would comment on {issue_key} with Chargebee docs findings."
            attachments = [
                {
                    "preview_comment": comment_body,
                    "docs_answer": docs_answer,
                }
            ]
        else:
            comment_result = await comment_on_ticket(issue_key, comment_body)
            metadata["comment_id"] = comment_result.get("id")
            text = f"Posted Chargebee docs context comment to {issue_key}."
            attachments = [{"docs_answer": docs_answer}]

        return AgentResponse(
            text=text,
            metadata=metadata,
            attachments=attachments,
        )

    def _build_query(self, issue: dict) -> str:
        summary = issue.get("summary") or ""
        description = issue.get("description") or ""
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

