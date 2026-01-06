"""Problem type classification and recognition.

This module identifies what kind of problem is being solved and what
reasoning patterns are required.
"""

from dataclasses import dataclass
from typing import List, Set, Optional, Dict, Any
from enum import Enum


class ReasoningPattern(Enum):
    """Types of reasoning patterns the system can use."""

    # Logic and inference
    DEDUCTIVE = "deductive"  # A→B, A, therefore B
    INDUCTIVE = "inductive"  # Pattern from examples
    ABDUCTIVE = "abductive"  # Best explanation

    # Mathematical
    ALGEBRAIC = "algebraic"  # Equation solving, manipulation
    GEOMETRIC = "geometric"  # Spatial reasoning
    NUMERIC = "numeric"  # Arithmetic, pattern finding
    OPTIMIZATION = "optimization"  # Find min/max

    # Search and enumeration
    SYSTEMATIC_SEARCH = "systematic_search"  # Try all possibilities
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"  # Find values satisfying constraints
    BACKTRACKING = "backtracking"  # Try-and-retry with undo

    # Pattern recognition
    PATTERN_MATCHING = "pattern_matching"  # Find patterns in data
    ANALOGY = "analogy"  # Reason by similarity
    DECOMPOSITION = "decomposition"  # Break into subproblems

    # Hypothesis testing
    HYPOTHESIS_GENERATION = "hypothesis_generation"  # Create candidate solutions
    HYPOTHESIS_TESTING = "hypothesis_testing"  # Test candidates
    ELIMINATION = "elimination"  # Rule out impossibilities

    # Meta-reasoning
    STRATEGY_SELECTION = "strategy_selection"  # Choose solving approach
    REFLECTION = "reflection"  # Analyze own reasoning
    ADAPTATION = "adaptation"  # Modify strategy based on feedback

    # Visual reasoning (ARC-AGI specific)
    PROGRAM_SYNTHESIS = "program_synthesis"  # Synthesize programs from examples
    TRANSFORMATION_INFERENCE = "transformation_inference"  # Infer visual transformations
    VISUAL_PATTERN_RECOGNITION = "visual_pattern_recognition"  # Recognize visual patterns


class ProblemDomain(Enum):
    """High-level problem domains."""
    ALGEBRA = "algebra"
    GEOMETRY = "geometry"
    LOGIC = "logic"
    COMBINATORICS = "combinatorics"
    NUMBER_THEORY = "number_theory"
    VISUAL_REASONING = "visual_reasoning"
    WORD_PROBLEM = "word_problem"
    PROOF = "proof"
    OPTIMIZATION = "optimization"
    PATTERN_RECOGNITION = "pattern_recognition"
    UNKNOWN = "unknown"


@dataclass
class ProblemSignature:
    """A signature identifying key characteristics of a problem."""
    domain: ProblemDomain
    required_patterns: Set[ReasoningPattern]
    keywords: Set[str]
    structure: str  # e.g., "system_of_equations", "factorization", "geometric_constraint"
    complexity: int  # 1-10 scale
    input_types: List[str]  # e.g., ["equation", "constraint", "diagram"]
    output_type: str  # e.g., "numeric", "symbolic", "proof"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "domain": self.domain.value,
            "required_patterns": [p.value for p in self.required_patterns],
            "keywords": list(self.keywords),
            "structure": self.structure,
            "complexity": self.complexity,
            "input_types": self.input_types,
            "output_type": self.output_type,
        }


class ProblemClassifier:
    """Classifies problems and identifies required reasoning patterns."""

    def __init__(self):
        """Initialize with known problem signatures."""
        self.known_signatures: Dict[str, ProblemSignature] = {}
        self._initialize_base_signatures()

    def _initialize_base_signatures(self):
        """Initialize with basic problem type signatures."""

        # System of linear equations
        self.known_signatures["system_linear_equations"] = ProblemSignature(
            domain=ProblemDomain.ALGEBRA,
            required_patterns={
                ReasoningPattern.ALGEBRAIC,
                ReasoningPattern.CONSTRAINT_SATISFACTION,
                ReasoningPattern.SYSTEMATIC_SEARCH,
            },
            keywords={"equation", "system", "solve", "x", "y", "variable"},
            structure="system_of_equations",
            complexity=4,
            input_types=["equation", "equation"],
            output_type="numeric",
        )

        # Factorization
        self.known_signatures["polynomial_factorization"] = ProblemSignature(
            domain=ProblemDomain.ALGEBRA,
            required_patterns={
                ReasoningPattern.ALGEBRAIC,
                ReasoningPattern.SYSTEMATIC_SEARCH,
                ReasoningPattern.HYPOTHESIS_GENERATION,
                ReasoningPattern.HYPOTHESIS_TESTING,
                ReasoningPattern.OPTIMIZATION,
            },
            keywords={"factor", "polynomial", "x^2", "x^4", "expand"},
            structure="factorization",
            complexity=6,
            input_types=["polynomial"],
            output_type="factored_form",
        )

        # Grid pattern
        self.known_signatures["grid_number_pattern"] = ProblemSignature(
            domain=ProblemDomain.PATTERN_RECOGNITION,
            required_patterns={
                ReasoningPattern.PATTERN_MATCHING,
                ReasoningPattern.HYPOTHESIS_GENERATION,
                ReasoningPattern.HYPOTHESIS_TESTING,
                ReasoningPattern.NUMERIC,
            },
            keywords={"grid", "pattern", "row", "column", "?", "missing"},
            structure="grid_pattern",
            complexity=5,
            input_types=["grid"],
            output_type="numeric",
        )

        # Logic puzzle
        self.known_signatures["logic_puzzle"] = ProblemSignature(
            domain=ProblemDomain.LOGIC,
            required_patterns={
                ReasoningPattern.DEDUCTIVE,
                ReasoningPattern.CONSTRAINT_SATISFACTION,
                ReasoningPattern.BACKTRACKING,
            },
            keywords={"truth", "lie", "door", "guard", "always", "never"},
            structure="logic_puzzle",
            complexity=7,
            input_types=["logical_constraints"],
            output_type="strategy",
        )

        # Geometric reasoning
        self.known_signatures["circle_geometry"] = ProblemSignature(
            domain=ProblemDomain.GEOMETRY,
            required_patterns={
                ReasoningPattern.GEOMETRIC,
                ReasoningPattern.ALGEBRAIC,
                ReasoningPattern.DEDUCTIVE,
            },
            keywords={"circle", "diameter", "radius", "angle", "inscribed"},
            structure="geometric_constraint",
            complexity=6,
            input_types=["diagram", "measurements"],
            output_type="numeric",
        )

    def classify(self, problem_text: str, context: Optional[Dict] = None) -> ProblemSignature:
        """Classify a problem and return its signature.

        Args:
            problem_text: The problem statement
            context: Optional context (diagram data, etc.)

        Returns:
            ProblemSignature identifying the problem type
        """
        problem_lower = problem_text.lower()

        # Try to match against known signatures
        best_match = None
        best_score = 0

        for sig_name, signature in self.known_signatures.items():
            score = self._match_score(problem_lower, signature)
            if score > best_score:
                best_score = score
                best_match = signature

        if best_match and best_score > 0.3:
            return best_match

        # Unknown problem type - analyze from scratch
        return self._analyze_unknown_problem(problem_text, context)

    def _match_score(self, problem_text: str, signature: ProblemSignature) -> float:
        """Calculate match score between problem and signature."""
        keyword_matches = sum(1 for kw in signature.keywords if kw in problem_text)
        keyword_ratio = keyword_matches / len(signature.keywords) if signature.keywords else 0
        return keyword_ratio

    def _analyze_unknown_problem(
        self,
        problem_text: str,
        context: Optional[Dict]
    ) -> ProblemSignature:
        """Analyze an unknown problem type."""

        # Try to infer domain
        domain = self._infer_domain(problem_text)

        # Try to identify required patterns
        patterns = self._infer_patterns(problem_text, domain)

        # Extract keywords
        keywords = self._extract_keywords(problem_text)

        return ProblemSignature(
            domain=domain,
            required_patterns=patterns,
            keywords=keywords,
            structure="unknown",
            complexity=5,  # Default medium complexity
            input_types=["text"],
            output_type="unknown",
        )

    def _infer_domain(self, problem_text: str) -> ProblemDomain:
        """Infer problem domain from text."""
        text_lower = problem_text.lower()

        # Check for domain indicators
        if any(word in text_lower for word in ["equation", "solve", "x", "variable"]):
            return ProblemDomain.ALGEBRA
        elif any(word in text_lower for word in ["circle", "angle", "triangle", "diameter"]):
            return ProblemDomain.GEOMETRY
        elif any(word in text_lower for word in ["pattern", "sequence", "next", "grid"]):
            return ProblemDomain.PATTERN_RECOGNITION
        elif any(word in text_lower for word in ["truth", "lie", "logic", "always", "never"]):
            return ProblemDomain.LOGIC
        elif any(word in text_lower for word in ["minimum", "maximum", "optimize", "smallest"]):
            return ProblemDomain.OPTIMIZATION
        else:
            return ProblemDomain.UNKNOWN

    def _infer_patterns(self, problem_text: str, domain: ProblemDomain) -> Set[ReasoningPattern]:
        """Infer required reasoning patterns."""
        patterns = set()
        text_lower = problem_text.lower()

        # Pattern indicators
        if any(word in text_lower for word in ["solve", "find", "calculate"]):
            patterns.add(ReasoningPattern.ALGEBRAIC)

        if any(word in text_lower for word in ["pattern", "sequence", "repeat"]):
            patterns.add(ReasoningPattern.PATTERN_MATCHING)

        if any(word in text_lower for word in ["minimum", "maximum", "smallest", "largest"]):
            patterns.add(ReasoningPattern.OPTIMIZATION)

        if any(word in text_lower for word in ["if", "then", "therefore", "because"]):
            patterns.add(ReasoningPattern.DEDUCTIVE)

        if any(word in text_lower for word in ["try", "test", "check", "possible"]):
            patterns.add(ReasoningPattern.HYPOTHESIS_TESTING)

        # Default patterns based on domain
        if domain == ProblemDomain.ALGEBRA:
            patterns.add(ReasoningPattern.ALGEBRAIC)
        elif domain == ProblemDomain.GEOMETRY:
            patterns.add(ReasoningPattern.GEOMETRIC)
        elif domain == ProblemDomain.LOGIC:
            patterns.add(ReasoningPattern.DEDUCTIVE)

        return patterns

    def _extract_keywords(self, problem_text: str) -> Set[str]:
        """Extract key terms from problem text."""
        # Simple keyword extraction (could be enhanced with NLP)
        text_lower = problem_text.lower()

        # Common math/logic terms
        important_terms = {
            "equation", "solve", "find", "calculate", "prove", "show",
            "minimum", "maximum", "pattern", "sequence", "factor",
            "circle", "angle", "triangle", "diameter", "radius",
            "truth", "lie", "always", "never", "if", "then",
            "grid", "row", "column", "number", "value",
        }

        keywords = set()
        for term in important_terms:
            if term in text_lower:
                keywords.add(term)

        return keywords

    def register_signature(self, name: str, signature: ProblemSignature):
        """Register a new problem signature."""
        self.known_signatures[name] = signature

    def get_signature(self, name: str) -> Optional[ProblemSignature]:
        """Get a known signature by name."""
        return self.known_signatures.get(name)
