"""
Diagnostic action tools for troubleshooting customer issues.

These tools enable the agent to autonomously diagnose and fix problems
instead of just providing generic advice.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def verify_api_key(customer_id: str, api_key: str = None) -> Dict[str, Any]:
    """
    Verify if a customer's API key is valid and active.
    
    In production, this would make an actual API call to Chargebee.
    For demo, we simulate the diagnostic check.
    
    Args:
        customer_id: Customer identifier
        api_key: API key to verify (optional, fetches from profile if not provided)
        
    Returns:
        Dict with verification results
    """
    logger.info(f"🔍 [DIAGNOSTIC ACTION] Verifying API key for customer: {customer_id}")
    
    # In production: Make actual Chargebee API call
    # response = chargebee.api_key.verify(api_key)
    
    # Demo simulation
    from aegis.state.state_manager import get_state_manager
    state_manager = get_state_manager()
    profile = state_manager.get_customer(customer_id)
    
    if not profile:
        return {
            "valid": False,
            "error": "Customer not found",
            "action_taken": "Verified API key",
            "result": "FAILED - Customer profile not found"
        }
    
    # Simulate checking the key
    test_key = profile.test_api_key or profile.prod_api_key
    
    if not test_key:
        return {
            "valid": False,
            "error": "No API key found",
            "action_taken": "Checked customer API keys",
            "result": "FAILED - No API keys generated yet",
            "fix": "Generate API keys first using generate_api_keys()"
        }
    
    # Simulate a successful verification
    return {
        "valid": True,
        "action_taken": "Verified API key against Chargebee",
        "result": f"SUCCESS - Key {test_key[:15]}... is valid and active",
        "key_type": "test" if profile.test_api_key else "production",
        "created_at": profile.created_at.isoformat()
    }


def test_api_authentication(customer_id: str, environment: str = "test") -> Dict[str, Any]:
    """
    Make a test API call to verify authentication is working.
    
    Args:
        customer_id: Customer identifier
        environment: 'test' or 'production'
        
    Returns:
        Dict with test results
    """
    logger.info(f"🔍 [DIAGNOSTIC ACTION] Testing API authentication for {customer_id} in {environment} env")
    
    from aegis.state.state_manager import get_state_manager
    state_manager = get_state_manager()
    profile = state_manager.get_customer(customer_id)
    
    if not profile:
        return {
            "success": False,
            "action_taken": "Attempted test API call",
            "result": "FAILED - Customer not found"
        }
    
    api_key = profile.test_api_key if environment == "test" else profile.prod_api_key
    
    if not api_key:
        return {
            "success": False,
            "action_taken": "Attempted test API call",
            "result": f"FAILED - No {environment} API key found",
            "fix": "Generate API keys first"
        }
    
    # Simulate making a test API call (GET /v2/customers/limit=1)
    # In production: Make actual Chargebee API call
    # response = chargebee.Customer.list(limit=1, api_key=test_key)
    
    return {
        "success": True,
        "action_taken": f"Made test API call to GET /v2/customers (limit=1)",
        "result": "SUCCESS - Authentication working correctly",
        "response_code": 200,
        "api_key_used": f"{api_key[:15]}...",
        "environment": environment,
        "test_details": {
            "endpoint": "https://test.chargebee.com/api/v2/customers",
            "method": "GET",
            "auth_header": "Basic <base64_encoded_key>",
            "response_time_ms": 247
        }
    }


def diagnose_401_error(customer_id: str, error_details: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Diagnose the root cause of 401 authentication errors.
    
    Args:
        customer_id: Customer identifier
        error_details: Optional error details from failed request
        
    Returns:
        Dict with diagnosis and fix recommendations
    """
    logger.info(f"🔍 [DIAGNOSTIC ACTION] Diagnosing 401 error for customer: {customer_id}")
    
    from aegis.state.state_manager import get_state_manager
    state_manager = get_state_manager()
    profile = state_manager.get_customer(customer_id)
    
    if not profile:
        return {
            "diagnosis": "Customer profile not found",
            "action_taken": "Analyzed customer account",
            "root_cause": "UNKNOWN",
            "fix": "Please provide valid customer ID"
        }
    
    # Check multiple potential causes
    checks_performed = []
    root_cause = None
    fix_steps = []
    
    # Check 1: Do they have API keys?
    if not profile.test_api_key and not profile.prod_api_key:
        checks_performed.append("❌ API Key Check: No keys found")
        root_cause = "NO_API_KEYS"
        fix_steps.append("1. Generate API keys using the Chargebee dashboard")
        fix_steps.append("2. Use test keys for development: sk_test_xxx")
    else:
        checks_performed.append(f"✅ API Key Check: Found {profile.test_api_key[:15]}...")
    
    # Check 2: Are they using the right environment?
    if profile.subscription_tier in ["trial", "none"]:
        checks_performed.append("⚠️  Environment Check: Customer is on trial/free tier")
        if not root_cause:
            root_cause = "WRONG_ENVIRONMENT"
        fix_steps.append("3. Ensure you're using TEST keys (sk_test_xxx) not LIVE keys")
        fix_steps.append("4. Point to test environment: https://test.chargebee.com")
    
    # Check 3: Check error rate
    if profile.error_rate and profile.error_rate > 10:
        checks_performed.append(f"⚠️  Error Rate: {profile.error_rate}% (HIGH)")
        if not root_cause:
            root_cause = "INVALID_KEY_OR_HEADERS"
        fix_steps.append("5. Verify authentication header format: Authorization: Basic <base64(api_key)>")
    
    if not root_cause:
        root_cause = "KEY_VALID_BUT_HEADERS_INCORRECT"
        fix_steps.extend([
            "1. Check HTTP headers include: Authorization: Basic <base64_encoded_key>",
            "2. Verify Content-Type: application/json",
            "3. Ensure API key is base64 encoded correctly"
        ])
    
    return {
        "action_taken": "Performed comprehensive 401 error diagnosis",
        "checks_performed": checks_performed,
        "root_cause": root_cause,
        "diagnosis": _get_diagnosis_explanation(root_cause),
        "fix_steps": fix_steps,
        "customer_context": {
            "tier": profile.subscription_tier.value,
            "stage": profile.onboarding_stage.value,
            "has_test_key": bool(profile.test_api_key),
            "has_prod_key": bool(profile.prod_api_key),
            "error_rate": f"{profile.error_rate}%" if profile.error_rate else "0%"
        }
    }


def _get_diagnosis_explanation(root_cause: str) -> str:
    """Get human-readable explanation for diagnosis."""
    explanations = {
        "NO_API_KEYS": "No API keys have been generated for this customer yet",
        "WRONG_ENVIRONMENT": "Customer might be using production keys in test environment or vice versa",
        "INVALID_KEY_OR_HEADERS": "API key is present but authentication headers may be malformed",
        "KEY_VALID_BUT_HEADERS_INCORRECT": "API key appears valid but request headers are likely incorrect",
        "UNKNOWN": "Unable to determine root cause without more information"
    }
    return explanations.get(root_cause, "Unknown error")


def apply_fix_for_401(customer_id: str) -> Dict[str, Any]:
    """
    Autonomously apply fixes for common 401 errors.
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Dict with actions taken and results
    """
    logger.info(f"🔧 [FIX ACTION] Applying automated fixes for customer: {customer_id}")
    
    from aegis.state.state_manager import get_state_manager
    from aegis.tools.chargebee_actions import generate_api_keys
    
    state_manager = get_state_manager()
    profile = state_manager.get_customer(customer_id)
    
    actions_taken = []
    
    # Fix 1: Generate keys if missing
    if not profile.test_api_key:
        result = generate_api_keys(customer_id, environment="test")
        actions_taken.append({
            "action": "Generated test API keys",
            "result": "SUCCESS",
            "api_key": result.get("api_key", "")[:20] + "..."
        })
    
    # Fix 2: Provide correct header format
    actions_taken.append({
        "action": "Prepared authentication example",
        "result": "SUCCESS",
        "code_example": """
import base64
import requests

api_key = "sk_test_YOUR_KEY"
encoded = base64.b64encode(api_key.encode()).decode()

headers = {
    "Authorization": f"Basic {encoded}",
    "Content-Type": "application/json"
}

response = requests.get(
    "https://test.chargebee.com/api/v2/customers?limit=1",
    headers=headers
)
"""
    })
    
    return {
        "action_taken": "Applied automated fixes for 401 authentication error",
        "fixes_applied": len(actions_taken),
        "actions": actions_taken,
        "result": "COMPLETED - Customer should now be able to authenticate successfully",
        "next_steps": [
            "Test the authentication using the code example above",
            "Verify you get a 200 OK response",
            "If still failing, contact support with error details"
        ]
    }
