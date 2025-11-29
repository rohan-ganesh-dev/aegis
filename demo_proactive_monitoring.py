"""
Quick script to demonstrate proactive monitoring.

Run this to see the monitor detect customers needing attention.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aegis.state.state_manager import get_state_manager
from aegis.monitors.proactive_monitor import get_monitor
from aegis.tools.customer_context import list_customers_needing_attention


async def demo_proactive_monitoring():
    """Demonstrate proactive monitoring detection."""
    
    print("=" * 60)
    print("🔍 PROACTIVE MONITORING DEMO")
    print("=" * 60)
    
    # Get state manager
    state_manager = get_state_manager()
    print(f"\n✅ Loaded {len(state_manager._customers)} demo customers")
    
    # List all customers
    print("\n📋 Customer Profiles:")
    for customer_id, customer in state_manager._customers.items():
        print(f"  - {customer.company}: {customer.subscription_tier.value}, "
              f"Stage: {customer.onboarding_stage.value}, "
              f"API Calls: {customer.total_api_calls}")
    
    # Check for customers needing attention
    print("\n🎯 Analyzing Customer Health...")
    result = await list_customers_needing_attention()
    
    print(f"\n🚨 Found {result['count']} customers needing intervention:\n")
    
    for customer_data in result['customers']:
        print(f"{'='*60}")
        print(f"Customer: {customer_data['company']}")
        print(f"Health: {customer_data['health_status'].upper()}")
        print(f"Stage: {customer_data['onboarding_stage']}")
        print(f"Risk Factors: {', '.join(customer_data['risk_factors'])}")
        print(f"Recommended Action: {customer_data['recommended_action']}")
        print()
    
    # NOW run the monitor ONCE to generate interventions
    print("\n🤖 Running Proactive Monitor (single check)...")
    monitor = get_monitor()
    
    # Manually trigger one check cycle
    await monitor._check_all_customers()
    
    # Show interventions
    interventions = monitor.get_recent_interventions(limit=10)
    
    if interventions:
        print(f"\n📬 Generated {len(interventions)} Proactive Interventions:\n")
        for i, intervention in enumerate(interventions, 1):
            print(f"{i}. Type: {intervention['type'].replace('_', ' ').title()}")
            print(f"   Customer: {intervention['customer_name']}")
            print(f"   Reason: {intervention['reason']}")
            print(f"   Priority: {intervention['priority'].upper()}")
            print(f"   Message: {intervention['message'][:100]}...")
            print()
    else:
        print("\n⚠️  No interventions generated (customers might have been intervened recently)")
    
    print("=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_proactive_monitoring())
