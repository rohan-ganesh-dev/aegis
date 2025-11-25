"""
Supervisor CLI Runner.

Starts the supervisor agent and demonstrates agent-to-agent messaging.
This is a simple runner for development and testing.
"""

import asyncio
import logging
import sys
from datetime import datetime

from aegis.agents.base import AgentMessage
from aegis.agents.growth import GrowthAgent
from aegis.agents.integration import IntegrationAgent
from aegis.agents.onboarding import OnboardingAgent
from aegis.agents.proactive import ProactiveAgent
from aegis.agents.supervisor import SupervisorAgent
from aegis.config import config
from aegis.transports.in_memory_transport import InMemoryTransport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def demonstrate_agent_messaging():
    """
    Demonstrate the Aegis multi-agent system.

    This function:
    1. Creates transport and agents
    2. Starts all agents
    3. Sends sample messages
    4. Logs routing and responses
    5. Cleans up
    """
    logger.info("=" * 80)
    logger.info("Starting Aegis Supervisor Demo")
    logger.info("=" * 80)

    # Create transport
    transport = InMemoryTransport()
    await transport.start()
    logger.info("✓ Transport initialized")

    # Create agents
    supervisor = SupervisorAgent(transport=transport)
    onboarding = OnboardingAgent(transport=transport)
    integration = IntegrationAgent(transport=transport)
    proactive = ProactiveAgent(transport=transport)
    growth = GrowthAgent(transport=transport)

    # Start all agents
    agents = [supervisor, onboarding, integration, proactive, growth]
    for agent in agents:
        await agent.start()
    logger.info(f"✓ Started {len(agents)} agents")

    # Wait for initialization
    await asyncio.sleep(0.5)

    # Demonstrate different task types
    sample_tasks = [
        {
            "intent": "onboarding",
            "customer_id": "customer_abc123",
            "task_type": "documentation",
            "query": "How do I get started with the API?",
        },
        {
            "intent": "migration",
            "customer_id": "customer_xyz789",
            "task_type": "migration_plan",
            "source_platform": "AWS",
            "workload_size": "medium",
        },
        {
            "intent": "integration",
            "customer_id": "customer_def456",
            "task_type": "marketplace_search",
            "use_case": "payment processing",
        },
        {
            "intent": "churn",
            "customer_id": "customer_atrisk",
            "task_type": "churn_analysis",
        },
    ]

    logger.info(f"\n{'=' * 80}")
    logger.info(f"Sending {len(sample_tasks)} sample tasks to Supervisor")
    logger.info(f"{'=' * 80}\n")

    # Send tasks to supervisor
    for i, task_payload in enumerate(sample_tasks, 1):
        logger.info(f"\n--- Task {i}/{len(sample_tasks)} ---")
        logger.info(f"Intent: {task_payload['intent']}")
        logger.info(f"Customer: {task_payload['customer_id']}")

        message = AgentMessage(
            sender="cli_runner",
            recipient="supervisor",
            type="task",
            payload=task_payload,
        )

        await transport.send(message)
        logger.info(f"✓ Sent message {message.id}")

        # Allow time for processing
        await asyncio.sleep(1.0)

    logger.info(f"\n{'=' * 80}")
    logger.info("Demo complete - all tasks routed")
    logger.info(f"{'=' * 80}\n")

    # Give agents time to process
    await asyncio.sleep(2.0)

    # Stop all agents
    for agent in agents:
        await agent.stop()
    logger.info("✓ Stopped all agents")

    await transport.stop()
    logger.info("✓ Transport stopped")

    logger.info("\n" + "=" * 80)
    logger.info("Aegis Supervisor Demo Complete")
    logger.info("=" * 80)


async def main():
    """Main entry point."""
    try:
        await demonstrate_agent_messaging()
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Error running supervisor demo: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
