"""
Customer Context Tools.

Provides tools for retrieving and analyzing customer state.
Enables agents to understand customer context before taking action.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from aegis.state.state_manager import get_state_manager, CustomerProfile

logger = logging.getLogger(__name__)


async def get_customer_profile(customer_id: str) -> Dict[str, Any]:
    """
    Get comprehensive customer profile.
    
    Retrieves subscription status, onboarding stage, API keys, 
    integration status, and activity metrics.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Dictionary containing customer profile data
    """
    logger.info(f"Fetching profile for customer: {customer_id}")
    
    state_manager = get_state_manager()
    customer = await state_manager.get_customer(customer_id)
    
    if not customer:
        logger.warning(f"Customer {customer_id} not found")
        return {
            "found": False,
            "customer_id": customer_id,
            "message": "Customer not found - this appears to be a new customer"
        }
    
    profile = customer.to_dict()
    profile["found"] = True
    
    logger.info(f"Retrieved profile for {customer_id}: {customer.onboarding_stage.value}")
    return profile


async def get_customer_health(customer_id: str) -> Dict[str, Any]:
    """
    Analyze customer health metrics.
    
    Returns engagement signals, error rates, usage trends, and risk indicators.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Dictionary containing health metrics and signals
    """
    logger.info(f"Analyzing health for customer: {customer_id}")
    
    state_manager = get_state_manager()
    customer = await state_manager.get_customer(customer_id)
    
    if not customer:
        return {
            "found": False,
            "customer_id": customer_id
        }
    
    now = datetime.now()
    
    # Calculate activity metrics
    hours_since_last_api_call = None
    if customer.last_api_call:
        hours_since_last_api_call = (now - customer.last_api_call).total_seconds() / 3600
    
    hours_since_signup = (now - customer.created_at).total_seconds() / 3600
    
    # Determine health status
    health_status = "healthy"
    risk_factors = []
    
    if customer.error_rate > 0.1:
        health_status = "at_risk"
        risk_factors.append(f"High error rate: {customer.error_rate * 100:.1f}%")
    
    if customer.usage_trend == "declining":
        health_status = "at_risk"
        risk_factors.append("Usage declining")
    
    if (customer.onboarding_stage.value in ["api_keys_generated", "trial_created"] 
        and hours_since_signup > 48 
        and customer.total_api_calls == 0):
        health_status = "needs_attention"
        risk_factors.append("No API activity after 48h")
    
    if customer.total_api_calls == 0 and hours_since_signup < 24:
        health_status = "new"
    
    # Engagement score (0-100)
    engagement_score = 50
    if customer.total_api_calls > 0:
        engagement_score += 20
    if customer.integration_status == "live":
        engagement_score += 20
    if customer.error_rate < 0.05:
        engagement_score += 10
    if customer.usage_trend == "increasing":
        engagement_score += 10
    
    health = {
        "customer_id": customer_id,
        "health_status": health_status,  # healthy, needs_attention, at_risk
        "engagement_score": min(engagement_score, 100),
        "risk_factors": risk_factors,
        "metrics": {
            "total_api_calls": customer.total_api_calls,
            "hours_since_last_api_call": hours_since_last_api_call,
            "hours_since_signup": round(hours_since_signup, 1),
            "error_rate": customer.error_rate,
            "usage_trend": customer.usage_trend,
            "integration_status": customer.integration_status
        },
        "signals": {
            "has_api_activity": customer.total_api_calls > 0,
            "integration_complete": customer.integration_status == "live",
            "experiencing_errors": customer.error_rate > 0.05,
            "declining_usage": customer.usage_trend == "declining"
        }
    }
    
    logger.info(f"Health analysis for {customer_id}: {health_status} (score: {engagement_score})")
    return health


async def update_customer_state(
    customer_id: str, 
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update customer state.
    
    Used by agents to track workflow progress.
    
    Args:
        customer_id: Customer identifier
        updates: Dictionary of fields to update
        
    Returns:
        Updated customer profile
    """
    logger.info(f"Updating state for customer {customer_id}: {updates}")
    
    state_manager = get_state_manager()
    
    try:
        customer = await state_manager.update_customer(customer_id, updates)
        return {
            "success": True,
            "customer_id": customer_id,
            "updated_fields": list(updates.keys()),
            "current_state": customer.to_dict()
        }
    except ValueError as e:
        logger.error(f"Failed to update customer {customer_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def list_customers_needing_attention() -> Dict[str, Any]:
    """
    List customers that need proactive attention.
    
    Used by proactive monitoring to identify customers for check-in.
    
    Returns:
        Dictionary containing list of customers and reasons
    """
    logger.info("Identifying customers needing attention")
    
    state_manager = get_state_manager()
    customers = await state_manager.get_customers_needing_check()
    
    results = []
    for customer in customers:
        health = await get_customer_health(customer.customer_id)
        results.append({
            "customer_id": customer.customer_id,
            "email": customer.email,
            "company": customer.company,
            "onboarding_stage": customer.onboarding_stage.value,
            "health_status": health["health_status"],
            "risk_factors": health["risk_factors"],
            "recommended_action": _get_recommended_action(customer, health)
        })
    
    logger.info(f"Found {len(results)} customers needing attention")
    return {
        "count": len(results),
        "customers": results
    }


def _get_recommended_action(customer: CustomerProfile, health: Dict[str, Any]) -> str:
    """Determine recommended action for customer."""
    if "No API activity" in str(health["risk_factors"]):
        return "send_onboarding_check_in"
    elif "High error rate" in str(health["risk_factors"]):
        return "offer_debugging_help"
    elif "Usage declining" in str(health["risk_factors"]):
        return "schedule_retention_call"
    else:
        return "monitor"
