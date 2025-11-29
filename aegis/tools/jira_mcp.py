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

# Try to import MCP, but provide fallbacks if not available
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    # MCP is not available (likely Python < 3.10)
    MCP_AVAILABLE = False
    ClientSession = None  # type: ignore
    StdioServerParameters = None  # type: ignore
    stdio_client = None  # type: ignore

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
    if not MCP_AVAILABLE:
        raise JiraMCPError("MCP is not available. Requires Python 3.10+ and mcp package installed.")
    
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
    if not MCP_AVAILABLE:
        raise JiraMCPError("MCP is not available. Requires Python 3.10+ and mcp package installed.")
        
    server_params = _build_server_params()
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


# --- Direct API Fallback (for Python < 3.10) ---

import aiohttp
import base64
import json

def _get_auth_header() -> Dict[str, str]:
    """Generate Basic Auth header for Jira."""
    username = _required_env("JIRA_USERNAME")
    api_token = _required_env("JIRA_API_TOKEN")
    auth_str = f"{username}:{api_token}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    return {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def _get_base_url() -> str:
    """Get Jira base URL."""
    url = _required_env("JIRA_URL").rstrip("/")
    return url

async def _get_ticket_status_direct(issue_key: str) -> Dict[str, Any]:
    """Direct API call to get ticket status."""
    url = f"{_get_base_url()}/rest/api/3/issue/{issue_key}"
    headers = _get_auth_header()
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 404:
                return {"error": "Ticket not found"}
            if resp.status != 200:
                text = await resp.text()
                raise JiraMCPError(f"Jira API error ({resp.status}): {text}")
            
            data = await resp.json()
            fields = data.get("fields", {})
            return {
                "key": data.get("key"),
                "summary": fields.get("summary"),
                "status": fields.get("status", {}).get("name"),
                "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
                "priority": fields.get("priority", {}).get("name"),
                "description": fields.get("description")
            }

async def _create_ticket_direct(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    assignee: Optional[str] = None,
) -> Dict[str, Any]:
    """Direct API call to create ticket."""
    url = f"{_get_base_url()}/rest/api/3/issue"
    headers = _get_auth_header()
    
    # Construct ADF (Atlassian Document Format) for description if needed
    # For simplicity, we'll try to use the string description or a simple ADF wrapper
    # Jira Cloud often requires ADF for 'description' field in v3 API
    
    # Simple ADF wrapper for text
    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": description or "No description provided."
                    }
                ]
            }
        ]
    }
    
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": description_adf
        }
    }
    
    # Note: Assignee requires accountId, which is hard to guess from name/email directly without search.
    # Skipping assignee for direct fallback to avoid complexity.
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise JiraMCPError(f"Jira API error ({resp.status}): {text}")
            
            data = await resp.json()
            return {
                "key": data.get("key"),
                "id": data.get("id"),
                "self": data.get("self")
            }

async def _comment_on_ticket_direct(issue_key: str, comment: str) -> Dict[str, Any]:
    """Direct API call to add comment."""
    url = f"{_get_base_url()}/rest/api/3/issue/{issue_key}/comment"
    headers = _get_auth_header()
    
    # ADF for comment
    comment_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": comment
                    }
                ]
            }
        ]
    }
    
    payload = {"body": comment_adf}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 201:
                text = await resp.text()
                raise JiraMCPError(f"Jira API error ({resp.status}): {text}")
            
            data = await resp.json()
            return {"id": data.get("id"), "message": "Comment added successfully"}


# --- Main Tool Functions ---

async def get_ticket_details(issue_key: str) -> Dict[str, Any]:
    """
    Get comprehensive details for a specific Jira ticket.
    
    Use this tool when you need detailed information about a Jira issue including
    all fields, description, comments, and metadata. For just the status, prefer
    using get_ticket_status instead.
    
    Args:
        issue_key: The Jira issue key (e.g., 'KAN-7', 'PROJ-123').
    
    Returns:
        A dictionary containing all ticket details including key, summary, status,
        assignee, priority, description, and other custom fields.
    """
    if not MCP_AVAILABLE:
        return await _get_ticket_status_direct(issue_key)
        
    async with jira_mcp_client() as session:
        result = await session.call_tool(
            "jira_get_issue",
            arguments={"issue_key": issue_key}
        )
        
        if result.content and len(result.content) > 0:
            import json
            try:
                response_text = result.content[0].text
                if not response_text or response_text.strip() == "":
                    logger.warning(f"Empty response from MCP server for issue {issue_key}")
                    return {"error": "Empty response from Jira MCP server"}
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response for issue {issue_key}: {e}")
                logger.error(f"Response text: {result.content[0].text}")
                return {"error": f"Invalid JSON response from Jira MCP server: {str(e)}"}
        return {"error": "No content returned"}


async def get_ticket_status(issue_key: str) -> str:
    """
    Get the current status, summary, and other key details of a Jira ticket.
    
    Use this tool when the user asks about the status of a Jira ticket, mentions
    a ticket key (e.g., 'KAN-7', 'PROJ-123'), or wants to know what's happening
    with a specific issue.
    
    Args:
        issue_key: The Jira issue key (e.g., 'KAN-7', 'PROJ-123'). 
                  Can be in uppercase or lowercase - will be handled automatically.
    
    Returns:
        A formatted string containing the ticket key, status, and summary.
        Example: "Ticket KAN-7: In Progress - Fix login bug"
    """
    details = await get_ticket_details(issue_key)
    if "error" in details:
        return f"Error: {details['error']}"
    
    # Handle different response structures
    if "fields" in details: # This path is for MCP response
        status = details["fields"].get("status", {}).get("name", "Unknown")
        summary = details["fields"].get("summary", "")
        return f"Ticket {issue_key}: {status} - {summary}"
    
    # Fallback/Direct structure
    status = details.get("status", "Unknown")
    summary = details.get("summary", "")
    return f"Ticket {issue_key}: {status} - {summary}"


async def create_ticket(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    assignee: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new Jira ticket when users report issues or request features.
    
    Use this tool when:
    - Users report bugs, problems, or errors
    - Users request new features or improvements
    - Users provide negative feedback that should be tracked
    - Creating follow-up tasks or action items
    
    Args:
        project_key: The Jira project key (e.g., 'KAN', 'PROJ'). Always ask the user
                    for the project key if not mentioned in the conversation.
        summary: A concise title/summary for the ticket (e.g., 'Fix login bug').
        description: Detailed description of the issue or request.
        issue_type: Type of issue - 'Task', 'Bug', 'Story', or 'Epic'. Default is 'Task'.
        assignee: Optional username or email of the person to assign the ticket to.
    
    Returns:
        A dictionary containing the created ticket's key, id, and URL.
    """
    if not MCP_AVAILABLE:
        return await _create_ticket_direct(project_key, summary, description, issue_type, assignee)

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
    Add a comment to an existing Jira ticket.
    
    Use this tool when you need to:
    - Add updates or progress notes to existing tickets
    - Record additional information about a ticket
    - Communicate status updates or clarifications
    
    Args:
        issue_key: The Jira issue key to comment on (e.g., 'KAN-7', 'PROJ-123').
        comment: The comment text to add to the ticket.
    
    Returns:
        A dictionary with the comment ID and a success message.
    """
    if not MCP_AVAILABLE:
        return await _comment_on_ticket_direct(issue_key, comment)

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