"""
Session service singleton for managing ADK sessions.

Provides a centralized way to create and retrieve sessions across the application.
"""

from typing import Optional
from google.adk.sessions import InMemorySessionService, Session

# Singleton instance
_session_service: Optional[InMemorySessionService] = None


def get_session_service() -> InMemorySessionService:
    """
    Get the global session service instance.
    
    Returns:
        InMemorySessionService instance
    """
    global _session_service
    if _session_service is None:
        _session_service = InMemorySessionService()
    return _session_service


async def get_or_create_session(
    app_name: str,
    user_id: str,
    session_id: str
) -> Session:
    """
    Get an existing session or create a new one.
    
    Args:
        app_name: Application name (e.g., 'aegis')
        user_id: Unique user identifier
        session_id: Unique session identifier
        
    Returns:
        Session object
    """
    service = get_session_service()
    
    try:
        # Try to create a new session
        session = await service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
    except Exception:
        # If it already exists, retrieve it
        session = await service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
    
    return session
