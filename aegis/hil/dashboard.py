"""
HIL (Human-in-Loop) Dashboard.

Streamlit app for reviewing and approving agent actions.
Allows humans to approve/reject high-value or sensitive operations.
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock storage for approval requests (in-memory)
# TODO: Replace with persistent storage (Redis, PostgreSQL)
if "approval_requests" not in st.session_state:
    st.session_state.approval_requests = [
        {
            "id": "req_001",
            "timestamp": "2024-01-15T10:30:00Z",
            "agent": "growth_agent",
            "customer_id": "customer_abc123",
            "action_type": "apply_discount",
            "details": {
                "discount_percent": 25,
                "duration_months": 3,
                "estimated_cost": 375.00,
                "reason": "High churn risk (0.78)",
            },
            "status": "pending",
        },
        {
            "id": "req_002",
            "timestamp": "2024-01-15T11:00:00Z",
            "agent": "growth_agent",
            "customer_id": "customer_xyz789",
            "action_type": "apply_credits",
            "details": {
                "credit_amount": 500.00,
                "reason": "Retention incentive for at-risk customer",
            },
            "status": "pending",
        },
    ]


def approve_request(request_id: str) -> None:
    """Approve an action request."""
    for req in st.session_state.approval_requests:
        if req["id"] == request_id:
            req["status"] = "approved"
            req["approved_at"] = datetime.utcnow().isoformat()
            logger.info(f"Approved request: {request_id}")
            st.success(f"✅ Approved request {request_id}")
            # TODO: Send callback to agent system
            break


def reject_request(request_id: str) -> None:
    """Reject an action request."""
    for req in st.session_state.approval_requests:
        if req["id"] == request_id:
            req["status"] = "rejected"
            req["rejected_at"] = datetime.utcnow().isoformat()
            logger.info(f"Rejected request: {request_id}")
            st.error(f"❌ Rejected request {request_id}")
            # TODO: Send callback to agent system
            break


# Page configuration
st.set_page_config(
    page_title="Aegis HIL Dashboard",
    page_icon="🛡️",
    layout="wide",
)

# Header
st.title("🛡️ Aegis Human-in-Loop Dashboard")
st.markdown("Review and approve high-value agent actions")

# Tabs
tab1, tab2 = st.tabs(["Pending Approvals", "History"])

with tab1:
    st.header("Pending Approval Requests")

    pending_requests = [
        req
        for req in st.session_state.approval_requests
        if req["status"] == "pending"
    ]

    if not pending_requests:
        st.info("No pending approval requests")
    else:
        for req in pending_requests:
            with st.container():
                st.divider()

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.subheader(f"Request ID: {req['id']}")
                    st.write(f"**Agent:** {req['agent']}")
                    st.write(f"**Customer:** {req['customer_id']}")
                    st.write(f"**Action:** {req['action_type']}")
                    st.write(f"**Timestamp:** {req['timestamp']}")

                    st.write("**Details:**")
                    for key, value in req["details"].items():
                        st.write(f"- {key}: {value}")

                with col2:
                    st.write("**Actions**")

                    if st.button("✅ Approve", key=f"approve_{req['id']}"):
                        approve_request(req["id"])
                        st.rerun()

                    if st.button("❌ Reject", key=f"reject_{req['id']}"):
                        reject_request(req["id"])
                        st.rerun()

with tab2:
    st.header("Approval History")

    completed_requests = [
        req
        for req in st.session_state.approval_requests
        if req["status"] != "pending"
    ]

    if not completed_requests:
        st.info("No approval history")
    else:
        for req in completed_requests:
            status_emoji = "✅" if req["status"] == "approved" else "❌"
            with st.expander(f"{status_emoji} {req['id']} - {req['status'].upper()}"):
                st.write(f"**Agent:** {req['agent']}")
                st.write(f"**Customer:** {req['customer_id']}")
                st.write(f"**Action:** {req['action_type']}")
                st.write(f"**Status:** {req['status']}")
                st.json(req["details"])

# Footer
st.divider()
st.caption(
    "⚠️ BOILERPLATE: This is a mock dashboard. "
    "Production should integrate with persistent storage and agent callback system."
)
