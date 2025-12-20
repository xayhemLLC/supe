"""INGEST mode utilities for document learning.

Provides utilities for:
- Concept extraction from text
- Question generation from concepts
- Cornell note synthesis from evidence

INGEST mode is for learning from documentation, APIs, tutorials, and
other structured content. It focuses on extracting key concepts and
creating Q&A-style knowledge representation.
"""

import re
from typing import List, Dict, Any, Optional

from ..models import Question, Evidence, CornellNote, Belief
from ..types import QuestionType, EvidenceSource, Confidence, ID


# ============================================================================
# Concept Extraction
# ============================================================================


def extract_concepts(content: str, max_concepts: int = 10) -> List[str]:
    """Extract key concepts from text content.

    Uses simple heuristics to identify important concepts:
    - Capitalized words/phrases (likely proper nouns, APIs)
    - Words in code blocks
    - Repeated terms
    - Section headers

    Args:
        content: Text content to analyze.
        max_concepts: Maximum concepts to extract.

    Returns:
        List of concept strings.
    """
    concepts = set()

    # Extract from code blocks
    code_blocks = re.findall(r'```[^`]+```|`[^`]+`', content)
    for block in code_blocks:
        # Extract identifiers from code
        identifiers = re.findall(r'\b[A-Z][a-zA-Z0-9_]+\b', block)
        concepts.update(identifiers[:5])  # Limit per block

    # Extract capitalized terms (likely important nouns/names)
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
    for term in capitalized:
        if len(term) > 3 and term not in ['The', 'This', 'That', 'These', 'Those']:
            concepts.add(term)

    # Extract section headers (markdown)
    headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
    concepts.update([h.strip() for h in headers])

    # Extract repeated terms (appears 3+ times)
    words = re.findall(r'\b[a-z]{4,}\b', content.lower())
    word_counts = {}
    for word in words:
        if word not in ['that', 'this', 'with', 'from', 'have', 'will', 'been']:
            word_counts[word] = word_counts.get(word, 0) + 1

    frequent = [w for w, c in word_counts.items() if c >= 3]
    concepts.update(frequent[:5])

    # Sort by relevance (length is a simple proxy)
    sorted_concepts = sorted(concepts, key=len, reverse=True)
    return sorted_concepts[:max_concepts]


# ============================================================================
# Question Generation
# ============================================================================


def generate_questions(
    concepts: List[str],
    content: str,
    max_questions: int = 5,
) -> List[Question]:
    """Generate learning questions from concepts.

    Creates questions across 4 types:
    - CORE_CONCEPT: What is X?
    - OPERATIONAL: How do I use X?
    - CONSTRAINT: What are the limitations of X?
    - IMPACT: Why should I care about X?

    Args:
        concepts: List of extracted concepts.
        content: Original content for context.
        max_questions: Maximum questions to generate.

    Returns:
        List of Question objects.
    """
    questions = []

    # Question templates by type
    templates = {
        QuestionType.CORE_CONCEPT: [
            "What is {}?",
            "What does {} mean?",
            "How is {} defined?",
        ],
        QuestionType.OPERATIONAL: [
            "How do I use {}?",
            "How does {} work?",
            "What are the steps to use {}?",
        ],
        QuestionType.CONSTRAINT: [
            "What are the limitations of {}?",
            "When should I not use {}?",
            "What can go wrong with {}?",
        ],
        QuestionType.IMPACT: [
            "Why is {} important?",
            "What problems does {} solve?",
            "When should I use {}?",
        ],
    }

    # Generate questions for each concept
    question_types = list(templates.keys())
    for i, concept in enumerate(concepts[:max_questions]):
        # Rotate through question types
        q_type = question_types[i % len(question_types)]
        template = templates[q_type][i % len(templates[q_type])]

        question = Question.create(
            text=template.format(concept),
            question_type=q_type,
            source="concept_extraction",
        )
        question.related_concepts = [concept]
        questions.append(question)

        if len(questions) >= max_questions:
            break

    return questions


# ============================================================================
# Cornell Note Synthesis
# ============================================================================


def synthesize_cornell_note(
    question: Question,
    evidence_list: List[Evidence],
) -> CornellNote:
    """Synthesize a Cornell note from question and evidence.

    Cornell note structure:
    - Cue: The question
    - Notes: Detailed answer from evidence
    - Examples: Code snippets or concrete examples
    - Conceptual summary: High-level understanding
    - Operational summary: How to use it

    Args:
        question: The question being answered.
        evidence_list: Evidence supporting the answer.

    Returns:
        CornellNote with synthesized content.
    """
    # Cue is the question
    cue = question.text

    # Notes are the combined evidence texts
    notes_parts = []
    for evidence in evidence_list:
        notes_parts.append(f"- {evidence.text}")
    notes = "\n".join(notes_parts)

    # Extract examples from evidence (look for code blocks)
    examples = []
    for evidence in evidence_list:
        # Simple heuristic: look for lines with common code patterns
        code_lines = [
            line for line in evidence.text.split('\n')
            if any(marker in line for marker in ['()', '{}', '=>', 'def ', 'function', 'const ', 'let '])
        ]
        if code_lines:
            examples.extend(code_lines[:2])  # Max 2 per evidence

    # Conceptual summary: First sentence from each evidence
    conceptual_parts = []
    for evidence in evidence_list:
        sentences = evidence.text.split('.')
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 10:
                conceptual_parts.append(first_sentence)

    conceptual_summary = ". ".join(conceptual_parts[:3]) + "."

    # Operational summary: Look for action words
    operational_parts = []
    for evidence in evidence_list:
        # Look for sentences with action verbs
        sentences = evidence.text.split('.')
        for sentence in sentences:
            if any(verb in sentence.lower() for verb in ['use', 'call', 'create', 'run', 'execute', 'implement']):
                operational_parts.append(sentence.strip())
                break

    operational_summary = ". ".join(operational_parts[:2]) + "." if operational_parts else "No operational guidance found."

    return CornellNote(
        cue=cue,
        notes=notes,
        examples=examples[:5],  # Max 5 examples
        conceptual_summary=conceptual_summary,
        operational_summary=operational_summary,
    )


def create_belief_from_cornell_note(
    question: Question,
    note: CornellNote,
    evidence_list: List[Evidence],
    confidence: Optional[Confidence] = None,
) -> Belief:
    """Create a Belief from a Cornell note.

    Args:
        question: The question being answered.
        note: Cornell note with synthesized content.
        evidence_list: Supporting evidence.
        confidence: Optional confidence override.

    Returns:
        Belief wrapping the Cornell note.
    """
    # Calculate confidence from evidence if not provided
    if confidence is None:
        # Average confidence from all evidence
        if evidence_list:
            avg_conf = sum(float(e.confidence) for e in evidence_list) / len(evidence_list)
            confidence = Confidence(avg_conf)
        else:
            confidence = Confidence(0.5)  # Default moderate confidence

    evidence_ids = [ID(e.id) for e in evidence_list]

    return Belief.create_from_cornell_note(
        question_id=ID(question.id),
        note=note,
        confidence=confidence,
        evidence_ids=evidence_ids,
    )


# ============================================================================
# INGEST Workflow
# ============================================================================


def process_ingest_content(
    content: str,
    source_url: str = "",
    max_concepts: int = 10,
    max_questions: int = 5,
) -> Dict[str, Any]:
    """Process content in INGEST mode.

    Complete workflow:
    1. Extract concepts from content
    2. Generate questions from concepts
    3. Create evidence from content
    4. Synthesize Cornell notes
    5. Create beliefs

    Args:
        content: Text content to learn from.
        source_url: Source URL for citations.
        max_concepts: Maximum concepts to extract.
        max_questions: Maximum questions to generate.

    Returns:
        Dictionary with:
        {
            "concepts": List[str],
            "questions": List[Question],
            "evidence": Evidence,
        }
    """
    # 1. Extract concepts
    concepts = extract_concepts(content, max_concepts)

    # 2. Generate questions
    questions = generate_questions(concepts, content, max_questions)

    # 3. Create evidence from content
    evidence = Evidence.create(
        text=content[:1000],  # Truncate for storage
        source=EvidenceSource.DOC,
        citations=[source_url] if source_url else [],
    )
    evidence.validated = True
    evidence.validation_method = "source_document"

    return {
        "concepts": concepts,
        "questions": questions,
        "evidence": evidence,
    }
