"""State management package."""

from aegis.state.state_manager import (
    StateManager,
    CustomerProfile,
    OnboardingStage,
    SubscriptionTier,
    get_state_manager
)

__all__ = [
    'StateManager',
    'CustomerProfile', 
    'OnboardingStage',
    'SubscriptionTier',
    'get_state_manager'
]
