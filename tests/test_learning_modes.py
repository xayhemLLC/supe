"""Tests for INGEST and EXPLORE mode utilities (Phase 2)."""

import pytest

from supe.learning.models import Question, Evidence
from supe.learning.types import QuestionType, EvidenceSource, TheoremStatus
from supe.learning.modes.ingest import (
    extract_concepts,
    generate_questions,
    synthesize_cornell_note,
    create_belief_from_cornell_note,
    process_ingest_content,
)
from supe.learning.modes.explore import (
    parse_mathematical_claim,
    create_experiment_plan,
    synthesize_theorem,
    create_belief_from_theorem,
    execute_simple_test,
    process_explore_question,
)


# ============================================================================
# INGEST Mode Tests
# ============================================================================

def test_extract_concepts():
    """Should extract key concepts from text."""
    content = """
    React Hooks are functions that let you use state and other React features.
    The useState hook is the most common. You can also use useEffect for side effects.
    """

    concepts = extract_concepts(content, max_concepts=5)

    assert len(concepts) > 0
    assert any('React' in c or 'Hooks' in c or 'useState' in c for c in concepts)


def test_extract_concepts_from_code():
    """Should extract concepts from code blocks."""
    content = """
    Here's an example:
    ```javascript
    function MyComponent() {
        const [count, setCount] = useState(0);
    }
    ```
    """

    concepts = extract_concepts(content)
    # Should find MyComponent or useState
    assert len(concepts) > 0


def test_generate_questions():
    """Should generate questions from concepts."""
    concepts = ["React", "useState", "useEffect"]
    content = "Test content about React"

    questions = generate_questions(concepts, content, max_questions=5)

    assert len(questions) <= 5
    assert all(isinstance(q, Question) for q in questions)
    assert any(q.question_type == QuestionType.CORE_CONCEPT for q in questions)
    assert any(q.question_type == QuestionType.OPERATIONAL for q in questions)


def test_synthesize_cornell_note():
    """Should create Cornell note from question and evidence."""
    q = Question.create("What is React?", QuestionType.CORE_CONCEPT)
    e1 = Evidence.create("React is a library", EvidenceSource.DOC, [])
    e2 = Evidence.create("Use React to build UIs", EvidenceSource.DOC, [])

    note = synthesize_cornell_note(q, [e1, e2])

    assert note.cue == q.text
    assert "React" in note.notes
    assert len(note.conceptual_summary) > 0


def test_create_belief_from_cornell_note():
    """Should create belief from Cornell note."""
    q = Question.create("Test", QuestionType.CORE_CONCEPT)
    note = synthesize_cornell_note(q, [])

    belief = create_belief_from_cornell_note(q, note, [], confidence=0.8)

    assert belief.confidence == 0.8
    assert belief.question_id == q.id


def test_process_ingest_content():
    """Should process content through full INGEST pipeline."""
    content = "React Hooks let you use state in function components."

    result = process_ingest_content(content, "http://test.com", max_concepts=5, max_questions=3)

    assert "concepts" in result
    assert "questions" in result
    assert "evidence" in result
    assert len(result["concepts"]) > 0
    assert len(result["questions"]) <= 3
    assert isinstance(result["evidence"], Evidence)


# ============================================================================
# EXPLORE Mode Tests
# ============================================================================

def test_parse_mathematical_claim_commutative():
    """Should parse commutative property claim."""
    question = "Is addition commutative?"

    claim = parse_mathematical_claim(question)

    assert claim["property"] == "commutative"
    assert claim["operation"] == "addition"
    assert "commutative" in claim["hypothesis"].lower()
    assert len(claim["test_cases"]) > 0


def test_parse_mathematical_claim_associative():
    """Should parse associative property claim."""
    question = "Is multiplication associative?"

    claim = parse_mathematical_claim(question)

    assert claim["property"] == "associative"
    assert claim["operation"] == "multiplication"


def test_create_experiment_plan():
    """Should create experiment plan from claim."""
    q = Question.create("Is addition commutative?", QuestionType.MATH_STRUCTURE)
    claim = {
        "property": "commutative",
        "operation": "addition",
        "hypothesis": "Addition is commutative",
        "test_cases": [{"a": 2, "b": 3}],
    }

    plan = create_experiment_plan(q, claim)

    assert plan["title"]
    assert plan["hypothesis"] == "Addition is commutative"
    assert len(plan["tascs"]) == 1


def test_execute_simple_test_commutative_pass():
    """Should execute commutative test and pass."""
    test_case = {"a": 5, "b": 3, "test": "a op b == b op a"}

    result = execute_simple_test(test_case, "addition")

    assert result["passed"] is True
    assert "test_data" in result


def test_execute_simple_test_commutative_fail():
    """Subtraction should fail commutative test."""
    test_case = {"a": 5, "b": 3, "test": "a op b == b op a"}

    result = execute_simple_test(test_case, "subtraction")

    assert result["passed"] is False


def test_synthesize_theorem_proven():
    """Should synthesize PROVEN theorem."""
    q = Question.create("Is X true?", QuestionType.MATH_STRUCTURE)
    claim = {"property": "test", "hypothesis": "X is true"}
    experiment_results = [
        {"passed": True},
        {"passed": True},
        {"passed": True},
    ]

    theorem = synthesize_theorem(q, claim, experiment_results)

    assert theorem.status == TheoremStatus.PROVEN
    assert "3" in theorem.proof  # Should mention 3 tests
    assert theorem.counterexample is None


def test_synthesize_theorem_disproven():
    """Should synthesize DISPROVEN theorem."""
    q = Question.create("Is X true?", QuestionType.MATH_STRUCTURE)
    claim = {"property": "test", "hypothesis": "X is true"}
    experiment_results = [
        {"passed": False, "test_data": {"a": 1, "b": 2}},
    ]

    theorem = synthesize_theorem(q, claim, experiment_results)

    assert theorem.status == TheoremStatus.DISPROVEN
    assert theorem.counterexample is not None


def test_synthesize_theorem_conjecture():
    """Should synthesize CONJECTURE for partial evidence."""
    q = Question.create("Is X true?", QuestionType.MATH_STRUCTURE)
    claim = {"property": "test", "hypothesis": "X is true"}
    experiment_results = [
        {"passed": True},
        {"passed": False},
    ]

    theorem = synthesize_theorem(q, claim, experiment_results)

    assert theorem.status == TheoremStatus.CONJECTURE
    assert "1/2" in theorem.proof or "partially" in theorem.proof.lower()


def test_create_belief_from_theorem():
    """Should create belief from theorem."""
    q = Question.create("Test", QuestionType.MATH_STRUCTURE)
    theorem = synthesize_theorem(q, {"property": "test", "hypothesis": "X"}, [{"passed": True}])

    belief = create_belief_from_theorem(q, theorem, [])

    assert belief.mode.value == "EXPLORE"
    assert belief.confidence == 0.95  # PROVEN gets high confidence


def test_execute_simple_test_generic_is_heuristic():
    """Generic 'validate:' tests should be marked heuristic (not executable validation)."""
    test_case = {"n": 1, "test": "validate: some advanced claim"}

    result = execute_simple_test(test_case, "unknown")

    assert result["passed"] is True
    assert result.get("heuristic") is True


def test_synthesize_theorem_generic_is_conjecture():
    """Heuristic-only exploration should yield CONJECTURE, not PROVEN."""
    q = Question.create("Is some advanced claim true?", QuestionType.MATH_STRUCTURE)
    claim = {"property": "general", "hypothesis": "Some advanced claim"}
    experiment_results = [{"passed": True, "heuristic": True} for _ in range(3)]

    theorem = synthesize_theorem(q, claim, experiment_results)

    assert theorem.status == TheoremStatus.CONJECTURE
    assert "heuristic" in theorem.proof.lower()


def test_process_explore_question():
    """Should process question through EXPLORE pipeline."""
    q = Question.create("Is addition commutative?", QuestionType.MATH_STRUCTURE)

    result = process_explore_question(q)

    assert "claim" in result
    assert "experiment_plan" in result
    assert "test_cases" in result
    assert result["claim"]["property"] == "commutative"


def test_execute_simple_test_associative():
    """Should test associative property."""
    test_case = {
        "a": 2,
        "b": 3,
        "c": 4,
        "test": "(a op b) op c == a op (b op c)"
    }

    result = execute_simple_test(test_case, "addition")

    assert result["passed"] is True


def test_execute_simple_test_identity():
    """Should test identity property."""
    test_case = {
        "a": 5,
        "e": 0,
        "test": "a op e == a"
    }

    result = execute_simple_test(test_case, "addition")

    assert result["passed"] is True
