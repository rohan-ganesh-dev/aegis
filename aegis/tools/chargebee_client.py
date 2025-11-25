"""
Chargebee Client (Mock).

Provides billing and subscription management capabilities.
This is a stub - production should use actual Chargebee API.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ChargebeeClient:
    """
    Mock Chargebee API client for billing operations.

    BOILERPLATE: Production should use real Chargebee SDK.
    """

    def __init__(self, api_key: str = "PLACEHOLDER_KEY"):
        """
        Initialize Chargebee client.

        Args:
            api_key: Chargebee API key (placeholder)
        """
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.ChargebeeClient")
        self.logger.warning("Using mock Chargebee client - NO REAL API CALLS")

    async def get_subscription(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer subscription details.

        BOILERPLATE: Returns mock subscription data.

        Args:
            customer_id: Customer identifier

        Returns:
            Subscription details
        """
        self.logger.info(f"Fetching subscription for customer: {customer_id}")

        # TODO: Use real Chargebee API
        # import chargebee
        # result = chargebee.Subscription.retrieve(customer_id)

        mock_subscription = {
            "id": f"sub_{customer_id}",
            "customer_id": customer_id,
            "plan_id": "pro_plan",
            "status": "active",
            "current_term_start": "2024-01-01",
            "current_term_end": "2024-01-31",
            "mrr": 500.00,
            "currency": "USD",
            "billing_period": "monthly",
        }

        return mock_subscription

    async def get_invoices(
        self, customer_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get customer invoices.

        BOILERPLATE: Returns mock invoice data.

        Args:
            customer_id: Customer identifier
            limit: Number of recent invoices

        Returns:
            List of invoices
        """
        self.logger.info(f"Fetching {limit} invoices for customer: {customer_id}")

        # TODO: Use real Chargebee API
        mock_invoices = [
            {
                "id": f"inv_001_{customer_id}",
                "customer_id": customer_id,
                "date": "2024-01-01",
                "amount": 500.00,
                "status": "paid",
                "line_items": [
                    {"description": "Pro Plan - Monthly", "amount": 500.00}
                ],
            },
            {
                "id": f"inv_002_{customer_id}",
                "customer_id": customer_id,
                "date": "2023-12-01",
                "amount": 500.00,
                "status": "paid",
                "line_items": [
                    {"description": "Pro Plan - Monthly", "amount": 500.00}
                ],
            },
        ]

        return mock_invoices[:limit]

    async def create_credit_note(
        self, customer_id: str, amount: float, reason: str
    ) -> Dict[str, Any]:
        """
        Create a credit note for customer.

        BOILERPLATE: Mock credit note creation.

        Args:
            customer_id: Customer identifier
            amount: Credit amount
            reason: Reason for credit

        Returns:
            Credit note details
        """
        self.logger.info(
            f"Creating credit note for {customer_id}: ${amount} ({reason})"
        )

        # TODO: Use real Chargebee API
        mock_credit_note = {
            "id": f"cn_{customer_id}_mock",
            "customer_id": customer_id,
            "amount": amount,
            "reason": reason,
            "status": "adjusted",
            "created_at": "2024-01-01T00:00:00Z",
        }

        self.logger.warning("BOILERPLATE: Mock credit note, not actually created")
        return mock_credit_note
