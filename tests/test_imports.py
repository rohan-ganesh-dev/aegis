"""
Test module imports.

Validates that all core modules are importable.
This is a basic smoke test to catch import-time errors.
"""

import pytest


def test_import_config():
    """Test that config module imports successfully."""
    from aegis import config

    assert config is not None


def test_import_agents_base():
    """Test that agents.base module imports successfully."""
    from aegis.agents import base

    assert base.AgentMessage is not None
    assert base.AgentResponse is not None
    assert base.CustomerContext is not None
    assert base.BaseAgent is not None


def test_import_orchestrator():
    """Test that orchestrator agent imports successfully."""
    from aegis.agents import OrchestratorAgent

    assert OrchestratorAgent is not None


def test_import_specialist_agents():
    """Test that all specialist agents import successfully."""
    from aegis.agents import (
        OnboardingAgent,
        QueryResolutionAgent,
        FeedbackAgent,
    )

    assert OnboardingAgent is not None
    assert QueryResolutionAgent is not None
    assert FeedbackAgent is not None


def test_import_tools():
    """Test that all tools import successfully."""
    from aegis.tools import (
        ChargebeeClient,
    )

    assert ChargebeeClient is not None


def test_import_hil():
    """Test that HIL modules are importable."""
    # HIL modules use streamlit/fastapi so we just check they exist
    import aegis.hil.dashboard

    assert aegis.hil.dashboard is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
