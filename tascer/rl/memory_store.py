"""AB Memory integration for RL training.

Stores and retrieves:
- Successful solutions for similar problems
- (state, action, reward) tuples for experience replay
- Error patterns and their fixes
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Try to import AB Memory
try:
    from ab import ABMemory, Buffer
    HAS_AB = True
except ImportError:
    HAS_AB = False


@dataclass
class Experience:
    """A single (state, action, reward, next_state) experience."""
    
    problem_id: str
    state_hash: str
    action: str
    reward: float
    next_state_hash: str
    done: bool
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "state_hash": self.state_hash,
            "action": self.action,
            "reward": self.reward,
            "next_state_hash": self.next_state_hash,
            "done": self.done,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Solution:
    """A successful solution to a problem."""
    
    problem_id: str
    code: str
    language: str
    answer: str
    duration_ms: float
    iterations: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "language": self.language,
            "answer": self.answer,
            "duration_ms": self.duration_ms,
            "iterations": self.iterations,
            "timestamp": self.timestamp.isoformat(),
        }


class MemoryStore:
    """Store for RL experiences and solutions.
    
    Integrates with AB Memory for persistent, searchable storage.
    Falls back to in-memory storage if AB is not available.
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        max_experiences: int = 10000,
    ):
        self.max_experiences = max_experiences
        
        # Try AB Memory
        if HAS_AB and db_path:
            self.ab = ABMemory(db_path)
            self._use_ab = True
        else:
            self.ab = None
            self._use_ab = False
        
        # In-memory fallback
        self._experiences: List[Experience] = []
        self._solutions: Dict[str, List[Solution]] = {}
        self._error_patterns: Dict[str, List[str]] = {}  # error_hash -> fixes
    
    def store_experience(self, exp: Experience) -> None:
        """Store an experience for replay."""
        if self._use_ab:
            self.ab.store_card(
                label="rl_experience",
                buffers=[
                    Buffer(
                        name="data",
                        payload=str(exp.to_dict()).encode(),
                        headers={
                            "problem_id": exp.problem_id,
                            "reward": str(exp.reward),
                        },
                    )
                ],
            )
        else:
            self._experiences.append(exp)
            # Trim if over limit
            if len(self._experiences) > self.max_experiences:
                self._experiences = self._experiences[-self.max_experiences:]
    
    def store_solution(self, sol: Solution) -> None:
        """Store a successful solution."""
        if self._use_ab:
            self.ab.store_card(
                label="solution",
                buffers=[
                    Buffer(
                        name="code",
                        payload=sol.code.encode(),
                        headers={
                            "problem_id": sol.problem_id,
                            "language": sol.language,
                            "answer": sol.answer,
                        },
                    )
                ],
            )
        else:
            if sol.problem_id not in self._solutions:
                self._solutions[sol.problem_id] = []
            self._solutions[sol.problem_id].append(sol)
    
    def store_error_fix(self, error: str, fix: str) -> None:
        """Store an error pattern and its fix."""
        error_hash = hashlib.md5(error.encode()).hexdigest()[:8]
        
        if self._use_ab:
            self.ab.store_card(
                label="error_fix",
                buffers=[
                    Buffer(
                        name="pattern",
                        payload=f"{error}\n---\n{fix}".encode(),
                        headers={"error_hash": error_hash},
                    )
                ],
            )
        else:
            if error_hash not in self._error_patterns:
                self._error_patterns[error_hash] = []
            self._error_patterns[error_hash].append(fix)
    
    def get_solutions(self, problem_id: str) -> List[Solution]:
        """Get stored solutions for a problem."""
        if self._use_ab:
            # Search AB Memory
            # For now, return empty - would need semantic search
            return []
        else:
            return self._solutions.get(problem_id, [])
    
    def sample_experiences(
        self,
        batch_size: int = 32,
        problem_id: Optional[str] = None,
    ) -> List[Experience]:
        """Sample experiences for replay."""
        import random
        
        if self._use_ab:
            # Would need to implement proper sampling from AB
            return []
        else:
            pool = self._experiences
            if problem_id:
                pool = [e for e in pool if e.problem_id == problem_id]
            
            if len(pool) <= batch_size:
                return pool
            
            return random.sample(pool, batch_size)
    
    def get_similar_problems(
        self,
        problem_description: str,
        top_k: int = 5,
    ) -> List[str]:
        """Find similar problems using semantic search.
        
        Returns problem IDs of similar solved problems.
        """
        if self._use_ab:
            try:
                from ab import semantic_search
                results = semantic_search(self.ab, problem_description, top_k=top_k)
                return [r.card_id for r in results if r.label == "solution"]
            except Exception:
                return []
        return []
    
    def get_error_fixes(self, error: str) -> List[str]:
        """Get known fixes for an error pattern."""
        error_hash = hashlib.md5(error.encode()).hexdigest()[:8]
        
        if self._use_ab:
            # Would search AB
            return []
        else:
            return self._error_patterns.get(error_hash, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        return {
            "experiences": len(self._experiences),
            "solutions": sum(len(s) for s in self._solutions.values()),
            "problems_solved": len(self._solutions),
            "error_patterns": len(self._error_patterns),
            "using_ab": self._use_ab,
        }
    
    def clear(self) -> None:
        """Clear all stored data."""
        self._experiences.clear()
        self._solutions.clear()
        self._error_patterns.clear()
