"""
Test message schema serialization and deserialization.

Validates that AgentMessage can be properly serialized to/from dict format
for transport and storage.
"""

import pytest
from datetime import datetime

from aegis.agents.base import AgentMessage, AgentResponse, CustomerContext


def test_agent_message_creation():
    """Test basic AgentMessage creation."""
    msg = AgentMessage(
        sender="agent1",
        recipient="agent2",
        type="task",
        payload={"key": "value"},
    )

    assert msg.sender == "agent1"
    assert msg.recipient == "agent2"
    assert msg.type == "task"
    assert msg.payload == {"key": "value"}
    assert msg.id is not None  # Auto-generated
    assert isinstance(msg.timestamp, datetime)


def test_agent_message_to_dict():
    """Test AgentMessage serialization to dict."""
    msg = AgentMessage(
        sender="agent1",
        recipient="agent2",
        type="task",
        payload={"data": 123},
    )

    msg_dict = msg.to_dict()

    assert msg_dict["sender"] == "agent1"
    assert msg_dict["recipient"] == "agent2"
    assert msg_dict["type"] == "task"
    assert msg_dict["payload"] == {"data": 123}
    assert "id" in msg_dict
    assert "timestamp" in msg_dict
    assert isinstance(msg_dict["timestamp"], str)  # ISO format


def test_agent_message_from_dict():
    """Test AgentMessage deserialization from dict."""
    msg_dict = {
        "id": "test_id_123",
        "sender": "agent1",
        "recipient": "agent2",
        "type": "response",
        "payload": {"result": "success"},
        "timestamp": "2024-01-01T00:00:00",
    }

    msg = AgentMessage.from_dict(msg_dict)

    assert msg.id == "test_id_123"
    assert msg.sender == "agent1"
    assert msg.recipient == "agent2"
    assert msg.type == "response"
    assert msg.payload == {"result": "success"}
    assert isinstance(msg.timestamp, datetime)


def test_agent_message_roundtrip():
    """Test AgentMessage serialization roundtrip."""
    original = AgentMessage(
        sender="agent_a",
        recipient="agent_b",
        type="event",
        payload={"event_type": "billing_alert"},
    )

    # Serialize and deserialize
    msg_dict = original.to_dict()
    reconstructed = AgentMessage.from_dict(msg_dict)

    assert reconstructed.sender == original.sender
    assert reconstructed.recipient == original.recipient
    assert reconstructed.type == original.type
    assert reconstructed.payload == original.payload
    assert reconstructed.id == original.id


def test_agent_response_creation():
    """Test AgentResponse creation."""
    response = AgentResponse(
        text="Task completed successfully",
        actions=[{"type": "send_notification"}],
        attachments=[{"file": "report.pdf"}],
        metadata={"execution_time": 1.5},
    )

    assert response.text == "Task completed successfully"
    assert len(response.actions) == 1
    assert len(response.attachments) == 1
    assert response.metadata["execution_time"] == 1.5


def test_agent_response_to_dict():
    """Test AgentResponse serialization."""
    response = AgentResponse(
        text="Done",
        actions=[{"type": "update"}],
    )

    response_dict = response.to_dict()

    assert response_dict["text"] == "Done"
    assert response_dict["actions"] == [{"type": "update"}]
    assert "attachments" in response_dict
    assert "metadata" in response_dict


def test_customer_context_creation():
    """Test CustomerContext creation."""
    context = CustomerContext(
        customer_id="customer_123",
        preferences={"timezone": "UTC"},
        metadata={"tier": "enterprise"},
    )

    assert context.customer_id == "customer_123"
    assert context.preferences["timezone"] == "UTC"
    assert len(context.conversation_history) == 0


def test_customer_context_add_message():
    """Test adding messages to customer context."""
    context = CustomerContext(customer_id="customer_123")

    msg1 = AgentMessage(
        sender="user",
        recipient="agent",
        type="task",
        payload={"query": "help"},
    )
    msg2 = AgentMessage(
        sender="agent",
        recipient="user",
        type="response",
        payload={"answer": "How can I help?"},
    )

    context.add_message(msg1)
    context.add_message(msg2)

    assert len(context.conversation_history) == 2
    assert context.conversation_history[0] == msg1
    assert context.conversation_history[1] == msg2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
