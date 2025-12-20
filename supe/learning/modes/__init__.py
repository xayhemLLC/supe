"""Mode-specific utilities for INGEST and EXPLORE learning.

INGEST mode:
- Document and API learning
- Concept extraction
- Cornell notes synthesis

EXPLORE mode:
- Mathematical experimentation
- Theorem validation
- Property testing
"""

from .ingest import (
    extract_concepts,
    generate_questions,
    synthesize_cornell_note,
    create_belief_from_cornell_note,
    process_ingest_content,
)

from .explore import (
    parse_mathematical_claim,
    create_experiment_plan,
    synthesize_theorem,
    create_belief_from_theorem,
    process_explore_question,
    execute_simple_test,
)

__all__ = [
    # INGEST mode
    "extract_concepts",
    "generate_questions",
    "synthesize_cornell_note",
    "create_belief_from_cornell_note",
    "process_ingest_content",
    # EXPLORE mode
    "parse_mathematical_claim",
    "create_experiment_plan",
    "synthesize_theorem",
    "create_belief_from_theorem",
    "process_explore_question",
    "execute_simple_test",
]
