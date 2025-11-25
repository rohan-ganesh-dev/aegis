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


def test_import_supervisor():
    """Test that supervisor agent imports successfully."""
    from aegis.agents import SupervisorAgent

    assert SupervisorAgent is not None


def test_import_specialist_agents():
    """Test that all specialist agents import successfully."""
    from aegis.agents import (
        GrowthAgent,
        IntegrationAgent,
        OnboardingAgent,
        ProactiveAgent,
    )

    assert OnboardingAgent is not None
    assert IntegrationAgent is not None
    assert ProactiveAgent is not None
    assert GrowthAgent is not None


def test_import_tools():
    """Test that all tools import successfully."""
    from aegis.tools import (
        BillingMonitor,
        ChargebeeClient,
        PerksEngine,
        PlatformMonitor,
        SandboxAPITool,
        SupportMonitor,
        VectorDBClient,
        ZendeskClient,
    )

    assert VectorDBClient is not None
    assert ChargebeeClient is not None
    assert ZendeskClient is not None
    assert SandboxAPITool is not None
    assert BillingMonitor is not None
    assert PlatformMonitor is not None
    assert SupportMonitor is not None
    assert PerksEngine is not None


def test_import_transports():
    """Test that transport modules import successfully."""
    from aegis.transports import InMemoryTransport, RedisTransportAdapter

    assert InMemoryTransport is not None
    assert RedisTransportAdapter is not None


def test_import_hil():
    """Test that HIL modules are importable."""
    # HIL modules use streamlit/fastapi so we just check they exist
    import aegis.hil.api
    import aegis.hil.dashboard

    assert aegis.hil.api is not None
    assert aegis.hil.dashboard is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
