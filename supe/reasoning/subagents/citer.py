"""Citer subagent - Collects and validates evidence for claims.

This subagent gathers supporting evidence for reasoning:
1. Searches for citations that support claims
2. Validates evidence quality and relevance
3. Builds an evidence chain linking claims to sources
4. Scores evidence strength

Example output:
    ┌─────────────────────────────────────────────────┐
    │  EVIDENCE REPORT                                │
    ├─────────────────────────────────────────────────┤
    │  Claim: NTT complexity is O(N log N)            │
    │  ─────────────────────────────────────────────  │
    │  📚 Source: Cormen et al, CLRS 4th ed          │
    │     "FFT/NTT has Θ(N log N) complexity"        │
    │     Relevance: 95%  Strength: Strong           │
    │  📚 Source: Wikipedia FFT article              │
    │     "Cooley-Tukey achieves O(N log N)"         │
    │     Relevance: 80%  Strength: Moderate         │
    ├─────────────────────────────────────────────────┤
    │  Evidence Score: 92/100 (Strong support)        │
    └─────────────────────────────────────────────────┘
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import re

from ab.abdb import ABMemory
from ab.models import Buffer

from .problem_solver import TASC


class EvidenceType(Enum):
    """Types of evidence."""
    CITATION = "citation"           # Academic/authoritative source
    CALCULATION = "calculation"     # Mathematical derivation
    EXPERIMENT = "experiment"       # Empirical test
    DEFINITION = "definition"       # Formal definition
    THEOREM = "theorem"            # Proven theorem
    EXAMPLE = "example"            # Supporting example
    COUNTEREXAMPLE = "counterexample"  # Disproof by example
    CONSENSUS = "consensus"         # Expert/community agreement


class EvidenceStrength(Enum):
    """Strength levels for evidence."""
    STRONG = "strong"           # Definitive proof
    MODERATE = "moderate"       # Good support
    WEAK = "weak"              # Some support
    SPECULATIVE = "speculative"  # Unverified


@dataclass
class EvidenceSource:
    """A source that provides evidence."""

    id: str
    source_type: str  # e.g., "textbook", "paper", "wikipedia", "calculation"
    title: str
    url: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    reliability: float = 0.5  # 0-1 reliability score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.source_type,
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "year": self.year,
            "reliability": self.reliability,
        }


@dataclass
class EvidenceItem:
    """A single piece of evidence."""

    id: str
    evidence_type: EvidenceType
    claim: str  # What claim this evidence supports
    content: str  # The actual evidence text
    source: EvidenceSource
    relevance: float = 0.0  # How relevant to the claim (0-1)
    strength: EvidenceStrength = EvidenceStrength.WEAK
    validated: bool = False
    validation_method: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def score(self) -> float:
        """Calculate overall evidence score."""
        strength_weights = {
            EvidenceStrength.STRONG: 1.0,
            EvidenceStrength.MODERATE: 0.7,
            EvidenceStrength.WEAK: 0.4,
            EvidenceStrength.SPECULATIVE: 0.1,
        }

        base = strength_weights[self.strength]
        relevance_factor = self.relevance
        reliability_factor = self.source.reliability
        validation_bonus = 0.1 if self.validated else 0

        return min(1.0, base * relevance_factor * reliability_factor + validation_bonus)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.evidence_type.value,
            "claim": self.claim,
            "content": self.content,
            "source": self.source.to_dict(),
            "relevance": self.relevance,
            "strength": self.strength.value,
            "validated": self.validated,
            "validation_method": self.validation_method,
            "score": self.score(),
            "metadata": self.metadata,
        }


@dataclass
class GatheredEvidence:
    """Complete evidence collection for a TASC."""

    tasc_id: str
    claims: List[str] = field(default_factory=list)
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    overall_score: float = 0.0
    gaps: List[str] = field(default_factory=list)  # Claims without evidence
    gathered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def calculate_score(self) -> float:
        """Calculate overall evidence score."""
        if not self.evidence_items:
            self.overall_score = 0.0
            return 0.0

        # Average of all evidence scores
        total = sum(e.score() for e in self.evidence_items)
        self.overall_score = total / len(self.evidence_items)

        # Penalty for gaps
        gap_penalty = len(self.gaps) * 0.1
        self.overall_score = max(0.0, self.overall_score - gap_penalty)

        return self.overall_score

    def get_strength_label(self) -> str:
        """Get a label for the overall evidence strength."""
        score = self.overall_score * 100
        if score >= 90:
            return "Very Strong"
        elif score >= 70:
            return "Strong"
        elif score >= 50:
            return "Moderate"
        elif score >= 30:
            return "Weak"
        else:
            return "Insufficient"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tasc_id": self.tasc_id,
            "claims": self.claims,
            "evidence": [e.to_dict() for e in self.evidence_items],
            "overall_score": self.overall_score,
            "strength_label": self.get_strength_label(),
            "gaps": self.gaps,
            "gathered_at": self.gathered_at,
        }

    def to_ascii(self) -> str:
        """Render as ASCII box format."""
        width = 60
        lines = []

        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        lines.append(f"│  EVIDENCE REPORT: {self.tasc_id:<{width-23}}│")
        lines.append("├" + "─" * (width - 2) + "┤")

        # Group evidence by claim
        claim_evidence: Dict[str, List[EvidenceItem]] = {}
        for e in self.evidence_items:
            if e.claim not in claim_evidence:
                claim_evidence[e.claim] = []
            claim_evidence[e.claim].append(e)

        for claim, evidences in claim_evidence.items():
            # Claim header
            claim_text = claim[:width-6] if len(claim) > width-6 else claim
            lines.append(f"│  Claim: {claim_text:<{width-12}}│")
            lines.append(f"│  {'─' * (width - 6):<{width-5}}│")

            for e in evidences:
                # Source line
                src = f"📚 {e.source.title[:width-15]}"
                lines.append(f"│  {src:<{width-5}}│")

                # Content line
                content = e.content[:width-10]
                lines.append(f"│     \"{content}\"{'...' if len(e.content) > width-10 else '':<{width-len(content)-12}}│")

                # Stats line
                stats = f"Relevance: {e.relevance*100:.0f}%  Strength: {e.strength.value.title()}"
                lines.append(f"│     {stats:<{width-8}}│")

            lines.append(f"│{' ' * (width - 2)}│")

        # Gaps
        if self.gaps:
            lines.append(f"│  ⚠️ Missing evidence for:{' ' * (width - 29)}│")
            for gap in self.gaps[:3]:
                gap_text = gap[:width-8]
                lines.append(f"│    - {gap_text:<{width-9}}│")

        lines.append("├" + "─" * (width - 2) + "┤")

        # Score
        score_line = f"Evidence Score: {self.overall_score*100:.0f}/100 ({self.get_strength_label()} support)"
        lines.append(f"│  {score_line:<{width-5}}│")

        lines.append("└" + "─" * (width - 2) + "┘")

        return "\n".join(lines)


class Citer:
    """Subagent that gathers and validates evidence for claims.

    The Citer:
    1. Extracts claims from TASC reasoning
    2. Searches for supporting evidence
    3. Validates evidence quality
    4. Identifies gaps where evidence is missing

    Example:
        citer = Citer(memory)
        evidence = await citer.gather(tasc)
        tasc.evidence.extend([e.to_dict() for e in evidence.evidence_items])
    """

    name = "citer"

    # Known reliable sources with reliability scores
    KNOWN_SOURCES = {
        "textbook": 0.95,
        "peer_reviewed": 0.90,
        "documentation": 0.85,
        "wikipedia": 0.70,
        "blog": 0.50,
        "forum": 0.40,
        "calculation": 0.95,  # Own verified calculations
        "experiment": 0.90,   # Own experiments
    }

    def __init__(self, memory: ABMemory, search_function: Optional[Callable] = None):
        """Initialize evidence gatherer.

        Args:
            memory: ABMemory instance
            search_function: Optional async function for searching external sources
        """
        self.memory = memory
        self.search_function = search_function
        self.evidence_counter = 0

    async def gather(self, tasc: TASC) -> GatheredEvidence:
        """Gather evidence for all claims in a TASC.

        Args:
            tasc: The TASC to gather evidence for

        Returns:
            GatheredEvidence with all found evidence
        """
        result = GatheredEvidence(tasc_id=tasc.id)

        # Step 1: Extract claims from reasoning
        claims = self._extract_claims(tasc)
        result.claims = claims

        # Step 2: Gather evidence for each claim
        for claim in claims:
            evidence = await self._gather_for_claim(claim, tasc)
            result.evidence_items.extend(evidence)

            # Track gaps
            if not evidence:
                result.gaps.append(claim)

        # Step 3: Calculate overall score
        result.calculate_score()

        # Step 4: Store in memory
        await self._store_evidence(result)

        return result

    def _extract_claims(self, tasc: TASC) -> List[str]:
        """Extract claims that need evidence from TASC."""
        claims = []

        # Main claim: the answer
        if tasc.proposed_answer and tasc.proposed_value is not None:
            claims.append(f"Answer is {tasc.proposed_answer} ({tasc.proposed_value})")

        # Claims from reasoning steps
        for step in tasc.reasoning_steps:
            if step.result is not None:
                claims.append(f"{step.description}: {step.result}")

            # Look for assertions in computation/observation
            if step.computation:
                # Extract equations or assertions
                equations = re.findall(r"[^=]+=\s*\d+", step.computation)
                for eq in equations[:2]:  # Limit to 2 per step
                    claims.append(eq.strip())

        return claims

    async def _gather_for_claim(
        self,
        claim: str,
        tasc: TASC,
    ) -> List[EvidenceItem]:
        """Gather evidence for a specific claim."""
        evidence = []

        # Method 1: Check internal calculations
        calc_evidence = self._check_calculations(claim, tasc)
        if calc_evidence:
            evidence.append(calc_evidence)

        # Method 2: Check for verification in TASC
        verify_evidence = self._check_verification(claim, tasc)
        if verify_evidence:
            evidence.append(verify_evidence)

        # Method 3: Search external sources (if search function provided)
        if self.search_function:
            external = await self._search_external(claim)
            evidence.extend(external)

        # Method 4: Check memory for prior knowledge
        memory_evidence = self._check_memory(claim)
        if memory_evidence:
            evidence.append(memory_evidence)

        return evidence

    def _check_calculations(self, claim: str, tasc: TASC) -> Optional[EvidenceItem]:
        """Check if claim is supported by calculations in TASC."""
        for step in tasc.reasoning_steps:
            if step.computation and step.status.value == "validated":
                # Check if step result matches claim
                if step.result is not None:
                    result_str = str(step.result)
                    if result_str in claim:
                        self.evidence_counter += 1
                        return EvidenceItem(
                            id=f"ev_{self.evidence_counter}",
                            evidence_type=EvidenceType.CALCULATION,
                            claim=claim,
                            content=step.computation,
                            source=EvidenceSource(
                                id="internal_calc",
                                source_type="calculation",
                                title=f"Step {step.step_number} calculation",
                                reliability=self.KNOWN_SOURCES["calculation"],
                            ),
                            relevance=0.9,
                            strength=EvidenceStrength.STRONG,
                            validated=step.status.value == "validated",
                            validation_method="step_checkpoint",
                        )
        return None

    def _check_verification(self, claim: str, tasc: TASC) -> Optional[EvidenceItem]:
        """Check if claim was independently verified in TASC."""
        # Look for verification steps
        for step in tasc.reasoning_steps:
            if "verify" in step.description.lower() or "check" in step.description.lower():
                if step.status.value == "validated":
                    self.evidence_counter += 1
                    return EvidenceItem(
                        id=f"ev_{self.evidence_counter}",
                        evidence_type=EvidenceType.CALCULATION,
                        claim=claim,
                        content=f"Verified in step {step.step_number}: {step.observation}",
                        source=EvidenceSource(
                            id="internal_verify",
                            source_type="calculation",
                            title="Independent verification",
                            reliability=0.90,
                        ),
                        relevance=0.85,
                        strength=EvidenceStrength.STRONG,
                        validated=True,
                        validation_method="independent_verification",
                    )
        return None

    async def _search_external(self, claim: str) -> List[EvidenceItem]:
        """Search external sources for evidence."""
        if not self.search_function:
            return []

        try:
            results = await self.search_function(claim)
            evidence = []

            for result in results[:3]:  # Limit to 3 external sources
                self.evidence_counter += 1

                # Determine source type and reliability
                source_type = self._classify_source(result.get("url", ""))
                reliability = self.KNOWN_SOURCES.get(source_type, 0.5)

                evidence.append(EvidenceItem(
                    id=f"ev_{self.evidence_counter}",
                    evidence_type=EvidenceType.CITATION,
                    claim=claim,
                    content=result.get("snippet", "")[:200],
                    source=EvidenceSource(
                        id=f"ext_{self.evidence_counter}",
                        source_type=source_type,
                        title=result.get("title", "External source"),
                        url=result.get("url"),
                        reliability=reliability,
                    ),
                    relevance=result.get("relevance", 0.5),
                    strength=self._assess_strength(result),
                    validated=False,
                ))

            return evidence
        except Exception:
            return []

    def _check_memory(self, claim: str) -> Optional[EvidenceItem]:
        """Check AB memory for prior relevant knowledge."""
        # Search memory for related cards
        try:
            results = self.memory.search_cards(claim, limit=3)
            if results:
                top_result = results[0]
                similarity = top_result.get("similarity", 0)

                if similarity > 0.7:  # High similarity threshold
                    self.evidence_counter += 1
                    return EvidenceItem(
                        id=f"ev_{self.evidence_counter}",
                        evidence_type=EvidenceType.CITATION,
                        claim=claim,
                        content=f"Prior knowledge: {top_result.get('label', 'Related card')}",
                        source=EvidenceSource(
                            id=f"memory_{top_result.get('id')}",
                            source_type="documentation",
                            title="Prior session knowledge",
                            reliability=0.8,
                        ),
                        relevance=similarity,
                        strength=EvidenceStrength.MODERATE,
                        validated=True,
                        validation_method="memory_recall",
                    )
        except Exception:
            pass
        return None

    def _classify_source(self, url: str) -> str:
        """Classify source type from URL."""
        url_lower = url.lower()

        if any(domain in url_lower for domain in [".edu", "arxiv.org", "acm.org", "ieee.org"]):
            return "peer_reviewed"
        elif "wikipedia.org" in url_lower:
            return "wikipedia"
        elif any(domain in url_lower for domain in ["docs.", "documentation", "reference"]):
            return "documentation"
        elif any(domain in url_lower for domain in ["medium.com", "blog", "dev.to"]):
            return "blog"
        elif any(domain in url_lower for domain in ["stackoverflow", "reddit", "forum"]):
            return "forum"
        else:
            return "blog"  # Default to blog reliability

    def _assess_strength(self, result: Dict[str, Any]) -> EvidenceStrength:
        """Assess evidence strength from search result."""
        relevance = result.get("relevance", 0.5)
        source_type = self._classify_source(result.get("url", ""))

        if source_type in ["peer_reviewed", "textbook"] and relevance > 0.8:
            return EvidenceStrength.STRONG
        elif source_type in ["documentation", "wikipedia"] and relevance > 0.6:
            return EvidenceStrength.MODERATE
        elif relevance > 0.5:
            return EvidenceStrength.WEAK
        else:
            return EvidenceStrength.SPECULATIVE

    async def _store_evidence(self, evidence: GatheredEvidence) -> int:
        """Store gathered evidence in AB memory."""
        import json

        evidence_json = json.dumps(evidence.to_dict()).encode("utf-8")
        evidence_ascii = evidence.to_ascii().encode("utf-8")

        buffers = [
            Buffer(
                name="evidence_json",
                headers={"type": "evidence", "format": "json"},
                payload=evidence_json,
            ),
            Buffer(
                name="evidence_ascii",
                headers={"type": "evidence", "format": "ascii"},
                payload=evidence_ascii,
            ),
        ]

        card = self.memory.store_card(
            label=f"Evidence: {evidence.tasc_id}",
            buffers=buffers,
            track="reasoning",
            master_input=", ".join(evidence.claims[:3]),
            master_output=f"Score: {evidence.overall_score*100:.0f}/100 ({evidence.get_strength_label()})",
        )

        return card.id
