"""ARC-AGI reasoning capabilities.

This module implements visual reasoning, pattern detection, and transformation
inference for the Abstraction and Reasoning Corpus (ARC-AGI) benchmark.
"""

from supe.reasoning.arc.grid import ARCGrid, ARCObject
from supe.reasoning.arc.detector import ObjectDetector
from supe.reasoning.arc.spatial import SpatialReasoner
from supe.reasoning.arc.shapes import ShapeRecognizer, ShapeType, LineOrientation, ShapeDescriptor
from supe.reasoning.arc.patterns import PatternDetector, PatternType, Pattern
from supe.reasoning.arc.transformation import (
    Transformation,
    TransformationType,
    TransformationResult,
    CompositeTransformation,
)
from supe.reasoning.arc.catalog import TransformationCatalog, TransformationMatch, get_catalog
from supe.reasoning.arc.dsl import (
    Program,
    ProgramNode,
    TransformNode,
    SequenceNode,
    ConditionNode,
    ForEachNode,
    IdentityNode,
    ExecutionContext,
)
from supe.reasoning.arc.synthesizer import ProgramSynthesizer, IncrementalSynthesizer, ProgramCandidate
from supe.reasoning.arc.visualizer import (
    visualize_grid,
    visualize_task,
    visualize_objects,
    visualize_transformation,
    visualize_comparison,
    print_grid,
    print_objects,
    print_task,
)
from supe.reasoning.arc.arc_capability import (
    ARCTask,
    ARCResult,
    ARCCapability,
    load_arc_task,
    save_arc_task,
)
from supe.reasoning.arc.arc_integration import (
    register_arc_capability,
    register_arc_problem_signatures,
    setup_arc_integration,
)
from supe.reasoning.arc.arc_evaluator import (
    TaskResult,
    EvaluationResults,
    ARCEvaluator,
    quick_evaluation,
)

__all__ = [
    "ARCGrid",
    "ARCObject",
    "ObjectDetector",
    "SpatialReasoner",
    "ShapeRecognizer",
    "ShapeType",
    "LineOrientation",
    "ShapeDescriptor",
    "PatternDetector",
    "PatternType",
    "Pattern",
    "Transformation",
    "TransformationType",
    "TransformationResult",
    "CompositeTransformation",
    "TransformationCatalog",
    "TransformationMatch",
    "get_catalog",
    "Program",
    "ProgramNode",
    "TransformNode",
    "SequenceNode",
    "ConditionNode",
    "ForEachNode",
    "IdentityNode",
    "ExecutionContext",
    "ProgramSynthesizer",
    "IncrementalSynthesizer",
    "ProgramCandidate",
    "visualize_grid",
    "visualize_task",
    "visualize_objects",
    "visualize_transformation",
    "visualize_comparison",
    "print_grid",
    "print_objects",
    "print_task",
    "ARCTask",
    "ARCResult",
    "ARCCapability",
    "load_arc_task",
    "save_arc_task",
    "register_arc_capability",
    "register_arc_problem_signatures",
    "setup_arc_integration",
    "TaskResult",
    "EvaluationResults",
    "ARCEvaluator",
    "quick_evaluation",
]
