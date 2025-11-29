"""
Onboarding Agent implementation using Google ADK.

Handles customer onboarding with AUTONOMOUS ACTION EXECUTION.
Not just documentation retrieval - truly agentic behavior.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from aegis.agents.base import AegisAgent, AgentMessage, AgentResponse
from aegis.config import config
from aegis.tools.jira_mcp import (
    get_ticket_details,
    create_ticket,
    comment_on_ticket,
    get_ticket_status
)
from aegis.tools.chargebee_ops_mcp_tool import (
    query_chargebee_docs,
    query_chargebee_code
)
# NEW: Import customer context and action tools
from aegis.tools.customer_context import (
    get_customer_profile,
    get_customer_health,
    update_customer_state
)
from aegis.tools.chargebee_actions import (
    create_trial_subscription,
    generate_api_keys,
    send_onboarding_email,
    provision_test_environment,
    track_api_activity
)
# NEW: Import diagnostic tools for troubleshooting
from aegis.tools.diagnostic_actions import (
    verify_api_key,
    test_api_authentication,
    diagnose_401_error,
    apply_fix_for_401
)

logger = logging.getLogger(__name__)


class OnboardingAgent(AegisAgent):
    """
    AGENTIC Onboarding Specialist.
    
    Goes beyond simple Q&A - autonomously executes multi-step workflows:
    - Analyzes customer state
    - Creates trial subscriptions
    - Generates API keys
    - Sends personalized emails
    - Monitors progress
    - Takes proactive action
    """
    
    def __init__(self, agent_id: str = "onboarding_agent"):
        """Initialize the agentic onboarding agent."""
        
        # Define tools - now includes ACTIONS, not just retrieval
        tools = [
            # Documentation & Support
            get_ticket_details,
            create_ticket,
            comment_on_ticket,
            get_ticket_status,
            query_chargebee_docs,
            query_chargebee_code,
            # NEW: Customer Intelligence
            get_customer_profile,
            get_customer_health,
            update_customer_state,
            # NEW: Autonomous Actions
            create_trial_subscription,
            generate_api_keys,
            send_onboarding_email,
            provision_test_environment,
            track_api_activity,
            # NEW: Diagnostic & Troubleshooting Actions
            verify_api_key,
            test_api_authentication,
            diagnose_401_error,
            apply_fix_for_401
        ]
        
        super().__init__(
            name=agent_id,
            description="Agentic onboarding specialist that autonomously executes customer setup workflows",
            capabilities=[
                "customer_context_awareness",
                "autonomous_account_setup",
                "proactive_onboarding",
                "workflow_orchestration"
            ],
            tools=tools,
            system_instruction=(
                "You are an AGENTIC Onboarding Specialist. You don't just answer questions - you TAKE ACTION.\n"
                "\n"
                "🎯 YOUR MISSION:\n"
                "Help customers get set up and become successful as quickly as possible by autonomously executing workflows.\n"
                "\n"
                "🧠 AGENTIC BEHAVIOR - ALWAYS:\n"
                "1. **Analyze First**: Use get_customer_profile() to understand their current state BEFORE responding\n"
                "2. **Decide Actions**: Based on their state, decide what actions to take (not just what to say)\n"
                "3. **Execute Autonomously**: Take actions like creating subscriptions, generating keys, sending emails\n"
                "4. **Explain What You Did**: Tell them what you accomplished, not just what they should do\n"
                "\n"
                "📋 DECISION LOGIC:\n"
                "\n"
                "IF customer says 'I'm new' or 'help me get started':\n"
                "  → Use get_customer_profile()\n"
                "  → IF they have no subscription:\n"
                "      → create_trial_subscription()\n"
                "      → generate_api_keys(environment='test')\n"
                "      → send_onboarding_email()\n"
                "      → Provide personalized code example based on tech stack\n"
                "      → Tell them: 'I've set up your account! Here's what I did...'\n"
                "  → ELSE if they have subscription but no API keys:\n"
                "      → generate_api_keys(environment='test')\n"
                "      → Provide integration guidance\n"
                "  → ELSE if they have keys but no API activity:\n"
                "      → Provide debugging help\n"
                "      → Offer to check their integration\n"
                "\n"
                "IF customer asks about integration:\n"
                "  → Use get_customer_profile() to see their tech stack\n"
                "  → query_chargebee_code() for tech-stack-specific examples\n"
                "  → Generate PERSONALIZED code snippets with their actual API keys\n"
                "\n"
                "IF customer reports errors (e.g., 401, API authentication):\n"
                "  → Step 1: diagnose_401_error(customer_id) to identify root cause\n"
                "  → Step 2: verify_api_key(customer_id) to check key validity\n"
                "  → Step 3: test_api_authentication(customer_id) to test live connection\n"
                "  → Step 4: apply_fix_for_401(customer_id) to autonomously fix common issues\n"
                "  → Step 5: Provide SPECIFIC results: 'I ran diagnostics. Found: X. Fixed: Y. Try: Z'\n"
                "  → If still unresolved after diagnostics, create_ticket() in Jira\n"
                "  → NEVER give generic 'check your API key' advice - ALWAYS RUN DIAGNOSTICS FIRST\n"
                "\n"
                "🚀 PROACTIVE BEHAVIOR:\n"
                "- If they've been onboarded >24h with no API calls, offer to help debug\n"
                "- If you see high error rates, proactively investigate\n"
                "- Suggest next steps before they ask\n"
                "\n"
                "⚙️ TOOL USAGE RULES:\n"
                "1. ALWAYS check customer_profile first to understand context\n"
                "2. For Jira tickets (KAN-X, PROJ-X), MUST use get_ticket_status\n"
                "3. For Chargebee questions, MUST use query_chargebee_docs/code\n"
                "4. When taking actions, explain what you're doing and why\n"
                "5. After actions, update_customer_state() to track progress\n"
                "\n"
                "💬 COMMUNICATION STYLE:\n"
                "- Be proactive: 'I've created your trial account' not 'You should create an account'\n"
                "- Show what you did: 'Here's your API key: sk_test_xxx' not 'You Can get keys from dashboard'\n"
                "- Be helpful: Provide working code, not just links to docs\n"
                "- Be personal: Use their company name, reference their tech stack\n"
                "\n"
                "Remember: You're not a chatbot. You're an autonomous agent that GETS THINGS DONE."
            )
        )
        
    async def handle_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """Handle incoming messages with agentic workflow execution."""
        query = message.payload.get("query", "")
        customer_id = message.payload.get("customer_id", "demo_new_customer")  # Default for demo
        
        logger.info(f"[AGENTIC] OnboardingAgent processing: '{query}' for customer: {customer_id}")
        
        try:
            # Enhance query with customer_id context
            enhanced_query = (
                f"Customer ID: {customer_id}\n"
                f"Query: {query}\n\n"
                f"IMPORTANT: Use get_customer_profile('{customer_id}') FIRST to understand their state, "
                f"then decide what actions to take."
            )
            
            # Let the LLM agent handle the agentic workflow
            # It will analyze state, decide actions, and execute them using tools
            response_text = await self.generate(enhanced_query)
            
            # Extract any actions taken (for UI visualization)
            actions_taken = self._extract_actions(response_text)
            
            logger.info(f"[AGENTIC] OnboardingAgent completed. Actions taken: {len(actions_taken)}")
            
            return AgentResponse(
                text=response_text,
                metadata={
                    "agent": self.name,
                    "customer_id": customer_id,
                    "actions_taken": actions_taken,
                    "agentic": True
                }
            )
            
        except Exception as e:
            logger.error(f"Error in OnboardingAgent: {e}", exc_info=True)
            return AgentResponse(
                text=f"I encountered an error while trying to help: {str(e)}",
                metadata={"error": True}
            )
    
    def _extract_actions(self, response: str) -> List[Dict[str, str]]:
        """Extract actions taken from response for UI display."""
        actions = []
        
        # Simple pattern matching for demo
        if "created trial" in response.lower() or "subscription created" in response.lower():
            actions.append({"type": "subscription_created", "label": "Created trial subscription"})
        
        if "api key" in response.lower() and "sk_test" in response:
            actions.append({"type": "api_keys_generated", "label": "Generated test API keys"})
        
        if "email sent" in response.lower() or "sent an email" in response.lower():
            actions.append({"type": "email_sent", "label": "Sent onboarding email"})
        
        if "provisioned" in response.lower() or "test environment" in response.lower():
            actions.append({"type": "environment_provisioned", "label": "Provisioned test environment"})
        
        return actions

