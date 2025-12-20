"""INTEGRATE_KNOWLEDGE state - Synthesize beliefs from evidence.

This state is shared by both INGEST and EXPLORE modes. It:
1. Collects evidence gathered in previous states
2. Synthesizes mode-specific knowledge representation:
   - INGEST: CornellNote
   - EXPLORE: Theorem
3. Creates Belief wrapping the knowledge
4. Stores belief in context and AB Memory

This is where raw evidence becomes structured knowledge.
"""

from ..models import LearningContext, Belief
from ..types import LearningState, Mode, QuestionStatus, Confidence
from ..modes.ingest import synthesize_cornell_note, create_belief_from_cornell_note
from ..modes.explore import synthesize_theorem, create_belief_from_theorem
from ..storage import store_belief
from .base import BaseState


class IntegrateKnowledgeState(BaseState):
    """Integrate evidence into structured knowledge."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Synthesize belief from collected evidence.

        Args:
            context: Learning context.

        Returns:
            Next state (SELF_TEST or IDLE).
        """
        self._log("Integrating knowledge from evidence")

        if context.focus_question is None:
            self._log("ERROR: No focus question")
            return LearningState.IDLE_OR_TERMINATE

        question = context.focus_question
        evidence_list = context.evidence_collected

        self._log(f"Question: {question.text}")
        self._log(f"Evidence count: {len(evidence_list)}")

        if not evidence_list:
            self._log("WARNING: No evidence collected - creating gap")
            context.add_gap(f"No evidence found for: {question.text}")
            # Mark question as deferred
            question.status = QuestionStatus.DEFERRED
            self._log_transition(LearningState.INTEGRATE_KNOWLEDGE, LearningState.IDLE_OR_TERMINATE)
            return LearningState.IDLE_OR_TERMINATE

        # Synthesize based on mode
        if context.mode == Mode.INGEST:
            belief = self._synthesize_ingest_belief(question, evidence_list)
        elif context.mode == Mode.EXPLORE:
            belief = self._synthesize_explore_belief(question, evidence_list, context)
        else:
            self._log(f"ERROR: Unknown mode {context.mode}")
            return LearningState.IDLE_OR_TERMINATE

        # Add belief to context
        context.add_belief(belief)
        self._log(f"Belief created with confidence {belief.confidence:.2f}")

        # Store belief (would need question_card_id for proper linking)
        # For now, store without question link
        # store_belief(self.machine.memory, belief, question_card_id=?, evidence_card_ids=[])

        # Mark question as answered
        question.status = QuestionStatus.ANSWERED

        # Transition to SELF_TEST to validate learning
        self._log_transition(LearningState.INTEGRATE_KNOWLEDGE, LearningState.SELF_TEST)
        return LearningState.SELF_TEST

    def _synthesize_ingest_belief(self, question, evidence_list) -> Belief:
        """Synthesize belief for INGEST mode (Cornell note).

        Args:
            question: The question being answered.
            evidence_list: List of Evidence objects.

        Returns:
            Belief with CornellNote content.
        """
        self._log("Synthesizing Cornell note...")

        # Create Cornell note
        cornell_note = synthesize_cornell_note(question, evidence_list)

        self._log(f"  Cue: {cornell_note.cue[:50]}...")
        self._log(f"  Notes: {len(cornell_note.notes)} chars")
        self._log(f"  Examples: {len(cornell_note.examples)}")

        # Calculate confidence from evidence
        if evidence_list:
            avg_confidence = sum(float(e.confidence) for e in evidence_list) / len(evidence_list)
            confidence = Confidence(avg_confidence)
        else:
            confidence = Confidence(0.5)

        # Create belief
        belief = create_belief_from_cornell_note(
            question=question,
            note=cornell_note,
            evidence_list=evidence_list,
            confidence=confidence,
        )

        return belief

    def _synthesize_explore_belief(self, question, evidence_list, context) -> Belief:
        """Synthesize belief for EXPLORE mode (Theorem).

        Args:
            question: The question being answered.
            evidence_list: List of Evidence objects.
            context: Learning context with experiment results.

        Returns:
            Belief with Theorem content.
        """
        self._log("Synthesizing theorem...")

        # Get experiment results from context metadata
        claim = context.metadata.get("explore_claim", {})
        experiment_results = context.metadata.get("experiment_results", [])

        self._log(f"  Claim: {claim.get('hypothesis', 'unknown')}")
        self._log(f"  Experiments: {len(experiment_results)}")

        # Create theorem
        theorem = synthesize_theorem(question, claim, experiment_results)

        self._log(f"  Status: {theorem.status.value}")
        self._log(f"  Properties validated: {theorem.properties_validated}")

        # Create belief
        belief = create_belief_from_theorem(
            question=question,
            theorem=theorem,
            evidence_list=evidence_list,
        )

        return belief
