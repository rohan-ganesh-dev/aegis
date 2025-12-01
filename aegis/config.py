"""
Configuration management for Aegis.

Loads environment variables and provides centralized config access.
IMPORTANT: All API keys are placeholders. Replace with real keys in production.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AegisConfig:
    """Central configuration for Aegis system."""

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Gemini Model Configuration (NO API KEYS - use ADK configuration)
    # TODO: Configure actual ADK authentication in production
    gemini_supervisor_model: str = os.getenv("GEMINI_SUPERVISOR_MODEL", "gemini-2.5-pro")
    gemini_specialist_model: str = os.getenv("GEMINI_SPECIALIST_MODEL", "gemini-2.0-flash")

    # Vector DB Configuration (Mock)
    vector_db_url: str = os.getenv("VECTOR_DB_URL", "http://localhost:6333")
    vector_db_collection: str = os.getenv("VECTOR_DB_COLLECTION", "aegis_docs")

    # Transport Configuration
    transport_type: str = os.getenv("TRANSPORT_TYPE", "in_memory")  # in_memory | redis
    redis_url: Optional[str] = os.getenv("REDIS_URL", None)

    # HIL Configuration
    hil_api_url: str = os.getenv("HIL_API_URL", "http://localhost:8001")
    hil_dashboard_url: str = os.getenv("HIL_DASHBOARD_URL", "http://localhost:8501")

    # External API Placeholders (DO NOT USE REAL KEYS)
    # TODO: Replace with actual keys in production environment
    chargebee_api_key: str = os.getenv("CHARGEBEE_API_KEY", "PLACEHOLDER_CHARGEBEE_KEY")
    zendesk_api_key: str = os.getenv("ZENDESK_API_KEY", "PLACEHOLDER_ZENDESK_KEY")
    support_api_key: str = os.getenv("SUPPORT_API_KEY", "PLACEHOLDER_SUPPORT_KEY")

    # Jira Configuration (for MCP integration)
    jira_url: str = os.getenv("JIRA_URL", "")
    jira_username: str = os.getenv("JIRA_USERNAME", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "")
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "")  # e.g., https://yourorg.atlassian.net/browse
    
    # Jira MCP Server Configuration
    jira_mcp_command: str = os.getenv("JIRA_MCP_COMMAND", "docker")
    jira_mcp_image: str = os.getenv("JIRA_MCP_IMAGE", "")

    # Chargebee MCP Configuration
    chargebee_mcp_url: str = os.getenv("CHARGEBEE_MCP_URL", "")

    # Google ADK Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    adk_agent_card_port: int = int(os.getenv("ADK_AGENT_CARD_PORT", "8080"))
    adk_session_store: str = os.getenv("ADK_SESSION_STORE", "in_memory")

    def __post_init__(self):
        """Set up logging after initialization."""
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the application."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


# Global config instance
config = AegisConfig()
