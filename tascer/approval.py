"""Approval System for Human Sign-Off.

Provides approval gates for AI agents to request human authorization
before proceeding with dangerous or critical actions.

Key features:
- Multi-approver support (N of M required)
- No timeout (pending until handled)
- Simple API for external integrations
"""

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

# Default dangerous actions that always require approval
DANGEROUS_ACTIONS = {
    "delete_file",
    "delete_directory", 
    "deploy",
    "publish",
    "push_to_main",
    "modify_secrets",
    "modify_permissions",
    "run_sudo",
    "database_migration",
    "production_access",
}


@dataclass
class Approval:
    """A single approval from one approver."""
    approver: str
    approved: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    comment: Optional[str] = None


@dataclass
class ApprovalRequest:
    """Request for human sign-off on an action or plan.
    
    Supports multi-approver workflows where N of M approvers must approve.
    """
    id: str
    tasc_id: str
    plan_id: Optional[str]
    title: str
    description: str
    action_type: str  # e.g., "deploy", "delete_file", "manual_gate"
    requested_by: str  # "agent", "system", or agent name
    requested_at: str
    status: Literal["pending", "approved", "rejected", "partial"]
    
    # Multi-approver settings
    required_approvals: int = 1  # How many approvals needed
    approvals: List[Approval] = field(default_factory=list)
    
    # Context for the approver
    context: Dict[str, Any] = field(default_factory=dict)  # command, files, diff, etc.
    
    # Rejection info
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "tasc_id": self.tasc_id,
            "plan_id": self.plan_id,
            "title": self.title,
            "description": self.description,
            "action_type": self.action_type,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at,
            "status": self.status,
            "required_approvals": self.required_approvals,
            "approvals": [
                {
                    "approver": a.approver,
                    "approved": a.approved,
                    "timestamp": a.timestamp,
                    "comment": a.comment,
                }
                for a in self.approvals
            ],
            "context": self.context,
            "rejection_reason": self.rejection_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ApprovalRequest":
        approvals = [
            Approval(
                approver=a["approver"],
                approved=a["approved"],
                timestamp=a.get("timestamp", ""),
                comment=a.get("comment"),
            )
            for a in data.get("approvals", [])
        ]
        return cls(
            id=data["id"],
            tasc_id=data["tasc_id"],
            plan_id=data.get("plan_id"),
            title=data["title"],
            description=data["description"],
            action_type=data.get("action_type", "unknown"),
            requested_by=data["requested_by"],
            requested_at=data["requested_at"],
            status=data["status"],
            required_approvals=data.get("required_approvals", 1),
            approvals=approvals,
            context=data.get("context", {}),
            rejection_reason=data.get("rejection_reason"),
        )
    
    @property
    def approval_count(self) -> int:
        """Count of approvals (not rejections)."""
        return sum(1 for a in self.approvals if a.approved)
    
    @property
    def rejection_count(self) -> int:
        """Count of rejections."""
        return sum(1 for a in self.approvals if not a.approved)
    
    @property
    def is_approved(self) -> bool:
        """Check if enough approvals have been received."""
        return self.approval_count >= self.required_approvals
    
    @property
    def is_rejected(self) -> bool:
        """Check if any rejection has been received."""
        return self.rejection_count > 0


class ApprovalStore:
    """Storage for approval requests.
    
    Uses a simple JSON file for persistence.
    Can be extended to use SQLite, AB Memory, etc.
    """
    
    def __init__(self, path: str = ".tascer/approvals.json"):
        self.path = path
        self._ensure_dir()
    
    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._save({})
    
    def _load(self) -> Dict[str, Dict]:
        if os.path.exists(self.path):
            with open(self.path) as f:
                return json.load(f)
        return {}
    
    def _save(self, data: Dict):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save(self, request: ApprovalRequest):
        data = self._load()
        data[request.id] = request.to_dict()
        self._save(data)
    
    def get(self, request_id: str) -> Optional[ApprovalRequest]:
        data = self._load()
        if request_id in data:
            return ApprovalRequest.from_dict(data[request_id])
        return None
    
    def list_pending(self, plan_id: Optional[str] = None) -> List[ApprovalRequest]:
        data = self._load()
        results = []
        for item in data.values():
            if item["status"] == "pending":
                if plan_id is None or item.get("plan_id") == plan_id:
                    results.append(ApprovalRequest.from_dict(item))
        return results
    
    def list_all(self, limit: int = 50) -> List[ApprovalRequest]:
        data = self._load()
        items = sorted(data.values(), key=lambda x: x["requested_at"], reverse=True)
        return [ApprovalRequest.from_dict(item) for item in items[:limit]]


# Global store instance
_store: Optional[ApprovalStore] = None


def get_store() -> ApprovalStore:
    """Get the global approval store."""
    global _store
    if _store is None:
        _store = ApprovalStore()
    return _store


def request_approval(
    tasc_id: str,
    title: str,
    description: str,
    action_type: str = "manual_gate",
    requested_by: str = "agent",
    plan_id: Optional[str] = None,
    required_approvals: int = 1,
    context: Optional[Dict[str, Any]] = None,
) -> ApprovalRequest:
    """Create a new approval request.
    
    Args:
        tasc_id: ID of the Tasc this approval is for
        title: Short title for the approval request
        description: Detailed description of what needs approval
        action_type: Type of action (e.g., "deploy", "delete_file")
        requested_by: Who requested this (e.g., "agent", "claude-code")
        plan_id: ID of the parent plan (optional)
        required_approvals: How many approvers needed (default: 1)
        context: Additional context (command, diff, files, etc.)
    
    Returns:
        ApprovalRequest in pending state
    """
    request = ApprovalRequest(
        id=f"approval_{uuid.uuid4().hex[:12]}",
        tasc_id=tasc_id,
        plan_id=plan_id,
        title=title,
        description=description,
        action_type=action_type,
        requested_by=requested_by,
        requested_at=datetime.now().isoformat(),
        status="pending",
        required_approvals=required_approvals,
        context=context or {},
    )
    
    get_store().save(request)
    return request


def approve(
    request_id: str,
    approver: str,
    comment: Optional[str] = None,
) -> ApprovalRequest:
    """Approve a pending request.
    
    Args:
        request_id: ID of the approval request
        approver: Name/ID of the approver
        comment: Optional comment
    
    Returns:
        Updated ApprovalRequest
    
    Raises:
        ValueError: If request not found or already resolved
    """
    store = get_store()
    request = store.get(request_id)
    
    if request is None:
        raise ValueError(f"Approval request not found: {request_id}")
    
    if request.status not in ("pending", "partial"):
        raise ValueError(f"Request already resolved: {request.status}")
    
    # Check if this approver already voted
    if any(a.approver == approver for a in request.approvals):
        raise ValueError(f"Approver {approver} already voted")
    
    # Add approval
    request.approvals.append(Approval(
        approver=approver,
        approved=True,
        comment=comment,
    ))
    
    # Update status
    if request.is_approved:
        request.status = "approved"
    elif len(request.approvals) > 0:
        request.status = "partial"
    
    store.save(request)
    return request


def reject(
    request_id: str,
    approver: str,
    reason: str,
) -> ApprovalRequest:
    """Reject a pending request.
    
    Args:
        request_id: ID of the approval request
        approver: Name/ID of the rejector
        reason: Reason for rejection
    
    Returns:
        Updated ApprovalRequest
    
    Raises:
        ValueError: If request not found
    """
    store = get_store()
    request = store.get(request_id)
    
    if request is None:
        raise ValueError(f"Approval request not found: {request_id}")
    
    if request.status not in ("pending", "partial"):
        raise ValueError(f"Request already resolved: {request.status}")
    
    # Add rejection
    request.approvals.append(Approval(
        approver=approver,
        approved=False,
        comment=reason,
    ))
    
    request.status = "rejected"
    request.rejection_reason = reason
    
    store.save(request)
    return request


def get_pending_approvals(plan_id: Optional[str] = None) -> List[ApprovalRequest]:
    """Get all pending approval requests.
    
    Args:
        plan_id: Optional filter by plan
    
    Returns:
        List of pending ApprovalRequest objects
    """
    return get_store().list_pending(plan_id)


def get_approval(request_id: str) -> Optional[ApprovalRequest]:
    """Get an approval request by ID."""
    return get_store().get(request_id)


def is_dangerous_action(action_type: str) -> bool:
    """Check if an action type requires approval."""
    return action_type.lower() in DANGEROUS_ACTIONS


def require_approval_for(action_type: str) -> bool:
    """Check if this action type should require approval.
    
    Uses the DANGEROUS_ACTIONS set by default.
    """
    return is_dangerous_action(action_type)
