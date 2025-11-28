import asyncio
import os
import logging
from aegis.agents.jira_chargebee_agent import JiraChargebeeAgent
from aegis.agents.base import AgentMessage

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_agent():
    # Set environment variables
    os.environ["CHARGEBEE_MCP_URL"] = "https://scalableai-test.mcp.chargebee.com/knowledge_base_agent"
    # Jira env vars should be set in the environment or added here if missing
    
    print("🚀 Initializing JiraChargebeeAgent...")
    agent = JiraChargebeeAgent(agent_id="test-agent-1")
    
    # Test case: KAN-7 (assuming this ticket exists from previous context)
    issue_key = "KAN-7"
    
    print(f"\n📝 Sending message to agent for issue {issue_key} (Dry Run)...")
    message = AgentMessage(
        sender="user",
        recipient="test-agent-1",
        type="task",
        payload={
            "issue_key": issue_key,
            "dry_run": True, # Set to False to actually post the comment
            "query": "How does metered billing work?" # Optional: override query derived from ticket
        }
    )
    
    try:
        response = await agent.handle_message(message)
        
        print("\n✅ Agent Response:")
        print(f"Text: {response.text}")
        print(f"Metadata: {response.metadata}")
        
        if response.attachments:
            print("\n📎 Attachments:")
            for attachment in response.attachments:
                if "preview_comment" in attachment:
                    print("\n--- Preview Comment ---")
                    print(attachment["preview_comment"])
                    print("-----------------------")
                if "docs_answer" in attachment:
                    print("\n--- Docs Answer ---")
                    # Print first 500 chars to avoid clutter
                    print(attachment["docs_answer"][:500] + "..." if len(attachment["docs_answer"]) > 500 else attachment["docs_answer"])
                    print("-------------------")
                    
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
