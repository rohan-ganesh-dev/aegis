"""
Zendesk Client (Mock).

Provides support ticket management capabilities.
This is a stub - production should use actual Zendesk API.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ZendeskClient:
    """
    Mock Zendesk API client for support operations.

    BOILERPLATE: Production should use real Zendesk SDK.
    """

    def __init__(self, api_key: str = "PLACEHOLDER_KEY"):
        """
        Initialize Zendesk client.

        Args:
            api_key: Zendesk API key (placeholder)
        """
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.ZendeskClient")
        self.logger.warning("Using mock Zendesk client - NO REAL API CALLS")

    async def get_tickets(
        self, customer_email: str, status: str = "open"
    ) -> List[Dict[str, Any]]:
        """
        Get support tickets for customer.

        BOILERPLATE: Returns mock ticket data.

        Args:
            customer_email: Customer email address
            status: Ticket status filter

        Returns:
            List of tickets
        """
        self.logger.info(f"Fetching {status} tickets for: {customer_email}")

        # TODO: Use real Zendesk API
        # from zenpy import Zenpy
        # tickets = zenpy_client.search(type='ticket', requester=customer_email)

        mock_tickets = [
            {
                "id": "ticket_001",
                "subject": "API rate limit errors",
                "status": "open",
                "priority": "high",
                "created_at": "2024-01-15T10:00:00Z",
                "requester_email": customer_email,
                "description": "Getting 429 errors when calling the API...",
            },
            {
                "id": "ticket_002",
                "subject": "Billing question",
                "status": "pending",
                "priority": "normal",
                "created_at": "2024-01-14T14:30:00Z",
                "requester_email": customer_email,
                "description": "Can you explain the charges on my last invoice?",
            },
        ]

        # Filter by status
        filtered = [t for t in mock_tickets if t["status"] == status]
        return filtered

    async def create_ticket(
        self, subject: str, description: str, customer_email: str, priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Create a new support ticket.

        BOILERPLATE: Mock ticket creation.

        Args:
            subject: Ticket subject
            description: Ticket description
            customer_email: Customer email
            priority: Ticket priority

        Returns:
            Created ticket details
        """
        self.logger.info(f"Creating ticket for {customer_email}: {subject}")

        # TODO: Use real Zendesk API
        mock_ticket = {
            "id": "ticket_mock_new",
            "subject": subject,
            "description": description,
            "status": "new",
            "priority": priority,
            "requester_email": customer_email,
            "created_at": "2024-01-01T00:00:00Z",
        }

        self.logger.warning("BOILERPLATE: Mock ticket, not actually created")
        return mock_ticket

    async def update_ticket(
        self, ticket_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing ticket.

        BOILERPLATE: Mock ticket update.

        Args:
            ticket_id: Ticket ID
            updates: Fields to update

        Returns:
            Updated ticket details
        """
        self.logger.info(f"Updating ticket {ticket_id}: {updates}")

        # TODO: Use real Zendesk API
        mock_updated_ticket = {
            "id": ticket_id,
            **updates,
            "updated_at": "2024-01-01T00:00:00Z",
        }

        self.logger.warning("BOILERPLATE: Mock update, not actually applied")
        return mock_updated_ticket
