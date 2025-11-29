"""
Proactive Customer Monitor.

Background task that monitors customer health signals and triggers
autonomous agent actions without user input.

This is what makes the system truly agentic - taking initiative!
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from aegis.state.state_manager import get_state_manager, CustomerProfile, OnboardingStage
from aegis.tools.customer_context import get_customer_health, list_customers_needing_attention

logger = logging.getLogger(__name__)


class ProactiveMonitor:
    """
    Monitors customer signals and triggers proactive agent interventions.
    
    Runs in background and detects:
    - New customers stuck in onboarding
    - API errors requiring debugging help
    - Usage spikes (upsell opportunities)
    - Declining engagement (churn risk)
    """
    
    def __init__(self, check_interval_seconds: int = 300):
        """
        Initialize proactive monitor.
        
        Args:
            check_interval_seconds: Time between monitoring runs (default: 5min)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.interventions: List[Dict[str, Any]] = []  # Store interventions for UI
        logger.info(f"ProactiveMonitor initialized (interval: {check_interval_seconds}s)")
    
    async def start(self):
        """Start the monitoring loop."""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("✅ Proactive monitor started")
    
    async def stop(self):
        """Stop the monitoring loop."""
        if not self.running:
            return
        
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️  Proactive monitor stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop that runs continuously."""
        logger.info("🔍 Monitoring loop started")
        
        while self.running:
            try:
                await self._check_all_customers()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_customers(self):
        """Check all customers for intervention opportunities."""
        logger.debug("Running customer health check...")
        
        state_manager = get_state_manager()
        customers = await state_manager.list_customers()
        
        interventions_this_cycle = 0
        
        for customer in customers:
            try:
                # Analyze customer health
                health = await get_customer_health(customer.customer_id)
                
                # Detect and trigger interventions
                intervention = await self._detect_and_intervene(customer, health)
                
                if intervention:
                    interventions_this_cycle += 1
                    self.interventions.append(intervention)
                    # Keep only last 50 interventions
                    self.interventions = self.interventions[-50:]
                    
            except Exception as e:
                logger.error(f"Error checking customer {customer.customer_id}: {e}")
       
        if interventions_this_cycle > 0:
            logger.info(f"🎯 Triggered {interventions_this_cycle} proactive interventions")
    
    async def _detect_and_intervene(
        self, 
        customer: CustomerProfile, 
        health: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if customer needs intervention and trigger appropriate action.
        
        Returns intervention details if action was taken.
        """
        now = datetime.now()
        
        # Intervention 1: Onboarding stuck (API keys generated but no activity for 24h)
        if (customer.onboarding_stage == OnboardingStage.API_KEYS_GENERATED
            and customer.total_api_calls == 0
            and health["metrics"]["hours_since_signup"] > 24):
            
            # Check if we haven't intervened recently
            if not self._recently_intervened(customer.customer_id, "onboarding_check_in"):
                logger.info(f"🚨 Onboarding stuck: {customer.customer_id} ({customer.company})")
                
                return {
                    "type": "onboarding_check_in",
                    "customer_id": customer.customer_id,
                    "customer_name": customer.company,
                    "reason": "No API activity 24h after key generation",
                    "recommended_action": "Send debug help offer",
                    "priority": "medium",
                    "created_at": now.isoformat(),
                    "message": (
                        f"Hi {customer.company}! I noticed you generated API keys 24h ago "
                        f"but haven't made any API calls yet. Need help with integration? "
                        f"I can provide code examples or help debug any issues."
                    )
                }
        
        # Intervention 2: High error rate detected
        if health["metrics"]["error_rate"] > 0.1 and customer.total_api_calls > 10:
            if not self._recently_intervened(customer.customer_id, "error_debugging"):
                logger.info(f"🚨 High error rate: {customer.customer_id} ({health['metrics']['error_rate']:.1%})")
                
                return {
                    "type": "error_debugging",
                    "customer_id": customer.customer_id,
                    "customer_name": customer.company,
                    "reason": f"Error rate: {health['metrics']['error_rate']:.1%}",
                    "recommended_action": "Analyze errors and offer debugging",
                    "priority": "high",
                    "created_at": now.isoformat(),
                    "message": (
                        f"Hi {customer.company}, I detected a high error rate ({health['metrics']['error_rate']:.1%}) "
                        f"in your API calls. I can help investigate. Common causes are authentication issues "
                        f"or incorrect parameter formatting. Would you like me to analyze your recent errors?"
                    )
                }
        
        # Intervention 3: Usage declining (churn risk)
        if (health["metrics"]["usage_trend"] == "declining" 
           and customer.subscription_tier.value in ["pro", "enterprise"]):
            if not self._recently_intervened(customer.customer_id, "retention_outreach"):
                logger.info(f"🚨 Declining usage: {customer.customer_id} ({customer.company})")
                
                return {
                    "type": "retention_outreach",
                    "customer_id": customer.customer_id,
                    "customer_name": customer.company,
                    "reason": "Usage declining",
                    "recommended_action": "Schedule retention call",
                    "priority": "high",
                    "created_at": now.isoformat(),
                    "message": (
                        f"Hi {customer.company}, I noticed your API usage has been declining. "
                        f"Is everything working as expected? I'd love to understand if there's "
                        f"anything we can help with or if you're exploring other solutions."
                    )
                }
        
        # Intervention 4: Usage spike (upsell opportunity)
        if (health["metrics"]["usage_trend"] == "increasing" 
            and customer.total_api_calls > 1000
            and customer.subscription_tier.value in ["trial", "starter"]):
            if not self._recently_intervened(customer.customer_id, "upsell_suggestion"):
                logger.info(f"🚨 Upsell opportunity: {customer.customer_id} ({customer.company})")
                
                return {
                    "type": "upsell_suggestion",
                    "customer_id": customer.customer_id,
                    "customer_name": customer.company,
                    "reason": "Usage growing rapidly",
                    "recommended_action": "Suggest upgrade",
                    "priority": "medium",
                    "created_at": now.isoformat(),
                    "message": (
                        f"Great news! Your usage is growing. You've made {customer.total_api_calls} API calls "
                        f"and might benefit from our Pro plan, which includes higher limits and priority support. "
                        f"Would you like to discuss an upgrade?"
                    )
                }
        
        return None
    
    def _recently_intervened(self, customer_id: str, intervention_type: str) -> bool:
        """Check if we've intervened for this customer/type recently (within 24h)."""
        cutoff = datetime.now() - timedelta(hours=24)
        
        for intervention in reversed(self.interventions):
            if (intervention["customer_id"] == customer_id 
                and intervention["type"] == intervention_type
                and datetime.fromisoformat(intervention["created_at"]) > cutoff):
                return True
        
        return False
    
    def get_recent_interventions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interventions for UI display."""
        return list(reversed(self.interventions[-limit:]))


# Global monitor instance
_monitor: Optional[ProactiveMonitor] = None


def get_monitor() -> ProactiveMonitor:
    """Get or create global monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = ProactiveMonitor()
    return _monitor


async def start_monitoring():
    """Start the global monitor."""
    monitor = get_monitor()
    await monitor.start()


async def stop_monitoring():
    """Stop the global monitor."""
    monitor = get_monitor()
    await monitor.stop()
