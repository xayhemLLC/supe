"""Base team configuration and abstractions.

Defines the core building blocks for team styles:
- TeamStyle: Enum of available team patterns
- AgentRole: Enum of agent roles
- TeamConfig: Configuration dataclass
- BaseTeam: Abstract team implementation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4
import asyncio


class TeamStyle(Enum):
    """Available team working styles."""

    STARTUP = "startup"           # Fast iteration, minimal process
    ENTERPRISE = "enterprise"     # Full governance, audit trails
    RESEARCH = "research"         # Hypothesis-driven exploration
    SOLO = "solo"                 # Single dev with AI assistance
    PAIR = "pair"                 # Driver/navigator pattern
    MOB = "mob"                   # Whole team, one task
    OPEN_SOURCE = "open_source"   # Async, PR-based collaboration
    AGENCY = "agency"             # Client-facing, deliverable-focused


class AgentRole(Enum):
    """Roles agents can take in a team."""

    LEAD = "lead"                 # Technical leadership, final decisions
    DEVELOPER = "developer"       # Implementation
    REVIEWER = "reviewer"         # Code review, quality gates
    QA = "qa"                     # Testing, validation
    ARCHITECT = "architect"       # System design, patterns
    RESEARCHER = "researcher"     # Investigation, spikes
    DOCUMENTARIAN = "documentarian"  # Docs, knowledge capture
    DEVOPS = "devops"             # Infrastructure, CI/CD
    SECURITY = "security"         # Security review, audits


class CeremonyType(Enum):
    """Team ceremonies/rituals."""

    STANDUP = "standup"           # Daily sync
    PLANNING = "planning"         # Work selection
    REVIEW = "review"             # Demo/review
    RETRO = "retro"               # Improvement
    REFINEMENT = "refinement"     # Backlog grooming
    SYNC = "sync"                 # Ad-hoc coordination


@dataclass
class CeremonyConfig:
    """Configuration for a team ceremony."""

    ceremony_type: CeremonyType
    frequency: str = "daily"      # "daily", "weekly", "sprint", "on-demand"
    duration_minutes: int = 15
    required_roles: List[AgentRole] = field(default_factory=list)
    auto_trigger: bool = True


@dataclass
class ValidationConfig:
    """Validation configuration for a team."""

    require_review: bool = True
    require_tests: bool = True
    require_docs: bool = False
    min_reviewers: int = 1
    auto_merge: bool = False
    proof_generation: bool = True
    store_to_memory: bool = True

    # Gate configurations
    pre_commit_gates: List[str] = field(default_factory=lambda: ["lint", "type_check"])
    pre_merge_gates: List[str] = field(default_factory=lambda: ["tests_pass", "review_approved"])
    post_deploy_gates: List[str] = field(default_factory=list)


@dataclass
class TeamConfig:
    """Configuration for a development team.

    Defines team composition, ceremonies, and validation rules.
    """

    name: str
    style: TeamStyle

    # Team composition
    roles: Dict[AgentRole, int] = field(default_factory=dict)

    # Process configuration
    ceremonies: List[CeremonyConfig] = field(default_factory=list)
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    # Resource limits
    max_concurrent_tasks: int = 3
    max_wip_per_agent: int = 1
    iteration_length_days: int = 14

    # Communication
    async_first: bool = True
    decision_timeout_hours: int = 24

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def total_agents(self) -> int:
        """Total number of agents in team."""
        return sum(self.roles.values())

    def has_role(self, role: AgentRole) -> bool:
        """Check if team has a specific role."""
        return self.roles.get(role, 0) > 0


@dataclass
class TaskAssignment:
    """A task assigned to an agent."""

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    title: str = ""
    description: str = ""
    assigned_to: Optional[str] = None
    status: str = "pending"  # pending, in_progress, review, done, blocked
    priority: int = 5

    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Evidence
    proof_hash: Optional[str] = None
    files_changed: List[str] = field(default_factory=list)

    def start(self, agent_id: str) -> None:
        self.assigned_to = agent_id
        self.status = "in_progress"
        self.started_at = datetime.now()

    def complete(self, proof_hash: str = None) -> None:
        self.status = "done"
        self.completed_at = datetime.now()
        self.proof_hash = proof_hash


class MessageBus:
    """Simple message bus for inter-agent communication."""

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._history: List[Dict[str, Any]] = []

    def register(self, agent_id: str) -> None:
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()

    async def send(self, sender: str, recipient: str, content: Dict[str, Any]) -> None:
        msg = {
            "id": str(uuid4())[:8],
            "sender": sender,
            "recipient": recipient,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self._history.append(msg)

        if recipient in self._queues:
            await self._queues[recipient].put(msg)

    async def broadcast(self, sender: str, content: Dict[str, Any]) -> None:
        for agent_id in self._queues:
            if agent_id != sender:
                await self.send(sender, agent_id, content)

    async def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        if agent_id not in self._queues:
            return None
        try:
            return await asyncio.wait_for(self._queues[agent_id].get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


class BaseTeam(ABC):
    """Abstract base class for team implementations.

    Provides common functionality for all team styles.
    """

    def __init__(self, config: TeamConfig):
        self.config = config
        self.message_bus = MessageBus()
        self.agents: Dict[str, Any] = {}
        self.tasks: Dict[str, TaskAssignment] = {}
        self._running = False
        self._cycle_count = 0

    @abstractmethod
    def _create_agents(self) -> None:
        """Create agents based on config. Implement in subclass."""
        pass

    def add_task(self, title: str, description: str = "", priority: int = 5) -> TaskAssignment:
        """Add a task to the team's queue."""
        task = TaskAssignment(
            title=title,
            description=description,
            priority=priority,
        )
        self.tasks[task.id] = task
        return task

    # =========================================================================
    # AUTO-DISCOVERY METHODS
    # =========================================================================

    async def discover_from_goal(
        self,
        goal: str,
        max_tasks: int = 8,
        context: str = None,
    ) -> List[TaskAssignment]:
        """Auto-discover tasks from a goal description using LLM.

        Args:
            goal: High-level goal like "Add user authentication"
            max_tasks: Maximum tasks to generate
            context: Optional context about the codebase

        Returns:
            List of created TaskAssignment objects

        Example:
            tasks = await team.discover_from_goal("Add dark mode support")
        """
        try:
            from tascer import generate_plan
        except ImportError:
            # Fallback: create single task from goal
            return [self.add_task(goal, description=goal, priority=1)]

        try:
            result = generate_plan(
                goal=goal,
                max_tascs=max_tasks,
                context=context,
                require_approval=False,
            )

            created = []
            for i, tasc in enumerate(result.plan.tascs):
                task = self.add_task(
                    title=tasc.title,
                    description=tasc.testing_instructions or tasc.title,
                    priority=i + 1,
                )
                created.append(task)

            return created
        except Exception:
            # Fallback if API not available
            return [self.add_task(goal, description=goal, priority=1)]

    def discover_from_issues(
        self,
        repo: str = None,
        labels: List[str] = None,
        limit: int = 10,
    ) -> List[TaskAssignment]:
        """Auto-discover tasks from GitHub issues.

        Args:
            repo: GitHub repo (owner/name). Defaults to current repo.
            labels: Filter by labels like ["bug", "enhancement"]
            limit: Max issues to fetch

        Returns:
            List of created TaskAssignment objects

        Example:
            tasks = team.discover_from_issues(labels=["good-first-issue"])
        """
        import subprocess
        import json

        cmd = ["gh", "issue", "list", "--json", "number,title,body,labels", "--limit", str(limit)]

        if repo:
            cmd.extend(["--repo", repo])
        if labels:
            for label in labels:
                cmd.extend(["--label", label])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

        created = []
        for i, issue in enumerate(issues):
            # Priority based on labels
            priority = 5
            label_names = [l.get("name", "") for l in issue.get("labels", [])]
            if "critical" in label_names or "urgent" in label_names:
                priority = 1
            elif "bug" in label_names:
                priority = 2
            elif "enhancement" in label_names:
                priority = 3

            task = self.add_task(
                title=f"#{issue['number']}: {issue['title']}",
                description=issue.get("body", "")[:500],
                priority=priority,
            )
            created.append(task)

        return created

    def discover_from_codebase(
        self,
        path: str = ".",
        patterns: List[str] = None,
    ) -> List[TaskAssignment]:
        """Auto-discover tasks from codebase TODOs, FIXMEs, etc.

        Args:
            path: Directory to scan
            patterns: Patterns to search for. Defaults to TODO, FIXME, HACK, XXX

        Returns:
            List of created TaskAssignment objects

        Example:
            tasks = team.discover_from_codebase(path="src/")
        """
        import subprocess

        patterns = patterns or ["TODO", "FIXME", "HACK", "XXX"]
        pattern_regex = "|".join(patterns)

        try:
            result = subprocess.run(
                ["grep", "-rn", "-E", f"({pattern_regex}):", path,
                 "--include=*.py", "--include=*.ts", "--include=*.js",
                 "--include=*.go", "--include=*.rs", "--include=*.java"],
                capture_output=True,
                text=True,
            )
            lines = result.stdout.strip().split("\n") if result.stdout else []
        except subprocess.CalledProcessError:
            return []

        created = []
        seen = set()

        for line in lines[:50]:  # Limit to 50 items
            if not line or line in seen:
                continue
            seen.add(line)

            # Parse: file:line:content
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue

            file_path, line_num, content = parts
            content = content.strip()

            # Determine priority from pattern
            priority = 5
            if "FIXME" in content:
                priority = 2
            elif "HACK" in content or "XXX" in content:
                priority = 3
            elif "TODO" in content:
                priority = 4

            task = self.add_task(
                title=content[:80],
                description=f"{file_path}:{line_num}\n{content}",
                priority=priority,
            )
            created.append(task)

        return created

    def discover_from_plan(self, plan_path: str) -> List[TaskAssignment]:
        """Load tasks from a supe plan JSON file.

        Args:
            plan_path: Path to plan JSON file

        Returns:
            List of created TaskAssignment objects

        Example:
            tasks = team.discover_from_plan(".supe/plans/feature.json")
        """
        import json

        with open(plan_path) as f:
            plan = json.load(f)

        created = []
        tascs = plan.get("tascs", plan.get("tasks", []))

        for i, tasc in enumerate(tascs):
            title = tasc.get("title", tasc.get("name", f"Task {i+1}"))
            desc = tasc.get("description", tasc.get("testing_instructions", ""))

            task = self.add_task(
                title=title,
                description=desc,
                priority=i + 1,
            )
            created.append(task)

        return created

    def discover_from_diff(self, base: str = "main") -> List[TaskAssignment]:
        """Auto-discover review tasks from git diff.

        Args:
            base: Base branch to diff against

        Returns:
            List of created TaskAssignment objects (one per changed file)

        Example:
            tasks = team.discover_from_diff(base="main")
        """
        import subprocess

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base],
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f for f in result.stdout.strip().split("\n") if f]
        except subprocess.CalledProcessError:
            return []

        created = []
        for i, file_path in enumerate(files):
            task = self.add_task(
                title=f"Review: {file_path}",
                description=f"Review changes in {file_path}",
                priority=i + 1,
            )
            created.append(task)

        return created

    def get_pending_tasks(self) -> List[TaskAssignment]:
        """Get tasks waiting to be worked on."""
        pending = [t for t in self.tasks.values() if t.status == "pending"]
        return sorted(pending, key=lambda t: t.priority)

    def get_in_progress_tasks(self) -> List[TaskAssignment]:
        """Get tasks currently being worked on."""
        return [t for t in self.tasks.values() if t.status == "in_progress"]

    async def assign_task(self, task: TaskAssignment, agent_id: str) -> bool:
        """Assign a task to an agent."""
        if task.status != "pending":
            return False

        # Check WIP limit
        agent_tasks = [t for t in self.tasks.values()
                       if t.assigned_to == agent_id and t.status == "in_progress"]
        if len(agent_tasks) >= self.config.max_wip_per_agent:
            return False

        task.start(agent_id)

        # Notify agent
        await self.message_bus.send(
            "orchestrator",
            agent_id,
            {"type": "task_assigned", "task_id": task.id, "title": task.title},
        )

        return True

    async def run_cycle(self) -> Dict[str, Any]:
        """Run one orchestration cycle."""
        self._cycle_count += 1

        # Assign pending tasks to available agents
        assignments = []
        pending = self.get_pending_tasks()

        for task in pending[:self.config.max_concurrent_tasks]:
            # Find available agent
            for agent_id, agent in self.agents.items():
                if getattr(agent, 'status', 'idle') == 'idle':
                    if await self.assign_task(task, agent_id):
                        assignments.append((task.id, agent_id))
                        break

        return {
            "cycle": self._cycle_count,
            "assignments": assignments,
            "pending": len(pending),
            "in_progress": len(self.get_in_progress_tasks()),
        }

    async def run(self, max_cycles: int = None) -> Dict[str, Any]:
        """Run the team autonomously."""
        self._running = True

        print(f"\n{'='*50}")
        print(f"{self.config.style.value.upper()} TEAM: {self.config.name}")
        print(f"{'='*50}")
        print(f"Agents: {self.config.total_agents()}")
        print(f"Tasks: {len(self.tasks)}")

        try:
            while self._running:
                if max_cycles and self._cycle_count >= max_cycles:
                    break

                result = await self.run_cycle()

                if result["assignments"]:
                    for task_id, agent_id in result["assignments"]:
                        task = self.tasks[task_id]
                        print(f"  [{self._cycle_count}] {agent_id} -> {task.title[:40]}")

                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print("\nShutdown requested")
        finally:
            self._running = False

        return self.get_status()

    def stop(self) -> None:
        """Stop the team."""
        self._running = False

    def get_status(self) -> Dict[str, Any]:
        """Get team status."""
        return {
            "name": self.config.name,
            "style": self.config.style.value,
            "running": self._running,
            "cycles": self._cycle_count,
            "agents": len(self.agents),
            "tasks": {
                "total": len(self.tasks),
                "pending": len([t for t in self.tasks.values() if t.status == "pending"]),
                "in_progress": len([t for t in self.tasks.values() if t.status == "in_progress"]),
                "done": len([t for t in self.tasks.values() if t.status == "done"]),
            },
        }
