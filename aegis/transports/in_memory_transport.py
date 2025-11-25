"""
In-Memory Transport.

Simple queue-based transport for agent-to-agent messaging in single-process mode.
Useful for development and testing.
"""

import asyncio
import logging
from typing import Callable, Any, Dict

from aegis.agents.base import AgentMessage, AgentTransport

logger = logging.getLogger(__name__)


class InMemoryTransport(AgentTransport):
    """
    In-memory message queue for agent communication.

    Messages are delivered asynchronously via registered handlers.
    This implementation is single-process only.
    """

    def __init__(self):
        """Initialize in-memory transport."""
        self.logger = logging.getLogger(f"{__name__}.InMemoryTransport")
        self.handlers: Dict[str, Callable[[AgentMessage], Any]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task: asyncio.Task = None

    async def start(self) -> None:
        """Start the transport message processor."""
        if self._running:
            return

        self.logger.info("Starting in-memory transport")
        self._running = True
        self._processor_task = asyncio.create_task(self._process_messages())

    async def stop(self) -> None:
        """Stop the transport message processor."""
        self.logger.info("Stopping in-memory transport")
        self._running = False

        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

    async def send(self, message: AgentMessage) -> None:
        """
        Send a message through the transport.

        Args:
            message: AgentMessage to send
        """
        self.logger.debug(
            f"Sending message {message.id}: {message.sender} -> {message.recipient}"
        )
        await self.message_queue.put(message)

    async def subscribe(
        self, agent_id: str, handler: Callable[[AgentMessage], Any]
    ) -> None:
        """
        Subscribe an agent to receive messages.

        Args:
            agent_id: Agent identifier
            handler: Async callback for handling messages
        """
        self.logger.info(f"Subscribing agent: {agent_id}")
        self.handlers[agent_id] = handler

    async def unsubscribe(self, agent_id: str) -> None:
        """
        Unsubscribe an agent from receiving messages.

        Args:
            agent_id: Agent identifier
        """
        self.logger.info(f"Unsubscribing agent: {agent_id}")
        self.handlers.pop(agent_id, None)

    async def _process_messages(self) -> None:
        """
        Internal message processor loop.

        Delivers messages to registered handlers.
        """
        self.logger.info("Message processor started")

        while self._running:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=1.0
                )

                # Find handler for recipient
                handler = self.handlers.get(message.recipient)

                if handler:
                    self.logger.debug(f"Delivering message {message.id} to {message.recipient}")
                    try:
                        await handler(message)
                    except Exception as e:
                        self.logger.error(
                            f"Error in handler for {message.recipient}: {e}",
                            exc_info=True,
                        )
                else:
                    self.logger.warning(
                        f"No handler registered for recipient: {message.recipient}"
                    )

            except asyncio.TimeoutError:
                # No messages, continue loop
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}", exc_info=True)

        self.logger.info("Message processor stopped")
