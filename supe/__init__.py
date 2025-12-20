"""Supe - The Main Orchestrator.

The Supe provides a goal-oriented async API for planning and executing work.

Example:
    from supe import Supe
    
    supe = Supe()
    result = await supe.exe("Ingest Discord API docs")
    answer = await supe.recall("How do slash commands work?")
"""

from .supe import Supe, AgentPort, RecallResult, ExecutionResult, AgentResponse

__version__ = "0.1.0"

__all__ = [
    "Supe",
    "AgentPort",
    "RecallResult",
    "ExecutionResult",
    "AgentResponse",
]
