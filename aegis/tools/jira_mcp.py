"""
Utilities for interacting with the Jira MCP server.

Agent code can import these helpers to:
- Fetch the status for a ticket
- Create a ticket
- Comment on a ticket

Each capability is implemented as its own async function so they can be
registered as separate tools in the agent layer.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_IMAGE = "ghcr.io/sooperset/mcp-atlassian:latest"
DEFAULT_COMMAND = "docker"


class JiraMCPError(RuntimeError):
    """Domain-specific exception for Jira MCP integration."""


def _required_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise JiraMCPError(f"Environment variable {var_name} is required for Jira MCP access.")
    return value


def _build_server_params() -> StdioServerParameters:
    """
    Create server parameters configured with the Jira credentials from env vars.
    """
    jira_url = os.getenv("JIRA_URL", "")
    jira_username = os.getenv("JIRA_USERNAME", "")
    jira_api_token = os.getenv("JIRA_API_TOKEN", "")

    command = os.getenv("JIRA_MCP_COMMAND", DEFAULT_COMMAND)
    image = os.getenv("JIRA_MCP_IMAGE", DEFAULT_IMAGE)

    args = [
        "run",
        "--rm",
        "-i",
        # Note: Do NOT use -t flag for stdio communication
        "-e", f"JIRA_URL={jira_url}",
        "-e", f"JIRA_USERNAME={jira_username}",
        "-e", f"JIRA_API_TOKEN={jira_api_token}",
        image,
    ]

    return StdioServerParameters(command=command, args=args)


@asynccontextmanager
async def jira_mcp_client() -> AsyncIterator[ClientSession]:
    """
    Async context manager that boots the MCP server and yields a connected session.
    """
    server_params = _build_server_params()
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def _fetch_issue(issue_key: str, fields: Optional[str] = None) -> Dict[str, Any]:
    """Internal helper to fetch an issue."""
    async with jira_mcp_client() as session:
        result = await session.call_tool(
            "jira_get_issue",
            arguments={
                "issue_key": issue_key
            },
        )
        # MCP returns a list of content items
        if result.content and len(result.content) > 0:
            import json
            return json.loads(result.content[0].text)
        return {}


async def get_ticket_status(issue_key: str) -> Dict[str, Any]:
    """
    Fetch a Jira issue and return its status info.
    """
    issue = await _fetch_issue(issue_key, "status,summary")
    fields = issue.get("fields", {})
    status = fields.get("status", {})
    return {
        "key": issue.get("key", issue_key),
        "summary": fields.get("summary", ""),
        "status_name": status.get("name"),
        "status_category": status.get("statusCategory", {}).get("name"),
    }


async def get_ticket_details(issue_key: str) -> Dict[str, Any]:
    """
    Fetch summary, description, and status for a ticket.
    """
    issue = await _fetch_issue(issue_key, "summary,description,status")
    return {
        "key": issue.get("key", issue_key),
        "summary": issue.get("summary"),
        "description": issue.get("description"),
        "status": issue.get("status"),
    }


async def create_ticket(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    assignee: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Jira ticket via the MCP server.
    """
    arguments: Dict[str, Any] = {
        "project_key": project_key,
        "summary": summary,
        "issue_type": issue_type,
    }
    
    if description:
        arguments["description"] = description

    if assignee:
        arguments["assignee"] = assignee

    async with jira_mcp_client() as session:
        result = await session.call_tool(
            "jira_create_issue",
            arguments=arguments
        )
        
        if result.content and len(result.content) > 0:
            import json
            return json.loads(result.content[0].text)
        return {}


async def comment_on_ticket(issue_key: str, comment: str) -> Dict[str, Any]:
    """
    Add a comment to a Jira issue.
    """
    async with jira_mcp_client() as session:
        result = await session.call_tool(
            "jira_add_comment",
            arguments={
                "issue_key": issue_key,
                "comment": comment,
            },
        )
        
        if result.content and len(result.content) > 0:
            import json
            return json.loads(result.content[0].text)
        return {}