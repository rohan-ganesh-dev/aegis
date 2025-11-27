# test_jira.py
import asyncio
import nest_asyncio
nest_asyncio.apply()
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aegis.tools.jira_mcp import get_ticket_details, create_ticket, comment_on_ticket
from aegis.tools.chargebee_ops_mcp_tool import (
    query_chargebee_docs,
    query_chargebee_code,
    test_chargebee_connection as ops_test_chargebee_connection,
)

async def test_connection():
    """Test basic connection to Jira MCP server"""
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run",
            "--rm",
            "-i",
            "-e", "JIRA_URL=",
            "-e", "JIRA_USERNAME=",
            "-e", "JIRA_API_TOKEN=",
            "ghcr.io/sooperset/mcp-atlassian:latest",
        ],
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ Connected successfully!")
                
                # List available tools
                tools = await session.list_tools()
                print(f"✅ Available tools: {len(tools.tools)}")
                for tool in tools.tools[:5]:
                    print(f"  - {tool.name}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")


async def test_get_ticket_status(ticket_key):
    """Test fetching a ticket's status"""
    try:
        result = await get_ticket_details(ticket_key)  # Use a real ticket key
        print(" final result is",result)
        assert "key" in result
        assert "summary" in result
    except Exception as e:
        print(f"❌ Failed: {e}")


async def test_create_ticket():
    """Test creating a new ticket"""
    try:
        result = await create_ticket(
            project_key="KAN",  # Your project key
            summary="Testing out ticket creation",
            description="This is a test",
            issue_type="Bug"
        )
        print(f"✅ Created ticket: {result.get('key')}")
        return result.get('key')
    except Exception as e:
        print(f"❌ Failed: {e}")


async def test_comment():
    """Test adding a comment"""
    ticket_key = "KAN-7"  # Use existing or created ticket
    try:
        result = await comment_on_ticket(
            ticket_key, 
            "Test comment from API for KAN-7"
        )
        print(f"✅ Added comment to {ticket_key}")
    except Exception as e:
        print(f"❌ Failed: {e}")


async def test_chargebee_connection():
    """Smoke-test connectivity to the Chargebee MCP server."""
    try:
        await ops_test_chargebee_connection()
    except Exception as e:
        print(f"❌ Chargebee connection failed: {e}")


async def test_chargebee_docs_query(
    query: str = "Explain how metered billing works in Chargebee.",
):
    """Test querying Chargebee docs via MCP."""
    try:
        response = await query_chargebee_docs(query)
        print("✅ Chargebee docs response:\n", response)
    except Exception as e:
        print(f"❌ Chargebee docs query failed: {e}")


async def test_chargebee_code_query(
    query: str = "Show sample code to create a subscription via Chargebee API.",
    task_id: str | None = None,
):
    """Test the Chargebee code-generation MCP tool."""
    try:
        response = await query_chargebee_code(query, task_id=task_id)
        print("✅ Chargebee code response:\n", response)
    except Exception as e:
        print(f"❌ Chargebee code query failed: {e}")


if __name__ == "__main__":
    # asyncio.run(test_connection())
    # asyncio.run(test_get_ticket_status("KAN-7"))
    # asyncio.run(test_create_ticket())
    # asyncio.run(test_comment())
    # asyncio.run(test_chargebee_connection())
    # asyncio.run(test_chargebee_docs_query("What is difference between subscriptiona and customer?"))
    asyncio.run(test_chargebee_code_query("generate code for connecting to chargebee server"))
    pass