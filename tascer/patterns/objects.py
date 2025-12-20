"""Pattern Objects - Templates for recurring behaviors.

Patterns are:
- Derived from exe ↔ moments comparison
- Stored in AB memory
- Retrievable by similarity
- Used to improve future decisions
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Pattern:
    """Base pattern object.
    
    Patterns capture recurring behaviors and can be matched
    against new situations for improved decision-making.
    """
    
    pattern_id: str
    pattern_type: str
    name: str
    description: str
    created_at: datetime
    occurrences: int = 1
    confidence: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "occurrences": self.occurrences,
            "confidence": self.confidence,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        return cls(
            pattern_id=data["pattern_id"],
            pattern_type=data["pattern_type"],
            name=data["name"],
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            occurrences=data.get("occurrences", 1),
            confidence=data.get("confidence", 0.5),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
    
    def increment_occurrence(self) -> None:
        """Record another occurrence of this pattern."""
        self.occurrences += 1
        # Confidence increases with occurrences (asymptotic to 1.0)
        self.confidence = min(0.95, 0.5 + (0.45 * (1 - 1 / (self.occurrences + 1))))


@dataclass
class FailurePattern(Pattern):
    """Pattern for recurring failures.
    
    Captures:
    - Error type and message patterns
    - Context conditions that lead to failure
    - Actions that triggered the failure
    """
    
    error_type: str = ""
    error_pattern: str = ""  # Regex or template
    trigger_actions: List[str] = field(default_factory=list)
    context_conditions: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.pattern_type = "failure"
    
    def matches(self, error_type: str, error_message: str) -> bool:
        """Check if an error matches this pattern."""
        import re
        if self.error_type and self.error_type != error_type:
            return False
        if self.error_pattern:
            return bool(re.search(self.error_pattern, error_message, re.IGNORECASE))
        return True


@dataclass
class FixPattern(Pattern):
    """Pattern for successful fixes.
    
    Captures:
    - What problem was fixed
    - What actions led to the fix
    - What evidence confirmed success
    """
    
    problem_signature: str = ""  # How to recognize the problem
    fix_actions: List[str] = field(default_factory=list)
    success_evidence: List[str] = field(default_factory=list)
    failure_pattern_ref: Optional[str] = None  # Links to FailurePattern
    
    def __post_init__(self):
        self.pattern_type = "fix"


@dataclass
class DecisionPattern(Pattern):
    """Pattern for recurring decision points.
    
    Captures:
    - When to make this type of decision
    - What alternatives were considered
    - What the typical best choice is
    """
    
    decision_trigger: str = ""  # Condition that triggers this decision
    alternatives: List[str] = field(default_factory=list)
    typical_choice: str = ""
    success_rate: float = 0.0
    
    def __post_init__(self):
        self.pattern_type = "decision"


@dataclass
class FrontendPattern(Pattern):
    """Pattern for frontend/UI behaviors.
    
    Captures:
    - UI state transitions
    - User interaction patterns
    - Expected vs actual behavior
    """
    
    framework: str = ""  # react, vue, svelte, etc.
    component_path: str = ""
    state_before: Dict[str, Any] = field(default_factory=dict)
    state_after: Dict[str, Any] = field(default_factory=dict)
    interaction: str = ""  # What triggered the change
    
    def __post_init__(self):
        self.pattern_type = "frontend"


class PatternStore:
    """Store and retrieve patterns.
    
    Provides:
    - Pattern storage and indexing
    - Similarity-based retrieval
    - Pattern merging when duplicates found
    """
    
    def __init__(self):
        self._patterns: Dict[str, Pattern] = {}
        self._by_type: Dict[str, List[str]] = {}
        self._by_tag: Dict[str, List[str]] = {}
    
    def add(self, pattern: Pattern) -> None:
        """Add a pattern to the store."""
        self._patterns[pattern.pattern_id] = pattern
        
        # Index by type
        if pattern.pattern_type not in self._by_type:
            self._by_type[pattern.pattern_type] = []
        self._by_type[pattern.pattern_type].append(pattern.pattern_id)
        
        # Index by tags
        for tag in pattern.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(pattern.pattern_id)
    
    def get(self, pattern_id: str) -> Optional[Pattern]:
        """Get pattern by ID."""
        return self._patterns.get(pattern_id)
    
    def get_by_type(self, pattern_type: str) -> List[Pattern]:
        """Get all patterns of a type."""
        ids = self._by_type.get(pattern_type, [])
        return [self._patterns[pid] for pid in ids if pid in self._patterns]
    
    def get_by_tag(self, tag: str) -> List[Pattern]:
        """Get all patterns with a tag."""
        ids = self._by_tag.get(tag, [])
        return [self._patterns[pid] for pid in ids if pid in self._patterns]
    
    def find_similar(
        self,
        pattern: Pattern,
        threshold: float = 0.7,
    ) -> List[tuple[Pattern, float]]:
        """Find patterns similar to the given one.
        
        Args:
            pattern: Pattern to match against.
            threshold: Minimum similarity score.
        
        Returns:
            List of (pattern, similarity) tuples.
        """
        similar = []
        
        for stored in self._patterns.values():
            if stored.pattern_id == pattern.pattern_id:
                continue
            
            score = self._compute_similarity(pattern, stored)
            if score >= threshold:
                similar.append((stored, score))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)
    
    def _compute_similarity(self, p1: Pattern, p2: Pattern) -> float:
        """Compute similarity between two patterns."""
        score = 0.0
        factors = 0
        
        # Type match
        if p1.pattern_type == p2.pattern_type:
            score += 0.3
        factors += 0.3
        
        # Tag overlap
        if p1.tags and p2.tags:
            overlap = set(p1.tags) & set(p2.tags)
            union = set(p1.tags) | set(p2.tags)
            if union:
                score += 0.3 * (len(overlap) / len(union))
        factors += 0.3
        
        # Name similarity (simple)
        name_words_1 = set(p1.name.lower().split())
        name_words_2 = set(p2.name.lower().split())
        if name_words_1 and name_words_2:
            overlap = name_words_1 & name_words_2
            union = name_words_1 | name_words_2
            score += 0.4 * (len(overlap) / len(union))
        factors += 0.4
        
        return score / factors if factors > 0 else 0.0
    
    def merge_similar(self, pattern: Pattern) -> Optional[Pattern]:
        """Find and merge with similar pattern if exists.
        
        Returns the merged pattern, or None if no merge occurred.
        """
        similar = self.find_similar(pattern, threshold=0.85)
        if similar:
            existing, score = similar[0]
            existing.increment_occurrence()
            # Merge metadata
            existing.metadata.update(pattern.metadata)
            # Add new tags
            existing.tags = list(set(existing.tags) | set(pattern.tags))
            return existing
        return None
    
    def add_or_merge(self, pattern: Pattern) -> Pattern:
        """Add pattern, merging if similar exists."""
        merged = self.merge_similar(pattern)
        if merged:
            return merged
        self.add(pattern)
        return pattern
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize store to dictionary."""
        return {
            "patterns": {pid: p.to_dict() for pid, p in self._patterns.items()},
        }
    
    def __len__(self) -> int:
        return len(self._patterns)


def create_pattern_id(pattern_type: str, name: str) -> str:
    """Generate a pattern ID."""
    content = f"{pattern_type}:{name}:{datetime.now().isoformat()}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]
