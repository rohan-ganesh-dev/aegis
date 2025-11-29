"""
State Manager for Customer Workflows.

Manages customer state, workflow progress, and context.
Production: Replace with Redis/PostgreSQL.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class OnboardingStage(Enum):
    """Customer onboarding stages."""
    NEW = "new"
    TRIAL_CREATED = "trial_created"
    API_KEYS_GENERATED = "api_keys_generated"
    FIRST_API_CALL = "first_api_call"
    INTEGRATION_VALIDATED = "integration_validated"
    PRODUCTION_READY = "production_ready"


class SubscriptionTier(Enum):
    """Subscription tiers."""
    NONE = "none"
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class CustomerProfile:
    """Customer profile with state and context."""
    customer_id: str
    email: str
    company: str
    created_at: datetime
    
    # Subscription info
    subscription_tier: SubscriptionTier = SubscriptionTier.NONE
    subscription_id: Optional[str] = None
    
    # Onboarding state
    onboarding_stage: OnboardingStage = OnboardingStage.NEW
    
    # API keys
    test_api_key: Optional[str] = None
    prod_api_key: Optional[str] = None
    
    # Activity tracking
    last_api_call: Optional[datetime] = None
    total_api_calls: int = 0
    last_login: Optional[datetime] = None
    
    # Integration status
    integration_status: str = "not_started"  # not_started, in_progress, live
    tech_stack: List[str] = field(default_factory=list)
    
    # Health metrics
    error_rate: float = 0.0
    usage_trend: str = "stable"  # increasing, stable, declining
    
    # Workflow metadata
    next_check: Optional[datetime] = None
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['subscription_tier'] = self.subscription_tier.value
        data['onboarding_stage'] = self.onboarding_stage.value
        # Convert datetimes to ISO format
        for key in ['created_at', 'last_api_call', 'last_login', 'next_check']:
            if data[key]:
                data[key] = data[key].isoformat()
        return data


class StateManager:
    """
    In-memory state manager for customer workflows.
    
    Production: Replace with Redis for persistence and multi-process support.
    """
    
    def __init__(self):
        """Initialize state manager."""
        self._customers: Dict[str, CustomerProfile] = {}
        self._lock = asyncio.Lock()
        self._initialize_demo_data()
        logger.info("StateManager initialized with demo data")
    
    def _initialize_demo_data(self):
        """Initialize with demo customer profiles."""
        now = datetime.now()
        
        # Demo customer 1: Brand new customer
        self._customers["demo_new_customer"] = CustomerProfile(
            customer_id="demo_new_customer",
            email="newuser@example.com",
            company="Example Corp",
            created_at=now,
            subscription_tier=SubscriptionTier.NONE,
            onboarding_stage=OnboardingStage.NEW
        )
        
        # Demo customer 2: Trial active, keys generated
        self._customers["demo_trial_customer"] = CustomerProfile(
            customer_id="demo_trial_customer",
            email="trial@startup.com",
            company="Startup Inc",
            created_at=now - timedelta(days=1),
            subscription_tier=SubscriptionTier.TRIAL,
            subscription_id="sub_trial_123",
            onboarding_stage=OnboardingStage.API_KEYS_GENERATED,
            test_api_key="sk_test_demo123",
            next_check=now + timedelta(hours=12)
        )
        
        # Demo customer 3: Active user
        self._customers["demo_active_customer"] = CustomerProfile(
            customer_id="demo_active_customer",
            email="dev@bigcorp.com",
            company="BigCorp Ltd",
            created_at=now - timedelta(days=30),
            subscription_tier=SubscriptionTier.PRO,
            subscription_id="sub_pro_456",
            onboarding_stage=OnboardingStage.PRODUCTION_READY,
            test_api_key="sk_test_demo456",
            prod_api_key="sk_live_demo456",
            last_api_call=now - timedelta(hours=2),
            total_api_calls=1543,
            last_login=now - timedelta(hours=1),
            integration_status="live",
            tech_stack=["Python", "Django", "PostgreSQL"],
            usage_trend="increasing"
        )
        
        # Demo customer 4: At-risk customer
        self._customers["demo_at_risk_customer"] = CustomerProfile(
            customer_id="demo_at_risk_customer",
            email="support@atrisk.com",
            company="AtRisk Co",
            created_at=now - timedelta(days=45),
            subscription_tier=SubscriptionTier.STARTER,
            subscription_id="sub_starter_789",
            onboarding_stage=OnboardingStage.PRODUCTION_READY,
            test_api_key="sk_test_demo789",
            prod_api_key="sk_live_demo789",
            last_api_call=now - timedelta(days=5),
            total_api_calls=234,
            last_login=now - timedelta(days=7),
            integration_status="live",
            error_rate=0.15,  # 15% error rate
            usage_trend="declining"
        )
    
    async def get_customer(self, customer_id: str) -> Optional[CustomerProfile]:
        """Get customer profile by ID."""
        async with self._lock:
            return self._customers.get(customer_id)
    
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> CustomerProfile:
        """Update customer profile."""
        async with self._lock:
            if customer_id not in self._customers:
                raise ValueError(f"Customer {customer_id} not found")
            
            customer = self._customers[customer_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(customer, key):
                    # Handle enum conversions
                    if key == 'onboarding_stage' and isinstance(value, str):
                        value = OnboardingStage(value)
                    elif key == 'subscription_tier' and isinstance(value, str):
                        value = SubscriptionTier(value)
                    setattr(customer, key, value)
            
            logger.info(f"Updated customer {customer_id}: {updates}")
            return customer
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> CustomerProfile:
        """Create new customer profile."""
        async with self._lock:
            customer_id = customer_data.get('customer_id')
            if customer_id in self._customers:
                raise ValueError(f"Customer {customer_id} already exists")
            
            customer = CustomerProfile(**customer_data)
            self._customers[customer_id] = customer
            
            logger.info(f"Created customer {customer_id}")
            return customer
    
    async def list_customers(self, filter_fn=None) -> List[CustomerProfile]:
        """List all customers, optionally filtered."""
        async with self._lock:
            customers = list(self._customers.values())
            if filter_fn:
                customers = [c for c in customers if filter_fn(c)]
            return customers
    
    async def get_customers_needing_check(self) -> List[CustomerProfile]:
        """Get customers that need proactive check-in."""
        now = datetime.now()
        
        def needs_check(customer: CustomerProfile) -> bool:
            # Check if next_check time has passed
            if customer.next_check and customer.next_check <= now:
                return True
            
            # Check if onboarded but no API activity for 24h
            if (customer.onboarding_stage == OnboardingStage.API_KEYS_GENERATED 
                and customer.last_api_call is None
                and (now - customer.created_at) > timedelta(hours=24)):
                return True
            
            # Check if high error rate
            if customer.error_rate > 0.1:
                return True
            
            # Check if usage declining
            if customer.usage_trend == "declining":
                return True
            
            return False
        
        return await self.list_customers(filter_fn=needs_check)


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
