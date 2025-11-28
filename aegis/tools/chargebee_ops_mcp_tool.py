"""
Chargebee RAG helper backed by the Chargebee MCP server.

Available functions:
- query_chargebee_docs(query): Get concept explanations and troubleshooting help
- query_chargebee_code(query, task_id): Get code examples and API documentation
"""
from __future__ import annotations

import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

try:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    HAS_STREAMABLE_HTTP = True
except ImportError:
    HAS_STREAMABLE_HTTP = False
    print("Warning: mcp.client.streamable_http not available, using fallback")

import httpx

DEFAULT_SERVER_URL = "https://scalableai-test.mcp.chargebee.com/knowledge_base_agent"
DEFAULT_TOOL_NAME = "query_knowledge_base"


class ChargebeeMCPError(RuntimeError):
    """Domain-specific exception for Chargebee MCP integration."""


if HAS_STREAMABLE_HTTP:
    @asynccontextmanager
    async def chargebee_mcp_client() -> AsyncIterator[ClientSession]:
        """Connect using Streamable HTTP client"""
        server_url = os.getenv("CHARGEBEE_MCP_URL", DEFAULT_SERVER_URL)
        
        # streamablehttp_client returns (read, write, get_session_id)
        async with streamablehttp_client(server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
else:
    # Fallback implementation
    class SimpleSSEClient:
        def __init__(self, url: str):
            self.url = url
            self.client = httpx.AsyncClient(timeout=60.0)
            self.request_id = 0
            self.initialized = False
        
        async def initialize(self):
            """Perform MCP initialize handshake"""
            if self.initialized:
                return
            
            self.request_id += 1
            async with self.client.stream(
                "POST",
                self.url,
                json={
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "aegis-chargebee-client",
                            "version": "1.0"
                        }
                    }
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            ) as response:
                print(f"Initialize response status: {response.status_code}")
                async for line in response.aiter_lines():
                    print(f"Initialize SSE line: {line}")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data and data != "[DONE]":
                            try:
                                msg = json.loads(data)
                                if "result" in msg:
                                    self.initialized = True
                                    print(f"Initialized successfully: {msg}")
                                elif "error" in msg:
                                    raise ChargebeeMCPError(f"Initialize failed: {msg['error']}")
                            except json.JSONDecodeError:
                                pass
        
        async def call_tool(self, name: str, arguments: dict) -> Any:
            self.request_id += 1
            
            # Try SSE endpoint
            try:
                async with self.client.stream(
                    "POST",
                    self.url,
                    json={
                        "jsonrpc": "2.0",
                        "id": self.request_id,
                        "method": "tools/call",
                        "params": {
                            "name": name,
                            "arguments": arguments
                        }
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream"
                    }
                ) as response:
                    result = []
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data and data != "[DONE]":
                                try:
                                    result.append(json.loads(data))
                                except:
                                    result.append(data)
                    return result
            except Exception as e:
                raise ChargebeeMCPError(f"SSE request failed: {e}")
        
        async def list_tools(self):
            self.request_id += 1
            async with self.client.stream(
                "POST",
                self.url,
                json={
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "method": "tools/list",
                    "params": {}
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                }
            ) as response:
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                result = []
                async for line in response.aiter_lines():
                    print(f"SSE line: {line}")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data and data != "[DONE]":
                            try:
                                result.append(json.loads(data))
                            except:
                                result.append(data)
                print(f"Parsed result: {result}")
                return result
        
        async def close(self):
            await self.client.aclose()
    
    @asynccontextmanager
    async def chargebee_mcp_client() -> AsyncIterator[SimpleSSEClient]:
        """Fallback SSE client"""
        server_url = os.getenv("CHARGEBEE_MCP_URL", DEFAULT_SERVER_URL)
        client = SimpleSSEClient(server_url)
        try:
            await client.initialize()
            yield client
        finally:
            await client.close()


async def list_chargebee_tools() -> list[str]:
    """List all available tools"""
    async with chargebee_mcp_client() as client:
        result = await client.list_tools()
        # result is a ListToolsResult object with a 'tools' attribute
        # Each tool has a 'name' attribute
        if hasattr(result, 'tools'):
            return [tool.name for tool in result.tools]
        return []


async def query_chargebee_docs(query: str) -> str:
    """
    Query Chargebee documentation via the MCP server.
    
    Args:
        query: The search query or question about Chargebee docs
    
    Returns:
        String containing the documentation response
    """
    try:
        async with chargebee_mcp_client() as client:
            # List tools to find the right one
            tools_result = await client.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]
            
            print(f"Available tools: {tool_names}")
            
            # Use the first available tool or configured one
            tool_name = tool_names[0] if tool_names else DEFAULT_TOOL_NAME
            print(f"Using tool: {tool_name}")
            
            # Call the tool
            result = await client.call_tool(
                tool_name,
                arguments={
                    "task_id": None,
                    "user_query": query
                }
            )
            
            # Parse response - result is a CallToolResult with content attribute
            if hasattr(result, 'content') and result.content:
                # Extract text from content items
                texts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        texts.append(item.text)
                return "\n".join(texts) if texts else "No response"
            
            return str(result)
            
    except Exception as e:
        if isinstance(e, ChargebeeMCPError):
            raise
        raise ChargebeeMCPError(f"Failed to query: {str(e)}") from e


async def query_chargebee_code(query: str, task_id: str = None) -> str:
    """
    Query Chargebee for code examples and API documentation via the code_generation_agent.
    
    Args:
        query: The code-related query (e.g., "How to create a subscription in Node.js")
        task_id: Optional task ID to reuse context from previous calls
    
    Returns:
        String containing code examples and API documentation
    """
    try:
        async with chargebee_mcp_client() as client:
            # Call the code_generation_agent tool
            result = await client.call_tool(
                "code_generation_agent",
                arguments={
                    "task_id": task_id,
                    "user_query": query
                }
            )
            
            # Parse response - result is a CallToolResult with content attribute
            if hasattr(result, 'content') and result.content:
                # Extract text from content items
                texts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        # Try to parse as JSON first
                        try:
                            import json
                            response = json.loads(item.text)
                            # Extract the content from the JSON response
                            if isinstance(response, dict):
                                content = response.get('output', {}).get('content', item.text)
                                texts.append(content)
                            else:
                                texts.append(item.text)
                        except json.JSONDecodeError:
                            texts.append(item.text)
                return "\n".join(texts) if texts else "No response"
            
            return str(result)
            
    except Exception as e:
        if isinstance(e, ChargebeeMCPError):
            raise
        raise ChargebeeMCPError(f"Failed to query code: {str(e)}") from e


async def test_chargebee_connection():
    """Test connection and list tools"""
    try:
        print(f"Connecting to: {os.getenv('CHARGEBEE_MCP_URL', DEFAULT_SERVER_URL)}")
        print(f"Using Streamable HTTP client: {HAS_STREAMABLE_HTTP}")
        tools = await list_chargebee_tools()
        print("✅ Connected successfully!")
        print(f"Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool}")
        return tools
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        #traceback.print_exc()
        raise