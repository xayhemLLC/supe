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
from .awareness import (  # noqa: F401
    create_awareness_card,
    subscribe_to_awareness,
    update_awareness_buffer,
)
from .benchmark import Benchmark, run_benchmarks, time_operation  # noqa: F401
from .debug import (  # noqa: F401
    Colors,
    DebugPrinter,
    MemoryInspector,
    trace,
    visualize_buffer,
    visualize_card,
)
from .decay import apply_decay_to_all, decay_formula, get_stale_cards  # noqa: F401
from .models import Buffer, Card, CardStats, Moment  # noqa: F401
from .moment_ledger import (  # noqa: F401
    get_moments_between,
    group_moments_by_day,
    group_moments_by_week,
    paginate_moments,
)
from .overlord import Overlord  # noqa: F401
from .rfs_recall import (  # noqa: F401
    attention_jump,
    build_recall_chain,
    get_connection_graph,
    rfs_recall,
)
from .search import search_cards, search_payload_keyword  # noqa: F401
from .self_agent import (  # noqa: F401
    ArchitectSelf,
    ExecutorSelf,
    PlannerSelf,
    Proposal,
    Self,
    SelfRegistry,
    self_registry,
)
from .subselves import LaneManager, propagate_subscriptions  # noqa: F401
from .transforms import TransformRegistry, apply_transform  # noqa: F401
from .transforms import registry as transform_registry  # noqa: F401
from .vector_search import (  # noqa: F401
    cosine_similarity,
    embed_text,
    find_similar_cards,
    semantic_search,
)
