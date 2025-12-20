"""12-Step Learning Protocol.

A curiosity-driven learning system that produces forward momentum,
not dead-end grades. Focused on gaps and unresolved questions.

Steps:
1. Sense - Acquire source
2. Orient - Topic, Scope, Goal
3. Extract - Meaningful concepts only
4. Question - 4 classes (Concepts, Operations, Constraints, Impact)
5. Answer - Own words, examples
6. Summarize - Conceptual + Operational
7. Experiment - Concrete tests
8. Self-Test - Retrieval practice
9. Gaps - What I still don't know
10. Unresolved - Follow-up questions
11. Iterate - Feed into next cycle
12. Reinforce - Spaced repetition

Endpoint: "What do I still not know, and what should next learning be?"
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import json
import re
import hashlib

from ab.abdb import ABMemory
from ab.models import Buffer, Card


class QuestionClass(Enum):
    """Four classes of questions."""
    CONCEPT = "concept"      # What is it?
    OPERATION = "operation"  # How do I use it?
    CONSTRAINT = "constraint"  # What breaks / edge cases?
    IMPACT = "impact"        # Why should I care?


@dataclass
class Question:
    """A question to answer."""
    text: str
    qclass: QuestionClass
    cue: str  # Cornell left-column cue
    

@dataclass
class Answer:
    """Answer in your own words."""
    question: Question
    text: str  # Own words, not copy-paste
    examples: List[str] = field(default_factory=list)
    citation: Optional[str] = None
    confidence: float = 0.0  # 0-1


@dataclass 
class Experiment:
    """A concrete test to verify understanding."""
    id: str
    instruction: str
    expected_outcome: str
    actual_outcome: Optional[str] = None
    passed: Optional[bool] = None


@dataclass
class Gap:
    """Something I still don't know."""
    question: str
    why_unknown: str  # Why couldn't I answer this?
    priority: int = 1  # 1-5, higher = more urgent


@dataclass
class LearningSession:
    """Result of one learning cycle."""
    
    # Step 2: Orient
    topic: str = ""
    scope: str = ""
    goal: str = ""
    
    # Step 3: Concepts
    concepts: List[str] = field(default_factory=list)
    
    # Steps 4-5: Q&A
    questions: List[Question] = field(default_factory=list)
    answers: List[Answer] = field(default_factory=list)
    
    # Step 6: Summaries
    conceptual_summary: str = ""  # What it means
    operational_summary: str = ""  # What I do differently
    
    # Step 7: Experiments
    experiments: List[Experiment] = field(default_factory=list)
    
    # Step 8-9: Test results and gaps
    test_passed: int = 0
    test_failed: int = 0
    gaps: List[Gap] = field(default_factory=list)
    certainties: List[str] = field(default_factory=list)
    
    # Step 10: Unresolved for next cycle
    unresolved: List[str] = field(default_factory=list)
    
    # Metadata
    source_url: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "scope": self.scope, 
            "goal": self.goal,
            "concepts": self.concepts,
            "questions": [{"text": q.text, "class": q.qclass.value, "cue": q.cue} for q in self.questions],
            "answers": [{"question": a.question.text, "text": a.text, "confidence": a.confidence} for a in self.answers],
            "conceptual_summary": self.conceptual_summary,
            "operational_summary": self.operational_summary,
            "experiments": [{"id": e.id, "instruction": e.instruction, "passed": e.passed} for e in self.experiments],
            "test_passed": self.test_passed,
            "test_failed": self.test_failed,
            "gaps": [{"question": g.question, "why": g.why_unknown, "priority": g.priority} for g in self.gaps],
            "certainties": self.certainties,
            "unresolved": self.unresolved,
            "source_url": self.source_url,
            "timestamp": self.timestamp,
        }


class Learner:
    """12-Step Learning Protocol implementation.
    
    Curiosity-driven learning that produces forward momentum.
    Endpoint: What do I still not know?
    
    Example:
        learner = Learner(memory, debug=True)
        session = await learner.learn(content, source_url)
        
        print(f"Gaps: {len(session.gaps)}")
        print(f"Unresolved for next cycle: {session.unresolved}")
    """
    
    def __init__(self, memory: ABMemory, debug: bool = False):
        self.memory = memory
        self.debug = debug
        self._session = LearningSession()
    
    def _log(self, step: int, name: str, msg: str) -> None:
        if self.debug:
            print(f"[Step {step}: {name}] {msg}")
    
    async def learn(
        self,
        content: str,
        source_url: str,
        prior_unresolved: Optional[List[str]] = None,
    ) -> LearningSession:
        """Execute full 12-step learning protocol.
        
        Args:
            content: Source content (HTML/text).
            source_url: Where this came from.
            prior_unresolved: Unresolved questions from previous cycle.
        
        Returns:
            LearningSession with gaps and unresolved for next cycle.
        """
        self._session = LearningSession(
            source_url=source_url,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        # Step 1: Sense (already done - content is input)
        self._log(1, "SENSE", f"Acquired {len(content):,} bytes from {source_url[:50]}...")
        
        # Step 2: Orient
        self._step_orient(content)
        
        # Step 3: Extract
        self._step_extract(content)
        
        # Step 4: Question (including prior unresolved)
        self._step_question(content, prior_unresolved or [])
        
        # Step 5: Answer
        self._step_answer(content)
        
        # Step 6: Summarize
        self._step_summarize()
        
        # Step 7: Experiment
        self._step_experiment()
        
        # Step 8: Self-Test
        self._step_self_test()
        
        # Step 9: Gaps
        self._step_gaps()
        
        # Step 10: Unresolved
        self._step_unresolved()
        
        # Store in memory
        self._store_session()
        
        # Output endpoint - NOT a grade!
        self._log(0, "ENDPOINT", 
            f"What I still don't know: {len(self._session.gaps)} gaps, "
            f"{len(self._session.unresolved)} unresolved for next cycle")
        
        return self._session
    
    # =========================================================================
    # Step 2: Orient - What is this about? Why? What outcome?
    # =========================================================================
    def _step_orient(self, content: str):
        self._log(2, "ORIENT", "Identifying topic, scope, goal...")
        
        # Extract topic from title or first heading
        title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            self._session.topic = title_match.group(1).strip()[:100]
        else:
            # First sentence
            first = re.search(r'[A-Z][^.!?]+[.!?]', content[:500])
            self._session.topic = first.group(0)[:100] if first else "Unknown topic"
        
        # Scope: what's covered?
        headings = re.findall(r'<h[1-3][^>]*>([^<]+)</h[1-3]>', content, re.IGNORECASE)
        if headings:
            self._session.scope = f"Covers: {', '.join(headings[:5])}"
        else:
            self._session.scope = "General coverage"
        
        # Goal: why am I learning this?
        self._session.goal = "Understand and apply concepts to build working systems"
        
        self._log(2, "ORIENT", f"Topic: {self._session.topic[:50]}...")
    
    def _step_extract(self, content: str):
        self._log(3, "EXTRACT", "Pulling core entities, operations, rules...")
        
        # Cleaned content for semantic extraction (no HTML tags)
        clean_content = re.sub(r'<[^>]*>', ' ', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        concepts = []
        
        # Entities (nouns that are defined) - search in clean content
        potential_entities = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', clean_content)
        concepts.extend(potential_entities)
        
        # Operations (verbs/actions) - search in clean content
        operations = re.findall(r'(?:can|should|must|will)\s+(\w+)', clean_content, re.IGNORECASE)
        concepts.extend([f"can {op}" for op in operations[:5]])
        
        # Rules (constraints) - search in clean content
        rules = re.findall(r'(?:must|cannot|should not|required)\s+([^.]+)', clean_content, re.IGNORECASE)
        concepts.extend([r[:50] for r in rules[:5]])
        
        # Changes (if changelog) - search in clean content
        changes = re.findall(r'(?:new|added|changed|updated|deprecated|removed):?\s*([^.]+)', clean_content, re.IGNORECASE)
        concepts.extend([f"CHANGE: {c[:40]}" for c in changes[:5]])
        
        # Deduplicate and Filter
        seen = set()
        unique = []
        
        # Noise filter for minified CSS/JS
        def is_noise(s: str) -> bool:
            # Minified things like 'JoMilv' are short and have high randomness
            if len(s) < 8 and re.search(r'[a-z][A-Z][a-z]', s):
                return True
            # Too short
            if len(s) < 4:
                return True
            # Common boilerplate/noise
            if s.lower() in {'the', 'and', 'with', 'from', 'this', 'that', 'javascript', 'react', 'next'}:
                return True
            # Contains digits but isn't a known pattern
            if any(char.isdigit() for char in s) and len(s) < 10:
                return True
            return False

        for c in concepts:
            # Strip tags repeatedly to handle nested/broken HTML
            c_label = c.strip()
            while '<' in c_label and '>' in c_label:
                new_label = re.sub(r'<[^>]*>', '', c_label).strip()
                if new_label == c_label: break
                c_label = new_label
            
            # Clean up the label for filtering
            clean_label = re.sub(r'^CHANGE: ', '', c_label).strip()
            clean_label = re.sub(r'^can ', '', clean_label).strip()
            # Remove any trailing fragments from broken HTML matches
            clean_label = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', clean_label)
            
            if is_noise(clean_label):
                continue
                
            # Stricter "looks like code" filter
            if any(char in clean_label for char in {'=', '{', '}', '[', ']', ';', '(', ')', '/', '\\'}):
                continue
            
            # Final check - must contain mostly letters/spaces
            if not re.search(r'[a-zA-Z]{4,}', clean_label):
                continue
                
            c_lower = c_label.lower()
            if c_lower and c_lower not in seen:
                seen.add(c_lower)
                unique.append(c_label)
        
        self._session.concepts = unique[:15]
        self._log(3, "EXTRACT", f"Found {len(self._session.concepts)} retrieval-worthy concepts")
    
    # =========================================================================
    # Step 4: Question - 4 classes
    # =========================================================================
    def _step_question(self, content: str, prior_unresolved: List[str]):
        self._log(4, "QUESTION", "Generating 4 classes of questions...")
        
        questions = []
        
        # Add prior unresolved as high-priority questions
        for unres in prior_unresolved:
            questions.append(Question(
                text=unres,
                qclass=QuestionClass.CONCEPT,
                cue="[PRIOR] " + unres[:30],
            ))
        
        for concept in self._session.concepts[:10]:
            # A) Core Concepts - What is it?
            questions.append(Question(
                text=f"What is {concept}?",
                qclass=QuestionClass.CONCEPT,
                cue=f"Define: {concept[:20]}",
            ))
            
            # B) Operations - How do I use it?
            questions.append(Question(
                text=f"How do I use {concept}?",
                qclass=QuestionClass.OPERATION,
                cue=f"Use: {concept[:20]}",
            ))
            
            # C) Constraints - What breaks?
            questions.append(Question(
                text=f"What are the limitations of {concept}?",
                qclass=QuestionClass.CONSTRAINT,
                cue=f"Limits: {concept[:20]}",
            ))
            
            # D) Impact - Why care?
            questions.append(Question(
                text=f"Why does {concept} matter?",
                qclass=QuestionClass.IMPACT,
                cue=f"Why: {concept[:20]}",
            ))
        
        self._session.questions = questions[:30]  # Limit
        self._log(4, "QUESTION", f"Generated {len(self._session.questions)} questions across 4 classes")
    
    # =========================================================================
    # Step 5: Answer - Own words, no copy-paste
    # =========================================================================
    def _step_answer(self, content: str):
        self._log(5, "ANSWER", "Answering in own words...")
        
        for q in self._session.questions:
            # Find relevant content
            term = self._extract_term(q.text)
            answer_text, examples, citation = self._find_answer(term, content)
            
            if answer_text:
                # Rephrase in own words (simplified for now)
                own_words = self._rephrase(answer_text)
                
                self._session.answers.append(Answer(
                    question=q,
                    text=own_words,
                    examples=examples,
                    citation=citation,
                    confidence=0.7 if examples else 0.5,
                ))
            else:
                # Can't answer - will become a gap
                self._session.answers.append(Answer(
                    question=q,
                    text="",
                    confidence=0.0,
                ))
        
        answered = sum(1 for a in self._session.answers if a.text)
        self._log(5, "ANSWER", f"Answered {answered}/{len(self._session.questions)}")
    
    def _extract_term(self, question: str) -> str:
        """Extract key term from question."""
        term = re.sub(r'^(What is|How do I use|What are the limitations of|Why does)\s+', '', question, flags=re.IGNORECASE)
        return term.rstrip('?').strip()
    
    def _find_answer(self, term: str, content: str) -> Tuple[str, List[str], Optional[str]]:
        """Find answer in content."""
        if not term:
            return "", [], None
            
        pattern = rf"(?i){re.escape(term[:30])}[^.]*\.([^.]+\.)"
        match = re.search(pattern, content)
        
        if match:
            answer = match.group(0).strip()[:200]
            # Look for code examples
            examples = []
            pos = match.start()
            code = re.search(r'<code>([^<]+)</code>', content[pos:pos+300])
            if code:
                examples.append(code.group(1))
            return answer, examples, self._session.source_url
        
        return "", [], None
    
    def _rephrase(self, text: str) -> str:
        """Rephrase in own words (placeholder - would use LLM)."""
        # For now, clean up HTML and simplify
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:150] + "..." if len(clean) > 150 else clean
    
    # =========================================================================
    # Step 6: Summarize - Conceptual + Operational
    # =========================================================================
    def _step_summarize(self):
        self._log(6, "SUMMARIZE", "Creating two-layer summary...")
        
        # Conceptual: What it means
        answered = [a for a in self._session.answers if a.text]
        if answered:
            self._session.conceptual_summary = (
                f"This covers {len(self._session.concepts)} concepts: "
                f"{', '.join(self._session.concepts[:5])}. "
                f"Key insight: {answered[0].text[:100] if answered else 'TBD'}"
            )
        else:
            self._session.conceptual_summary = "Unable to form conceptual summary - need more data"
        
        # Operational: What I do differently
        operations = [a for a in self._session.answers if a.question.qclass == QuestionClass.OPERATION and a.text]
        if operations:
            self._session.operational_summary = (
                f"Actions: {len(operations)} operations learned. "
                f"Next: Apply {operations[0].question.text[:50]}"
            )
        else:
            self._session.operational_summary = "No operational changes identified yet"
        
        self._log(6, "SUMMARIZE", f"Conceptual: {len(self._session.conceptual_summary)} chars, Operational: {len(self._session.operational_summary)} chars")
    
    # =========================================================================
    # Step 7: Experiment - Concrete tests
    # =========================================================================
    def _step_experiment(self):
        self._log(7, "EXPERIMENT", "Creating concrete tests...")
        
        for i, ans in enumerate(self._session.answers[:5]):
            if ans.text and ans.examples:
                exp = Experiment(
                    id=f"exp_{i+1}",
                    instruction=f"Try: {ans.question.text}",
                    expected_outcome=ans.text[:100],
                )
                self._session.experiments.append(exp)
        
        self._log(7, "EXPERIMENT", f"Created {len(self._session.experiments)} experiments")
    
    # =========================================================================
    # Step 8: Self-Test - Retrieval practice
    # =========================================================================
    def _step_self_test(self):
        self._log(8, "SELF-TEST", "Testing retrieval from cues only...")
        
        passed = 0
        failed = 0
        
        for ans in self._session.answers:
            # Can we retrieve the answer from just the cue?
            # For now: has answer + has citation or example = pass
            if ans.text and (ans.citation or ans.examples):
                passed += 1
            elif ans.text:
                passed += 1  # Partial
            else:
                failed += 1
        
        self._session.test_passed = passed
        self._session.test_failed = failed
        
        self._log(8, "SELF-TEST", f"Passed: {passed}, Failed: {failed}")
    
    # =========================================================================
    # Step 9: Gaps - What I still don't know
    # =========================================================================
    def _step_gaps(self):
        self._log(9, "GAPS", "Identifying what I still don't know...")
        
        gaps = []
        certainties = []
        
        for ans in self._session.answers:
            if not ans.text:
                gaps.append(Gap(
                    question=ans.question.text,
                    why_unknown="Could not find answer in source",
                    priority=3,
                ))
            elif ans.confidence < 0.5:
                gaps.append(Gap(
                    question=ans.question.text,
                    why_unknown="Low confidence - need verification",
                    priority=2,
                ))
            elif ans.confidence >= 0.7:
                certainties.append(ans.question.text)
        
        # Add constraint questions as gaps if not answered
        constraint_qs = [a for a in self._session.answers 
                        if a.question.qclass == QuestionClass.CONSTRAINT and not a.text]
        for cq in constraint_qs:
            gaps.append(Gap(
                question=cq.question.text,
                why_unknown="Edge cases not explored",
                priority=4,  # High priority
            ))
        
        self._session.gaps = gaps
        self._session.certainties = certainties
        
        self._log(9, "GAPS", f"Certain: {len(certainties)}, Gaps: {len(gaps)}")
    
    # =========================================================================
    # Step 10: Unresolved - Fuel for next cycle
    # =========================================================================
    def _step_unresolved(self):
        self._log(10, "UNRESOLVED", "Generating follow-up questions for next cycle...")
        
        unresolved = []
        
        # High-priority gaps become unresolved
        for gap in sorted(self._session.gaps, key=lambda g: -g.priority)[:5]:
            unresolved.append(gap.question)
        
        # Generate curiosity questions
        if self._session.concepts:
            # What else could this connect to?
            unresolved.append(f"How does {self._session.concepts[0]} relate to other systems?")
            # What are real-world examples?
            unresolved.append(f"What are production use cases for {self._session.topic[:30]}?")
        
        self._session.unresolved = unresolved
        
        self._log(10, "UNRESOLVED", f"{len(unresolved)} questions for next learning cycle")
    
    # =========================================================================
    # Store & Reinforce
    # =========================================================================
    def _store_session(self):
        """Store learning session in memory."""
        session_json = json.dumps(self._session.to_dict()).encode()
        
        # Calculate next review dates (spaced repetition)
        now = datetime.utcnow()
        review_schedule = {
            "day_1": (now + timedelta(days=1)).isoformat(),
            "day_3": (now + timedelta(days=3)).isoformat(),
            "day_7": (now + timedelta(days=7)).isoformat(),
            "day_14": (now + timedelta(days=14)).isoformat(),
        }
        
        buffers = [
            Buffer(
                name="session",
                headers={"type": "learning_session", "topic": self._session.topic[:50]},
                payload=session_json,
            ),
            Buffer(
                name="review_schedule",
                headers={"type": "spaced_repetition"},
                payload=json.dumps(review_schedule).encode(),
            ),
            Buffer(
                name="unresolved",
                headers={"type": "next_cycle_fuel", "count": len(self._session.unresolved)},
                payload=json.dumps(self._session.unresolved).encode(),
            ),
        ]
        
        card = self.memory.store_card(
            label="learning_12step",
            buffers=buffers,
            master_input=self._session.source_url,
            master_output=f"Gaps: {len(self._session.gaps)}, Unresolved: {len(self._session.unresolved)}",
            track="awareness",
        )
        
        self._log(12, "STORE", f"Stored as card {card.id}, scheduled for spaced review")
        
        return card.id
    
    def get_prior_unresolved(self) -> List[str]:
        """Get unresolved questions from previous sessions for next cycle."""
        cards = self.memory.search_cards("learning_12step", limit=1)
        if cards:
            for buf in cards[0].buffers:
                if buf.name == "unresolved":
                    return json.loads(buf.payload.decode())
        return []
