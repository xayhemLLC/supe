"""GENERATE_FOLLOWUP_QUESTIONS state - Create questions from gaps and insights.

This state generates follow-up questions based on:
- Identified knowledge gaps
- Unresolved questions
- Interesting patterns discovered
- Related topics that emerged during learning
"""

from typing import TYPE_CHECKING, List

from ..types import LearningState, QuestionType
from ..models import Question
from .base import BaseState

if TYPE_CHECKING:
    from ..models import LearningContext


class GenerateFollowupQuestionsState(BaseState):
    """Generate follow-up questions to address gaps and deepen understanding.

    This state:
    1. Analyzes identified gaps
    2. Reviews unresolved questions
    3. Examines beliefs for related concepts
    4. Creates targeted questions to fill gaps
    5. Adds questions to queue for future learning
    """

    async def execute(self, context: "LearningContext") -> LearningState:
        """Execute followup question generation.

        Args:
            context: Current learning context.

        Returns:
            Next state (SCHEDULE_REVIEW).
        """
        self._log("=== GENERATE_FOLLOWUP_QUESTIONS State ===")

        followup_questions = []

        # Generate questions from gaps
        gap_questions = self._generate_from_gaps(context)
        followup_questions.extend(gap_questions)
        self._log(f"Generated {len(gap_questions)} questions from gaps")

        # Generate questions from beliefs (related concepts)
        if context.beliefs_created:
            concept_questions = self._generate_from_beliefs(context)
            followup_questions.extend(concept_questions)
            self._log(f"Generated {len(concept_questions)} questions from beliefs")

        # Check for unresolved questions in gaps
        unresolved = context.metadata.get("unresolved_questions", [])
        if unresolved:
            clarification_questions = self._generate_clarifications(context)
            followup_questions.extend(clarification_questions)
            self._log(f"Generated {len(clarification_questions)} clarification questions")

        # Add questions to context
        for q in followup_questions:
            context.add_followup_question(q)

        self._log(f"Total followup questions: {len(followup_questions)}")

        return LearningState.SCHEDULE_REVIEW

    def _generate_from_gaps(self, context: "LearningContext") -> List[Question]:
        """Generate questions targeting knowledge gaps.

        Each gap becomes a direct question.

        Args:
            context: Learning context with gaps.

        Returns:
            List of questions addressing gaps.
        """
        questions = []

        for gap_text in context.gaps:
            # Create CORE_CONCEPT question for each gap
            question = Question.create(
                text=f"What is {gap_text}?",
                question_type=QuestionType.CORE_CONCEPT,
            )
            questions.append(question)

            # If gap seems operational, add operational question
            if self._seems_operational(gap_text):
                op_question = Question.create(
                    text=f"How do you use {gap_text}?",
                    question_type=QuestionType.OPERATIONAL,
                )
                questions.append(op_question)

        return questions

    def _generate_from_beliefs(self, context: "LearningContext") -> List[Question]:
        """Generate questions from belief content.

        Examines beliefs for related concepts and generates
        questions to deepen understanding.

        Args:
            context: Learning context with beliefs.

        Returns:
            List of questions about related concepts.
        """
        questions = []

        for belief in context.beliefs_created:
            # Extract related concepts from belief content
            related_concepts = self._extract_related_concepts(belief)

            # Generate questions for related concepts
            for concept in related_concepts[:3]:  # Limit to top 3
                question = Question.create(
                    text=f"How does {concept} relate to {context.focus_question.text if context.focus_question else 'the topic'}?",
                    question_type=QuestionType.IMPACT,
                )
                questions.append(question)

        return questions[:5]  # Limit total

    def _generate_clarifications(self, context: "LearningContext") -> List[Question]:
        """Generate clarification questions for unresolved questions.

        Takes unresolved questions and rephrases or breaks them down.

        Args:
            context: Learning context with unresolved questions.

        Returns:
            List of clarification questions.
        """
        questions = []

        # Get unresolved questions from metadata
        unresolved_list = context.metadata.get("unresolved_questions", [])

        for unresolved in unresolved_list[:3]:  # Limit
            # Create a simplified version
            clarification = Question.create(
                text=f"Can you clarify: {unresolved}",
                question_type=QuestionType.CORE_CONCEPT,
            )
            questions.append(clarification)

        return questions

    def _seems_operational(self, gap_text: str) -> bool:
        """Check if a gap seems to be about operations/usage.

        Args:
            gap_text: Gap description.

        Returns:
            True if gap seems operational.
        """
        operational_keywords = [
            "hook", "function", "method", "command", "tool",
            "api", "library", "framework", "system",
        ]

        gap_lower = gap_text.lower()
        return any(keyword in gap_lower for keyword in operational_keywords)

    def _extract_related_concepts(self, belief) -> List[str]:
        """Extract related concepts from belief.

        Args:
            belief: Belief to analyze.

        Returns:
            List of related concept names.
        """
        concepts = []

        # Extract from CornellNote content
        if hasattr(belief.content, 'notes'):
            notes = belief.content.notes

            # Simple extraction: capitalized words and technical terms
            words = notes.split()
            for word in words:
                # Capitalized words might be concepts
                if word and word[0].isupper() and len(word) > 3:
                    clean = word.strip('.,;:')
                    if clean not in concepts:
                        concepts.append(clean)

        # Extract from Theorem content
        if hasattr(belief.content, 'statement'):
            statement = belief.content.statement
            # Extract mathematical concepts
            math_terms = ['property', 'operation', 'function', 'relation']
            for term in math_terms:
                if term in statement.lower():
                    concepts.append(term)

        return concepts[:10]  # Limit
