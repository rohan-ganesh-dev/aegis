"""
HIL (Human-in-Loop) Dashboard.

Streamlit app for reviewing and approving agent actions.
Allows humans to approve/reject high-value or sensitive operations.
"""

import asyncio
import logging
import os
import re
import sys
from datetime import datetime
from typing import Optional

import streamlit as st

# Ensure project root is on sys.path when running via `streamlit run`
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from aegis.agents.base import AgentMessage, AgentResponse
from aegis.agents.orchestrator_agent import OrchestratorAgent
from aegis.config import config
from aegis.services.session_service import get_or_create_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ISSUE_KEY_PATTERN = re.compile(r"\b[A-Z]+-\d+\b")


def _extract_issue_key(issue_key: Optional[str], query: str) -> str:
    """
    Return an explicit issue key if provided, otherwise try to extract
    one from the free-form query text. Raises ValueError if none found.
    """
    if issue_key:
        return issue_key

    match = ISSUE_KEY_PATTERN.search(query.upper())
    if match:
        return match.group(0)



async def _run_jira_agent_async(
    issue_key: Optional[str], query: str, dry_run: bool, user_id: str, session_id: str
) -> AgentResponse:
    """
    Run the orchestrator agent asynchronously with session support.
    Orchestrator will route to appropriate specialized agent.

    Args:
        issue_key: Optional Jira ticket key
        query: User query
        dry_run: Whether to run in dry-run mode
        user_id: User identifier for session
        session_id: Session identifier for conversation threading

    Returns Response object from agent.
    """
    # Create or retrieve ADK session
    session = await get_or_create_session(
        app_name="aegis",
        user_id=user_id,
        session_id=session_id
    )
    logger.info(f"Using session for user: {user_id}, session: {session_id}")
    
    # Initialize the orchestrator (which is now an ADK LlmAgent)
    agent = OrchestratorAgent(agent_id="orchestrator_dashboard")
    
    # Start the agent (initializes resources)
    await agent.start()

    payload = {
        "query": query,
        "issue_key": issue_key,
        "dry_run": dry_run,
    }
    
    # Create message for backward compatibility
    message = AgentMessage(
        sender="hil_dashboard",
        recipient="orchestrator_dashboard",
        type="task",
        payload=payload,
    )

    try:
        # Use handle_message which wraps the ADK generate/route logic
        # TODO: Pass session to agent's generate() method
        response = await agent.handle_message(message)
    finally:
        await agent.stop()

    return response


def run_jira_agent(issue_key: Optional[str], query: str, dry_run: bool, user_id: str, session_id: str):
    """
    Synchronous wrapper used by the Streamlit dashboard.
    
    Args:
        issue_key: Optional Jira ticket key  
        query: User query
        dry_run: Whether to run in dry-run mode
        user_id: User identifier for session
        session_id: Session identifier for conversation threading
    """
    final_issue_key = _extract_issue_key(issue_key, query)
    print("final_issue_key is ",final_issue_key)
    return asyncio.run(_run_jira_agent_async(final_issue_key, query, dry_run, user_id, session_id))


async def _run_feedback_async(
    query: str,
    docs_answer: str,
    feedback_type: str,
    additional_feedback: Optional[str] = None,
    issue_key: Optional[str] = None,
) -> AgentResponse:
    """
    Process user feedback through the orchestrator.
    Creates a feedback query that gets routed to appropriate specialist.
    """
    # Create orchestrator
    agent = OrchestratorAgent(agent_id="orchestrator_dashboard")
    await agent.start()
    
    try:
        # Prepare feedback data
        feedback_data = {
            "query": query,
            "docs_answer": docs_answer,
            "feedback_type": feedback_type,
            "additional_feedback": additional_feedback,
            "issue_key": issue_key
        }
        
        # Delegate directly to the feedback agent via orchestrator
        # This ensures deterministic handling instead of relying on intent classification
        response = await agent.handle_feedback(feedback_data)
        
        return response
    finally:
        await agent.stop()



def run_feedback(
    query: str,
    docs_answer: str,
    feedback_type: str,
    additional_feedback: Optional[str] = None,
    issue_key: Optional[str] = None,
):
    """
    Synchronous wrapper for feedback submission from Streamlit.
    """
    return asyncio.run(_run_feedback_async(query, docs_answer, feedback_type, additional_feedback, issue_key))

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

# Initialize user and session IDs for ADK session management
if 'user_id' not in st.session_state:
    from uuid import uuid4
    st.session_state.user_id = str(uuid4())
    logger.info(f"Created new user_id: {st.session_state.user_id}")

if 'session_id' not in st.session_state:
    from uuid import uuid4
    st.session_state.session_id = str(uuid4())
    logger.info(f"Created new session_id: {st.session_state.session_id}")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Approvals Dashboard", "Jira Chargebee Agent"], index=1)

if page == "Approvals Dashboard":
    st.title("🛡️ Aegis Human-in-Loop Dashboard")
    st.markdown("Review and approve high-value agent actions")

    # Tabs for Approvals
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
    
    # Footer for Dashboard
    st.divider()
    st.caption(
        "⚠️ BOILERPLATE: This is a mock dashboard. "
        "Production should integrate with persistent storage and agent callback system."
    )

elif page == "Jira Chargebee Agent":
    st.header("🤖 Jira Chargebee Agent")
    st.markdown("Chat with the agent about Chargebee or Jira tickets.")
    
    # Sidebar options for Agent
    st.sidebar.divider()
    st.sidebar.header("Agent Settings")
    dry_run = st.sidebar.checkbox("Dry Run Mode", value=True, key="chat_dry_run", help="If checked, won't post to Jira")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I can help you with Chargebee documentation or Jira tickets. Ask me a question or mention a ticket key (e.g., KAN-7)."
        })
    
    # Initialize feedback tracking
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = {}

    # Display chat messages from history on app rerun
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            # Display agent name badge for assistant messages
            if message["role"] == "assistant" and "agent_name" in message:
                agent_name = message["agent_name"]
                badge_color = "#4CAF50" if "onboarding" in agent_name.lower() else "#2196F3"
                st.markdown(
                    f'<span style="background-color: {badge_color}; color: white; padding: 2px 8px; '
                    f'border-radius: 12px; font-size: 12px; font-weight: bold;">'
                    f'🤖 {agent_name}</span>',
                    unsafe_allow_html=True
                )
            
            st.markdown(message["content"])
            
            # Add feedback buttons for assistant messages (except the welcome message)
            if message["role"] == "assistant" and idx > 0:
                feedback_key = f"feedback_{idx}"
                
                # Check if feedback already given for this message
                if feedback_key not in st.session_state.feedback_given:
                    col1, col2, col3 = st.columns([1, 1, 10])
                    
                    with col1:
                        if st.button("👍", key=f"thumbs_up_{idx}"):
                            st.session_state.feedback_given[feedback_key] = "positive"
                            # Process positive feedback
                            with st.spinner("Processing feedback..."):
                                try:
                                    # Get the corresponding query (previous user message)
                                    user_query = st.session_state.messages[idx-1]["content"]
                                    docs_answer = message.get("docs_answer", message["content"])
                                    issue_key = message.get("issue_key")  # Get issue_key if query was about a ticket
                                    
                                    feedback_response = run_feedback(
                                        query=user_query,
                                        docs_answer=docs_answer,
                                        feedback_type="positive",
                                        issue_key=issue_key
                                    )
                                    st.success(feedback_response.text)
                                except Exception as e:
                                    st.error(f"Error processing feedback: {str(e)}")
                            st.rerun()
                    
                    with col2:
                        if st.button("👎", key=f"thumbs_down_{idx}"):
                            st.session_state.feedback_given[feedback_key] = "negative_pending"
                            st.rerun()
                
                # If negative feedback pending, show text input for additional context
                if st.session_state.feedback_given.get(feedback_key) == "negative_pending":
                    with st.form(key=f"feedback_form_{idx}"):
                        additional_feedback = st.text_area(
                            "Please tell us what was wrong or how we can improve:",
                            key=f"feedback_text_{idx}",
                            placeholder="Optional: Provide additional context..."
                        )
                        
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            submit = st.form_submit_button("Submit Feedback")
                        with col2:
                            cancel = st.form_submit_button("Cancel")
                        
                        if submit:
                            st.session_state.feedback_given[feedback_key] = "negative"
                            # Process negative feedback
                            with st.spinner("Creating Jira ticket..."):
                                try:
                                    # Get the corresponding query (previous user message)
                                    user_query = st.session_state.messages[idx-1]["content"]
                                    docs_answer = message.get("docs_answer", message["content"])
                                    issue_key = message.get("issue_key")  # Get issue_key if query was about a ticket
                                    
                                    feedback_response = run_feedback(
                                        query=user_query,
                                        docs_answer=docs_answer,
                                        feedback_type="negative",
                                        additional_feedback=additional_feedback if additional_feedback else None,
                                        issue_key=issue_key
                                    )
                                    
                                    # Store the ticket info in the message
                                    if feedback_response.metadata and "ticket_key" in feedback_response.metadata:
                                        ticket_key = feedback_response.metadata["ticket_key"]
                                        
                                        # Update the message in session state
                                        st.session_state.messages[idx]["feedback_ticket"] = ticket_key
                                        
                                        # Show prominent success message with clickable link
                                        jira_base_url = config.jira_base_url
                                        st.success(f"✅ {feedback_response.text}")
                                        st.info(f"🎫 **Track your feedback:** [{ticket_key}]({jira_base_url}/{ticket_key})")
                                    else:
                                        st.success(feedback_response.text)
                                except Exception as e:
                                    st.error(f"Error creating ticket: {str(e)}")
                                    logger.error(f"Feedback error: {e}", exc_info=True)
                            st.rerun()
                        
                        if cancel:
                            del st.session_state.feedback_given[feedback_key]
                            st.rerun()
                
                # Show feedback status if already given
                elif feedback_key in st.session_state.feedback_given:
                    feedback_status = st.session_state.feedback_given[feedback_key]
                    if feedback_status == "positive":
                        st.caption("✅ Positive feedback received")
                    elif feedback_status == "negative":
                        ticket_key = message.get("feedback_ticket", "Unknown")
                        if ticket_key != "Unknown":
                            # Create clickable Jira link (adjust URL to match your Jira instance)
                            jira_base_url = config.jira_base_url
                            st.info(f"📝 **Feedback Ticket Created:** [{ticket_key}]({jira_base_url}/{ticket_key})")
                        else:
                            st.caption(f"📝 Feedback ticket created: {ticket_key}")

    # React to user input
    if prompt := st.chat_input("Ask a question or mention a Jira ticket..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Run agent logic
        with st.spinner("Agent is thinking..."):
            try:
                response = run_jira_agent(
                    issue_key=None, # Agent extracts this from query now
                    query=prompt, 
                    dry_run=dry_run,
                    user_id=st.session_state.user_id,
                    session_id=st.session_state.session_id
                )
                
                agent_response_text = response.text
                
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    # Display routing information if available
                    if response.metadata and "orchestrator" in response.metadata:
                        orch_info = response.metadata["orchestrator"]
                        routed_to = orch_info.get("routed_to", "Unknown")
                        
                        # Display agent badge
                        badge_color = "#4CAF50" if "Onboarding" in routed_to else "#2196F3"
                        st.markdown(
                            f'<span style="background-color: {badge_color}; color: white; padding: 2px 8px; '
                            f'border-radius: 12px; font-size: 12px; font-weight: bold;">'
                            f'🤖 {routed_to}</span>',
                            unsafe_allow_html=True
                        )
                    
                    st.markdown(agent_response_text)
                    
                    # Show attachments if any
                    if response.attachments:
                        for att in response.attachments:
                            if "docs_answer" in att:
                                with st.expander("View Documentation Source"):
                                    st.markdown(att["docs_answer"])
                
                # Get docs answer from attachments
                docs_answer_text = agent_response_text
                if response.attachments:
                    for att in response.attachments:
                        if "docs_answer" in att:
                            docs_answer_text = att["docs_answer"]
                            break
                
                # Get issue_key if present (means query was about a specific ticket)
                issue_key = response.metadata.get("issue_key") if response.metadata else None
                
                # Get agent name from metadata
                agent_name = "Unknown Agent"
                if response.metadata and "orchestrator" in response.metadata:
                    agent_name = response.metadata["orchestrator"].get("routed_to", "Unknown Agent")
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": agent_response_text,
                    "docs_answer": docs_answer_text,  # Store for feedback
                    "issue_key": issue_key,  # Store to determine feedback action
                    "agent_name": agent_name  # Store agent name for display
                })
                
                # Force rerun to display feedback buttons immediately
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                logger.error(f"Agent error: {e}", exc_info=True)

