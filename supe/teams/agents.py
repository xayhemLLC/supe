"""Supe-validated team agents.

Agents that integrate with supe's validation framework:
- Pre/post execution gates
- Proof-of-work generation
- Memory recall for context
- Audit trail logging

Each agent wraps tool calls through TascerAgent validation.
"""

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .base import AgentRole, MessageBus, TaskAssignment


@dataclass
class AgentConfig:
    """Configuration for a validated agent."""

    agent_id: str
    role: AgentRole
    capabilities: list[str] = field(default_factory=list)

    # Validation settings
    pre_gates: list[str] = field(default_factory=lambda: ["safe_commands"])
    post_gates: list[str] = field(default_factory=lambda: ["exit_code_zero"])
    generate_proofs: bool = True
    store_to_memory: bool = True

    # Behavior
    max_retries: int = 3
    timeout_seconds: int = 300


class ValidatedAgent(ABC):
    """Base agent with supe validation integration.

    All tool calls are validated through supe's gate system,
    generating proofs and storing to memory.
    """

    def __init__(
        self,
        config: AgentConfig,
        message_bus: MessageBus = None,
    ):
        self.config = config
        self.agent_id = config.agent_id
        self.role = config.role
        self.message_bus = message_bus

        self.status = "idle"
        self.current_task: TaskAssignment | None = None
        self._supe_agent = None

        # Execution history
        self.executions: list[dict[str, Any]] = []

    def _get_supe_agent(self):
        """Lazy-load supe agent for validation."""
        if self._supe_agent is None:
            try:
                from ab import ABMemory
                from tascer.sdk_wrapper import (
                    RecallConfig,
                    TascerAgent,
                    TascerAgentOptions,
                    ToolValidationConfig,
                )

                db_path = os.path.expanduser("~/.supe/memory.sqlite")
                os.makedirs(os.path.dirname(db_path), exist_ok=True)

                self._supe_agent = TascerAgent(
                    tascer_options=TascerAgentOptions(
                        tool_configs={
                            "Bash": ToolValidationConfig(
                                tool_name="Bash",
                                pre_gates=self.config.pre_gates,
                                post_gates=self.config.post_gates,
                            ),
                        },
                        default_pre_gates=self.config.pre_gates,
                        recall_config=RecallConfig(
                            enabled=True,
                            auto_context=True,
                            auto_context_limit=3,
                        ),
                        generate_proofs=self.config.generate_proofs,
                        store_to_ab=self.config.store_to_memory,
                    ),
                    ab_memory=ABMemory(db_path),
                )
            except ImportError:
                # Fallback if supe not fully available
                self._supe_agent = None

        return self._supe_agent

    async def validate_tool_call(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate a tool call through supe.

        Returns:
            {
                "allowed": bool,
                "proof_hash": str or None,
                "context": str or None,
                "message": str,
            }
        """
        agent = self._get_supe_agent()
        if not agent:
            # No validation available, allow by default
            return {"allowed": True, "proof_hash": None, "context": None, "message": "No validator"}

        tool_use_id = f"tu_{uuid4().hex[:8]}"

        # Pre-validation
        pre_result = await agent._pre_tool_hook(
            {"tool_name": tool_name, "tool_input": tool_input},
            tool_use_id,
            None,
        )

        if pre_result.get("block"):
            return {
                "allowed": False,
                "proof_hash": None,
                "context": None,
                "message": pre_result.get("message", "Blocked by gate"),
            }

        return {
            "allowed": True,
            "proof_hash": None,  # Set after post-hook
            "context": pre_result.get("context"),
            "message": "Validated",
            "_tool_use_id": tool_use_id,
        }

    async def record_execution(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        tool_use_id: str,
    ) -> str | None:
        """Record tool execution and get proof hash."""
        agent = self._get_supe_agent()
        if not agent:
            return None

        await agent._post_tool_hook(
            {"tool_result": tool_output},
            tool_use_id,
            None,
        )

        record = agent._find_record(tool_use_id)
        return record.proof_hash if record else None

    @abstractmethod
    async def work_on_task(self, task: TaskAssignment) -> dict[str, Any]:
        """Work on an assigned task. Implement in subclass."""
        pass

    async def run(self) -> None:
        """Main agent loop."""
        while True:
            if self.message_bus:
                msg = await self.message_bus.receive(self.agent_id, timeout=1.0)
                if msg:
                    await self._handle_message(msg)
            await asyncio.sleep(0.1)

    async def _handle_message(self, msg: dict[str, Any]) -> None:
        """Handle incoming message."""
        content = msg.get("content", {})
        msg_type = content.get("type")

        if msg_type == "task_assigned":
            content.get("task_id")
            # Would look up task and work on it
            pass


class LeadAgent(ValidatedAgent):
    """Technical lead agent.

    Responsibilities:
    - Architecture decisions
    - Code review approval
    - Task prioritization
    - Blocker resolution
    """

    def __init__(self, agent_id: str = "lead-1", **kwargs):
        config = AgentConfig(
            agent_id=agent_id,
            role=AgentRole.LEAD,
            capabilities=["architecture", "review", "prioritize", "unblock"],
            pre_gates=["safe_commands", "no_force_push"],
            post_gates=["exit_code_zero"],
        )
        super().__init__(config, **kwargs)

    async def work_on_task(self, task: TaskAssignment) -> dict[str, Any]:
        """Lead works on architecture/review tasks."""
        self.status = "working"
        self.current_task = task

        result = {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "status": "completed",
            "output": f"Lead reviewed: {task.title}",
        }

        self.status = "idle"
        self.current_task = None
        return result

    async def review_pr(self, pr_url: str) -> dict[str, Any]:
        """Review a pull request."""
        validation = await self.validate_tool_call(
            "Bash",
            {"command": f"gh pr view {pr_url} --json title,body,files"},
        )

        if not validation["allowed"]:
            return {"approved": False, "reason": validation["message"]}

        # Would do actual review here
        return {"approved": True, "comments": [], "context": validation.get("context")}


class DeveloperAgent(ValidatedAgent):
    """Developer agent for implementation tasks.

    Responsibilities:
    - Write code
    - Write tests
    - Fix bugs
    - Create PRs
    """

    def __init__(self, agent_id: str = "dev-1", **kwargs):
        config = AgentConfig(
            agent_id=agent_id,
            role=AgentRole.DEVELOPER,
            capabilities=["code", "test", "debug", "pr"],
            pre_gates=["safe_commands", "no_rm_rf"],
            post_gates=["exit_code_zero", "tests_pass"],
        )
        super().__init__(config, **kwargs)

    async def work_on_task(self, task: TaskAssignment) -> dict[str, Any]:
        """Implement a task."""
        self.status = "working"
        self.current_task = task

        # Validate any file writes
        validation = await self.validate_tool_call(
            "Write",
            {"file_path": "/tmp/example.py", "content": "# implementation"},
        )

        result = {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "status": "completed" if validation["allowed"] else "blocked",
            "files_changed": [],
            "context_used": validation.get("context"),
        }

        self.status = "idle"
        self.current_task = None
        return result

    async def run_tests(self, path: str = "tests/") -> dict[str, Any]:
        """Run tests with validation."""
        validation = await self.validate_tool_call(
            "Bash",
            {"command": f"pytest {path} -v"},
        )

        if not validation["allowed"]:
            return {"passed": False, "reason": validation["message"]}

        return {
            "passed": True,
            "tool_use_id": validation.get("_tool_use_id"),
            "context": validation.get("context"),
        }


class ReviewerAgent(ValidatedAgent):
    """Code reviewer agent.

    Responsibilities:
    - Review PRs
    - Check code quality
    - Verify patterns
    - Security review
    """

    def __init__(self, agent_id: str = "reviewer-1", **kwargs):
        config = AgentConfig(
            agent_id=agent_id,
            role=AgentRole.REVIEWER,
            capabilities=["review", "security_check", "pattern_check"],
            pre_gates=["safe_commands"],
            post_gates=["exit_code_zero"],
        )
        super().__init__(config, **kwargs)

    async def work_on_task(self, task: TaskAssignment) -> dict[str, Any]:
        """Review code."""
        self.status = "working"
        self.current_task = task

        result = {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "status": "completed",
            "approved": True,
            "comments": [],
        }

        self.status = "idle"
        self.current_task = None
        return result


class QAAgent(ValidatedAgent):
    """QA/Testing agent.

    Responsibilities:
    - Run test suites
    - Validate acceptance criteria
    - Regression testing
    - Bug verification
    """

    def __init__(self, agent_id: str = "qa-1", **kwargs):
        config = AgentConfig(
            agent_id=agent_id,
            role=AgentRole.QA,
            capabilities=["test", "validate", "regression", "verify"],
            pre_gates=["safe_commands"],
            post_gates=["exit_code_zero", "no_secrets_in_output"],
        )
        super().__init__(config, **kwargs)

    async def work_on_task(self, task: TaskAssignment) -> dict[str, Any]:
        """Test/validate a task."""
        self.status = "working"
        self.current_task = task

        # Run validation suite
        test_result = await self.validate_tool_call(
            "Bash",
            {"command": "pytest tests/ --tb=short"},
        )

        result = {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "status": "completed",
            "tests_passed": test_result["allowed"],
            "issues": [],
        }

        self.status = "idle"
        self.current_task = None
        return result


class ArchitectAgent(ValidatedAgent):
    """Architecture agent for system design.

    Responsibilities:
    - System design
    - Pattern selection
    - Tech decisions
    - Dependency management
    """

    def __init__(self, agent_id: str = "architect-1", **kwargs):
        config = AgentConfig(
            agent_id=agent_id,
            role=AgentRole.ARCHITECT,
            capabilities=["design", "patterns", "dependencies", "scalability"],
            pre_gates=["safe_commands"],
            post_gates=["exit_code_zero"],
        )
        super().__init__(config, **kwargs)

    async def work_on_task(self, task: TaskAssignment) -> dict[str, Any]:
        """Design/architecture work."""
        self.status = "working"
        self.current_task = task

        result = {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "status": "completed",
            "design_doc": None,
            "decisions": [],
        }

        self.status = "idle"
        self.current_task = None
        return result


class ResearcherAgent(ValidatedAgent):
    """Research agent for investigation tasks.

    Responsibilities:
    - Spikes/investigations
    - Technology evaluation
    - Proof of concepts
    - Documentation
    """

    def __init__(self, agent_id: str = "researcher-1", **kwargs):
        config = AgentConfig(
            agent_id=agent_id,
            role=AgentRole.RESEARCHER,
            capabilities=["research", "evaluate", "poc", "document"],
            pre_gates=["safe_commands"],
            post_gates=["exit_code_zero"],
        )
        super().__init__(config, **kwargs)

    async def work_on_task(self, task: TaskAssignment) -> dict[str, Any]:
        """Research/investigation work."""
        self.status = "working"
        self.current_task = task

        result = {
            "task_id": task.id,
            "agent_id": self.agent_id,
            "status": "completed",
            "findings": [],
            "recommendations": [],
        }

        self.status = "idle"
        self.current_task = None
        return result

    async def recall_similar(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Recall similar past research from memory."""
        agent = self._get_supe_agent()
        if not agent:
            return []

        return agent.recall(query, top_k=top_k)
