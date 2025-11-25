"""
HIL (Human-in-Loop) API.

FastAPI endpoints for HIL approval workflows.
Provides REST API for submitting and querying approval requests.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Aegis HIL API",
    description="Human-in-Loop approval API for Aegis agents",
    version="0.1.0",
)

# Mock in-memory storage
# TODO: Replace with persistent database (PostgreSQL, Redis)
approval_requests_db: Dict[str, Dict[str, Any]] = {}


class ApprovalRequest(BaseModel):
    """Schema for approval request."""

    agent_id: str
    customer_id: str
    action_type: str
    details: Dict[str, Any]


class ApprovalResponse(BaseModel):
    """Schema for approval response."""

    request_id: str
    decision: str  # "approved" or "rejected"
    notes: str = ""


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Aegis HIL API",
        "status": "operational",
        "version": "0.1.0",
    }


@app.post("/api/hil/approvals")
async def create_approval_request(request: ApprovalRequest) -> Dict[str, Any]:
    """
    Create a new approval request.

    BOILERPLATE: Stores in-memory. Production should persist to database.

    Args:
        request: Approval request details

    Returns:
        Created approval request with ID
    """
    request_id = f"req_{uuid4().hex[:8]}"

    approval_data = {
        "id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": request.agent_id,
        "customer_id": request.customer_id,
        "action_type": request.action_type,
        "details": request.details,
        "status": "pending",
    }

    approval_requests_db[request_id] = approval_data

    logger.info(f"Created approval request: {request_id}")

    return approval_data


@app.get("/api/hil/approvals/{request_id}")
async def get_approval_request(request_id: str) -> Dict[str, Any]:
    """
    Get approval request by ID.

    Args:
        request_id: Request identifier

    Returns:
        Approval request details

    Raises:
        HTTPException: If request not found
    """
    if request_id not in approval_requests_db:
        raise HTTPException(status_code=404, detail="Approval request not found")

    return approval_requests_db[request_id]


@app.get("/api/hil/approvals")
async def list_approval_requests(
    status: str = None, limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List approval requests with optional status filter.

    Args:
        status: Filter by status (pending, approved, rejected)
        limit: Maximum number of results

    Returns:
        List of approval requests
    """
    requests = list(approval_requests_db.values())

    if status:
        requests = [r for r in requests if r["status"] == status]

    # Sort by timestamp (most recent first)
    requests.sort(key=lambda x: x["timestamp"], reverse=True)

    return requests[:limit]


@app.post("/api/hil/approvals/{request_id}/approve")
async def approve_request(request_id: str, notes: str = "") -> Dict[str, Any]:
    """
    Approve an action request.

    BOILERPLATE: Updates in-memory. Production should trigger agent callback.

    Args:
        request_id: Request identifier
        notes: Optional approval notes

    Returns:
        Updated approval request

    Raises:
        HTTPException: If request not found
    """
    if request_id not in approval_requests_db:
        raise HTTPException(status_code=404, detail="Approval request not found")

    approval_requests_db[request_id]["status"] = "approved"
    approval_requests_db[request_id]["approved_at"] = datetime.utcnow().isoformat()
    approval_requests_db[request_id]["notes"] = notes

    logger.info(f"Approved request: {request_id}")

    # TODO: Trigger callback to agent system to execute approved action

    return approval_requests_db[request_id]


@app.post("/api/hil/approvals/{request_id}/reject")
async def reject_request(request_id: str, notes: str = "") -> Dict[str, Any]:
    """
    Reject an action request.

    BOILERPLATE: Updates in-memory. Production should trigger agent callback.

    Args:
        request_id: Request identifier
        notes: Optional rejection notes

    Returns:
        Updated approval request

    Raises:
        HTTPException: If request not found
    """
    if request_id not in approval_requests_db:
        raise HTTPException(status_code=404, detail="Approval request not found")

    approval_requests_db[request_id]["status"] = "rejected"
    approval_requests_db[request_id]["rejected_at"] = datetime.utcnow().isoformat()
    approval_requests_db[request_id]["notes"] = notes

    logger.info(f"Rejected request: {request_id}")

    # TODO: Trigger callback to agent system to notify of rejection

    return approval_requests_db[request_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
