"""Integration of ARC capability into supe's reasoning system.

This module registers ARC as a reasoning capability and adds ARC-specific
problem signatures to the problem classifier.
"""

from supe.reasoning.capability_registry import CapabilityRegistry, ReasoningCapability
from supe.reasoning.problem_types import (
    ReasoningPattern,
    ProblemDomain,
    ProblemSignature,
    ProblemClassifier,
)
from supe.reasoning.arc.arc_capability import ARCCapability


def register_arc_capability(
    registry: CapabilityRegistry,
    max_depth: int = 3,
    beam_width: int = 5,
    enable_learning: bool = True,
) -> ARCCapability:
    """Register ARC capability with the capability registry.

    Args:
        registry: The capability registry to register with
        max_depth: Maximum program depth for synthesis
        beam_width: Beam search width
        enable_learning: Whether to enable incremental learning

    Returns:
        The created ARCCapability instance
    """
    # Create ARC capability instance
    arc_capability = ARCCapability(
        max_depth=max_depth,
        beam_width=beam_width,
        enable_learning=enable_learning,
    )

    # Register capability for program synthesis pattern
    registry.register(ReasoningCapability(
        name="arc_program_synthesis",
        pattern=ReasoningPattern.PROGRAM_SYNTHESIS,
        domains={ProblemDomain.VISUAL_REASONING},
        description="Synthesize transformation programs from visual examples (ARC-AGI)",
        implementation=arc_capability,
        prerequisites=set(),
        confidence=0.85,  # High confidence for visual reasoning tasks
    ))

    # Register capability for transformation inference
    registry.register(ReasoningCapability(
        name="arc_transformation_inference",
        pattern=ReasoningPattern.TRANSFORMATION_INFERENCE,
        domains={ProblemDomain.VISUAL_REASONING},
        description="Infer visual transformations from input-output pairs",
        implementation=arc_capability,
        prerequisites=set(),
        confidence=0.90,  # Very high confidence for transformation tasks
    ))

    # Register capability for visual pattern recognition
    registry.register(ReasoningCapability(
        name="arc_visual_patterns",
        pattern=ReasoningPattern.VISUAL_PATTERN_RECOGNITION,
        domains={ProblemDomain.VISUAL_REASONING, ProblemDomain.PATTERN_RECOGNITION},
        description="Recognize patterns in visual grids (shapes, repetition, symmetry)",
        implementation=arc_capability,
        prerequisites=set(),
        confidence=0.80,
    ))

    return arc_capability


def register_arc_problem_signatures(classifier: ProblemClassifier):
    """Register ARC-specific problem signatures with the classifier.

    Args:
        classifier: The problem classifier to register with
    """
    # ARC transformation task signature
    classifier.register_signature("arc_transformation_task", ProblemSignature(
        domain=ProblemDomain.VISUAL_REASONING,
        required_patterns={
            ReasoningPattern.PROGRAM_SYNTHESIS,
            ReasoningPattern.TRANSFORMATION_INFERENCE,
            ReasoningPattern.VISUAL_PATTERN_RECOGNITION,
            ReasoningPattern.INDUCTIVE,  # Learn from examples
        },
        keywords={"grid", "transform", "visual", "pattern", "example", "input", "output"},
        structure="visual_transformation",
        complexity=8,  # Complex visual reasoning task
        input_types=["grid_examples"],
        output_type="grid",
    ))

    # Visual pattern recognition signature
    classifier.register_signature("visual_pattern_recognition", ProblemSignature(
        domain=ProblemDomain.VISUAL_REASONING,
        required_patterns={
            ReasoningPattern.VISUAL_PATTERN_RECOGNITION,
            ReasoningPattern.PATTERN_MATCHING,
            ReasoningPattern.INDUCTIVE,
        },
        keywords={"grid", "pattern", "shape", "color", "symmetry", "repetition"},
        structure="visual_pattern",
        complexity=6,
        input_types=["grid"],
        output_type="pattern_description",
    ))

    # Object transformation signature
    classifier.register_signature("object_transformation", ProblemSignature(
        domain=ProblemDomain.VISUAL_REASONING,
        required_patterns={
            ReasoningPattern.TRANSFORMATION_INFERENCE,
            ReasoningPattern.GEOMETRIC,
            ReasoningPattern.PATTERN_MATCHING,
        },
        keywords={"object", "transform", "rotate", "flip", "scale", "move"},
        structure="object_transformation",
        complexity=7,
        input_types=["grid_objects"],
        output_type="transformed_grid",
    ))


def setup_arc_integration(
    registry: CapabilityRegistry,
    classifier: ProblemClassifier,
    max_depth: int = 3,
    beam_width: int = 5,
    enable_learning: bool = True,
) -> ARCCapability:
    """Complete ARC integration setup.

    Registers both capabilities and problem signatures.

    Args:
        registry: Capability registry
        classifier: Problem classifier
        max_depth: Maximum program depth
        beam_width: Beam search width
        enable_learning: Enable incremental learning

    Returns:
        The created ARCCapability instance
    """
    # Register ARC capabilities
    arc_capability = register_arc_capability(
        registry=registry,
        max_depth=max_depth,
        beam_width=beam_width,
        enable_learning=enable_learning,
    )

    # Register problem signatures
    register_arc_problem_signatures(classifier)

    return arc_capability
