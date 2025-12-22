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
import re
from typing import Dict, List, Tuple


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
        try:
            queries = self._build_search_queries(query)
            if not queries:
                queries = [query]

            # Collect and score results across multiple query strings.
            scored: Dict[int, float] = {}
            cards_by_id: Dict[int, object] = {}

            for qi, q in enumerate(queries):
                # ABMemory.search_cards() is LIKE-based; short focused queries work best.
                cards = self.machine.memory.search_cards(
                    q,
                    limit=8,
                    track="awareness",
                )
                for rank, card in enumerate(cards):
                    cards_by_id[card.id] = card
                    # Higher score for earlier query + higher rank.
                    score = (len(queries) - qi) * 10.0 + (8 - rank)
                    scored[card.id] = scored.get(card.id, 0.0) + score

            # Sort by score desc, then by recency (higher id tends to be newer)
            ordered_ids = sorted(scored.keys(), key=lambda cid: (scored[cid], cid), reverse=True)

            results = []
            for cid in ordered_ids[:8]:
                card = cards_by_id[cid]
                content = self._extract_card_text(card)
                if content:
                    results.append((cid, content))

            return results

        except Exception as e:
            self._log(f"Memory search failed: {e}")
            return []

    def _build_search_queries(self, question: str) -> List[str]:
        """Build small, high-signal queries from a natural-language question.

        ABMemory search is LIKE-based over master fields, so shorter keyword
        queries are much more effective than full sentences.
        """
        q = (question or "").strip().lower()
        if not q:
            return []

        # Pull tokens and drop common stopwords.
        tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", q)
        stop = {
            "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "without",
            "is", "are", "was", "were", "be", "been", "being", "does", "do", "did",
            "how", "what", "why", "when", "where", "explain", "describe",
            "work", "works", "working",
        }
        tokens = [t for t in tokens if t not in stop and len(t) >= 3]

        # Prefer known Discord doc anchors if present.
        keywords_priority = [
            "oauth2", "gateway", "intents", "identify", "resume", "heartbeat",
            "rate", "limits", "rate-limits", "opcodes", "status", "permissions",
            "interactions", "interaction", "application", "commands",
            "webhook", "webhooks", "channels", "channel", "guild", "guilds",
            "user", "users",
        ]

        phrases: List[str] = []
        if "rate" in tokens and "limits" in tokens:
            phrases.append("rate limits")
        if "gateway" in tokens and "events" in tokens:
            phrases.append("gateway events")
        if "application" in tokens and "commands" in tokens:
            phrases.append("application commands")

        # Build ordered query list (unique, stable).
        queries: List[str] = []
        seen = set()

        def add(s: str):
            s = s.strip()
            if not s or s in seen:
                return
            seen.add(s)
            queries.append(s)

        for p in phrases:
            add(p)

        for k in keywords_priority:
            if k in tokens:
                add(k)

        # Add a few longest remaining tokens (often specific nouns).
        for t in sorted(tokens, key=len, reverse=True)[:6]:
            add(t)

        return queries[:12]

    def _extract_card_text(self, card) -> str:
        """Extract readable, searchable text from a card (prioritize docs buffers)."""
        parts: List[str] = []

        # Include master fields (ABMemory search uses these; they often include a snippet).
        if getattr(card, "master_output", None):
            parts.append(str(card.master_output)[:4000])
        if getattr(card, "master_input", None):
            parts.append(str(card.master_input)[:500])

        # Prefer these buffers for docs ingestion.
        preferred = {"text", "raw", "content", "md", "markdown", "title"}
        for buf in getattr(card, "buffers", []) or []:
            if buf.name not in preferred:
                continue
            try:
                txt = buf.payload.decode("utf-8", errors="ignore")
            except Exception:
                continue
            if not txt:
                continue
            parts.append(txt[:8000])

        # Fallback: take a small slice of any buffer.
        if not parts:
            for buf in getattr(card, "buffers", []) or []:
                try:
                    txt = buf.payload.decode("utf-8", errors="ignore")
                except Exception:
                    continue
                if txt:
                    parts.append(txt[:2000])
                    break

        return "\n\n".join(parts).strip()

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
