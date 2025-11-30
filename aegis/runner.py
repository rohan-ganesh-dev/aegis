"""
ADK Runner infrastructure for Aegis agents.

Provides centralized runner and session management for ADK-based agents.
"""

import json
import logging
import os
import warnings
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from aegis.config import config

# Suppress warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class AegisRunner:
    """
    Centralized runner for ADK agents in Aegis.
    
    Manages session service, Gemini model configuration, and agent lifecycle.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Aegis runner.
        
        Args:
            api_key: Google API key (defaults to config value)
        """
        self.api_key = api_key or config.google_api_key
        
        if not self.api_key:
            logger.warning(
                "No Google API key configured. Set GOOGLE_API_KEY in .env file. "
                "Get your key from: https://aistudio.google.com/app/apikey"
            )
        
        # Initialize session service
        self.session_service = InMemorySessionService()
        
        logger.info("✅ ADK Session Service initialized")
    
    def create_gemini_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
    ) -> Gemini:
        """
        Create a Gemini model instance with configured parameters.
        
        Args:
            model_name: Model name (defaults to config supervisor model)
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            Configured Gemini model instance
        """
        model_name = model_name or config.gemini_supervisor_model
        print(f"DEBUG: AegisRunner.create_gemini_model: model_name='{model_name}'")
        
        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
        )
        
        model = Gemini(
            model_name=model_name,
            api_key=self.api_key,
            generation_config=generation_config,
        )
        print(f"DEBUG: Created Gemini model. Attributes: {dir(model)}")
        if hasattr(model, '_model_name'):
            print(f"DEBUG: Gemini._model_name: {model._model_name}")
        return model
    
    def register_agent(self, agent: LlmAgent) -> None:
        """
        Register an agent with the runner.
        
        Args:
            agent: LlmAgent instance to register
        """
        logger.info(f"Registered agent: {agent.name if hasattr(agent, 'name') else 'unknown'}")
    
    async def run_agent(
        self,
        agent: LlmAgent,
        user_input: str,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Run an agent with user input.
        
        Args:
            agent: LlmAgent to run
            user_input: User input text
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Agent response text
        """
        try:
            # Create a runner for this specific agent execution
            # ADK Runner requires agent and app_name
            runner = Runner(
                agent=agent,
                app_name="aegis",
                session_service=self.session_service
            )
            
            # Use runner to execute agent
            response = await runner.run(
                user_input=user_input,
                session_id=session_id,
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            raise


# Global runner instance
_global_runner: Optional[AegisRunner] = None


def get_runner() -> AegisRunner:
    """Get or create the global ADK runner instance."""
    global _global_runner
    
    if _global_runner is None:
        _global_runner = AegisRunner()
    
    return _global_runner


def create_gemini_model(model_name: Optional[str] = None, **kwargs) -> Gemini:
    """
    Convenience function to create a Gemini model.
    
    Args:
        model_name: Model name (optional)
        **kwargs: Additional parameters for model configuration
        
    Returns:
        Configured Gemini model instance
    """
    runner = get_runner()
    return runner.create_gemini_model(model_name=model_name, **kwargs)
