"""
Orchestrator Agent implementation using Google ADK.

The Orchestrator is responsible for:
1. Analyzing user intent
2. Routing tasks to specialist agents via A2A protocol
3. Synthesizing responses
"""

import logging
from typing import Dict, List, Optional, Any

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini

from aegis.agents.base import AegisAgent, AgentMessage, AgentResponse
from aegis.config import config
from aegis.runner import create_gemini_model

logger = logging.getLogger(__name__)


from pydantic import PrivateAttr

class OrchestratorAgent(AegisAgent):
    """
    Central orchestrator that routes queries to specialist agents.
    
    Uses Gemini to classify intent and delegates to local specialist agents.
    """
    
    _specialists: Dict[str, AegisAgent] = PrivateAttr(default_factory=dict)
    
    def __init__(self, agent_id: str = "orchestrator"):
        """
        Initialize the orchestrator agent.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        # Create Gemini model for intent classification
        model = create_gemini_model(
            model_name="gemini-2.0-flash",
            temperature=0.2,  # Lower temperature for classification
        )
        
        super().__init__(
            name=agent_id,
            model=model,
            description="Orchestrator agent that routes user queries to specialists",
            capabilities=["intent_classification", "routing", "synthesis"],
            system_instruction=(
                "You are the Aegis Orchestrator. Your job is to analyze user queries "
                "and route them to the appropriate specialist agent. "
                "You have access to: "
                "1. OnboardingAgent: For new customer onboarding, setup, and migration "
                "2. QueryResolutionAgent: For general questions, features, bugs, and documentation"
            )
        )
        
        # Initialize specialist agents map
        self._specialists = {}
        self._init_specialists()

    @property
    def specialists(self):
        """Expose specialists map."""
        return self._specialists
        
    def _init_specialists(self):
        """Initialize local specialist agents."""
        # Import here to avoid circular dependencies
        from aegis.agents.onboarding_agent import OnboardingAgent
        from aegis.agents.query_resolution_agent import QueryResolutionAgent
        from aegis.agents.feedback_agent import FeedbackAgent
        
        # Instantiate specialist agents locally
        # Both agents now have full access to Jira + Chargebee tools
        self._specialists["onboarding"] = OnboardingAgent()
        self._specialists["query_resolution"] = QueryResolutionAgent()
        self._specialists["feedback"] = FeedbackAgent()
        
    async def route_request(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Analyze query and route to appropriate specialist.
        
        Args:
            query: User query text
            context: Optional context
            
        Returns:
            AgentResponse from the specialist
        """
        # 1. Analyze intent using Gemini
        intent_prompt = f"""
        Analyze the following user query and determine the best agent to handle it.
        
        Query: "{query}"
        
        Available Agents:
        - onboarding: For new customer setup, account creation, API key generation, migration planning, 
          AND error troubleshooting (401 errors, authentication issues, API failures). 
          This agent has DIAGNOSTIC TOOLS to verify keys, test authentication, and fix issues.
        - query_resolution: For platform usage documentation, feature how-to guides, 
          conceptual questions, and general documentation queries (no actions, just info).
        
        FORCED ROUTING RULES (MUST OBEY):
        - If query contains "401" OR "error" OR "failing" OR "authentication" OR "unauthorized" -> onboarding
        - If query contains "get started" OR "setup" OR "new customer" -> onboarding
        - If query about troubleshooting OR diagnosing problems -> onboarding
        - Otherwise -> query_resolution
        
        Guidelines:
        - "How do I create a customer?" -> query_resolution (Usage/API docs)
        - "Help me get started" -> onboarding (Setup + Actions)
        - "My API calls are failing with 401" -> onboarding (ERROR TROUBLESHOOTING)
        - "I'm getting authentication errors" -> onboarding (ERROR TROUBLESHOOTING)
        - "Why am I getting 401 errors?" -> onboarding (ERROR TROUBLESHOOTING)
        - "API calls keep failing" -> onboarding (ERROR TROUBLESHOOTING)
        - "My payment failed" -> query_resolution (General issue info)
        - "I need to migrate from Stripe" -> onboarding (Migration)
        - "Where do I find my API keys?" -> onboarding (Setup)
        - "How does subscription billing work?" -> query_resolution (Conceptual)
        
        CRITICAL: ANY query about API errors, authentication failures, or troubleshooting -> onboarding
        (The onboarding agent has diagnostic tools to actually FIX issues, not just explain them)
        
        Return ONLY the agent name (onboarding or query_resolution).
        """
        
        try:
            intent_response = await self.generate(intent_prompt)
            target_agent = intent_response.strip().lower()
            
            logger.info(f"Routed query '{query}' to {target_agent}")
            
            # 2. Forward to specialist
            if target_agent in self._specialists:
                specialist = self._specialists[target_agent]
                
                # Start the specialist agent
                await specialist.start()
                
                try:
                    # Create message to send to specialist
                    message = AgentMessage(
                        sender=self.name,
                        recipient=specialist.name,
                        type="task",
                        payload={"query": query, **(context or {})}
                    )
                    
                    # Call the specialist's handle_message method
                    response = await specialist.handle_message(message)
                    
                    # Add routing metadata
                    if response.metadata is None:
                        response.metadata = {}
                    response.metadata["routed_to"] = target_agent
                    response.metadata["orchestrator"] = {
                        "routed_to": specialist.name,
                        "classification": target_agent
                    }
                    
                    return response
                finally:
                    # Stop the specialist agent
                    await specialist.stop()
            else:
                # Fallback to local handling if agent not found
                return AgentResponse(
                    text=f"I couldn't find an appropriate specialist for: {query}. Available specialists: {list(self._specialists.keys())}",
                    metadata={"routed_to": "self", "error": "no_specialist_found"}
                )
                
        except Exception as e:
            logger.error(f"Routing error: {e}", exc_info=True)
            return AgentResponse(
                text=f"Error routing request: {str(e)}",
                metadata={"error": True}
            )

    async def handle_feedback(self, feedback_data: Dict[str, Any]) -> AgentResponse:
        """
        Delegate feedback handling to the FeedbackAgent.
        
        Args:
            feedback_data: Dictionary containing feedback details
            
        Returns:
            AgentResponse from the feedback agent
        """
        feedback_type = feedback_data.get("feedback_type", "unknown")
        
        # If feedback is positive (thumbs up), just acknowledge and return
        if feedback_type == "positive":
            logger.info("Received positive feedback - no action needed")
            return AgentResponse(
                text="Thank you for your positive feedback! We're glad we could help.",
                metadata={"feedback_type": "positive", "action": "acknowledged"}
            )
        
        # Only create tickets or add comments for negative feedback
        agent = self._specialists["feedback"]
        await agent.start()
        
        try:
            # Create a prompt for the feedback agent
            query = feedback_data.get("query", "")
            additional_feedback = feedback_data.get("additional_feedback", "")
            docs_answer = feedback_data.get("docs_answer", "")
            issue_key = feedback_data.get("issue_key")  # Extract issue_key
            
            # Include issue_key in the prompt if present
            if issue_key:
                prompt = f"""
Analyze this user feedback and ADD A COMMENT to the existing ticket {issue_key}.

Feedback Type: {feedback_type}
Original User Query: "{query}"
Agent Answer: "{docs_answer}"
User Comments: "{additional_feedback}"
Existing Ticket: {issue_key}

Use comment_on_ticket to add this feedback to ticket {issue_key}.
                """
            else:
                prompt = f"""
Analyze this user feedback and CREATE A NEW Jira ticket.

Feedback Type: {feedback_type}
Original User Query: "{query}"
Agent Answer: "{docs_answer}"
User Comments: "{additional_feedback}"

Please create a ticket with a clear summary and description.
                """
            
            message = AgentMessage(
                sender=self.name,
                recipient=agent.name,
                type="task",
                payload={"query": prompt, "issue_key": issue_key}  # Pass issue_key in payload
            )
            
            response = await agent.handle_message(message)
            return response
            
        finally:
            await agent.stop()

    async def handle_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """Override handle_message to use routing logic."""
        query = message.payload.get("query", "")
        return await self.route_request(query, message.payload)
