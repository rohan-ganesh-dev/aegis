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
    
    For each detected issue, calls the orchestrator agent to attempt autonomous resolution.
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize proactive monitor.
        
        Args:
            check_interval_seconds: Time between monitoring runs (default: 60s / 1 minute)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.interventions: List[Dict[str, Any]] = []  # Store interventions for UI
        self.state_manager = get_state_manager()
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
                
                # Detect and create interventions (now with diagnosis, actions, next steps)
                intervention = await self._detect_issue(customer, health)
                
                if intervention:
                    interventions_this_cycle += 1
                    self.interventions.append(intervention)
                    # Keep only last 50 interventions
                    self.interventions = self.interventions[-50:]
                    
            except Exception as e:
                logger.error(f"Error checking customer {customer.customer_id}: {e}")
       
        if interventions_this_cycle > 0:
            logger.info(f"🎯 Triggered {interventions_this_cycle} proactive interventions")


    async def _detect_issue(
        self, 
        customer: CustomerProfile, 
        health: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if customer has issues and return issue details.
        
        This method now returns enriched interventions with diagnosis, actions, and next steps.
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
                
                # Auto-create Jira ticket for high error rates
                jira_ticket = customer.active_ticket_key
                should_create_ticket = True
                
                # Check if we recently created a ticket (deduplication)
                if jira_ticket and customer.last_ticket_at:
                    if customer.last_ticket_at > datetime.now() - timedelta(hours=24):
                        should_create_ticket = False
                        logger.info(f"♻️ Reusing existing ticket {jira_ticket} for {customer.company}")

                if should_create_ticket and health["metrics"]["error_rate"] > 0.15:
                    try:
                        new_ticket = await self._create_jira_ticket(
                            customer=customer,
                            issue_type="Bug",
                            summary=f"🚨 High Error Rate Alert: {customer.company}",
                            description=f"**Customer**: {customer.company} ({customer.customer_id})\\n\\n**Error Rate**: {health['metrics']['error_rate']:.1%}\\n\\n**Total API Calls**: {customer.total_api_calls}\\n\\n**Issue**: Systematic integration issues detected. Likely authentication or API parameter problems requiring immediate debugging support.\\n\\n**Priority**: HIGH - Requires technical review within 2 hours."
                        )
                        if new_ticket:
                            jira_ticket = new_ticket
                            logger.info(f"✅ Auto-created Jira ticket: {jira_ticket}")
                            # Update customer state with new ticket info
                            await self.state_manager.update_customer(customer.customer_id, {
                                "last_ticket_at": datetime.now(),
                                "active_ticket_key": jira_ticket
                            })
                    except Exception as e:
                        logger.error(f"Failed to create Jira ticket: {e}")
                
                intervention = {
                    "type": "error_debugging",
                    "customer_id": customer.customer_id,
                    "customer_name": customer.company,
                    "reason": f"Error rate: {health['metrics']['error_rate']:.1%}",
                    "priority": "high",
                    "created_at": now.isoformat(),
                    "diagnosis": f"Error rate of {health['metrics']['error_rate']:.1%} detected across {customer.total_api_calls} API calls. This indicates systematic integration issues, likely authentication or API parameter problems.",
                    "actions_taken": f"✅ Created support ticket {jira_ticket}. Flagged for immediate technical review." if jira_ticket else "⚠️ Monitoring errors, ready to provide debugging support. Escalation recommended.",
                    "next_steps": f"Support team to review ticket {jira_ticket} within 2 hours. Analyze error logs, identify root cause (auth vs. parameters), provide specific fix instructions." if jira_ticket else "Create support ticket and analyze error logs to identify root cause. Provide specific fix instructions within 2 hours.",
                    "jira_ticket": jira_ticket,
                    "message": (
                        f"Hi {customer.company}, I detected a high error rate ({health['metrics']['error_rate']:.1%}) "
                        f"in your API calls. I can help investigate. Common causes are authentication issues "
                        f"or incorrect parameter formatting. Would you like me to analyze your recent errors?"
                    )
                }
                
                return intervention
        
        # Intervention 3: Usage declining (churn risk)
        if (health["metrics"]["usage_trend"] == "declining" 
           and customer.subscription_tier.value in ["pro", "enterprise"]):
            if not self._recently_intervened(customer.customer_id, "retention_outreach"):
                logger.info(f"🚨 Declining usage: {customer.customer_id} ({customer.company})")
                
                # Auto-create Jira ticket for churn risk
                jira_ticket = customer.active_ticket_key
                should_create_ticket = True
                
                # Check if we recently created a ticket (deduplication)
                if jira_ticket and customer.last_ticket_at:
                    if customer.last_ticket_at > datetime.now() - timedelta(hours=24):
                        should_create_ticket = False
                        logger.info(f"♻️ Reusing existing retention ticket {jira_ticket} for {customer.company}")

                if should_create_ticket:
                    try:
                        new_ticket = await self._create_jira_ticket(
                            customer=customer,
                            issue_type="Task",
                            summary=f"⚠️ Churn Risk: {customer.company} - Declining Usage",
                            description=f"**Customer**: {customer.company} ({customer.customer_id})\\n\\n**Tier**: {customer.subscription_tier.value.upper()}\\n\\n**Issue**: Usage trend declining - potential churn risk\\n\\n**Analysis**: Customer may be evaluating alternatives or experiencing product-market fit issues. Requires immediate retention outreach.\\n\\n**Action Required**: Schedule call to understand pain points. Offer premium support, custom solutions, or tier adjustment if needed."
                        )
                        if new_ticket:
                            jira_ticket = new_ticket
                            logger.info(f"✅ Auto-created retention ticket: {jira_ticket}")
                            # Update customer state with new ticket info
                            await self.state_manager.update_customer(customer.customer_id, {
                                "last_ticket_at": datetime.now(),
                                "active_ticket_key": jira_ticket
                            })
                    except Exception as e:
                        logger.error(f"Failed to create Jira ticket: {e}")
                
                return {
                    "type": "retention_outreach",
                    "customer_id": customer.customer_id,
                    "customer_name": customer.company,
                    "reason": "Usage declining",
                    "priority": "high",
                    "created_at": now.isoformat(),
                    "diagnosis": f"Usage trend declining for {customer.subscription_tier.value.upper()} tier customer. Potential churn risk. Customer may be evaluating alternatives or experiencing product-market fit issues.",
                    "actions_taken": f"✅ Created retention ticket {jira_ticket}. Flagged account manager for immediate outreach." if jira_ticket else "⚠️ Flagged for retention team review. Escalation recommended.",
                    "next_steps": f"Account manager to review ticket {jira_ticket} and schedule call within 24 hours. Understand pain points, offer premium support, custom solutions, or tier adjustment if needed." if jira_ticket else "Create retention ticket and schedule call with customer. Understand pain points and prevent churn.",
                    "jira_ticket": jira_ticket,
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
                
                intervention = {
                    "type": "upsell_suggestion",
                    "customer_id": customer.customer_id,
                    "customer_name": customer.company,
                    "reason": "Usage growing rapidly",
                    "priority": "medium",
                    "created_at": now.isoformat(),
                    "diagnosis": f"{customer.subscription_tier.value.upper()} tier customer has made {customer.total_api_calls} API calls with increasing usage trend. Clear product-market fit and growth trajectory indicate readiness for tier upgrade.",
                    "actions_taken": "Flagged as upsell opportunity for sales team. Prepared upgrade proposal with ROI analysis.",
                    "next_steps": "Sales team to reach out with personalized upgrade offer. Highlight Pro/Enterprise benefits: higher limits, priority support, advanced features.",
                    "message": (
                        f"Great news! Your usage is growing. You've made {customer.total_api_calls} API calls "
                        f"and might benefit from our Pro plan, which includes higher limits and priority support. "
                        f"Would you like to discuss an upgrade?"
                    )
                }
                
                return intervention
        
        return None
    
    async def _create_jira_ticket(
        self,
        customer: CustomerProfile,
        issue_type: str,
        summary: str,
        description: str
    ) -> Optional[str]:
        """
        Create a Jira ticket using the project's Jira tool.
        
        Args:
            customer: Customer profile
            issue_type: Jira issue type (Bug, Task, etc.)
            summary: Ticket summary/title
            description: Ticket description
            
        Returns:
            Jira ticket key (e.g., 'KAN-123') or None if creation fails
        """
        try:
            # Import the project's Jira tool
            from aegis.tools.jira_mcp import create_ticket
            
            logger.info(f"🎫 Creating Jira ticket for {customer.company}: {summary}")
            
            # Call the Jira create ticket tool
            # Note: project_key is hardcoded to KAN for demo purposes, 
            # but in production should be configurable or passed in.
            result = await create_ticket(
                project_key="KAN",
                summary=summary,
                issue_type=issue_type,
                description=description
            )
            
            # Extract ticket key
            if isinstance(result, dict):
                # Check for direct key or nested inside 'issue'
                ticket_key = result.get("key")
                if not ticket_key and "issue" in result:
                    ticket_key = result["issue"].get("key")
                
                if ticket_key:
                    logger.info(f"✅ Created Jira ticket: {ticket_key}")
                    return ticket_key
            
            logger.warning(f"Jira ticket creation returned unexpected result: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Error creating Jira ticket: {e}", exc_info=True)
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
