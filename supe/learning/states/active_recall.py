"""ACTIVE_RECALL_TEST state - Test knowledge without looking at sources.

This state implements active recall testing:
1. Generate answer WITHOUT providing source evidence
2. Compare generated answer to stored belief
3. Score recall quality (similarity + fact coverage)
4. Update confidence based on recall performance
5. Schedule next review using SM-2 algorithm

Active recall is proven to be more effective than passive review:
- Forces retrieval from memory (strengthens connections)
- Identifies gaps in understanding
- Enables accurate confidence calibration
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from ..types import LearningState, Confidence
from ..models import Belief, Question
from .base import BaseState

if TYPE_CHECKING:
    from ..models import LearningContext


@dataclass
class ActiveRecallTest:
    """Result of an active recall test."""

    id: str
    question_id: str
    belief_id: str

    # The test itself
    question_text: str
    generated_answer: str       # Answer WITHOUT looking at sources
    stored_belief_text: str     # What we learned (ground truth)

    # Scoring components
    similarity_score: float     # 0.0-1.0 (embedding cosine similarity)
    key_facts_recalled: int     # How many facts mentioned
    key_facts_total: int        # Total facts in belief
    factual_accuracy: float     # Were stated facts correct? 0.0-1.0

    # Combined score
    recall_quality: float       # Overall recall quality 0.0-1.0

    # Timing
    tested_at: str
    response_time_ms: float     # How long to generate answer
    next_test_at: Optional[str] = None

    # Review scheduling
    previous_interval_days: int = 1
    new_interval_days: int = 1
    easiness_factor: float = 2.5  # SM-2 easiness factor

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "belief_id": self.belief_id,
            "question_text": self.question_text,
            "generated_answer": self.generated_answer,
            "stored_belief_text": self.stored_belief_text,
            "similarity_score": self.similarity_score,
            "key_facts_recalled": self.key_facts_recalled,
            "key_facts_total": self.key_facts_total,
            "factual_accuracy": self.factual_accuracy,
            "recall_quality": self.recall_quality,
            "tested_at": self.tested_at,
            "response_time_ms": self.response_time_ms,
            "next_test_at": self.next_test_at,
            "previous_interval_days": self.previous_interval_days,
            "new_interval_days": self.new_interval_days,
            "easiness_factor": self.easiness_factor,
        }


class ActiveRecallState(BaseState):
    """Test recall of learned information without referring to sources.

    This state implements the active recall testing paradigm:

    1. HIDE all source evidence (don't provide citations/docs)
    2. ASK the system to answer the question from memory
    3. COMPARE the generated answer to the stored belief
    4. SCORE based on:
       - Semantic similarity (embedding comparison)
       - Fact recall (key points mentioned)
       - Accuracy (no false statements)
    5. SCHEDULE next review using SM-2 algorithm

    The key insight: Recognition is easy, recall is hard.
    By forcing recall, we:
    - Build stronger memory traces
    - Identify true gaps vs. false confidence
    - Enable accurate learning progress tracking
    """

    async def execute(self, context: "LearningContext") -> LearningState:
        """Execute active recall test.

        Args:
            context: Current learning context.

        Returns:
            Next state (EVALUATE_AND_UPDATE_CONFIDENCE).
        """
        self._log("=== ACTIVE_RECALL_TEST State ===")

        if not context.beliefs_created:
            self._log("No beliefs to test, skipping active recall")
            return LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

        # Get the most recent belief and its question
        latest_belief = context.beliefs_created[-1]
        question = context.focus_question

        if not question:
            self._log("No focus question, skipping active recall")
            return LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

        self._log(f"Testing recall for: {question.text}")
        self._log(f"Belief confidence: {latest_belief.confidence}")

        # Run the active recall test
        test_result = await self._run_recall_test(question, latest_belief)

        # Store test result in context metadata
        if not hasattr(context, '_recall_tests'):
            context._recall_tests = {}
        context._recall_tests[question.id] = test_result

        # Also update _test_results for EVALUATE state compatibility
        if not hasattr(context, '_test_results'):
            context._test_results = {}
        context._test_results[question.id] = {
            "recall_quality": test_result.recall_quality,
            "belief_id": latest_belief.id,
            "tested_at": test_result.tested_at,
            "similarity_score": test_result.similarity_score,
            "facts_recalled": f"{test_result.key_facts_recalled}/{test_result.key_facts_total}",
        }

        self._log(f"Recall quality: {test_result.recall_quality:.2f}")
        self._log(f"Similarity: {test_result.similarity_score:.2f}")
        self._log(f"Facts recalled: {test_result.key_facts_recalled}/{test_result.key_facts_total}")
        self._log(f"Next review in: {test_result.new_interval_days} days")

        # Update belief review schedule
        latest_belief.review_interval_days = test_result.new_interval_days
        latest_belief.last_reviewed_at = int(datetime.now().timestamp() * 1000)

        if test_result.next_test_at:
            next_dt = datetime.fromisoformat(test_result.next_test_at)
            latest_belief.next_review_at = int(next_dt.timestamp() * 1000)

        self._log_transition(
            LearningState.SELF_TEST,  # Using SELF_TEST as placeholder
            LearningState.EVALUATE_AND_UPDATE_CONFIDENCE
        )
        return LearningState.EVALUATE_AND_UPDATE_CONFIDENCE

    async def _run_recall_test(
        self,
        question: Question,
        belief: Belief
    ) -> ActiveRecallTest:
        """Run the active recall test.

        Args:
            question: The question to answer.
            belief: The stored belief (ground truth).

        Returns:
            ActiveRecallTest with full results.
        """
        import time
        start_time = time.time()

        # Extract belief text based on type
        belief_text = self._extract_belief_text(belief)
        belief_facts = self._extract_key_facts(belief)

        # Generate answer WITHOUT providing sources
        generated_answer = await self._generate_answer_from_memory(question.text)

        response_time_ms = (time.time() - start_time) * 1000

        # Score the recall
        similarity_score = self._compute_similarity(generated_answer, belief_text)
        recalled_facts = self._check_facts_recalled(generated_answer, belief_facts)
        factual_accuracy = self._check_accuracy(generated_answer, belief_facts)

        # Compute overall recall quality
        # Weighted combination: similarity (50%) + fact recall (30%) + accuracy (20%)
        fact_recall_score = len(recalled_facts) / len(belief_facts) if belief_facts else 1.0
        recall_quality = (
            similarity_score * 0.5 +
            fact_recall_score * 0.3 +
            factual_accuracy * 0.2
        )

        # Apply recall penalty (recall is harder than recognition)
        recall_quality *= 0.95

        # Clamp to valid range
        recall_quality = max(0.0, min(1.0, recall_quality))

        # Schedule next review using SM-2
        current_interval = belief.review_interval_days
        new_interval, new_ef = self._sm2_schedule(
            recall_quality,
            current_interval,
            getattr(belief, '_easiness_factor', 2.5)
        )

        next_test_at = datetime.now() + timedelta(days=new_interval)

        return ActiveRecallTest(
            id=str(uuid4()),
            question_id=question.id,
            belief_id=belief.id,
            question_text=question.text,
            generated_answer=generated_answer,
            stored_belief_text=belief_text,
            similarity_score=similarity_score,
            key_facts_recalled=len(recalled_facts),
            key_facts_total=len(belief_facts),
            factual_accuracy=factual_accuracy,
            recall_quality=recall_quality,
            tested_at=datetime.now().isoformat(),
            response_time_ms=response_time_ms,
            next_test_at=next_test_at.isoformat(),
            previous_interval_days=current_interval,
            new_interval_days=new_interval,
            easiness_factor=new_ef,
        )

    async def _generate_answer_from_memory(self, question_text: str) -> str:
        """Generate an answer WITHOUT providing source material.

        In production, this calls an LLM with only the question,
        NOT the evidence or stored belief.

        Args:
            question_text: The question to answer.

        Returns:
            Generated answer from "memory" alone.
        """
        # In a real implementation, this would:
        # 1. Call the LLM with ONLY the question
        # 2. NOT include any evidence, citations, or stored beliefs
        # 3. The LLM must rely on what it "remembers" from training + context

        # For demo, simulate a recall attempt
        # In production: return await self.machine.llm.generate(prompt)

        # Simulate partial recall with some degradation
        self._log("Generating answer from memory (no sources provided)...")

        # Return a simulated answer
        # In real implementation, this would be LLM-generated
        return f"Based on my understanding, regarding '{question_text}': [Simulated recall response]"

    def _extract_belief_text(self, belief: Belief) -> str:
        """Extract searchable text from a belief."""
        from ..models import CornellNote, Theorem

        if hasattr(belief.content, 'notes'):
            # CornellNote
            note = belief.content
            parts = [note.cue, note.notes]
            if note.examples:
                parts.extend(note.examples)
            if note.conceptual_summary:
                parts.append(note.conceptual_summary)
            return " ".join(parts)

        elif hasattr(belief.content, 'statement'):
            # Theorem
            theorem = belief.content
            parts = [theorem.statement, theorem.proof]
            if theorem.counterexample:
                parts.append(theorem.counterexample)
            return " ".join(parts)

        else:
            return str(belief.content)

    def _extract_key_facts(self, belief: Belief) -> List[str]:
        """Extract key facts from a belief for recall checking."""
        from ..models import CornellNote, Theorem

        facts = []

        if hasattr(belief.content, 'notes'):
            # CornellNote - split notes into sentences
            note = belief.content
            sentences = note.notes.replace('\n', '. ').split('. ')
            facts.extend([s.strip() for s in sentences if len(s.strip()) > 10])

            # Add examples as facts
            facts.extend(note.examples)

        elif hasattr(belief.content, 'statement'):
            # Theorem
            theorem = belief.content
            facts.append(theorem.statement)
            if theorem.proof:
                facts.append(theorem.proof)
            facts.extend(theorem.properties_validated)

        # Filter out very short "facts"
        return [f for f in facts if len(f) > 10][:10]  # Max 10 facts

    def _compute_similarity(self, answer: str, belief_text: str) -> float:
        """Compute semantic similarity between answer and belief.

        In production, this uses embeddings and cosine similarity.
        For demo, uses simple word overlap.
        """
        # Simple word overlap (production would use embeddings)
        answer_words = set(answer.lower().split())
        belief_words = set(belief_text.lower().split())

        if not belief_words:
            return 0.0

        overlap = len(answer_words & belief_words)
        jaccard = overlap / len(answer_words | belief_words)

        # Scale to be more lenient (Jaccard is harsh)
        return min(jaccard * 2, 1.0)

    def _check_facts_recalled(
        self,
        answer: str,
        facts: List[str]
    ) -> List[str]:
        """Check which facts from the belief were mentioned in the answer."""
        recalled = []
        answer_lower = answer.lower()

        for fact in facts:
            # Check if key words from fact appear in answer
            fact_words = [w for w in fact.lower().split() if len(w) > 3]

            if not fact_words:
                continue

            # Require at least half the significant words to match
            matches = sum(1 for w in fact_words if w in answer_lower)
            if matches >= len(fact_words) * 0.5:
                recalled.append(fact)

        return recalled

    def _check_accuracy(self, answer: str, facts: List[str]) -> float:
        """Check if the answer contains false statements.

        In production, this would use an LLM to verify claims.
        For demo, assumes high accuracy (no false detection).
        """
        # In production: Use LLM to check if answer contradicts known facts
        # For demo, return high accuracy
        return 0.9

    def _sm2_schedule(
        self,
        recall_quality: float,
        current_interval: int,
        easiness_factor: float
    ) -> tuple:
        """SM-2 spaced repetition scheduling algorithm.

        Args:
            recall_quality: 0.0-1.0 quality of recall
            current_interval: Current interval in days
            easiness_factor: Current EF (2.5 default)

        Returns:
            (new_interval, new_easiness_factor)
        """
        # Convert recall_quality (0-1) to SM-2 quality (0-5)
        # 0.8+ = 5 (perfect), 0.6-0.8 = 4, 0.4-0.6 = 3, etc.
        q = int(recall_quality * 5)

        # SM-2 algorithm
        if q >= 3:  # Successful recall
            if current_interval == 1:
                new_interval = 1
            elif current_interval == 2:
                new_interval = 6
            else:
                new_interval = int(current_interval * easiness_factor)

            # Update easiness factor
            new_ef = easiness_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            new_ef = max(1.3, new_ef)  # Minimum EF is 1.3

        else:  # Failed recall - reset
            new_interval = 1
            new_ef = easiness_factor  # Keep EF unchanged on failure

        # Cap at reasonable maximum
        new_interval = min(new_interval, 365)

        return new_interval, new_ef


class ActiveRecallTester:
    """Standalone tester for active recall outside state machine.

    Use this to test recall of beliefs independently,
    e.g., for scheduled review sessions.
    """

    def __init__(self, memory=None, llm=None, debug: bool = False):
        """Initialize tester.

        Args:
            memory: ABMemory instance for loading beliefs
            llm: LLM client for generating answers
            debug: Enable debug logging
        """
        self.memory = memory
        self.llm = llm
        self.debug = debug

    async def test_belief(self, belief: Belief, question: Question) -> ActiveRecallTest:
        """Test recall of a specific belief.

        Args:
            belief: The belief to test
            question: The associated question

        Returns:
            ActiveRecallTest result
        """
        # Create a mock state to reuse logic
        class MockMachine:
            def __init__(self, debug):
                self.debug = debug
                self.memory = None

        mock = MockMachine(self.debug)
        state = ActiveRecallState(mock)

        return await state._run_recall_test(question, belief)

    async def get_due_reviews(self, limit: int = 10) -> List[Belief]:
        """Get beliefs that are due for review.

        Args:
            limit: Max beliefs to return

        Returns:
            List of beliefs needing review
        """
        if not self.memory:
            return []

        now = int(datetime.now().timestamp() * 1000)

        # In production: query beliefs where next_review_at <= now
        # For demo, return empty list
        return []

    async def run_review_session(self) -> List[ActiveRecallTest]:
        """Run a full review session for all due beliefs.

        Returns:
            List of test results
        """
        due_beliefs = await self.get_due_reviews()
        results = []

        for belief in due_beliefs:
            # Need to reconstruct the question
            # In production, this would be stored with the belief
            question = Question(
                id=belief.question_id,
                text="[Reconstructed question]",
                question_type="CORE_CONCEPT",
            )

            result = await self.test_belief(belief, question)
            results.append(result)

            if self.debug:
                print(f"Tested belief {belief.id}: {result.recall_quality:.2f}")

        return results
