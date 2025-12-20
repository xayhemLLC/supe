"""INGEST_DOC state - Learn from documentation and structured content.

This state implements INGEST mode learning:
1. Search AB Memory for relevant content
2. Extract text from cards/buffers
3. Create Evidence with citations
4. Store evidence and link to question

The evidence will be synthesized into Cornell notes in the INTEGRATE_KNOWLEDGE state.
"""

from ..models import LearningContext, Evidence
from ..types import LearningState, EvidenceSource
from ..modes.ingest import process_ingest_content
from ..storage import store_evidence
from .base import BaseState


class IngestDocState(BaseState):
    """INGEST mode: Learn from documentation."""

    async def execute(self, context: LearningContext) -> LearningState:
        """Gather evidence from documentation.

        Args:
            context: Learning context.

        Returns:
            Next state (INTEGRATE_KNOWLEDGE).
        """
        self._log("Starting INGEST mode evidence gathering")

        if context.focus_question is None:
            self._log("ERROR: No focus question")
            return LearningState.IDLE_OR_TERMINATE

        question = context.focus_question
        self._log(f"Learning about: {question.text}")

        # Step 1: Search AB Memory for relevant content
        self._log("Searching AB Memory for relevant content...")
        search_results = self._search_memory(question.text)

        if not search_results:
            self._log("No relevant content found in memory")
            # Create a gap for missing content
            context.add_gap(f"No documentation found for: {question.text}")

            # For demo purposes, create synthetic evidence
            evidence = self._create_synthetic_evidence(question.text)
            context.add_evidence(evidence)

            # Store evidence
            # Note: No question_card_id link yet (would need to store question first)
            store_evidence(self.machine.memory, evidence)

        else:
            # Step 2: Process found content
            self._log(f"Found {len(search_results)} relevant items")
            for card_id, content in search_results[:3]:  # Process top 3 results
                self._log(f"Processing card {card_id}...")

                # Use INGEST utilities to process content
                result = process_ingest_content(
                    content=content,
                    source_url=f"card:{card_id}",
                    max_concepts=5,
                    max_questions=2,
                )

                # Store evidence
                evidence = result["evidence"]
                context.add_evidence(evidence)
                store_evidence(self.machine.memory, evidence)

                # Store generated questions as followup questions
                for q in result["questions"]:
                    context.add_followup_question(q)

                self._log(f"Extracted {len(result['concepts'])} concepts, {len(result['questions'])} questions")

        self._log(f"Total evidence collected: {len(context.evidence_collected)}")
        self._log(f"Total followup questions: {len(context.followup_questions)}")

        # Transition to knowledge integration
        self._log_transition(LearningState.INGEST_DOC, LearningState.INTEGRATE_KNOWLEDGE)
        return LearningState.INTEGRATE_KNOWLEDGE

    def _search_memory(self, query: str) -> list:
        """Search AB Memory for relevant content.

        Args:
            query: Search query.

        Returns:
            List of (card_id, content) tuples.
        """
        # Search for cards in awareness track
        try:
            # Use semantic search if available
            cards = self.machine.memory.search_cards(
                query_text=query,
                track="awareness",
                limit=5,
            )

            results = []
            for card in cards:
                # Extract text content from buffers
                content_parts = []
                for buffer in card.buffers:
                    try:
                        text = buffer.payload.decode('utf-8')
                        content_parts.append(text[:1000])  # First 1000 chars
                    except:
                        continue

                if content_parts:
                    results.append((card.id, "\n".join(content_parts)))

            return results

        except Exception as e:
            self._log(f"Memory search failed: {e}")
            return []

    def _create_synthetic_evidence(self, question: str) -> Evidence:
        """Create synthetic evidence for demonstration.

        In production, this would be replaced with actual content retrieval.

        Args:
            question: The question text.

        Returns:
            Evidence object.
        """
        # Create a simple explanation based on the question
        if "react" in question.lower() and "hook" in question.lower():
            text = """React Hooks are functions that let you use state and other React features
            without writing a class. The most common hooks are useState for managing state and
            useEffect for side effects. Hooks must be called at the top level of your component."""
        elif "api" in question.lower():
            text = f"""An API (Application Programming Interface) provides a way for different
            software systems to communicate. It defines methods and data formats for requesting
            and exchanging information."""
        else:
            text = f"""The topic '{question}' is a fundamental concept in computer science.
            Understanding this concept is important for building robust software systems."""

        evidence = Evidence.create(
            text=text,
            source=EvidenceSource.DOC,
            citations=["synthetic_demo"],
        )
        evidence.validated = True
        evidence.validation_method = "synthetic_generation"
        evidence.confidence = 0.6  # Lower confidence for synthetic

        return evidence
