"""
Monitoring Mocks.

Mock monitoring services for billing, platform status, and support.
These are stubs - production should integrate with real monitoring/alerting systems.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BillingMonitor:
    """
    Mock billing monitoring service.

    BOILERPLATE: Production should integrate with billing system and anomaly detection.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.BillingMonitor")
        self.logger.warning("Using mock BillingMonitor - NO REAL MONITORING")

    async def get_billing_status(self, customer_id: str) -> Dict[str, Any]:
        """
        Get billing status and detect anomalies.

        BOILERPLATE: Returns mock billing data.

        Args:
            customer_id: Customer identifier

        Returns:
            Billing status with anomaly flags
        """
        self.logger.info(f"Checking billing for: {customer_id}")

        # TODO: Implement real billing monitoring
        # - Fetch recent charges from billing system
        # - Compare with historical patterns
        # - Detect anomalies (spikes, unexpected charges)
        # - Calculate trends

        mock_data = {
            "customer_id": customer_id,
            "status": "normal",
            "current_month_spend": 1250.00,
            "last_month_spend": 1200.00,
            "average_monthly_spend": 1150.00,
            "trend": "increasing",
            "anomalies_detected": False,
            "alerts": [],
        }

        return mock_data


class PlatformMonitor:
    """
    Mock platform status monitoring service.

    BOILERPLATE: Production should integrate with status page and monitoring systems.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PlatformMonitor")
        self.logger.warning("Using mock PlatformMonitor - NO REAL MONITORING")

    async def get_status(self, region: str = "all") -> Dict[str, Any]:
        """
        Get platform health status.

        BOILERPLATE: Returns mock platform status.

        Args:
            region: Region to check (or "all")

        Returns:
            Platform status details
        """
        self.logger.info(f"Checking platform status for region: {region}")

        # TODO: Implement real platform monitoring
        # - Query health check endpoints
        # - Check service uptime
        # - Fetch recent incidents
        # - Monitor SLA metrics

        mock_status = {
            "overall_status": "operational",
            "region": region,
            "services": [
                {
                    "name": "API Gateway",
                    "status": "operational",
                    "uptime_percent": 99.99,
                },
                {
                    "name": "Compute Service",
                    "status": "operational",
                    "uptime_percent": 99.95,
                },
                {
                    "name": "Storage Service",
                    "status": "degraded",
                    "uptime_percent": 99.80,
                    "message": "Increased latency in us-west region",
                },
            ],
            "recent_incidents": [
                {
                    "id": "inc_001",
                    "title": "Storage latency issue",
                    "status": "investigating",
                    "started_at": "2024-01-01T10:00:00Z",
                }
            ],
        }

        return mock_status


class SupportMonitor:
    """
    Mock support ticket monitoring service.

    BOILERPLATE: Production should integrate with support system (Zendesk, etc.).
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SupportMonitor")
        self.logger.warning("Using mock SupportMonitor - NO REAL MONITORING")

    async def get_trends(self, timeframe: str = "7d") -> Dict[str, Any]:
        """
        Get support ticket trends and analysis.

        BOILERPLATE: Returns mock support trends.

        Args:
            timeframe: Time period to analyze (e.g., "7d", "30d")

        Returns:
            Support trends analysis
        """
        self.logger.info(f"Analyzing support trends for: {timeframe}")

        # TODO: Implement real support analytics
        # - Fetch tickets from timeframe
        # - Categorize by type/topic
        # - Calculate resolution times
        # - Identify trending issues

        mock_trends = {
            "timeframe": timeframe,
            "total_tickets": 47,
            "open_tickets": 12,
            "average_resolution_hours": 18.5,
            "top_categories": [
                {"category": "API Issues", "count": 15, "trend": "increasing"},
                {"category": "Billing Questions", "count": 10, "trend": "stable"},
                {"category": "Migration Help", "count": 8, "trend": "decreasing"},
            ],
            "customer_satisfaction": 4.2,  # out of 5
            "emerging_issues": [
                "Multiple reports of rate limiting errors in API v2"
            ],
        }

        return mock_trends
