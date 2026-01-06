"""Buffer handling with proper text normalization.

Buffers can contain any type of data:
- Plain text (may contain newlines, markdown, etc.)
- JSON arrays (facts, concepts)
- JSON objects (structured data)
- Numbers, booleans, etc.

This module ensures all buffer types are properly handled for:
- Storage (preserving structure)
- Search (normalizing for comparison)
- Display (formatting for output)
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union


@dataclass
class BufferValue:
    """A normalized buffer value with metadata."""
    raw: Any                    # Original value as stored
    text: str                   # Normalized text for search
    words: Set[str]             # Extracted words for matching
    lines: List[str]            # Lines (preserving structure)
    is_json: bool = False       # Was parsed from JSON
    is_list: bool = False       # Is a list/array

    @classmethod
    def from_raw(cls, value: Any, min_word_len: int = 3) -> "BufferValue":
        """Create BufferValue from any raw input."""
        if value is None:
            return cls(raw=None, text="", words=set(), lines=[])

        # Try to parse JSON if string looks like JSON
        parsed = value
        is_json = False
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith(('[', '{')):
                try:
                    parsed = json.loads(value)
                    is_json = True
                except json.JSONDecodeError:
                    pass

        # Extract text representation
        text = cls._extract_text(parsed)

        # Extract lines (preserving newlines)
        lines = cls._extract_lines(parsed)

        # Extract words
        words = cls._extract_words(text, min_word_len)

        return cls(
            raw=value,
            text=text,
            words=words,
            lines=lines,
            is_json=is_json,
            is_list=isinstance(parsed, list),
        )

    @staticmethod
    def _extract_text(value: Any) -> str:
        """Extract searchable text from any value."""
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        if isinstance(value, (int, float, bool)):
            return str(value)

        if isinstance(value, list):
            # Join list items with newlines to preserve structure
            parts = []
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    # Extract values from dict
                    parts.extend(str(v) for v in item.values() if v)
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        if isinstance(value, dict):
            # Extract all string values
            parts = []
            for v in value.values():
                if isinstance(v, str):
                    parts.append(v)
                elif v is not None:
                    parts.append(str(v))
            return "\n".join(parts)

        return str(value)

    @staticmethod
    def _extract_lines(value: Any) -> List[str]:
        """Extract lines preserving structure."""
        if value is None:
            return []

        if isinstance(value, str):
            return value.split('\n')

        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, str):
                    lines.extend(item.split('\n'))
                else:
                    lines.append(str(item))
            return lines

        if isinstance(value, dict):
            return [f"{k}: {v}" for k, v in value.items() if v]

        return [str(value)]

    @staticmethod
    def _extract_words(text: str, min_len: int = 3) -> Set[str]:
        """Extract significant words for matching."""
        if not text:
            return set()

        # Tokenize
        words = re.findall(r'[a-zA-Z][a-zA-Z0-9_]*', text.lower())

        # Filter by length and common stopwords
        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'her', 'was', 'one', 'our', 'out', 'has', 'have',
            'been', 'this', 'that', 'with', 'they', 'from', 'will',
            'would', 'there', 'their', 'what', 'about', 'which',
            'when', 'make', 'like', 'into', 'just', 'over', 'such',
        }

        return {w for w in words if len(w) >= min_len and w not in stopwords}


class BufferStore:
    """Manages a collection of buffers for a card."""

    def __init__(self, raw_buffers: Dict[str, Any] = None):
        self._raw: Dict[str, Any] = raw_buffers or {}
        self._normalized: Dict[str, BufferValue] = {}

        # Normalize all buffers
        for name, value in self._raw.items():
            self._normalized[name] = BufferValue.from_raw(value)

    def get_raw(self, name: str) -> Any:
        """Get raw buffer value."""
        return self._raw.get(name)

    def get_text(self, name: str) -> str:
        """Get normalized text for a buffer."""
        if name in self._normalized:
            return self._normalized[name].text
        return ""

    def get_words(self, name: str) -> Set[str]:
        """Get extracted words from a buffer."""
        if name in self._normalized:
            return self._normalized[name].words
        return set()

    def get_lines(self, name: str) -> List[str]:
        """Get lines from a buffer."""
        if name in self._normalized:
            return self._normalized[name].lines
        return []

    def all_text(self) -> str:
        """Get all text from all buffers concatenated."""
        parts = []
        for bv in self._normalized.values():
            if bv.text:
                parts.append(bv.text)
        return "\n".join(parts)

    def all_words(self) -> Set[str]:
        """Get all words from all buffers."""
        words = set()
        for bv in self._normalized.values():
            words.update(bv.words)
        return words

    def search(self, query: str, buffer_names: List[str] = None) -> float:
        """Search buffers and return relevance score (0-1)."""
        query_words = BufferValue._extract_words(query.lower())
        if not query_words:
            return 0.0

        # Get words to search
        if buffer_names:
            search_words = set()
            for name in buffer_names:
                search_words.update(self.get_words(name))
        else:
            search_words = self.all_words()

        if not search_words:
            return 0.0

        # Calculate Jaccard-like similarity
        matches = query_words & search_words
        if not matches:
            return 0.0

        return len(matches) / len(query_words)

    def contains(self, text: str, buffer_name: str = None) -> bool:
        """Check if text is contained in buffer(s)."""
        text_lower = text.lower()

        if buffer_name:
            return text_lower in self.get_text(buffer_name).lower()

        return text_lower in self.all_text().lower()

    def matches_regex(self, pattern: str, buffer_name: str = None) -> bool:
        """Check if pattern matches buffer(s)."""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return False

        if buffer_name:
            return bool(regex.search(self.get_text(buffer_name)))

        return bool(regex.search(self.all_text()))

    def to_dict(self) -> Dict[str, Any]:
        """Export raw buffers as dict."""
        return dict(self._raw)

    def __repr__(self) -> str:
        return f"BufferStore({list(self._raw.keys())})"


def normalize_observation(obs: Dict[str, Any]) -> Dict[str, BufferValue]:
    """Normalize a claude-mem observation into BufferValues."""
    result = {}

    # Standard fields
    for field in ['title', 'subtitle', 'narrative', 'type', 'project']:
        if field in obs and obs[field]:
            result[field] = BufferValue.from_raw(obs[field])

    # JSON fields (facts, concepts)
    for field in ['facts', 'concepts']:
        if field in obs and obs[field]:
            value = obs[field]
            # Parse if string
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
            result[field] = BufferValue.from_raw(value)

    # Timestamp
    if 'created_at' in obs:
        result['created_at'] = BufferValue.from_raw(obs['created_at'])

    return result
