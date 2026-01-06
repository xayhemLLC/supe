"""Capability Manager for Problem Solver Scripts.

This module manages the registry of scripts that the problem solver can use
to tackle specific types of problems. Each script represents a capability that
can be invoked when needed.
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Capability:
    """Represents a problem-solving capability (script)."""

    id: str
    name: str
    description: str
    script_path: str
    problem_patterns: List[str] = field(default_factory=list)  # Keywords to match
    input_format: str = ""  # How to pass data to script
    output_format: str = ""  # What the script returns
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used: Optional[str] = None
    usage_count: int = 0
    success_rate: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "script_path": self.script_path,
            "problem_patterns": self.problem_patterns,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Capability":
        """Create capability from dictionary."""
        return cls(**data)

    def matches_problem(self, problem_text: str) -> float:
        """Check if this capability matches a problem.

        Returns:
            Match score between 0.0 and 1.0
        """
        problem_lower = problem_text.lower()
        matches = sum(1 for pattern in self.problem_patterns if pattern.lower() in problem_lower)
        return matches / len(self.problem_patterns) if self.problem_patterns else 0.0


class CapabilityManager:
    """Manages problem solver capabilities."""

    def __init__(self, scripts_dir: Optional[Path] = None):
        """Initialize capability manager.

        Args:
            scripts_dir: Directory containing scripts (defaults to this file's directory)
        """
        self.scripts_dir = scripts_dir or Path(__file__).parent
        self.registry_path = self.scripts_dir / "capabilities.json"
        self.capabilities: Dict[str, Capability] = {}
        self._load_registry()

    def _load_registry(self):
        """Load capabilities from registry file."""
        if not self.registry_path.exists():
            self._save_registry()
            return

        with open(self.registry_path) as f:
            data = json.load(f)
            for cap_data in data.get("capabilities", []):
                cap = Capability.from_dict(cap_data)
                self.capabilities[cap.id] = cap

    def _save_registry(self):
        """Save capabilities to registry file."""
        data = {
            "version": "1.0.0",
            "capabilities": [cap.to_dict() for cap in self.capabilities.values()],
            "metadata": {
                "updated_at": datetime.utcnow().isoformat(),
                "total_capabilities": len(self.capabilities),
            },
        }
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register(self, capability: Capability) -> None:
        """Register a new capability.

        Args:
            capability: The capability to register
        """
        self.capabilities[capability.id] = capability
        self._save_registry()

    def unregister(self, capability_id: str) -> bool:
        """Unregister a capability.

        Args:
            capability_id: ID of capability to remove

        Returns:
            True if removed, False if not found
        """
        if capability_id in self.capabilities:
            del self.capabilities[capability_id]
            self._save_registry()
            return True
        return False

    def find_capabilities(self, problem_text: str, threshold: float = 0.3) -> List[Capability]:
        """Find capabilities that match a problem.

        Args:
            problem_text: The problem to match against
            threshold: Minimum match score (0.0 to 1.0)

        Returns:
            List of matching capabilities, sorted by match score
        """
        matches = []
        for cap in self.capabilities.values():
            score = cap.matches_problem(problem_text)
            if score >= threshold:
                matches.append((score, cap))

        # Sort by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        return [cap for _, cap in matches]

    def execute_capability(
        self,
        capability_id: str,
        input_data: str,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Execute a capability script.

        Args:
            capability_id: ID of capability to execute
            input_data: Input to pass to the script
            timeout: Maximum execution time in seconds

        Returns:
            Dictionary with:
                - success: bool
                - output: str (stdout)
                - error: str (stderr)
                - return_code: int
        """
        if capability_id not in self.capabilities:
            return {
                "success": False,
                "output": "",
                "error": f"Capability {capability_id} not found",
                "return_code": -1,
            }

        cap = self.capabilities[capability_id]
        script_path = self.scripts_dir / cap.script_path

        if not script_path.exists():
            return {
                "success": False,
                "output": "",
                "error": f"Script not found: {script_path}",
                "return_code": -1,
            }

        try:
            result = subprocess.run(
                ["python3", str(script_path)],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # Update usage stats
            cap.usage_count += 1
            cap.last_used = datetime.utcnow().isoformat()
            if result.returncode == 0:
                cap.success_rate = (
                    cap.success_rate * (cap.usage_count - 1) + 1.0
                ) / cap.usage_count
            else:
                cap.success_rate = (
                    cap.success_rate * (cap.usage_count - 1)
                ) / cap.usage_count
            self._save_registry()

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Script execution timed out after {timeout}s",
                "return_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "return_code": -1,
            }

    def list_capabilities(self, tags: Optional[List[str]] = None) -> List[Capability]:
        """List all capabilities, optionally filtered by tags.

        Args:
            tags: Optional list of tags to filter by

        Returns:
            List of capabilities
        """
        caps = list(self.capabilities.values())

        if tags:
            caps = [
                cap for cap in caps
                if any(tag in cap.tags for tag in tags)
            ]

        # Sort by usage count descending
        caps.sort(key=lambda x: x.usage_count, reverse=True)
        return caps

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """Get a specific capability by ID.

        Args:
            capability_id: ID of the capability

        Returns:
            Capability if found, None otherwise
        """
        return self.capabilities.get(capability_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about capabilities.

        Returns:
            Dictionary with stats
        """
        if not self.capabilities:
            return {
                "total": 0,
                "avg_success_rate": 0.0,
                "total_usage": 0,
                "most_used": None,
            }

        caps = list(self.capabilities.values())
        return {
            "total": len(caps),
            "avg_success_rate": sum(c.success_rate for c in caps) / len(caps),
            "total_usage": sum(c.usage_count for c in caps),
            "most_used": max(caps, key=lambda x: x.usage_count).name,
            "by_tag": self._count_by_tag(),
        }

    def _count_by_tag(self) -> Dict[str, int]:
        """Count capabilities by tag."""
        counts: Dict[str, int] = {}
        for cap in self.capabilities.values():
            for tag in cap.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return counts
