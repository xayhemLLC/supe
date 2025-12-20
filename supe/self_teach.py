"""Self-Teaching Learning System.

A system that:
1. Consumes documentation
2. Generates questions
3. Finds answers with citations
4. Creates hands-on exercises
5. Tests and grades itself

Like a scientist: prove correctness via evidence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json
import re

from ab.abdb import ABMemory
from ab.models import Buffer, Card


@dataclass
class Knowledge:
    """A piece of learned knowledge with proof."""
    
    question: str
    answer: str
    citations: List[str] = field(default_factory=list)  # Source URLs/refs
    examples: List[str] = field(default_factory=list)   # Code examples
    confidence: float = 0.0  # 0-1 confidence from self-test
    verified: bool = False   # Has it been verified?
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "citations": self.citations,
            "examples": self.examples,
            "confidence": self.confidence,
            "verified": self.verified,
        }


@dataclass
class Exercise:
    """A hands-on exercise to verify understanding."""
    
    id: str
    instruction: str
    expected_outcome: str
    hints: List[str] = field(default_factory=list)
    solution: Optional[str] = None
    passed: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "instruction": self.instruction,
            "expected_outcome": self.expected_outcome,
            "hints": self.hints,
            "solution": self.solution,
            "passed": self.passed,
        }


@dataclass
class TestResult:
    """Result of self-testing."""
    
    question: str
    given_answer: str
    correct_answer: str
    score: float  # 0-1
    citation_found: bool
    example_verified: bool


class SelfTeacher:
    """A self-teaching system that learns and tests itself.
    
    Process:
    1. Consume docs
    2. Extract key concepts
    3. Generate questions
    4. Find answers with citations
    5. Create exercises
    6. Test itself
    7. Grade performance
    
    Example:
        teacher = SelfTeacher(memory, debug=True)
        await teacher.learn(content, source_url)
        results = await teacher.test_self()
        print(f"Score: {results['score']:.1%}")
    """
    
    def __init__(self, memory: ABMemory, debug: bool = False):
        self.memory = memory
        self.debug = debug
        self._knowledge: List[Knowledge] = []
        self._exercises: List[Exercise] = []
    
    def _log(self, step: str, message: str) -> None:
        """Debug logging."""
        if self.debug:
            print(f"[{step}] {message}")
    
    async def learn(
        self,
        content: str,
        source_url: str,
        title: str = "",
    ) -> Dict[str, Any]:
        """Learn from content.
        
        Args:
            content: HTML/text content to learn from.
            source_url: Source URL for citations.
            title: Optional title.
        
        Returns:
            Learning summary.
        """
        self._log("LEARN", f"Starting to learn from: {title or source_url}")
        
        # 1. Extract key concepts
        self._log("EXTRACT", "Extracting key concepts...")
        concepts = self._extract_concepts(content)
        self._log("EXTRACT", f"Found {len(concepts)} concepts")
        
        # 2. Generate questions
        self._log("QUESTIONS", "Generating questions...")
        questions = self._generate_questions(concepts, content)
        self._log("QUESTIONS", f"Generated {len(questions)} questions")
        
        # 3. Find answers with citations
        self._log("ANSWERS", "Finding answers with citations...")
        for q in questions:
            answer, citations, examples = self._find_answer(q, content, source_url)
            if answer:
                knowledge = Knowledge(
                    question=q,
                    answer=answer,
                    citations=citations,
                    examples=examples,
                )
                self._knowledge.append(knowledge)
                self._log("ANSWERS", f"  Q: {q[:50]}... -> Found answer with {len(citations)} citations")
        
        # 4. Create exercises
        self._log("EXERCISES", "Creating exercises...")
        self._exercises = self._create_exercises(self._knowledge, content)
        self._log("EXERCISES", f"Created {len(self._exercises)} exercises")
        
        # 5. Store in memory
        self._log("STORE", "Storing knowledge in memory...")
        card_id = self._store_learning(source_url, title)
        self._log("STORE", f"Stored as card {card_id}")
        
        return {
            "concepts": len(concepts),
            "questions": len(questions),
            "knowledge": len(self._knowledge),
            "exercises": len(self._exercises),
            "card_id": card_id,
        }
    
    def _extract_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content."""
        concepts = []
        
        # Look for headings (traditional HTML)
        headings = re.findall(r'<h[1-3][^>]*>([^<]+)</h[1-3]>', content, re.IGNORECASE)
        concepts.extend([h.strip() for h in headings if len(h.strip()) > 3])
        
        # Look for bold/strong text
        bold = re.findall(r'<(?:b|strong)[^>]*>([^<]+)</(?:b|strong)>', content, re.IGNORECASE)
        concepts.extend([b.strip() for b in bold if len(b.strip()) > 3 and len(b.strip()) < 50])
        
        # Look for title/aria-label attributes (React/Next.js apps)
        titles = re.findall(r'(?:title|aria-label)="([^"]+)"', content)
        concepts.extend([t.strip() for t in titles if len(t.strip()) > 3 and len(t.strip()) < 60])
        
        # Look for JSON object keys that might be concepts
        json_keys = re.findall(r'"([A-Z][a-zA-Z_]+)":', content)
        concepts.extend([k for k in json_keys if len(k) > 3])
        
        # Look for code identifiers (likely API names)
        code_ids = re.findall(r'<code>([A-Z][a-zA-Z_]+)</code>', content)
        concepts.extend([c for c in code_ids if len(c) > 3])
        
        # Look for "Component" patterns (Discord specific)
        components = re.findall(r'([A-Z][a-z]+(?:Component|Button|Select|Modal|Action|Row)s?)', content)
        concepts.extend(components)
        
        # Look for section markers in text
        sections = re.findall(r'(?:^|\n)#+\s*([A-Za-z][^\n]+)', content)
        concepts.extend([s.strip() for s in sections if len(s) > 3])
        
        # Definition patterns in plain text
        definitions = re.findall(r'(\w+(?:\s+\w+)?)\s+(?:is|are)\s+(?:a|an|the)', content)
        concepts.extend([d.strip() for d in definitions if len(d.strip()) > 3])
        
        # API endpoint names
        endpoints = re.findall(r'/(?:api/)?v\d+/([a-z_]+)', content)
        concepts.extend([e for e in endpoints if len(e) > 2])
        
        # Clean and deduplicate
        seen = set()
        unique = []
        stopwords = {'the', 'and', 'for', 'this', 'that', 'with', 'from', 'null', 'true', 'false', 'none', 'data'}
        for c in concepts:
            c_lower = c.lower().strip()
            if c_lower and c_lower not in seen and c_lower not in stopwords and len(c_lower) > 2:
                seen.add(c_lower)
                unique.append(c.strip())
        
        self._log("EXTRACT", f"  Raw: {len(concepts)}, Unique: {len(unique)}")
        return unique[:20]
    
    def _generate_questions(self, concepts: List[str], content: str) -> List[str]:
        """Generate questions from concepts."""
        questions = []
        
        for concept in concepts[:10]:
            questions.append(f"What is {concept}?")
            questions.append(f"How do you use {concept}?")
        
        # Extract existing questions from content
        existing = re.findall(r"[A-Z][^.!?]*\?", content)
        questions.extend([q.strip() for q in existing[:5] if len(q) < 100])
        
        return questions[:15]  # Limit
    
    def _find_answer(
        self,
        question: str,
        content: str,
        source_url: str,
    ) -> Tuple[str, List[str], List[str]]:
        """Find answer to question in content."""
        # Extract key term from question
        term = re.sub(r'^(What is|How do you use|What are)\s+', '', question, flags=re.IGNORECASE)
        term = term.rstrip('?').strip()
        
        # Search for term in content
        pattern = rf"(?i){re.escape(term)}[^.]*\.([^.]+\.)"
        match = re.search(pattern, content)
        
        if match:
            answer = match.group(0).strip()[:300]
            citations = [source_url]
            
            # Look for code examples near the answer
            examples = []
            pos = match.start()
            code_block = re.search(r'<code[^>]*>([^<]+)</code>', content[pos:pos+500])
            if code_block:
                examples.append(code_block.group(1))
            
            return answer, citations, examples
        
        return "", [], []
    
    def _create_exercises(
        self,
        knowledge: List[Knowledge],
        content: str,
    ) -> List[Exercise]:
        """Create hands-on exercises from knowledge."""
        exercises = []
        
        for i, k in enumerate(knowledge[:5]):
            # Create exercise based on knowledge
            exercise = Exercise(
                id=f"ex_{i+1}",
                instruction=f"Demonstrate your understanding of: {k.question}",
                expected_outcome=k.answer[:100] + "...",
                hints=[f"Hint: {k.answer[:50]}..."] if k.answer else [],
                solution=k.examples[0] if k.examples else None,
            )
            exercises.append(exercise)
        
        return exercises
    
    def _store_learning(self, source_url: str, title: str) -> int:
        """Store learning in memory."""
        knowledge_json = json.dumps([k.to_dict() for k in self._knowledge]).encode()
        exercises_json = json.dumps([e.to_dict() for e in self._exercises]).encode()
        
        buffers = [
            Buffer(
                name="knowledge",
                headers={"type": "knowledge", "count": len(self._knowledge)},
                payload=knowledge_json,
            ),
            Buffer(
                name="exercises",
                headers={"type": "exercises", "count": len(self._exercises)},
                payload=exercises_json,
            ),
        ]
        
        card = self.memory.store_card(
            label="self_teaching",
            buffers=buffers,
            master_input=source_url,
            master_output=f"Learned {len(self._knowledge)} facts, {len(self._exercises)} exercises",
            track="awareness",
        )
        
        return card.id
    
    async def test_self(self) -> Dict[str, Any]:
        """Test self on learned knowledge.
        
        Returns:
            Test results with score.
        """
        if not self._knowledge:
            return {"score": 0, "correct": 0, "total": 0, "message": "No knowledge to test", "results": []}
        
        self._log("TEST", f"Testing self on {len(self._knowledge)} knowledge items...")
        
        results = []
        correct = 0
        
        for k in self._knowledge:
            # Simulate answering (in real system, would use LLM)
            # For now, check if we have citation/example proof
            has_citation = len(k.citations) > 0
            has_example = len(k.examples) > 0
            
            score = 0.0
            if has_citation:
                score += 0.5
            if has_example:
                score += 0.5
            if k.answer:
                score = max(score, 0.3)  # At least partial credit for having answer
            
            k.confidence = score
            k.verified = score >= 0.5
            
            result = TestResult(
                question=k.question,
                given_answer=k.answer[:100] if k.answer else "No answer",
                correct_answer=k.answer[:100] if k.answer else "Unknown",
                score=score,
                citation_found=has_citation,
                example_verified=has_example,
            )
            results.append(result)
            
            if score >= 0.5:
                correct += 1
            
            self._log("TEST", f"  Q: {k.question[:40]}... Score: {score:.1%}")
        
        overall_score = correct / len(self._knowledge) if self._knowledge else 0
        
        self._log("TEST", f"Overall score: {overall_score:.1%} ({correct}/{len(self._knowledge)})")
        
        return {
            "score": overall_score,
            "correct": correct,
            "total": len(self._knowledge),
            "results": [
                {
                    "question": r.question,
                    "score": r.score,
                    "citation": r.citation_found,
                    "example": r.example_verified,
                }
                for r in results
            ],
        }
    
    async def exercise(self, exercise_id: str) -> Dict[str, Any]:
        """Attempt an exercise.
        
        Returns:
            Exercise result.
        """
        ex = next((e for e in self._exercises if e.id == exercise_id), None)
        if not ex:
            return {"error": f"Exercise {exercise_id} not found"}
        
        self._log("EXERCISE", f"Attempting: {ex.instruction[:50]}...")
        
        # In real system, would execute the exercise
        # For now, check if we have solution
        if ex.solution:
            ex.passed = True
            self._log("EXERCISE", f"Passed! Solution: {ex.solution[:50]}...")
        else:
            ex.passed = False
            self._log("EXERCISE", "No solution available")
        
        return {
            "exercise": ex.to_dict(),
            "passed": ex.passed,
        }
