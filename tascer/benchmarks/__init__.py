"""Benchmarks package - Capability validation experiments.

These are scientific experiments, not unit tests.
Each benchmark tests a specific capability.
"""

from .core import (
    Benchmark,
    BenchmarkResult,
    BenchmarkSuite,
    run_benchmark,
    run_suite,
)

__all__ = [
    "Benchmark",
    "BenchmarkResult",
    "BenchmarkSuite",
    "run_benchmark",
    "run_suite",
]
