"""AB core memory engine implementation.

This package provides a self-contained implementation of the AB
memory engine using only Python's standard library. The goal is to
mirror the structural concepts described in the AB FAQ—moments,
cards, and buffers—while persisting all state in a local SQLite
database. No external services or databases are required.

Key components:

* ``models``: Data classes representing Moments, Cards, Buffers and CardStats.
* ``abdb``: A high-level wrapper around ``sqlite3`` that manages
  moments, cards and buffer storage. It provides a simple API to
  create moments, store cards with buffers, and retrieve them.
* ``transforms``: Transform registry and execution engine for buffer payloads.
* ``decay``: Time-based memory decay utilities.
* ``self_agent``: Formal Self class with think() interface.
* ``rfs_recall``: Recursive Feature Similarity recall with multi-hop traversal.
* ``vector_search``: Semantic search using bag-of-words similarity.
* ``debug``: Colored output, card visualization, and tracing utilities.
* ``benchmark``: Performance benchmarking tools.
"""

from .abdb import ABMemory  # noqa: F401
from .models import Moment, Card, Buffer, CardStats  # noqa: F401
from .moment_ledger import get_moments_between, paginate_moments, group_moments_by_day, group_moments_by_week  # noqa: F401
from .subselves import LaneManager, propagate_subscriptions  # noqa: F401
from .overlord import Overlord  # noqa: F401
from .search import search_cards, search_payload_keyword  # noqa: F401
from .awareness import create_awareness_card, subscribe_to_awareness, update_awareness_buffer  # noqa: F401
from .transforms import TransformRegistry, registry as transform_registry, apply_transform  # noqa: F401
from .decay import decay_formula, apply_decay_to_all, get_stale_cards  # noqa: F401
from .self_agent import Self, Proposal, PlannerSelf, ArchitectSelf, ExecutorSelf, SelfRegistry, self_registry  # noqa: F401
from .rfs_recall import rfs_recall, attention_jump, build_recall_chain, get_connection_graph  # noqa: F401
from .vector_search import semantic_search, find_similar_cards, embed_text, cosine_similarity  # noqa: F401
from .debug import DebugPrinter, MemoryInspector, Colors, trace, visualize_card, visualize_buffer  # noqa: F401
from .benchmark import Benchmark, run_benchmarks, time_operation  # noqa: F401