"""Benchmarking utilities for AB memory operations.

This module provides tools for measuring the performance of recall,
search, indexing, and traversal operations. It includes utilities
for loading public datasets and generating benchmark reports.

Usage:
    from ab.benchmark import Benchmark, load_wikipedia_sample
    
    # Load sample data
    memory = ABMemory(":memory:")
    load_wikipedia_sample(memory, n=100)
    
    # Run benchmarks
    bench = Benchmark(memory)
    results = bench.run_all()
    bench.print_report(results)
"""

from __future__ import annotations

import json
import random
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .abdb import ABMemory

from .models import Buffer
from .debug import Colors, colored


# ---------------------------------------------------------------------------
# Timing Utilities
# ---------------------------------------------------------------------------

@dataclass
class TimingResult:
    """Result of a timed operation."""
    name: str
    iterations: int
    total_ms: float
    min_ms: float
    max_ms: float
    avg_ms: float
    ops_per_sec: float
    metadata: Dict[str, Any] = field(default_factory=dict)


def time_operation(
    name: str,
    func: Callable,
    iterations: int = 100,
    warmup: int = 5,
    **metadata
) -> TimingResult:
    """Time an operation over multiple iterations.
    
    Args:
        name: Name of the operation.
        func: Function to time (takes no arguments).
        iterations: Number of iterations to run.
        warmup: Number of warmup iterations (not counted).
        **metadata: Additional metadata to include in result.
    
    Returns:
        TimingResult with statistics.
    """
    # Warmup
    for _ in range(warmup):
        func()
    
    # Timed runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)
    
    total = sum(times)
    avg = total / iterations
    ops_per_sec = 1000 / avg if avg > 0 else float('inf')
    
    return TimingResult(
        name=name,
        iterations=iterations,
        total_ms=total,
        min_ms=min(times),
        max_ms=max(times),
        avg_ms=avg,
        ops_per_sec=ops_per_sec,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Sample Data Loaders
# ---------------------------------------------------------------------------

# Sample news headlines for testing
SAMPLE_NEWS = [
    "Scientists discover new species in Amazon rainforest",
    "Stock market reaches all-time high amid economic optimism",
    "New AI model achieves breakthrough in language understanding",
    "Climate summit brings together world leaders for urgent talks",
    "Tech giant announces revolutionary smartphone with foldable display",
    "Medical researchers develop promising vaccine candidate",
    "Space agency reveals plans for Mars colony by 2040",
    "Electric vehicle sales surge as battery costs decline",
    "Cybersecurity experts warn of new phishing attack wave",
    "Renewable energy now cheaper than fossil fuels in most regions",
    "Gene therapy offers hope for rare genetic disorders",
    "Quantum computer solves problem in seconds that would take years",
    "Social media platform faces antitrust investigation",
    "Autonomous vehicles begin testing on public roads",
    "Neural implant helps paralyzed patient walk again",
]

# Sample Wikipedia-style articles
SAMPLE_WIKIPEDIA = [
    ("Python (programming language)", "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability with the use of significant indentation. Python supports multiple programming paradigms, including structured, object-oriented, and functional programming."),
    ("Machine learning", "Machine learning is a field of inquiry devoted to understanding and building methods that learn, that is, methods that leverage data to improve performance on some set of tasks. It is seen as a part of artificial intelligence."),
    ("Neural network", "A neural network is a network or circuit of biological neurons, or, in a modern sense, an artificial neural network, composed of artificial neurons or nodes."),
    ("Database", "A database is an organized collection of structured information, or data, typically stored electronically in a computer system. A database is usually controlled by a database management system (DBMS)."),
    ("Algorithm", "In mathematics and computer science, an algorithm is a finite sequence of rigorous instructions, typically used to solve a class of specific problems or to perform a computation."),
    ("Data structure", "In computer science, a data structure is a data organization, management, and storage format that is usually chosen for efficient access to data."),
    ("Graph theory", "Graph theory is the study of graphs, which are mathematical structures used to model pairwise relations between objects."),
    ("Natural language processing", "Natural language processing is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language."),
    ("Computer vision", "Computer vision is an interdisciplinary scientific field that deals with how computers can gain high-level understanding from digital images or videos."),
    ("Reinforcement learning", "Reinforcement learning is an area of machine learning concerned with how intelligent agents ought to take actions in an environment in order to maximize the notion of cumulative reward."),
]


def load_sample_news(memory: "ABMemory", n: int = 50) -> List[int]:
    """Load sample news headlines into memory.
    
    Args:
        memory: The ABMemory instance.
        n: Number of articles to create.
    
    Returns:
        List of created card IDs.
    """
    card_ids = []
    for i in range(n):
        headline = SAMPLE_NEWS[i % len(SAMPLE_NEWS)]
        # Add some variation
        headline = f"{headline} (Article {i+1})"
        
        card = memory.store_card(
            label="news",
            buffers=[
                Buffer(name="headline", payload=headline.encode(), headers={"type": "text"}),
                Buffer(name="category", payload=b"general", headers={}),
            ]
        )
        card_ids.append(card.id)
    
    return card_ids


def load_sample_wikipedia(memory: "ABMemory", n: int = 20) -> List[int]:
    """Load sample Wikipedia-style articles into memory.
    
    Args:
        memory: The ABMemory instance.
        n: Number of articles to create.
    
    Returns:
        List of created card IDs.
    """
    card_ids = []
    for i in range(n):
        title, content = SAMPLE_WIKIPEDIA[i % len(SAMPLE_WIKIPEDIA)]
        
        card = memory.store_card(
            label="wikipedia",
            buffers=[
                Buffer(name="title", payload=title.encode(), headers={}),
                Buffer(name="content", payload=content.encode(), headers={"type": "text"}),
            ]
        )
        card_ids.append(card.id)
    
    # Create some connections between related articles
    if len(card_ids) >= 10:
        # Python -> Machine Learning
        memory.create_connection(card_ids[0], card_ids[1], "related_to", strength=1.5)
        # Machine Learning -> Neural Network
        memory.create_connection(card_ids[1], card_ids[2], "uses", strength=2.0)
        # Neural Network -> NLP
        memory.create_connection(card_ids[2], card_ids[7], "applied_in", strength=1.8)
        # Machine Learning -> Reinforcement Learning
        memory.create_connection(card_ids[1], card_ids[9], "includes", strength=2.0)
    
    return card_ids


def create_relationship_graph(memory: "ABMemory", n_nodes: int = 50, n_edges: int = 100) -> Dict[str, Any]:
    """Create a random relationship graph for benchmarking traversal.
    
    Args:
        memory: The ABMemory instance.
        n_nodes: Number of nodes (cards) to create.
        n_edges: Number of edges (connections) to create.
    
    Returns:
        Dict with node_ids and edge_count.
    """
    relations = ["relates_to", "depends_on", "references", "contains", "follows"]
    
    # Create nodes
    node_ids = []
    for i in range(n_nodes):
        card = memory.store_card(
            label="node",
            buffers=[Buffer(name="data", payload=f"Node {i}".encode(), headers={})]
        )
        node_ids.append(card.id)
    
    # Create random edges
    for _ in range(n_edges):
        source = random.choice(node_ids)
        target = random.choice(node_ids)
        if source != target:
            relation = random.choice(relations)
            strength = random.uniform(0.5, 3.0)
            try:
                memory.create_connection(source, target, relation, strength)
            except Exception:
                pass  # Ignore duplicate connections
    
    return {"node_ids": node_ids, "edge_count": n_edges}


# ---------------------------------------------------------------------------
# Benchmark Suite
# ---------------------------------------------------------------------------

class Benchmark:
    """Benchmark suite for AB memory operations."""
    
    def __init__(self, memory: "ABMemory"):
        self.memory = memory
        self.results: List[TimingResult] = []
    
    def benchmark_card_creation(self, n: int = 100) -> TimingResult:
        """Benchmark card creation speed."""
        i = [0]  # Use list for closure
        
        def create_card():
            self.memory.store_card(
                label="bench",
                buffers=[Buffer(name="data", payload=f"Test {i[0]}".encode(), headers={})]
            )
            i[0] += 1
        
        result = time_operation("Card Creation", create_card, iterations=n, warmup=5)
        self.results.append(result)
        return result
    
    def benchmark_card_retrieval(self, card_ids: List[int], n: int = 100) -> TimingResult:
        """Benchmark card retrieval speed."""
        idx = [0]
        
        def get_card():
            card_id = card_ids[idx[0] % len(card_ids)]
            self.memory.get_card(card_id)
            idx[0] += 1
        
        result = time_operation(
            "Card Retrieval",
            get_card,
            iterations=n,
            warmup=5,
            sample_size=len(card_ids)
        )
        self.results.append(result)
        return result
    
    def benchmark_keyword_search(self, keywords: List[str], n: int = 50) -> TimingResult:
        """Benchmark keyword search speed."""
        from .search import search_cards
        
        idx = [0]
        
        def search():
            keyword = keywords[idx[0] % len(keywords)]
            search_cards(self.memory, keyword=keyword)
            idx[0] += 1
        
        result = time_operation(
            "Keyword Search",
            search,
            iterations=n,
            warmup=3,
            keywords_count=len(keywords)
        )
        self.results.append(result)
        return result
    
    def benchmark_semantic_search(self, queries: List[str], n: int = 30) -> TimingResult:
        """Benchmark semantic search speed."""
        from .vector_search import semantic_search
        
        idx = [0]
        
        def search():
            query = queries[idx[0] % len(queries)]
            semantic_search(self.memory, query, top_k=5)
            idx[0] += 1
        
        result = time_operation(
            "Semantic Search",
            search,
            iterations=n,
            warmup=2,
            queries_count=len(queries)
        )
        self.results.append(result)
        return result
    
    def benchmark_rfs_recall(self, start_ids: List[int], n: int = 30) -> TimingResult:
        """Benchmark RFS recall with multi-hop traversal."""
        from .rfs_recall import rfs_recall
        
        idx = [0]
        
        def recall():
            start_id = start_ids[idx[0] % len(start_ids)]
            rfs_recall(self.memory, start_id, max_hops=3, max_results=10, strengthen_path=False)
            idx[0] += 1
        
        result = time_operation(
            "RFS Recall (3 hops)",
            recall,
            iterations=n,
            warmup=2,
            start_ids_count=len(start_ids)
        )
        self.results.append(result)
        return result
    
    def benchmark_card_stats(self, card_ids: List[int], n: int = 100) -> TimingResult:
        """Benchmark card stats operations."""
        idx = [0]
        
        def recall_card():
            card_id = card_ids[idx[0] % len(card_ids)]
            self.memory.recall_card(card_id)
            idx[0] += 1
        
        result = time_operation(
            "Card Recall (stats update)",
            recall_card,
            iterations=n,
            warmup=5,
            sample_size=len(card_ids)
        )
        self.results.append(result)
        return result
    
    def benchmark_connection_traversal(self, card_ids: List[int], n: int = 50) -> TimingResult:
        """Benchmark connection listing and traversal."""
        idx = [0]
        
        def list_connections():
            card_id = card_ids[idx[0] % len(card_ids)]
            self.memory.list_connections(card_id=card_id)
            idx[0] += 1
        
        result = time_operation(
            "Connection Listing",
            list_connections,
            iterations=n,
            warmup=5,
            sample_size=len(card_ids)
        )
        self.results.append(result)
        return result
    
    def run_all(self, dataset_size: int = 100) -> List[TimingResult]:
        """Run all benchmarks with sample data.
        
        Args:
            dataset_size: Base size for sample data.
        
        Returns:
            List of all benchmark results.
        """
        print(f"{colored('Running AB Benchmarks', Colors.BOLD + Colors.CYAN)}")
        print(f"Dataset size: {dataset_size}\n")
        
        # Load sample data
        print("Loading sample data...")
        news_ids = load_sample_news(self.memory, n=dataset_size)
        wiki_ids = load_sample_wikipedia(self.memory, n=min(dataset_size // 5, 20))
        graph = create_relationship_graph(self.memory, n_nodes=dataset_size // 2, n_edges=dataset_size)
        all_ids = news_ids + wiki_ids + graph["node_ids"]
        
        print(f"Created {len(all_ids)} cards, {graph['edge_count']} connections\n")
        
        # Run benchmarks
        print("Running benchmarks...")
        
        self.benchmark_card_creation(n=100)
        self._print_result(self.results[-1])
        
        self.benchmark_card_retrieval(all_ids, n=200)
        self._print_result(self.results[-1])
        
        self.benchmark_keyword_search(["Python", "machine", "data", "network", "Article"], n=50)
        self._print_result(self.results[-1])
        
        self.benchmark_semantic_search(["artificial intelligence", "programming language", "neural networks"], n=20)
        self._print_result(self.results[-1])
        
        if graph["node_ids"]:
            self.benchmark_rfs_recall(graph["node_ids"][:10], n=20)
            self._print_result(self.results[-1])
        
        self.benchmark_card_stats(all_ids[:50], n=100)
        self._print_result(self.results[-1])
        
        self.benchmark_connection_traversal(graph["node_ids"][:20], n=50)
        self._print_result(self.results[-1])
        
        return self.results
    
    def _print_result(self, result: TimingResult) -> None:
        """Print a single benchmark result."""
        color = Colors.GREEN if result.ops_per_sec > 1000 else Colors.YELLOW if result.ops_per_sec > 100 else Colors.RED
        
        print(f"  {colored('✓', color)} {result.name}")
        print(f"      Avg: {result.avg_ms:.3f}ms  Min: {result.min_ms:.3f}ms  Max: {result.max_ms:.3f}ms")
        print(f"      {colored(f'{result.ops_per_sec:.0f} ops/sec', color)}")
    
    def print_report(self) -> None:
        """Print a summary report of all benchmarks."""
        print(f"\n{colored('═' * 60, Colors.CYAN)}")
        print(f"{colored(' Benchmark Report', Colors.BOLD + Colors.CYAN)}")
        print(f"{colored('═' * 60, Colors.CYAN)}\n")
        
        print(f"{'Operation':<30} {'Avg (ms)':<12} {'Ops/sec':<12}")
        print(f"{'-' * 54}")
        
        for result in self.results:
            color = Colors.GREEN if result.ops_per_sec > 1000 else Colors.YELLOW if result.ops_per_sec > 100 else Colors.RED
            print(f"{result.name:<30} {result.avg_ms:<12.3f} {colored(f'{result.ops_per_sec:<12.0f}', color)}")
        
        print(f"\n{colored('Legend:', Colors.DIM)}")
        print(f"  {colored('■', Colors.GREEN)} >1000 ops/sec (fast)")
        print(f"  {colored('■', Colors.YELLOW)} >100 ops/sec (moderate)")
        print(f"  {colored('■', Colors.RED)} <100 ops/sec (slow)")


def run_benchmarks(memory: "ABMemory", dataset_size: int = 100) -> List[TimingResult]:
    """Convenience function to run all benchmarks.
    
    Args:
        memory: The ABMemory instance.
        dataset_size: Base size for sample data.
    
    Returns:
        List of benchmark results.
    """
    bench = Benchmark(memory)
    results = bench.run_all(dataset_size)
    bench.print_report()
    return results
