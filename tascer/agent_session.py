"""Agent Session Tracking.

Track agent execution sessions for debugging, replay, and learning.
"""

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


@dataclass
class StepLog:
    """Log of a single step in an agent session.
    
    Each step represents one decision + action cycle.
    """
    step_index: int
    mode: Literal["plan", "execute", "verify", "critic"]
    
    # Agent's reasoning
    thought: str
    subgoal: Optional[str] = None
    
    # What was planned vs executed
    planned_actions: List[Dict[str, Any]] = field(default_factory=list)
    executed_actions: List[Dict[str, Any]] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Critic's evaluation (if applicable)
    critic_verdict: Optional[str] = None  # "accept", "revise", "rollback", "ask_user"
    critic_notes: List[str] = field(default_factory=list)
    
    # Timing
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "mode": self.mode,
            "thought": self.thought,
            "subgoal": self.subgoal,
            "planned_actions": self.planned_actions,
            "executed_actions": self.executed_actions,
            "results": self.results,
            "critic_verdict": self.critic_verdict,
            "critic_notes": self.critic_notes,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StepLog":
        return cls(
            step_index=data.get("step_index", 0),
            mode=data.get("mode", "execute"),
            thought=data.get("thought", ""),
            subgoal=data.get("subgoal"),
            planned_actions=data.get("planned_actions", []),
            executed_actions=data.get("executed_actions", []),
            results=data.get("results", []),
            critic_verdict=data.get("critic_verdict"),
            critic_notes=data.get("critic_notes", []),
            timestamp=data.get("timestamp", ""),
            duration_ms=data.get("duration_ms", 0),
        )


@dataclass
class AgentSession:
    """A complete agent execution session.
    
    Tracks everything an agent did from start to finish.
    """
    id: str
    tasc_id: str
    goal: str
    
    # Session metadata
    model: str = "unknown"  # LLM model used
    agent_name: str = "agent"
    
    # Status
    status: Literal["in_progress", "success", "failed", "aborted", "paused"] = "in_progress"
    
    # Execution log
    steps: List[StepLog] = field(default_factory=list)
    
    # Constraints and context
    constraints: List[str] = field(default_factory=list)
    context_summary: str = ""
    
    # Timing
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Summary (filled on completion)
    final_summary: Optional[str] = None
    final_risks: List[str] = field(default_factory=list)
    final_follow_ups: List[str] = field(default_factory=list)
    
    @property
    def total_steps(self) -> int:
        return len(self.steps)
    
    @property
    def total_duration_ms(self) -> float:
        return sum(s.duration_ms for s in self.steps)
    
    def add_step(self, step: StepLog):
        """Add a step to the session."""
        self.steps.append(step)
        self.updated_at = datetime.now().isoformat()
    
    def complete(
        self,
        success: bool,
        summary: str,
        risks: Optional[List[str]] = None,
        follow_ups: Optional[List[str]] = None,
    ):
        """Mark session as complete."""
        self.status = "success" if success else "failed"
        self.final_summary = summary
        self.final_risks = risks or []
        self.final_follow_ups = follow_ups or []
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tasc_id": self.tasc_id,
            "goal": self.goal,
            "model": self.model,
            "agent_name": self.agent_name,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "constraints": self.constraints,
            "context_summary": self.context_summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "final_summary": self.final_summary,
            "final_risks": self.final_risks,
            "final_follow_ups": self.final_follow_ups,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSession":
        steps = [StepLog.from_dict(s) for s in data.get("steps", [])]
        return cls(
            id=data.get("id", ""),
            tasc_id=data.get("tasc_id", ""),
            goal=data.get("goal", ""),
            model=data.get("model", "unknown"),
            agent_name=data.get("agent_name", "agent"),
            status=data.get("status", "in_progress"),
            steps=steps,
            constraints=data.get("constraints", []),
            context_summary=data.get("context_summary", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            final_summary=data.get("final_summary"),
            final_risks=data.get("final_risks", []),
            final_follow_ups=data.get("final_follow_ups", []),
        )
    
    @classmethod
    def create(
        cls,
        tasc_id: str,
        goal: str,
        model: str = "unknown",
        agent_name: str = "agent",
        constraints: Optional[List[str]] = None,
        context_summary: str = "",
    ) -> "AgentSession":
        """Create a new session."""
        return cls(
            id=f"session_{uuid.uuid4().hex[:12]}",
            tasc_id=tasc_id,
            goal=goal,
            model=model,
            agent_name=agent_name,
            constraints=constraints or [],
            context_summary=context_summary,
        )


class SessionStore:
    """Storage for agent sessions."""
    
    def __init__(self, path: str = ".tascer/sessions"):
        self.path = path
        os.makedirs(path, exist_ok=True)
    
    def _session_path(self, session_id: str) -> str:
        return os.path.join(self.path, f"{session_id}.json")
    
    def save(self, session: AgentSession):
        """Save a session to storage."""
        with open(self._session_path(session.id), 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
    
    def load(self, session_id: str) -> Optional[AgentSession]:
        """Load a session by ID."""
        path = self._session_path(session_id)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return AgentSession.from_dict(json.load(f))
    
    def list_sessions(self, limit: int = 50) -> List[AgentSession]:
        """List recent sessions."""
        sessions = []
        files = sorted(
            [f for f in os.listdir(self.path) if f.endswith('.json')],
            reverse=True,
        )[:limit]
        
        for fname in files:
            path = os.path.join(self.path, fname)
            with open(path) as f:
                sessions.append(AgentSession.from_dict(json.load(f)))
        
        return sessions
    
    def get_sessions_for_tasc(self, tasc_id: str) -> List[AgentSession]:
        """Get all sessions for a specific tasc."""
        return [s for s in self.list_sessions() if s.tasc_id == tasc_id]


def start_session(
    tasc_id: str,
    goal: str,
    model: str = "unknown",
    agent_name: str = "agent",
    **kwargs,
) -> AgentSession:
    """Start a new agent session.
    
    Example:
        session = start_session(
            tasc_id="fix_bug_123",
            goal="Fix the login 500 error",
            model="claude-3-opus",
            constraints=["Keep changes minimal"],
        )
    """
    session = AgentSession.create(
        tasc_id=tasc_id,
        goal=goal,
        model=model,
        agent_name=agent_name,
        **kwargs,
    )
    
    # Save initial state
    store = SessionStore()
    store.save(session)
    
    return session


def log_step(
    session: AgentSession,
    mode: str,
    thought: str,
    subgoal: Optional[str] = None,
    planned_actions: Optional[List[Dict]] = None,
    executed_actions: Optional[List[Dict]] = None,
    results: Optional[List[Dict]] = None,
    critic_verdict: Optional[str] = None,
    duration_ms: float = 0,
) -> StepLog:
    """Log a step in a session.
    
    Example:
        step = log_step(
            session=session,
            mode="execute",
            thought="Need to read the login handler",
            executed_actions=[{"type": "READ_FILE", "path": "src/auth.py"}],
            results=[{"status": "ok", "output": "..."}],
        )
    """
    step = StepLog(
        step_index=len(session.steps),
        mode=mode,
        thought=thought,
        subgoal=subgoal,
        planned_actions=planned_actions or [],
        executed_actions=executed_actions or [],
        results=results or [],
        critic_verdict=critic_verdict,
        duration_ms=duration_ms,
    )
    
    session.add_step(step)
    
    # Save updated session
    store = SessionStore()
    store.save(session)
    
    return step


def complete_session(
    session: AgentSession,
    success: bool,
    summary: str,
    risks: Optional[List[str]] = None,
    follow_ups: Optional[List[str]] = None,
):
    """Mark a session as complete.
    
    Example:
        complete_session(
            session=session,
            success=True,
            summary="Fixed login error by adding null check",
            risks=["Edge case for empty username not tested"],
            follow_ups=["Add unit test for empty username"],
        )
    """
    session.complete(success, summary, risks, follow_ups)
    
    # Save final state
    store = SessionStore()
    store.save(session)


def replay_session(session_id: str) -> Optional[AgentSession]:
    """Load a session for replay/debugging."""
    store = SessionStore()
    return store.load(session_id)


def get_session_summary(session: AgentSession) -> str:
    """Generate a human-readable session summary."""
    lines = [
        f"Session: {session.id}",
        f"Goal: {session.goal}",
        f"Status: {session.status}",
        f"Steps: {session.total_steps}",
        f"Duration: {session.total_duration_ms:.1f}ms",
        "",
        "Steps:",
    ]
    
    for step in session.steps:
        verdict = f" [{step.critic_verdict}]" if step.critic_verdict else ""
        lines.append(f"  {step.step_index}. [{step.mode}]{verdict} {step.thought[:50]}...")
    
    if session.final_summary:
        lines.extend([
            "",
            f"Summary: {session.final_summary}",
        ])
    
    if session.final_risks:
        lines.append(f"Risks: {', '.join(session.final_risks)}")
    
    if session.final_follow_ups:
        lines.append(f"Follow-ups: {', '.join(session.final_follow_ups)}")
    
    return "\n".join(lines)
