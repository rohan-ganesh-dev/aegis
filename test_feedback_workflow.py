"""
Test script for the feedback workflow.

This script tests:
1. Positive feedback handling
2. Negative feedback handling with ticket creation
"""

import asyncio
import logging
from aegis.agents.jira_chargebee_agent import JiraChargebeeAgent

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_feedback_workflow():
    """Test the feedback handling functionality."""
    
    print("🚀 Initializing JiraChargebeeAgent...")
    agent = JiraChargebeeAgent(
        agent_id="test-feedback-agent",
        feedback_project_key="KAN"  # Use your project key
    )
    
    # Test positive feedback
    print("\n" + "="*60)
    print("TEST 1: Positive Feedback")
    print("="*60)
    
    query = "What is the difference between subscription and customer?"
    docs_answer = "A subscription represents a recurring billing arrangement, while a customer is the entity that owns one or more subscriptions."
    
    response = await agent.handle_feedback(
        query=query,
        docs_answer=docs_answer,
        feedback_type="positive"
    )
    
    print(f"\n✅ Response: {response.text}")
    print(f"📊 Metadata: {response.metadata}")
    
    # Test negative feedback without additional comments
    print("\n" + "="*60)
    print("TEST 2: Negative Feedback (No Additional Comments)")
    print("="*60)
    
    response = await agent.handle_feedback(
        query=query,
        docs_answer=docs_answer,
        feedback_type="negative"
    )
    
    print(f"\n📝 Response: {response.text}")
    print(f"📊 Metadata: {response.metadata}")
    if "ticket_key" in response.metadata:
        print(f"🎫 Ticket created: {response.metadata['ticket_key']}")
    
    # Test negative feedback with additional comments
    print("\n" + "="*60)
    print("TEST 3: Negative Feedback (With Additional Comments)")
    print("="*60)
    
    response = await agent.handle_feedback(
        query=query,
        docs_answer=docs_answer,
        feedback_type="negative",
        additional_feedback="The answer doesn't explain the pricing implications or how they relate to each other in the billing cycle."
    )
    
    print(f"\n📝 Response: {response.text}")
    print(f"📊 Metadata: {response.metadata}")
    if "ticket_key" in response.metadata:
        print(f"🎫 Ticket created: {response.metadata['ticket_key']}")
    
    print("\n" + "="*60)
    print("✅ All feedback tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_feedback_workflow())
