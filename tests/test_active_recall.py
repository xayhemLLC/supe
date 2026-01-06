"""Tests for Active Recall Testing system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, str(__file__).rsplit("/tests", 1)[0])

from supe.learning.types import LearningState, Mode, QuestionType, QuestionStatus, Confidence
from supe.learning.models import Question, Belief, CornellNote, Evidence
from supe.learning.states.active_recall import (
    ActiveRecallState, ActiveRecallTest, ActiveRecallTester
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_question():
    """Create a sample question."""
    return Question(
        id="q_test_001",
        text="How do React hooks work?",
        question_type=QuestionType.CORE_CONCEPT,
        status=QuestionStatus.OPEN,
    )


@pytest.fixture
def sample_belief(sample_question):
    """Create a sample belief with CornellNote."""
    note = CornellNote(
        cue="How do React hooks work?",
        notes="React hooks let you use state and lifecycle features without classes. "
              "useState manages state, useEffect handles side effects. "
              "Rules: call at top level, only in React functions.",
        examples=[
            "const [count, setCount] = useState(0)",
            "useEffect(() => { document.title = count }, [count])"
        ],
        conceptual_summary="Hooks enable functional components to have state",
        operational_summary="Use useState for state, useEffect for side effects",
    )

    return Belief(
        id="b_test_001",
        question_id=sample_question.id,
        mode=Mode.INGEST,
        content=note,
        confidence=Confidence(0.8),
        evidence_ids=["e_001", "e_002"],
        review_interval_days=1,
    )


@pytest.fixture
def mock_machine():
    """Create a mock state machine."""
    machine = MagicMock()
    machine.debug = True
    machine.memory = None
    return machine


# =============================================================================
# ActiveRecallTest Dataclass Tests
# =============================================================================

class TestActiveRecallTestDataclass:
    """Test ActiveRecallTest dataclass."""

    def test_to_dict(self, sample_question, sample_belief):
        """Test serialization to dict."""
        test = ActiveRecallTest(
            id="art_001",
            question_id=sample_question.id,
            belief_id=sample_belief.id,
            question_text=sample_question.text,
            generated_answer="Hooks let you use state in functional components",
            stored_belief_text="React hooks let you use state...",
            similarity_score=0.85,
            key_facts_recalled=3,
            key_facts_total=5,
            factual_accuracy=0.9,
            recall_quality=0.78,
            tested_at=datetime.now().isoformat(),
            response_time_ms=1500.0,
            next_test_at=(datetime.now() + timedelta(days=3)).isoformat(),
            previous_interval_days=1,
            new_interval_days=3,
            easiness_factor=2.5,
        )

        data = test.to_dict()

        assert data["id"] == "art_001"
        assert data["similarity_score"] == 0.85
        assert data["key_facts_recalled"] == 3
        assert data["recall_quality"] == 0.78


# =============================================================================
# ActiveRecallState Tests
# =============================================================================

class TestActiveRecallState:
    """Test ActiveRecallState execution."""

    @pytest.mark.asyncio
    async def test_execute_no_beliefs(self, mock_machine):
        """Test state skips when no beliefs."""
        from supe.learning.models import LearningContext

        context = LearningContext.create(mode=Mode.INGEST)
        # No beliefs_created

        state = ActiveRecallState(mock_machine)
        next_state = await state.execute(context)

        assert next_state == LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

    @pytest.mark.asyncio
    async def test_execute_no_question(self, mock_machine, sample_belief):
        """Test state skips when no focus question."""
        from supe.learning.models import LearningContext

        context = LearningContext.create(mode=Mode.INGEST)
        context.beliefs_created = [sample_belief]
        context.focus_question = None

        state = ActiveRecallState(mock_machine)
        next_state = await state.execute(context)

        assert next_state == LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

    @pytest.mark.asyncio
    async def test_execute_runs_recall_test(
        self, mock_machine, sample_question, sample_belief
    ):
        """Test state executes recall test."""
        from supe.learning.models import LearningContext

        context = LearningContext.create(mode=Mode.INGEST, initial_question=sample_question)
        context.beliefs_created = [sample_belief]

        state = ActiveRecallState(mock_machine)
        next_state = await state.execute(context)

        assert next_state == LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

        # Check test results were stored
        assert hasattr(context, '_recall_tests')
        assert sample_question.id in context._recall_tests

        assert hasattr(context, '_test_results')
        assert sample_question.id in context._test_results

    @pytest.mark.asyncio
    async def test_extract_belief_text_cornell_note(
        self, mock_machine, sample_question, sample_belief
    ):
        """Test extracting text from CornellNote belief."""
        state = ActiveRecallState(mock_machine)

        text = state._extract_belief_text(sample_belief)

        assert "React hooks" in text
        assert "useState" in text
        assert "useEffect" in text

    @pytest.mark.asyncio
    async def test_extract_key_facts(
        self, mock_machine, sample_question, sample_belief
    ):
        """Test extracting key facts from belief."""
        state = ActiveRecallState(mock_machine)

        facts = state._extract_key_facts(sample_belief)

        assert len(facts) > 0
        # Should include examples
        assert any("useState" in f for f in facts)

    def test_compute_similarity(self, mock_machine):
        """Test similarity computation."""
        state = ActiveRecallState(mock_machine)

        # Identical texts should have high similarity
        sim = state._compute_similarity(
            "React hooks let you use state",
            "React hooks let you use state"
        )
        assert sim > 0.9

        # Different texts should have lower similarity
        sim = state._compute_similarity(
            "React hooks are great",
            "Python is awesome for data science"
        )
        assert sim < 0.5

    def test_check_facts_recalled(self, mock_machine):
        """Test checking which facts were recalled."""
        state = ActiveRecallState(mock_machine)

        facts = [
            "React hooks enable state in functional components",
            "useState manages component state",
            "useEffect handles side effects",
        ]

        answer = "Hooks like useState let functional components have state and manage side effects"

        recalled = state._check_facts_recalled(answer, facts)

        # Should recall at least some facts
        assert len(recalled) >= 1

    def test_sm2_schedule_good_recall(self, mock_machine):
        """Test SM-2 scheduling for good recall."""
        state = ActiveRecallState(mock_machine)

        new_interval, new_ef = state._sm2_schedule(
            recall_quality=0.9,  # Good recall
            current_interval=3,
            easiness_factor=2.5
        )

        # Should increase interval
        assert new_interval > 3

    def test_sm2_schedule_poor_recall(self, mock_machine):
        """Test SM-2 scheduling for poor recall."""
        state = ActiveRecallState(mock_machine)

        new_interval, new_ef = state._sm2_schedule(
            recall_quality=0.3,  # Poor recall
            current_interval=7,
            easiness_factor=2.5
        )

        # Should reset to 1 day
        assert new_interval == 1


# =============================================================================
# ActiveRecallTester Tests
# =============================================================================

class TestActiveRecallTester:
    """Test standalone ActiveRecallTester."""

    @pytest.mark.asyncio
    async def test_test_belief(self, sample_question, sample_belief):
        """Test testing a belief."""
        tester = ActiveRecallTester(debug=True)

        result = await tester.test_belief(sample_belief, sample_question)

        assert isinstance(result, ActiveRecallTest)
        assert result.question_id == sample_question.id
        assert result.belief_id == sample_belief.id
        assert 0.0 <= result.recall_quality <= 1.0
        assert result.new_interval_days >= 1

    @pytest.mark.asyncio
    async def test_get_due_reviews_empty(self):
        """Test getting due reviews with no memory."""
        tester = ActiveRecallTester()

        due = await tester.get_due_reviews()

        assert due == []


# =============================================================================
# Integration Tests
# =============================================================================

class TestActiveRecallIntegration:
    """Integration tests for active recall system."""

    @pytest.mark.asyncio
    async def test_full_recall_flow(self, mock_machine, sample_question, sample_belief):
        """Test full recall test flow."""
        from supe.learning.models import LearningContext

        # Create context with question and belief
        context = LearningContext.create(mode=Mode.INGEST, initial_question=sample_question)
        context.beliefs_created = [sample_belief]

        # Run active recall state
        state = ActiveRecallState(mock_machine)
        next_state = await state.execute(context)

        # Verify outcomes
        assert next_state == LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

        # Check belief was updated
        assert sample_belief.last_reviewed_at is not None

        # Check recall test was stored
        assert sample_question.id in context._recall_tests
        test_result = context._recall_tests[sample_question.id]

        assert isinstance(test_result, ActiveRecallTest)
        assert test_result.recall_quality > 0

    @pytest.mark.asyncio
    async def test_recall_updates_review_schedule(
        self, mock_machine, sample_question, sample_belief
    ):
        """Test that recall test updates review schedule."""
        from supe.learning.models import LearningContext

        original_interval = sample_belief.review_interval_days

        context = LearningContext.create(mode=Mode.INGEST, initial_question=sample_question)
        context.beliefs_created = [sample_belief]

        state = ActiveRecallState(mock_machine)
        await state.execute(context)

        # Review interval should be updated based on recall quality
        # (might be same, increased, or reset to 1)
        assert sample_belief.review_interval_days >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
