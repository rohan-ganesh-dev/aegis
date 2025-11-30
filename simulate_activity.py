#!/usr/bin/env python3
"""
Real-time Customer Activity Simulator

Simulates customer behavior by updating their profiles every 30 seconds:
- API calls
- Error rates
- Usage trends
- New customer signups

Run this alongside the dashboard to see proactive interventions trigger in real-time!

Usage:
    python simulate_activity.py
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from aegis.state.state_manager import (
    get_state_manager,
    OnboardingStage,
    SubscriptionTier,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def simulate_api_calls(state_manager):
    """Simulate API calls for active customers."""
    customers = await state_manager.list_customers()
    
    for customer in customers:
        # Skip new customers without keys
        if customer.onboarding_stage == OnboardingStage.NEW:
            continue
        
        # Simulate API calls (random between 0-50 per cycle)
        if random.random() > 0.3:  # 70% chance of activity
            new_calls = random.randint(0, 50)
            
            await state_manager.update_customer(
                customer.customer_id,
                {
                    'total_api_calls': customer.total_api_calls + new_calls,
                    'last_api_call': datetime.now()
                }
            )
            
            logger.info(f"📞 {customer.company}: +{new_calls} API calls (total: {customer.total_api_calls + new_calls})")


async def simulate_errors(state_manager):
    """Aggressively change errors to trigger different interventions."""
    customers = await state_manager.list_customers()
    
    for customer in customers:
        if customer.total_api_calls < 10:
            continue
        
        # 60% chance to dramatically change error rate (was 20%)
        if random.random() < 0.6:
            # Randomly choose: no errors, moderate errors, or high errors
            scenarios = [
                (0.0, "No errors"),
                (0.02, "Low errors"),
                (0.15, "High error spike!"),
                (0.25, "Critical error rate!"),
            ]
            
            new_error_rate, description = random.choice(scenarios)
            
            if abs(customer.error_rate - new_error_rate) > 0.03:  # Only log significant changes
                logger.info(f"🚨 {customer.company}: {description} ({customer.error_rate:.1%} → {new_error_rate:.1%})")
            
            await state_manager.update_customer(
                customer.customer_id,
                {'error_rate': new_error_rate}
            )


async def simulate_usage_trends(state_manager):
    """Aggressively change usage trends to trigger different interventions."""
    customers = await state_manager.list_customers()
    
    for customer in customers:
        if customer.total_api_calls < 10:
            continue
        
        # 50% chance to change trend (was 30%)
        if random.random() < 0.5:
            trends = ['increasing', 'stable', 'declining']
            old_trend = customer.usage_trend
            new_trend = random.choice(trends)
            
            if old_trend != new_trend:
                await state_manager.update_customer(
                    customer.customer_id,
                    {'usage_trend': new_trend}
                )
                
                emoji = "📈" if new_trend == "increasing" else "📉" if new_trend == "declining" else "➡️"
                logger.info(f"{emoji} {customer.company}: Usage trend {old_trend} → {new_trend}")



async def simulate_onboarding_progress(state_manager):
    """Simulate customers progressing through onboarding."""
    customers = await state_manager.list_customers()
    now = datetime.now()
    
    for customer in customers:
        # If customer has been stuck in API_KEYS_GENERATED for a while, maybe progress them
        if customer.onboarding_stage == OnboardingStage.API_KEYS_GENERATED:
            hours_since_keys = (now - customer.created_at).total_seconds() / 3600
            
            # 10% chance to progress if they've had keys for >2 hours
            if hours_since_keys > 2 and random.random() < 0.1:
                await state_manager.update_customer(
                    customer.customer_id,
                    {
                        'onboarding_stage': OnboardingStage.FIRST_API_CALL.value,
                        'total_api_calls': 1,
                        'last_api_call': now
                    }
                )
                logger.info(f"🎉 {customer.company}: Made first API call!")


async def create_new_customer(state_manager):
    """Randomly create a new customer (10% chance per cycle)."""
    if random.random() < 0.1:
        customer_id = f"sim_customer_{datetime.now().timestamp()}"
        company_name = f"SimCo {random.randint(100, 999)}"
        
        try:
            await state_manager.create_customer({
                'customer_id': customer_id,
                'email': f'contact@{company_name.lower().replace(" ", "")}.com',
                'company': company_name,
                'created_at': datetime.now(),
                'subscription_tier': SubscriptionTier.NONE,
                'onboarding_stage': OnboardingStage.NEW
            })
            logger.info(f"🆕 New customer signed up: {company_name}")
        except Exception as e:
            logger.error(f"Error creating customer: {e}")




async def cycle_customer_scenarios(state_manager):
    """Cycle customers through different scenarios to demonstrate all intervention types."""
    customers = await state_manager.list_customers()
    now = datetime.now()
    
    # Every cycle, pick 1-2 customers to put into a specific "crisis" state
    if random.random() < 0.7:  # 70% chance
        target_customers = random.sample(
            [c for c in customers if c.customer_id.startswith('demo_')],
            min(2, len([c for c in customers if c.customer_id.startswith('demo_')]))
        )
        
        scenarios = [
            {
                'name': 'High Errors',
                'updates': {'error_rate': random.uniform(0.15, 0.30), 'total_api_calls': max(20, random.randint(10, 100))},
                'emoji': '🔥'
            },
            {
                'name': 'Onboarding Stuck',
                'updates': {
                    'onboarding_stage': OnboardingStage.API_KEYS_GENERATED.value,
                    'total_api_calls': 0,
                    'created_at': now - timedelta(days=2)
                },
                'emoji': '⏰'
            },
            {
                'name': 'Declining Usage',
                'updates': {
                    'usage_trend': 'declining',
                    'subscription_tier': SubscriptionTier.PRO.value,
                    'total_api_calls': max(50, random.randint(50, 200))
                },
                'emoji': '📉'
            },
            {
                'name': 'Growing Fast',
                'updates': {
                    'usage_trend': 'increasing',
                    'total_api_calls': random.randint(1000, 2000),
                    'subscription_tier': SubscriptionTier.TRIAL.value
                },
                'emoji': '🚀'
            }
        ]
        
        for customer in target_customers:
            scenario = random.choice(scenarios)
            await state_manager.update_customer(customer.customer_id, scenario['updates'])
            logger.info(f"{scenario['emoji']} {customer.company}: Scenario → {scenario['name']}")


async def simulation_cycle(state_manager):
    """Run one simulation cycle."""
    logger.info("=" * 60)
    logger.info("🔄 Running simulation cycle...")
    
    # Run all simulations
    await simulate_api_calls(state_manager)
    await simulate_errors(state_manager)
    await simulate_usage_trends(state_manager)
    await cycle_customer_scenarios(state_manager)  # NEW: Dramatic changes
    await simulate_onboarding_progress(state_manager)
    await create_new_customer(state_manager)
    
    logger.info("✅ Cycle complete - Click 'Run Monitor Check' to see new interventions!")
    logger.info("=" * 60)



async def main():
    """Main simulation loop."""
    logger.info("🚀 Starting Customer Activity Simulator")
    logger.info("📊 Updating customer data every 15 seconds")
    logger.info("💡 Keep the dashboard open to see proactive interventions trigger!")
    logger.info("")
    
    state_manager = get_state_manager()
    
    # Run simulation cycles every 15 seconds
    while True:
        try:
            await simulation_cycle(state_manager)
            await asyncio.sleep(15)  # Changed from 30 to 15 seconds
        except KeyboardInterrupt:
            logger.info("\n⏹️  Simulator stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in simulation: {e}", exc_info=True)
            await asyncio.sleep(15)  # Changed from 30 to 15 seconds



if __name__ == "__main__":
    asyncio.run(main())
