# Real-Time Activity Simulator Guide

## Purpose

The `simulate_activity.py` script creates a **live, dynamic demo** of the proactive monitoring system by simulating real customer behavior in real-time.

## What It Does

Every 30 seconds, the simulator:

1. **Simulates API Calls** 📞
   - Active customers make random API calls
   - Updates `total_api_calls` and `last_api_call` timestamps

2. **Introduces/Fixes Errors** 🚨
   - Randomly increases error rates (simulating bugs)
   - Randomly decreases error rates (simulating fixes)
   - Triggers "Error Debugging" interventions when >10%

3. **Changes Usage Trends** 📈
   - Switches between `increasing`, `stable`, `declining`
   - Triggers retention or upsell interventions

4. **Progresses Onboarding** 🎉
   - Customers stuck in onboarding eventually make their first API call
   - Clears "Onboarding Check In" interventions

5. **Creates New Customers** 🆕
   - 10% chance per cycle to add a new customer
   - Starts in NEW stage with no subscription

## How to Use

### Step 1: Start the Dashboard
```bash
streamlit run aegis/hil/dashboard.py
```

### Step 2: Start the Simulator (in a new terminal)
```bash
python simulate_activity.py
```

### Step 3: Watch the Magic! ✨

1. **Open the dashboard** (http://localhost:8501)
2. **Click "🔄 Run Monitor Check"** in the sidebar
3. **Wait 30 seconds** and click again
4. **See new interventions appear** as customer behavior changes!

## Example Output

```
2025-11-30 13:45:00 - INFO - 🚀 Starting Customer Activity Simulator
2025-11-30 13:45:00 - INFO - 📊 Updating customer data every 30 seconds
============================================================
2025-11-30 13:45:00 - INFO - 🔄 Running simulation cycle...
2025-11-30 13:45:01 - INFO - 📞 Startup Inc: +23 API calls (total: 23)
2025-11-30 13:45:01 - INFO - 🚨 AtRisk Co: Error rate spike! 5.0% → 18.2%
2025-11-30 13:45:01 - INFO - 📈 BigCorp Ltd: Usage trend stable → increasing
2025-11-30 13:45:01 - INFO - ✅ Cycle complete
============================================================
```

## What You'll See in the Dashboard

- **Proactive Interventions section** will show:
  - New "Error Debugging" when error rates spike
  - "Onboarding Check In" clears when customers progress
  - "Upsell Suggestion" when usage increases
  - "Retention Outreach" when usage declines

## Stopping the Simulator

Press `Ctrl+C` in the terminal running the simulator.

## Production Use

In production, replace this simulator with:
- Real customer data from your database
- Real API usage logs from your gateway
- Real error tracking from your monitoring system
- Real billing events from Stripe/Chargebee

The proactive monitor would then detect **actual** customer issues, not simulated ones! 🎯
