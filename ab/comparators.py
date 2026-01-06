"""Universal Buffer Comparators for Tree-Web Memory.

Buffers are generic containers with:
- name: identifier
- payload: raw bytes (can be any data type)
- headers: metadata dict
- exe: optional transform rule

This module provides universal comparison functions that work with any buffer type:
- Text/string comparison (contains, regex, fuzzy)
- Numeric comparison (eq, gt, lt, range)
- Binary comparison (hash, bytes match)
- JSON/structured comparison (jsonpath, key exists)
- List/set comparison (contains, overlap, subset)
- Temporal comparison (before, after, range)
- Semantic comparison (embedding similarity)

Comparators are composable and can be chained with AND/OR logic.
"""

import hashlib
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class CompareOp(Enum):
    """Comparison operators."""
    # Equality
    EQ = "eq"           # Equal
    NE = "ne"           # Not equal

    # Numeric
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    BETWEEN = "between" # Between two values

    # Text
    CONTAINS = "contains"     # Substring match
    STARTS_WITH = "starts"    # Prefix match
    ENDS_WITH = "ends"        # Suffix match
    REGEX = "regex"           # Regex pattern
    FUZZY = "fuzzy"           # Fuzzy/approximate match

    # Collection
    IN = "in"                 # Value in list
    NOT_IN = "not_in"         # Value not in list
    OVERLAPS = "overlaps"     # Sets have common elements
    SUBSET = "subset"         # Is subset of
    SUPERSET = "superset"     # Is superset of

    # Existence
    EXISTS = "exists"         # Buffer exists and has value
    NOT_EXISTS = "not_exists" # Buffer doesn't exist or is empty
    IS_NULL = "is_null"       # Value is None
    NOT_NULL = "not_null"     # Value is not None

    # Semantic
    SIMILAR = "similar"       # Embedding similarity above threshold

    # Binary
    HASH_EQ = "hash_eq"       # SHA256 hash equals


@dataclass
class CompareResult:
    """Result of a comparison operation."""
    matched: bool
    score: float = 1.0      # 0.0-1.0, for ranking
    reason: str = ""        # Human-readable explanation
    metadata: Dict[str, Any] = field(default_factory=dict)


class BufferComparator(ABC):
    """Abstract base for buffer comparators."""

    @abstractmethod
    def compare(self, value: Any) -> CompareResult:
        """Compare a buffer value against this comparator's criteria."""
        pass

    @abstractmethod
    def describe(self) -> str:
        """Human-readable description of this comparator."""
        pass


# =============================================================================
# Value Extraction (handle different buffer payload types)
# =============================================================================

def extract_value(payload: Any, headers: Dict = None) -> Any:
    """Extract comparable value from buffer payload.

    Handles:
    - bytes → decode to string or keep as bytes
    - JSON string → parse to dict/list
    - Already decoded values → pass through

    Args:
        payload: Raw buffer payload
        headers: Buffer headers (may contain type hints)

    Returns:
        Extracted value ready for comparison.
    """
    headers = headers or {}

    # If payload is bytes, try to decode
    if isinstance(payload, bytes):
        # Check if headers specify encoding
        encoding = headers.get("encoding", "utf-8")
        content_type = headers.get("content_type", "")

        try:
            decoded = payload.decode(encoding)

            # If JSON content type, parse it
            if "json" in content_type.lower() or decoded.startswith(("{", "[")):
                try:
                    return json.loads(decoded)
                except json.JSONDecodeError:
                    pass

            return decoded
        except UnicodeDecodeError:
            # Keep as bytes for binary comparison
            return payload

    # If string that looks like JSON, parse it
    if isinstance(payload, str):
        if payload.startswith(("{", "[")):
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                pass

    return payload


def extract_text(value: Any) -> str:
    """Convert any value to searchable text."""
    if value is None:
        return ""

    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="ignore")
        except:
            return ""

    if isinstance(value, (list, tuple)):
        return " ".join(extract_text(v) for v in value)

    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            parts.append(f"{k}: {extract_text(v)}")
        return " ".join(parts)

    return str(value)


def extract_words(value: Any, min_length: int = 3) -> Set[str]:
    """Extract significant words from any value."""
    text = extract_text(value).lower()

    # Stopwords to filter
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "this", "that", "these", "those", "it", "its", "they", "we", "you",
    }

    # Extract alphanumeric tokens
    tokens = re.findall(r'[a-z0-9_-]+', text)

    return {t for t in tokens if len(t) >= min_length and t not in stopwords}


# =============================================================================
# Concrete Comparators
# =============================================================================

@dataclass
class TextComparator(BufferComparator):
    """Compare text/string values."""
    op: CompareOp
    value: str
    case_sensitive: bool = False

    def compare(self, buffer_value: Any) -> CompareResult:
        text = extract_text(buffer_value)
        compare_text = text if self.case_sensitive else text.lower()
        compare_value = self.value if self.case_sensitive else self.value.lower()

        if self.op == CompareOp.EQ:
            matched = compare_text == compare_value
        elif self.op == CompareOp.NE:
            matched = compare_text != compare_value
        elif self.op == CompareOp.CONTAINS:
            matched = compare_value in compare_text
        elif self.op == CompareOp.STARTS_WITH:
            matched = compare_text.startswith(compare_value)
        elif self.op == CompareOp.ENDS_WITH:
            matched = compare_text.endswith(compare_value)
        elif self.op == CompareOp.REGEX:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            matched = bool(re.search(self.value, text, flags))
        elif self.op == CompareOp.FUZZY:
            # Simple fuzzy: check if most words match
            query_words = set(compare_value.split())
            text_words = set(compare_text.split())
            overlap = len(query_words & text_words)
            matched = overlap >= len(query_words) * 0.6
        else:
            matched = False

        score = 1.0 if matched else 0.0
        return CompareResult(matched=matched, score=score, reason=f"{self.op.value}: {self.value}")

    def describe(self) -> str:
        return f"text {self.op.value} '{self.value}'"


@dataclass
class NumericComparator(BufferComparator):
    """Compare numeric values."""
    op: CompareOp
    value: Union[float, int]
    value2: Optional[Union[float, int]] = None  # For BETWEEN

    def compare(self, buffer_value: Any) -> CompareResult:
        try:
            num = float(extract_text(buffer_value))
        except (ValueError, TypeError):
            return CompareResult(matched=False, score=0.0, reason="Not a number")

        if self.op == CompareOp.EQ:
            matched = num == self.value
        elif self.op == CompareOp.NE:
            matched = num != self.value
        elif self.op == CompareOp.GT:
            matched = num > self.value
        elif self.op == CompareOp.GTE:
            matched = num >= self.value
        elif self.op == CompareOp.LT:
            matched = num < self.value
        elif self.op == CompareOp.LTE:
            matched = num <= self.value
        elif self.op == CompareOp.BETWEEN:
            if self.value2 is None:
                return CompareResult(matched=False, reason="BETWEEN requires value2")
            matched = self.value <= num <= self.value2
        else:
            matched = False

        return CompareResult(matched=matched, score=1.0 if matched else 0.0)

    def describe(self) -> str:
        if self.op == CompareOp.BETWEEN:
            return f"number between {self.value} and {self.value2}"
        return f"number {self.op.value} {self.value}"


@dataclass
class TemporalComparator(BufferComparator):
    """Compare timestamp/datetime values."""
    op: CompareOp
    value: Union[datetime, int, str]  # datetime, epoch ms, or ISO string
    value2: Optional[Union[datetime, int, str]] = None  # For BETWEEN

    def _parse_datetime(self, v: Any) -> Optional[datetime]:
        """Parse various datetime formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, (int, float)):
            # Assume epoch milliseconds
            return datetime.fromtimestamp(v / 1000)
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                pass
        return None

    def compare(self, buffer_value: Any) -> CompareResult:
        dt = self._parse_datetime(buffer_value)
        if dt is None:
            return CompareResult(matched=False, reason="Cannot parse datetime")

        target = self._parse_datetime(self.value)
        if target is None:
            return CompareResult(matched=False, reason="Invalid comparison value")

        if self.op == CompareOp.EQ:
            matched = dt == target
        elif self.op == CompareOp.GT:
            matched = dt > target
        elif self.op == CompareOp.GTE:
            matched = dt >= target
        elif self.op == CompareOp.LT:
            matched = dt < target
        elif self.op == CompareOp.LTE:
            matched = dt <= target
        elif self.op == CompareOp.BETWEEN:
            target2 = self._parse_datetime(self.value2)
            if target2 is None:
                return CompareResult(matched=False, reason="Invalid range end")
            matched = target <= dt <= target2
        else:
            matched = False

        return CompareResult(matched=matched, score=1.0 if matched else 0.0)

    def describe(self) -> str:
        return f"time {self.op.value} {self.value}"


@dataclass
class CollectionComparator(BufferComparator):
    """Compare collections (lists, sets)."""
    op: CompareOp
    values: List[Any]

    def compare(self, buffer_value: Any) -> CompareResult:
        # Extract as set for comparison
        if isinstance(buffer_value, (list, tuple, set)):
            buffer_set = set(buffer_value)
        elif isinstance(buffer_value, str):
            # Try JSON parse
            try:
                parsed = json.loads(buffer_value)
                if isinstance(parsed, list):
                    buffer_set = set(parsed)
                else:
                    buffer_set = {buffer_value}
            except:
                buffer_set = {buffer_value}
        else:
            buffer_set = {buffer_value}

        target_set = set(self.values)

        if self.op == CompareOp.IN:
            # buffer_value is in target list
            matched = len(buffer_set & target_set) > 0
        elif self.op == CompareOp.NOT_IN:
            matched = len(buffer_set & target_set) == 0
        elif self.op == CompareOp.OVERLAPS:
            matched = len(buffer_set & target_set) > 0
        elif self.op == CompareOp.SUBSET:
            matched = buffer_set.issubset(target_set)
        elif self.op == CompareOp.SUPERSET:
            matched = buffer_set.issuperset(target_set)
        else:
            matched = False

        # Score based on overlap
        if target_set:
            overlap = len(buffer_set & target_set) / len(target_set)
        else:
            overlap = 0.0

        return CompareResult(matched=matched, score=overlap if matched else 0.0)

    def describe(self) -> str:
        return f"collection {self.op.value} {self.values[:3]}..."


@dataclass
class ExistenceComparator(BufferComparator):
    """Check existence/nullness of buffer values."""
    op: CompareOp

    def compare(self, buffer_value: Any) -> CompareResult:
        is_empty = buffer_value is None or buffer_value == "" or buffer_value == b""

        if self.op == CompareOp.EXISTS:
            matched = not is_empty
        elif self.op == CompareOp.NOT_EXISTS:
            matched = is_empty
        elif self.op == CompareOp.IS_NULL:
            matched = buffer_value is None
        elif self.op == CompareOp.NOT_NULL:
            matched = buffer_value is not None
        else:
            matched = False

        return CompareResult(matched=matched, score=1.0 if matched else 0.0)

    def describe(self) -> str:
        return f"value {self.op.value}"


@dataclass
class HashComparator(BufferComparator):
    """Compare binary content by hash."""
    expected_hash: str
    algorithm: str = "sha256"

    def compare(self, buffer_value: Any) -> CompareResult:
        if isinstance(buffer_value, str):
            data = buffer_value.encode()
        elif isinstance(buffer_value, bytes):
            data = buffer_value
        else:
            data = str(buffer_value).encode()

        if self.algorithm == "sha256":
            computed = hashlib.sha256(data).hexdigest()
        elif self.algorithm == "md5":
            computed = hashlib.md5(data).hexdigest()
        else:
            return CompareResult(matched=False, reason=f"Unknown algorithm: {self.algorithm}")

        matched = computed == self.expected_hash
        return CompareResult(
            matched=matched,
            score=1.0 if matched else 0.0,
            metadata={"computed_hash": computed}
        )

    def describe(self) -> str:
        return f"hash({self.algorithm}) == {self.expected_hash[:16]}..."


@dataclass
class SemanticComparator(BufferComparator):
    """Compare by embedding similarity."""
    embedding: List[float]
    threshold: float = 0.8

    def compare(self, buffer_value: Any) -> CompareResult:
        # Expect buffer_value to be an embedding vector
        if not isinstance(buffer_value, (list, tuple)):
            return CompareResult(matched=False, reason="Not an embedding vector")

        if len(buffer_value) != len(self.embedding):
            return CompareResult(matched=False, reason="Embedding dimension mismatch")

        # Cosine similarity
        dot = sum(a * b for a, b in zip(self.embedding, buffer_value))
        norm_a = sum(x * x for x in self.embedding) ** 0.5
        norm_b = sum(x * x for x in buffer_value) ** 0.5

        if norm_a == 0 or norm_b == 0:
            similarity = 0.0
        else:
            similarity = dot / (norm_a * norm_b)

        matched = similarity >= self.threshold
        return CompareResult(
            matched=matched,
            score=similarity,
            metadata={"similarity": similarity}
        )

    def describe(self) -> str:
        return f"semantic similarity >= {self.threshold}"


@dataclass
class WordOverlapComparator(BufferComparator):
    """Compare by shared significant words."""
    words: Set[str]
    min_overlap: int = 2

    def compare(self, buffer_value: Any) -> CompareResult:
        buffer_words = extract_words(buffer_value)
        shared = self.words & buffer_words

        matched = len(shared) >= self.min_overlap

        # Score based on Jaccard similarity
        union = self.words | buffer_words
        score = len(shared) / len(union) if union else 0.0

        return CompareResult(
            matched=matched,
            score=score,
            metadata={"shared_words": list(shared), "shared_count": len(shared)}
        )

    def describe(self) -> str:
        return f"word overlap >= {self.min_overlap} with {list(self.words)[:3]}..."


@dataclass
class JSONPathComparator(BufferComparator):
    """Compare by JSONPath expression."""
    path: str  # e.g., "$.status" or "$.data[0].name"
    op: CompareOp
    value: Any

    def _extract_jsonpath(self, data: Any, path: str) -> Any:
        """Simple JSONPath extraction (supports $.key and $.key[index])."""
        if not path.startswith("$."):
            return None

        parts = path[2:].split(".")
        current = data

        for part in parts:
            if current is None:
                return None

            # Handle array index
            match = re.match(r'(\w+)\[(\d+)\]', part)
            if match:
                key, idx = match.groups()
                if isinstance(current, dict) and key in current:
                    current = current[key]
                    if isinstance(current, list) and int(idx) < len(current):
                        current = current[int(idx)]
                    else:
                        return None
                else:
                    return None
            else:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

        return current

    def compare(self, buffer_value: Any) -> CompareResult:
        # Parse JSON if needed
        if isinstance(buffer_value, str):
            try:
                data = json.loads(buffer_value)
            except:
                return CompareResult(matched=False, reason="Cannot parse JSON")
        else:
            data = buffer_value

        extracted = self._extract_jsonpath(data, self.path)

        if self.op == CompareOp.EXISTS:
            matched = extracted is not None
        elif self.op == CompareOp.EQ:
            matched = extracted == self.value
        elif self.op == CompareOp.NE:
            matched = extracted != self.value
        elif self.op == CompareOp.CONTAINS:
            matched = self.value in str(extracted) if extracted else False
        else:
            # Delegate to appropriate comparator based on value type
            if isinstance(self.value, (int, float)):
                result = NumericComparator(self.op, self.value).compare(extracted)
                return result
            else:
                result = TextComparator(self.op, str(self.value)).compare(extracted)
                return result

        return CompareResult(matched=matched, score=1.0 if matched else 0.0)

    def describe(self) -> str:
        return f"jsonpath {self.path} {self.op.value} {self.value}"


# =============================================================================
# Composite Comparators
# =============================================================================

@dataclass
class AndComparator(BufferComparator):
    """All comparators must match."""
    comparators: List[BufferComparator]

    def compare(self, buffer_value: Any) -> CompareResult:
        results = [c.compare(buffer_value) for c in self.comparators]
        matched = all(r.matched for r in results)

        # Score is average of all scores
        score = sum(r.score for r in results) / len(results) if results else 0.0

        return CompareResult(
            matched=matched,
            score=score,
            reason=" AND ".join(r.reason for r in results if r.reason)
        )

    def describe(self) -> str:
        return " AND ".join(c.describe() for c in self.comparators)


@dataclass
class OrComparator(BufferComparator):
    """Any comparator can match."""
    comparators: List[BufferComparator]

    def compare(self, buffer_value: Any) -> CompareResult:
        results = [c.compare(buffer_value) for c in self.comparators]
        matched = any(r.matched for r in results)

        # Score is max of all scores
        score = max(r.score for r in results) if results else 0.0

        return CompareResult(
            matched=matched,
            score=score,
            reason=" OR ".join(r.reason for r in results if r.matched)
        )

    def describe(self) -> str:
        return " OR ".join(c.describe() for c in self.comparators)


@dataclass
class NotComparator(BufferComparator):
    """Negate a comparator."""
    comparator: BufferComparator

    def compare(self, buffer_value: Any) -> CompareResult:
        result = self.comparator.compare(buffer_value)
        return CompareResult(
            matched=not result.matched,
            score=1.0 - result.score,
            reason=f"NOT ({result.reason})"
        )

    def describe(self) -> str:
        return f"NOT ({self.comparator.describe()})"


# =============================================================================
# Filter Builder (fluent API)
# =============================================================================

class FilterBuilder:
    """Fluent API for building buffer filters."""

    def __init__(self, buffer_name: str):
        self.buffer_name = buffer_name
        self._comparators: List[BufferComparator] = []

    def eq(self, value: Any) -> "FilterBuilder":
        if isinstance(value, (int, float)):
            self._comparators.append(NumericComparator(CompareOp.EQ, value))
        else:
            self._comparators.append(TextComparator(CompareOp.EQ, str(value)))
        return self

    def contains(self, value: str, case_sensitive: bool = False) -> "FilterBuilder":
        self._comparators.append(TextComparator(CompareOp.CONTAINS, value, case_sensitive))
        return self

    def regex(self, pattern: str) -> "FilterBuilder":
        self._comparators.append(TextComparator(CompareOp.REGEX, pattern))
        return self

    def gt(self, value: Union[int, float]) -> "FilterBuilder":
        self._comparators.append(NumericComparator(CompareOp.GT, value))
        return self

    def lt(self, value: Union[int, float]) -> "FilterBuilder":
        self._comparators.append(NumericComparator(CompareOp.LT, value))
        return self

    def between(self, start: Any, end: Any) -> "FilterBuilder":
        if isinstance(start, datetime) or isinstance(end, datetime):
            self._comparators.append(TemporalComparator(CompareOp.BETWEEN, start, end))
        else:
            self._comparators.append(NumericComparator(CompareOp.BETWEEN, start, end))
        return self

    def in_list(self, values: List[Any]) -> "FilterBuilder":
        self._comparators.append(CollectionComparator(CompareOp.IN, values))
        return self

    def exists(self) -> "FilterBuilder":
        self._comparators.append(ExistenceComparator(CompareOp.EXISTS))
        return self

    def not_exists(self) -> "FilterBuilder":
        self._comparators.append(ExistenceComparator(CompareOp.NOT_EXISTS))
        return self

    def words_overlap(self, words: Set[str], min_overlap: int = 2) -> "FilterBuilder":
        self._comparators.append(WordOverlapComparator(words, min_overlap))
        return self

    def similar_to(self, embedding: List[float], threshold: float = 0.8) -> "FilterBuilder":
        self._comparators.append(SemanticComparator(embedding, threshold))
        return self

    def jsonpath(self, path: str, op: CompareOp, value: Any) -> "FilterBuilder":
        self._comparators.append(JSONPathComparator(path, op, value))
        return self

    def build(self) -> Tuple[str, BufferComparator]:
        """Build the final comparator."""
        if len(self._comparators) == 1:
            return self.buffer_name, self._comparators[0]
        else:
            return self.buffer_name, AndComparator(self._comparators)


def Filter(buffer_name: str) -> FilterBuilder:
    """Start building a filter for a buffer."""
    return FilterBuilder(buffer_name)


# =============================================================================
# Usage Examples
# =============================================================================

"""
# Simple filters
Filter("type").eq("feature")
Filter("title").contains("ComfyUI")
Filter("narrative").regex(r"error|bug|fix")
Filter("created_at").between(start_date, end_date)

# Numeric filters
Filter("recall_count").gt(5)
Filter("strength").between(0.5, 1.0)

# Collection filters
Filter("concepts").in_list(["how-it-works", "pattern"])
Filter("type").in_list(["feature", "bugfix"])

# Word overlap (for finding related cards)
Filter("title").words_overlap({"ComfyUI", "SDXL", "inpainting"}, min_overlap=2)

# JSON path filters
Filter("metadata").jsonpath("$.status", CompareOp.EQ, "success")
Filter("config").jsonpath("$.features[0].enabled", CompareOp.EQ, True)

# Semantic similarity
Filter("embedding").similar_to(query_embedding, threshold=0.85)

# Composite filters
AndComparator([
    Filter("project").eq("ComfyUI").build()[1],
    Filter("type").in_list(["feature", "discovery"]).build()[1],
    Filter("created_at").between(week_ago, now).build()[1],
])
"""
