"""
Chargebee RAG helper backed by the Chargebee MCP server.

This module exposes a simple async function you can use as the
`docs_client` for JiraChargebeeAgent (or any other agent):

    from aegis.tools.chargebee_rag_tool import query_chargebee_docs
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
import shlex
from typing import Any, AsyncIterator, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_COMMAND = os.getenv("CHARGEBEE_MCP_COMMAND", "")
DEFAULT_TOOL_NAME = os.getenv("CHARGEBEE_MCP_TOOL_NAME", "docs_explainer")


class ChargebeeMCPError(RuntimeError):
    """Domain-specific exception for Chargebee MCP integration."""


def _build_server_params() -> StdioServerParameters:
    """
    Create a server process configured for the Chargebee MCP server.

    This no longer assumes Docker. Instead, you must provide the exact
    command used to start your Chargebee MCP server via:

      - CHARGEBEE_MCP_COMMAND  (required, e.g. 'mcp-chargebee')
      - CHARGEBEE_MCP_ARGS     (optional, shell-style args string)

    Example:
        CHARGEBEE_MCP_COMMAND=\"mcp\"
        CHARGEBEE_MCP_ARGS=\"run chargebee-knowledge-base\"
    """
    command = os.getenv("CHARGEBEE_MCP_COMMAND", "").strip()
    if not command:
        raise ChargebeeMCPError(
            "CHARGEBEE_MCP_COMMAND must be set to the Chargebee MCP server executable."
        )

    raw_args = os.getenv("CHARGEBEE_MCP_ARGS", "").strip()
    args = shlex.split(raw_args) if raw_args else []

    return StdioServerParameters(command=command, args=args)


@asynccontextmanager
async def chargebee_mcp_client() -> AsyncIterator[ClientSession]:
    """
    Async context manager that boots the Chargebee MCP server and yields a client session.
    """
    server_params = _build_server_params()
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def query_chargebee_docs(query: str) -> str:
    """
    Query Chargebee documentation via the MCP server and return plain text.

    This is intended to be used as the `docs_client` for JiraChargebeeAgent:

        agent = JiraChargebeeAgent(
            agent_id="jira_chargebee_agent",
            docs_client=query_chargebee_docs,
        )
    """
    async with chargebee_mcp_client() as session:
        result = await session.call_tool(
            DEFAULT_TOOL_NAME,
            arguments={"query": query},
        )

    if not result.content:
        return "No documentation response returned."

    # Concatenate all content items into a single string.
    parts = []
    for item in result.content:
        text = getattr(item, "text", "") or ""
        parts.append(text)

    return "\n".join(parts).strip() or "No documentation response returned."
