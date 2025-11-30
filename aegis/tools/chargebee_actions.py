"""
Chargebee Action Tools.

Provides action-oriented tools for Chargebee operations.
Enables agents to autonomously execute customer onboarding workflows.

Production: Replace mock implementations with real Chargebee API calls.
"""

import logging
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from aegis.state.state_manager import get_state_manager, OnboardingStage, SubscriptionTier

logger = logging.getLogger(__name__)


async def create_trial_subscription(
    customer_id: str,
    plan: str = "starter_trial"
) -> Dict[str, Any]:
    """
    Create a trial subscription for customer.
    
    DEMO: Mock implementation. Production would call Chargebee API.
    
    Args:
        customer_id: Customer identifier
        plan: Plan ID (default: starter_trial)
        
    Returns:
        Subscription details
    """
    logger.info(f"Creating trial subscription for {customer_id}, plan: {plan}")
    
    state_manager = get_state_manager()
    customer = await state_manager.get_customer(customer_id)
    
    if not customer:
        return {
            "success": False,
            "error": "Customer not found"
        }
    
    if customer.subscription_tier != SubscriptionTier.NONE:
        return {
            "success": False,
            "error": f"Customer already has subscription: {customer.subscription_tier.value}"
        }
    
    # DEMO: Mock subscription creation
    subscription_id = f"sub_trial_{secrets.token_hex(4)}"
    
    # Update customer state
    await state_manager.update_customer(customer_id, {
        "subscription_tier": SubscriptionTier.TRIAL,
        "subscription_id": subscription_id,
        "onboarding_stage": OnboardingStage.TRIAL_CREATED,
        "workflow_metadata": {
            "trial_created_at": datetime.now().isoformat(),
            "trial_expires_at": (datetime.now() + timedelta(days=14)).isoformat()
        }
    })
    
    logger.info(f"✅ Created trial subscription {subscription_id} for {customer_id}")
    
    return {
        "success": True,
        "subscription_id": subscription_id,
        "plan": plan,
        "status": "trial",
        "trial_end": (datetime.now() + timedelta(days=14)).isoformat(),
        "message": "Trial subscription created successfully"
    }


async def generate_api_keys(
    customer_id: str,
    environment: str = "test"
) -> Dict[str, Any]:
    """
    Generate API keys for customer.
    
    DEMO: Mock implementation. Production would call Chargebee API.
    
    Args:
        customer_id: Customer identifier
        environment: "test" or "production"
        
    Returns:
        API key details
    """
    logger.info(f"Generating {environment} API keys for {customer_id}")
    
    if environment not in ["test", "production"]:
        return {
            "success": False,
            "error": "Environment must be 'test' or 'production'"
        }
    
    state_manager = get_state_manager()
    customer = await state_manager.get_customer(customer_id)
    
    if not customer:
        return {
            "success": False,
            "error": "Customer not found"
        }
    
    # DEMO: Generate mock API keys
    prefix = "sk_test" if environment == "test" else "sk_live"
    api_key = f"{prefix}_{secrets.token_hex(16)}"
    
    # Update customer state
    update_data = {}
    if environment == "test":
        update_data["test_api_key"] = api_key
        update_data["onboarding_stage"] = OnboardingStage.API_KEYS_GENERATED
        update_data["next_check"] = datetime.now() + timedelta(hours=24)
    else:
        update_data["prod_api_key"] = api_key
    
    await state_manager.update_customer(customer_id, update_data)
    
    logger.info(f"✅ Generated {environment} API key for {customer_id}")
    
    return {
        "success": True,
        "environment": environment,
        "api_key": api_key,
        "created_at": datetime.now().isoformat(),
        "message": f"{environment.capitalize()} API key generated successfully"
    }


async def send_onboarding_email(
    customer_id: str,
    template: str = "welcome_with_keys",
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send onboarding email to customer.
    
    DEMO: Mock implementation. Production would use SendGrid/SES.
    
    Args:
        customer_id: Customer identifier
        template: Email template name
        data: Template data (API keys, setup instructions, etc.)
        
    Returns:
        Email send status
    """
    logger.info(f"Sending onboarding email to {customer_id}, template: {template}")
    
    state_manager = get_state_manager()
    customer = await state_manager.get_customer(customer_id)
    
    if not customer:
        return {
            "success": False,
            "error": "Customer not found"
        }
    
    # DEMO: Mock email sending
    email_data = {
        "to": customer.email,
        "from": "success@aegis.ai",
        "subject": "Welcome to Chargebee - Let's Get Started!",
        "template": template,
        "data": data or {}
    }
    
    # Update metadata
    await state_manager.update_customer(customer_id, {
        "workflow_metadata": {
            **customer.workflow_metadata,
            "onboarding_email_sent_at": datetime.now().isoformat(),
            "email_template": template
        }
    })
    
    logger.info(f"✅ Sent onboarding email to {customer.email}")
    
    return {
        "success": True,
        "email_id": f"email_{secrets.token_hex(4)}",
        "recipient": customer.email,
        "template": template,
        "sent_at": datetime.now().isoformat(),
        "message": "Onboarding email sent successfully"
    }


async def provision_test_environment(
    customer_id: str
) -> Dict[str, Any]:
    """
    Provision sandbox test environment for customer.
    
    DEMO: Mock implementation. Production would create test resources.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Test environment details
    """
    logger.info(f"Provisioning test environment for {customer_id}")
    
    state_manager = get_state_manager()
    customer = await state_manager.get_customer(customer_id)
    
    if not customer:
        return {
            "success": False,
            "error": "Customer not found"
        }
    
    # DEMO: Mock test environment
    test_env = {
        "sandbox_url": f"https://sandbox.chargebee.com/{customer_id}",
        "test_site": f"{customer_id}-test",
        "webhook_url": f"https://api.example.com/webhooks/{customer_id}",
        "dashboard_url": f"https://dashboard.chargebee.com/test/{customer_id}"
    }
    
    # Update metadata
    await state_manager.update_customer(customer_id, {
        "workflow_metadata": {
            **customer.workflow_metadata,
            "test_environment": test_env,
            "test_env_provisioned_at": datetime.now().isoformat()
        }
    })
    
    logger.info(f"✅ Provisioned test environment for {customer_id}")
    
    return {
        "success": True,
        **test_env,
        "provisioned_at": datetime.now().isoformat(),
        "message": "Test environment provisioned successfully"
    }


async def track_api_activity(
    customer_id: str,
    endpoint: str,
    status_code: int
) -> Dict[str, Any]:
    """
    Track customer API activity.
    
    Used to detect first API call and monitor usage patterns.
    
    Args:
        customer_id: Customer identifier
        endpoint: API endpoint called
        status_code: HTTP status code
        
    Returns:
        Activity tracking result
    """
    logger.info(f"Tracking API activity for {customer_id}: {endpoint} -> {status_code}")
    
    state_manager = get_state_manager()
    customer = await state_manager.get_customer(customer_id)
    
    if not customer:
        return {"success": False, "error": "Customer not found"}
    
    # Update activity metrics
    updates = {
        "last_api_call": datetime.now(),
        "total_api_calls": customer.total_api_calls + 1
    }
    
    # If this is first API call, update stage
    if customer.total_api_calls == 0:
        updates["onboarding_stage"] = OnboardingStage.FIRST_API_CALL
        updates["integration_status"] = "in_progress"
        logger.info(f"🎉 First API call detected for {customer_id}!")
    
    # Update error rate
    is_error = status_code >= 400
    if is_error:
        # Simple error rate calculation
        new_error_rate = (customer.error_rate * customer.total_api_calls + 1) / (customer.total_api_calls + 1)
        updates["error_rate"] = new_error_rate
    
    await state_manager.update_customer(customer_id, updates)
    
    return {
        "success": True,
        "is_first_call": customer.total_api_calls == 0,
        "total_calls": customer.total_api_calls + 1,
        "is_error": is_error
    }
