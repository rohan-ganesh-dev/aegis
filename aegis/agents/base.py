"""
Base agent classes and message schemas for Aegis with ADK integration.

This module defines the foundational interfaces for the multi-agent system,
including ADK LlmAgent wrappers, message schemas, and A2A protocol support.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from google.adk.agents import LlmAgent
# from google.adk.a2a.utils.agent_to_a2a import to_a2a  # Not needed for local agents
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_request import LlmRequest
from google.genai import types
from pydantic import PrivateAttr

from aegis.config import config
from aegis.runner import create_gemini_model

logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """
    Standard message format for agent-to-agent communication.

    Attributes:
        id: Unique message identifier
        sender: ID of the sending agent
        recipient: ID of the receiving agent
        type: Message type (e.g., 'task', 'response', 'event')
        payload: Message payload as a dictionary
        timestamp: Message creation timestamp
    """

    sender: str
    recipient: str
    type: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class AgentResponse:
    """
    Standard response format from agent message handlers.

    Attributes:
        text: Human-readable response text
        actions: List of actions to be executed
        attachments: Additional data attachments
        metadata: Extra metadata for tracking/debugging
        execution_steps: Execution flow tracking for UI visualization
    """

    text: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_steps: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return asdict(self)


@dataclass
class CustomerContext:
    """
    Per-customer context for maintaining state across interactions.

    Attributes:
        customer_id: Unique customer identifier
        conversation_history: List of previous messages
        preferences: Customer preferences
        metadata: Additional context data
    """

    customer_id: str
    conversation_history: List[AgentMessage] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append(message)


class AgentTransport(ABC):
    """
    Abstract transport interface for agent-to-agent messaging.

    Concrete implementations include in-memory queues, Redis, etc.
    """

    @abstractmethod
    async def send(self, message: AgentMessage) -> None:
        """Send a message to the transport."""
        pass

    @abstractmethod
    async def subscribe(
        self, agent_id: str, handler: Callable[[AgentMessage], Any]
    ) -> None:
        """Subscribe an agent to receive messages."""
        pass

    @abstractmethod
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe an agent from receiving messages."""
        pass

class AegisAgent(LlmAgent):
    """
    Base class for all Aegis agents using Google ADK.
    
    Extends LlmAgent with Aegis-specific functionality including:
    - Agent card generation for A2A discovery
    - Message handling compatibility
    - Tool registration
    """
    
    # Define additional Pydantic fields
    capabilities: List[str] = field(default_factory=list)
    
    # Private attributes for internal state
    _logger: Any = PrivateAttr()
    _running: bool = PrivateAttr(default=False)
    
    def __init__(
        self,
        name: str,
        model: Optional[Gemini] = None,
        description: str = "",
        capabilities: Optional[List[str]] = None,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Any]] = None,
    ):
        """
        Initialize Aegis agent with ADK LlmAgent.
        
        Args:
            name: Agent name/identifier
            model: Gemini model instance (creates default if None)
            description: Agent description for A2A discovery
            capabilities: List of agent capabilities
            system_instruction: System instruction for the agent
            tools: List of tools available to the agent
        """
        # Create default model if not provided
        if model is None:
            model = create_gemini_model("gemini-2.0-flash")
        
        # Initialize LlmAgent
        super().__init__(
            name=name,
            model=model,
            description=description,
            instruction=system_instruction or self._default_system_instruction(),
            tools=tools or [],
            capabilities=capabilities or [],
        )
        
        self._logger = logging.getLogger(f"{__name__}.{name}")
        self._running = False
        
        self._logger.info(f"Initialized ADK agent: {name}")

    @property
    def logger(self):
        """Expose logger for subclasses."""
        return self._logger
    
    def _default_system_instruction(self) -> str:
        """Default system instruction for the agent."""
        return (
            "You are a helpful AI agent in the Aegis multi-agent system. "
            "Provide accurate, concise, and helpful responses."
        )
    
    def get_agent_card(self) -> Dict[str, Any]:
        """
        Generate agent card for A2A discovery.
        
        Returns:
            Agent card dictionary with capabilities and metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "version": "1.0.0",
            "metadata": {
                "framework": "google-adk",
                "system": "aegis",
            }
        }
    
    async def start(self) -> None:
        """Start the agent."""
        self.logger.info(f"Starting ADK agent: {self.name}")
        self._running = True
        # Agent card can be served via well-known endpoint
        self.logger.info(f"Agent {self.name} started successfully")
    
    async def stop(self) -> None:
        """Stop the agent."""
        self.logger.info(f"Stopping ADK agent: {self.name}")
        self._running = False
        self.logger.info(f"Agent {self.name} stopped successfully")
    
    async def handle_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """
        Handle incoming message (for backward compatibility).
        
        This method provides compatibility with the existing message-based system.
        Subclasses can override this for custom message handling.
        
        Args:
            message: Incoming agent message
            
        Returns:
            AgentResponse or None
        """
        # Default implementation: convert message to text and use LLM
        try:
            query = message.payload.get("query", "")
            
            # Use the LlmAgent's generate method
            response_text = await self.generate(query)
            
            return AgentResponse(
                text=response_text,
                metadata={"agent": self.name, "message_id": message.id}
            )
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}", exc_info=True)
            return AgentResponse(
                text=f"Error processing request: {str(e)}",
                metadata={"error": True}
            )
    
    def _format_function_result(self, func_name: str, result: Any, user_query: str) -> str:
        """
        Format function result into the standard 3-section response.
        
        Args:
            func_name: Name of the function that was called
            result: Result from the function
            user_query: Original user query
            
        Returns:
            Formatted string in 3-section format
        """
        # Extract content from result if it's a dict with nested structure
        content = result
        if isinstance(result, dict):
            if 'output' in result and isinstance(result['output'], dict):
                content = result['output'].get('content', result)
            elif 'result' in result:
                content = result['result']
        
        # Convert to string if needed
        content_str = content if isinstance(content, str) else json.dumps(content, indent=2)
        
        # Extract code blocks for better presentation
        import re
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content_str, re.DOTALL)
        
        # Build formatted response
        formatted_codes = ""
        if code_blocks:
            formatted_codes = "\n\n**Code Examples:**\n"
            for i, code in enumerate(code_blocks, 1):
                formatted_codes += f"\nExample {i}:\n```python\n{code.strip()}\n```\n"
        
        return f"""**Diagnostic Results:**
- Found information about {user_query}
- Retrieved from {func_name} tool
{content_str[:500]}...

**Actions Taken:**
- Executed {func_name} tool to search Chargebee documentation
- Retrieved integration guides and code examples
{formatted_codes}

**Next Steps:**
1. Install the SDK: `pip install chargebee`
2. Try the code examples above
3. Check the full documentation at: https://apidocs.chargebee.com/docs/api?lang=python
4. Let me know if you need help with a specific use case!
"""
    
    async def generate(self, user_input: str, **kwargs) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            user_input: User input text
            **kwargs: Additional arguments
            
        Returns:
        """
        try:
            # BYPASS ADK: Call google-genai client API directly
            # The ADK Gemini wrapper has a bug where _model_name is always None
            # So we call the underlying API client directly
            
            model_name = "gemini-2.0-flash"
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"
            
            print(f"DEBUG: Using model: {model_name}")
            
            # Always create a fresh client to avoid MagicMock issues
            from google.genai import Client
            import os
            client = Client(api_key=os.getenv("GOOGLE_API_KEY"))
            
            # Call the API directly WITH TOOLS
            from google.genai import types
            
            # Build config with tools and system instruction
            config_dict = {}
            tools = getattr(self, 'tools', None)
            instruction = getattr(self, 'instruction', None)
            if tools:
                config_dict['tools'] = tools
                # Use AUTO mode so model can choose
                config_dict['tool_config'] = {'function_calling_config': {'mode': 'AUTO'}}
                # CRITICAL: Disable SDK's automatic execution because our tools are async
                # and we handle execution manually
                config_dict['automatic_function_calling'] = {'disable': True}
            if instruction:
                config_dict['system_instruction'] = instruction
            
            # Create config object if we have any settings
            config = types.GenerateContentConfig(**config_dict) if config_dict else None
            self.logger.info(f"Config created with tools: {len(tools) if tools else 0}")
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=user_input,
                config=config
            )
            
            
            self.logger.info(f"Response received, type: {type(response)}")
            
            # Check for function calls in the response
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    
                    # Check if there are function calls that need to be executed
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                func_call = part.function_call
                                self.logger.info(f"Model requested function call: {func_call.name}")
                                self.logger.info(f"Function arguments: {dict(func_call.args)}")
                                
                                
                                # Find and execute the function
                                tool_func = None
                                for tool in (tools or []):
                                    if hasattr(tool, '__name__') and tool.__name__ == func_call.name:
                                        tool_func = tool
                                        break
                                
                                if tool_func:
                                    try:
                                        # Execute the async function
                                        import inspect
                                        import asyncio
                                        
                                        # Convert Struct args to dict
                                        args_dict = dict(func_call.args)
                                        print(f"DEBUG: Calling {tool_func.__name__} with args: {args_dict}")
                                        
                                        if inspect.iscoroutinefunction(tool_func):
                                            result = await tool_func(**args_dict)
                                        else:
                                            result = tool_func(**args_dict)
                                        
                                        print(f"DEBUG: Function result: {result}")
                                        
                                        # Send the function result back to the model
                                        function_response_parts = [
                                            types.Part.from_function_response(
                                                name=func_call.name,
                                                response={"result": result}
                                            )
                                        ]
                                        
                                        # Make a second call with the function result, with RETRY logic
                                        import asyncio
                                        max_retries = 3
                                        base_delay = 2
                                        
                                        response2 = None
                                        for attempt in range(max_retries):
                                            try:
                                                response2 = await client.aio.models.generate_content(
                                                    model=model_name,
                                                    contents=[
                                                        user_input,
                                                        content,  # Original response with function call
                                                        types.Content(
                                                            parts=function_response_parts,
                                                            role="function"
                                                        )
                                                    ],
                                                    config=config
                                                )
                                                break # Success
                                            except Exception as retry_e:
                                                # Check if it's the INVALID_ARGUMENT function mismatch error
                                                if "INVALID_ARGUMENT" in str(retry_e) and "function response parts" in str(retry_e):
                                                    self.logger.warning(f"Function calling mismatch error, formatting result directly")
                                                    # Format the result according to the 3-section format
                                                    formatted_result = self._format_function_result(func_call.name, result, user_input)
                                                    return formatted_result
                                                elif "429" in str(retry_e) and attempt < max_retries - 1:
                                                    delay = base_delay * (2 ** attempt)
                                                    self.logger.warning(f"Rate limit hit, retrying in {delay}s...")
                                                    await asyncio.sleep(delay)
                                                else:
                                                    raise retry_e
                                        
                                        self.logger.info("Sent function result back to model")
                                        
                                        # Check if second response has text
                                        if hasattr(response2, 'text') and response2.text:
                                            self.logger.info(f"Final response: {response2.text[:100]}...")
                                            return response2.text
                                        else:
                                            # Model is still trying to call functions or returned no text
                                            self.logger.warning("Model didn't provide text response after function call, returning function result directly")
                                            return f"Function executed successfully. Result: {result}"
                                        
                                        
                                    except Exception as e:
                                        print(f"ERROR: Failed to execute function {func_call.name}: {e}")
                                        import traceback
                                        traceback.print_exc()
                                        return f"Error executing tool: {str(e)}"
                                else:
                                    print(f"ERROR: Function {func_call.name} not found in tools")
                                    return f"Error: Tool '{func_call.name}' not found"
            
            # Try to get text from response (if no function calls)
            if hasattr(response, 'text'):
                print(f"DEBUG: Response text: {response.text[:200]}..." if len(response.text) > 200 else f"DEBUG: Response text: {response.text}")
                return response.text
            else:
                print(f"DEBUG: No 'text' attribute. Full response: {response}")
                return str(response)
            
            
            
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}", exc_info=True)
            print(f"ERROR: Exception type: {type(e)}")
            print(f"ERROR: Exception message: {str(e)}")
            import traceback
            print(f"ERROR: Traceback:\n{traceback.format_exc()}")
            raise


# Keep BaseAgent for backward compatibility
class BaseAgent(ABC):
    """
    Legacy base class for backward compatibility.
    
    New agents should extend AegisAgent instead.
    """

    def __init__(
        self,
        agent_id: str,
        transport: Optional[AgentTransport] = None,
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier for this agent
            transport: Message transport (optional)
        """
        self.agent_id = agent_id
        self.transport = transport
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        self._running = False

    async def start(self) -> None:
        """Start the agent and subscribe to transport."""
        self.logger.info(f"Starting agent: {self.agent_id}")
        self._running = True

        if self.transport:
            await self.transport.subscribe(self.agent_id, self._handle_message_wrapper)

        self.logger.info(f"Agent {self.agent_id} started successfully")

    async def stop(self) -> None:
        """Stop the agent and cleanup resources."""
        self.logger.info(f"Stopping agent: {self.agent_id}")
        self._running = False

        if self.transport:
            await self.transport.unsubscribe(self.agent_id)

        self.logger.info(f"Agent {self.agent_id} stopped successfully")

    async def _handle_message_wrapper(self, message: AgentMessage) -> None:
        """Internal wrapper for message handling with error handling."""
        try:
            self.logger.debug(f"Received message: {message.id} from {message.sender}")
            response = await self.handle_message(message)
            self.logger.debug(f"Processed message: {message.id}")

            # Send response if applicable
            if response and self.transport:
                response_msg = AgentMessage(
                    sender=self.agent_id,
                    recipient=message.sender,
                    type="response",
                    payload=response.to_dict(),
                )
                await self.transport.send(response_msg)

        except Exception as e:
            self.logger.error(f"Error handling message {message.id}: {e}", exc_info=True)

    @abstractmethod
    async def handle_message(self, message: AgentMessage) -> Optional[AgentResponse]:
        """
        Handle incoming message and return response.

        Args:
            message: Incoming agent message

        Returns:
            AgentResponse or None if no response needed
        """
        pass
