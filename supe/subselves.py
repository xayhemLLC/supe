"""Subselves for the Supe.

Subselves are specialized cognitive agents that process input:
- LearnerSubself: Cornell Q&A style note-taking
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import re

from ab.abdb import ABMemory
from ab.models import Buffer, Card


@dataclass
class CornellNote:
    """A Cornell-style note with Q&A format.
    
    Left column: Questions, prompts, cues
    Right column: Answers, examples, demos
    Bottom: 1-paragraph summary
    """
    
    questions: List[str] = field(default_factory=list)  # Cues/Questions
    answers: Dict[str, str] = field(default_factory=dict)  # Question -> Answer
    examples: List[str] = field(default_factory=list)  # Examples/demos
    summary: str = ""  # 1-paragraph summary
    citations: List[str] = field(default_factory=list)  # Sources
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "questions": self.questions,
            "answers": self.answers,
            "examples": self.examples,
            "summary": self.summary,
            "citations": self.citations,
        }
    
    def to_markdown(self) -> str:
        """Render as Cornell notes markdown."""
        lines = ["# Cornell Notes\n"]
        
        # Q&A pairs
        if self.questions:
            lines.append("## Questions & Answers\n")
            lines.append("| Cue/Question | Answer |")
            lines.append("|--------------|--------|")
            for q in self.questions:
                a = self.answers.get(q, "TBD")[:100]
                lines.append(f"| {q} | {a} |")
            lines.append("")
        
        # Examples
        if self.examples:
            lines.append("## Examples\n")
            for ex in self.examples[:5]:
                lines.append(f"- {ex}")
            lines.append("")
        
        # Summary
        if self.summary:
            lines.append("## Summary\n")
            lines.append(self.summary)
            lines.append("")
        
        # Citations
        if self.citations:
            lines.append("## Sources\n")
            for c in self.citations:
                lines.append(f"- {c}")
        
        return "\n".join(lines)


class LearnerSubself:
    """A subself that learns from inputs using Cornell Q&A notes.
    
    Ingests master card inputs and creates structured notes:
    - Extracts key questions from content
    - Finds answers in the text
    - Identifies examples/demos
    - Creates 1-paragraph summary
    
    Example:
        learner = LearnerSubself(memory)
        notes = await learner.learn(master_card)
    """
    
    name = "learner"
    
    def __init__(self, memory: ABMemory):
        self.memory = memory
    
    async def learn(self, master_card: Card) -> CornellNote:
        """Learn from master card inputs using Cornell method.
        
        Args:
            master_card: The master card with input buffers.
        
        Returns:
            CornellNote with structured Q&A.
        """
        # Extract text from all buffers
        texts = []
        citations = []
        
        for buf in master_card.buffers:
            if buf.payload:
                try:
                    text = buf.payload.decode("utf-8")
                    texts.append(text)
                    # Get citation from headers
                    if buf.headers.get("url"):
                        citations.append(buf.headers["url"])
                    elif buf.headers.get("title"):
                        citations.append(buf.headers["title"])
                except:
                    pass
        
        full_text = "\n".join(texts)
        
        # Extract questions, answers, examples
        notes = CornellNote(citations=citations)
        
        # Find questions in text (sentences ending with ?)
        questions = re.findall(r"[A-Z][^.!?]*\?", full_text)
        notes.questions = questions[:10]  # Limit
        
        # For each question, try to find answer (next sentence)
        for q in notes.questions:
            pos = full_text.find(q)
            if pos != -1:
                after = full_text[pos + len(q):pos + len(q) + 500]
                # First sentence after question
                match = re.search(r"[A-Z][^.!?]*[.!]", after)
                if match:
                    notes.answers[q] = match.group(0).strip()
        
        # Find examples (lines with "example", "for instance", code blocks)
        example_patterns = [
            r"[Ee]xample:?\s*([^\n]+)",
            r"[Ff]or instance:?\s*([^\n]+)",
            r"```[\s\S]*?```",
        ]
        for pattern in example_patterns:
            matches = re.findall(pattern, full_text)
            notes.examples.extend(matches[:3])
        
        # Generate summary (first paragraph after any "summary" heading, or first para)
        summary_match = re.search(r"[Ss]ummary[:\s]*\n([^\n]+)", full_text)
        if summary_match:
            notes.summary = summary_match.group(1)
        elif full_text:
            # First substantial paragraph
            paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 50]
            if paragraphs:
                notes.summary = paragraphs[0][:300]
        
        # Store notes as a card
        await self._store_notes(notes, master_card.id)
        
        return notes
    
    async def _store_notes(self, notes: CornellNote, source_card_id: int) -> int:
        """Store Cornell notes as a card in awareness track."""
        notes_json = json.dumps(notes.to_dict()).encode("utf-8")
        notes_md = notes.to_markdown().encode("utf-8")
        
        buffers = [
            Buffer(
                name="notes_json",
                headers={"type": "cornell_notes", "format": "json"},
                payload=notes_json,
            ),
            Buffer(
                name="notes_md",
                headers={"type": "cornell_notes", "format": "markdown"},
                payload=notes_md,
            ),
        ]
        
        card = self.memory.store_card(
            label="cornell_notes",
            buffers=buffers,
            track="awareness",
            master_input=f"source_card:{source_card_id}",
            master_output=notes.summary[:100] if notes.summary else "Notes",
        )
        
        # Link to source
        self.memory.create_connection(
            source_card_id=source_card_id,
            target_card_id=card.id,
            relation="produced_notes",
        )
        
        return card.id
