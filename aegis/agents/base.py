"""
Base agent classes and message schemas for Aegis.

This module defines the foundational interfaces for the multi-agent system,
including message schemas, agent lifecycle, and transport abstractions.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """
    Standard message format for agent-to-agent communication.

    Attributes:
        id: Unique message identifier
        sender: ID of the sending agent
        recipient: ID of the receiving agent
        type: Message type (e.g., 'task', 'response', 'event')
        payload: Message payload as a dictionary
        timestamp: Message creation timestamp
    """

    sender: str
    recipient: str
    type: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class AgentResponse:
    """
    Standard response format from agent message handlers.

    Attributes:
        text: Human-readable response text
        actions: List of actions to be executed
        attachments: Additional data attachments
        metadata: Extra metadata for tracking/debugging
    """

    text: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return asdict(self)


@dataclass
class CustomerContext:
    """
    Per-customer context for maintaining state across interactions.

    Attributes:
        customer_id: Unique customer identifier
        conversation_history: List of previous messages
        preferences: Customer preferences
        metadata: Additional context data
    """

    customer_id: str
    conversation_history: List[AgentMessage] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append(message)


class AgentTransport(ABC):
    """
    Abstract transport interface for agent-to-agent messaging.

    Concrete implementations include in-memory queues, Redis, etc.
    """

    @abstractmethod
    async def send(self, message: AgentMessage) -> None:
        """Send a message to the transport."""
        pass

    @abstractmethod
    async def subscribe(
        self, agent_id: str, handler: Callable[[AgentMessage], Any]
    ) -> None:
        """Subscribe an agent to receive messages."""
        pass

    @abstractmethod
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe an agent from receiving messages."""
        pass


class BaseAgent(ABC):
    """
    Base class for all Aegis agents.

    Provides lifecycle management and message handling interface.
    Agents should inherit from this class and implement handle_message.
    """

    def __init__(
        self,
        agent_id: str,
        transport: Optional[AgentTransport] = None,
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier for this agent
            transport: Message transport (optional)
        """
        self.agent_id = agent_id
        self.transport = transport
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self._running = False

    async def start(self) -> None:
        """
        Start the agent and subscribe to transport.

        BOILERPLATE: Implement agent initialization logic.
        """
        self.logger.info(f"Starting agent: {self.agent_id}")
        self._running = True

        if self.transport:
            await self.transport.subscribe(self.agent_id, self._handle_message_wrapper)

        # TODO: Initialize agent-specific resources (vector DB, API clients, etc.)
        self.logger.info(f"Agent {self.agent_id} started successfully")

    async def stop(self) -> None:
        """
        Stop the agent and cleanup resources.

        BOILERPLATE: Implement cleanup logic.
        """
        self.logger.info(f"Stopping agent: {self.agent_id}")
        self._running = False

        if self.transport:
            await self.transport.unsubscribe(self.agent_id)

        # TODO: Cleanup agent-specific resources
        self.logger.info(f"Agent {self.agent_id} stopped successfully")

    async def _handle_message_wrapper(self, message: AgentMessage) -> None:
        """Internal wrapper for message handling with error handling."""
        try:
            self.logger.debug(f"Received message: {message.id} from {message.sender}")
            response = await self.handle_message(message)
            self.logger.debug(f"Processed message: {message.id}")

            # Send response if applicable
            if response and self.transport:
                response_msg = AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    type="response",
                    payload=response.to_dict(),
                )
                await self.transport.send(response_msg)

        except Exception as e:
            self.logger.error(f"Error handling message {message.id}: {e}", exc_info=True)

    @abstractmethod
    async def handle_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """
        Handle incoming message and return response.

        Args:
            message: Incoming agent message

        Returns:
            AgentResponse or None if no response needed
        """
        pass
