"""LLM Planner - Generate TascPlans from natural language goals.

Provides utilities for LLMs to generate validatable plans and track performance.

Uses Claude (Anthropic) by default for plan generation. Supports other LLMs through
the same interface.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from tasc.tasc import Tasc
from .llm_proof import TascPlan, create_plan, ProofType, ProofRequirement


# ---------------------------------------------------------------------------
# Tasc Citations - Reference other tascs as evidence/prior work
# ---------------------------------------------------------------------------

@dataclass
class TascCitation:
    """A citation to another Tasc or TascValidation.
    
    Allows tascs to reference prior work, evidence, or related tasks.
    This enables:
    - Building on proven solutions
    - Referencing successful patterns
    - Creating knowledge graphs of related work
    """
    source_tasc_id: str  # The tasc making the citation
    cited_tasc_id: str   # The tasc being cited
    citation_type: Literal["evidence", "prerequisite", "related", "supersedes", "derived_from"]
    description: str = ""
    proof_hash: Optional[str] = None  # Proof hash of cited tasc (for verification)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_tasc_id": self.source_tasc_id,
            "cited_tasc_id": self.cited_tasc_id,
            "citation_type": self.citation_type,
            "description": self.description,
            "proof_hash": self.proof_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TascCitation":
        return cls(
            source_tasc_id=data["source_tasc_id"],
            cited_tasc_id=data["cited_tasc_id"],
            citation_type=data.get("citation_type", "related"),
            description=data.get("description", ""),
            proof_hash=data.get("proof_hash"),
        )


# ---------------------------------------------------------------------------
# Performance Benchmarking
# ---------------------------------------------------------------------------

@dataclass
class PlanMetrics:
    """Metrics for tracking plan execution performance.
    
    Used to:
    - Benchmark agent performance over time
    - Identify slow/failing patterns
    - Compare approaches
    """
    plan_id: str
    total_tascs: int
    successful_tascs: int
    failed_tascs: int
    
    # Timing
    total_duration_ms: float = 0
    avg_tasc_duration_ms: float = 0
    max_tasc_duration_ms: float = 0
    
    # Quality
    first_pass_success_rate: float = 0  # % of tascs that passed on first try
    retry_count: int = 0
    
    # Citations
    citations_made: int = 0
    citations_verified: int = 0  # Citations with valid proof hashes
    
    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "total_tascs": self.total_tascs,
            "successful_tascs": self.successful_tascs,
            "failed_tascs": self.failed_tascs,
            "total_duration_ms": self.total_duration_ms,
            "avg_tasc_duration_ms": self.avg_tasc_duration_ms,
            "max_tasc_duration_ms": self.max_tasc_duration_ms,
            "first_pass_success_rate": self.first_pass_success_rate,
            "retry_count": self.retry_count,
            "citations_made": self.citations_made,
            "citations_verified": self.citations_verified,
            "timestamp": self.timestamp,
        }


@dataclass
class BenchmarkSuite:
    """A collection of standardized test cases for agent benchmarking.
    
    Categories:
    - Syntax/import checks
    - Unit test execution
    - Lint/format compliance
    - Integration tests
    - Performance thresholds
    """
    name: str
    description: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def create_standard_suite(cls) -> "BenchmarkSuite":
        """Create the standard benchmark suite for agent testing."""
        return cls(
            name="standard",
            description="Standard agent benchmarks",
            test_cases=[
                {
                    "id": "syntax_check",
                    "name": "Syntax Check",
                    "testing_instructions": "python -m py_compile {file}",
                    "category": "basic",
                    "timeout_seconds": 10,
                },
                {
                    "id": "import_check",
                    "name": "Import Check",
                    "testing_instructions": "python -c 'import {module}'",
                    "category": "basic",
                    "timeout_seconds": 30,
                },
                {
                    "id": "unit_tests",
                    "name": "Unit Tests",
                    "testing_instructions": "pytest {path} -v --tb=short",
                    "category": "testing",
                    "timeout_seconds": 300,
                },
                {
                    "id": "type_check",
                    "name": "Type Check",
                    "testing_instructions": "mypy {path} --ignore-missing-imports",
                    "category": "quality",
                    "timeout_seconds": 120,
                },
                {
                    "id": "lint",
                    "name": "Lint Check",
                    "testing_instructions": "ruff check {path}",
                    "category": "quality",
                    "timeout_seconds": 60,
                },
            ],
        )


# ---------------------------------------------------------------------------
# Plan Generation
# ---------------------------------------------------------------------------

@dataclass
class PlanGenerationRequest:
    """Request for generating a TascPlan from natural language."""
    goal: str
    context: str = ""  # Codebase summary, constraints
    constraints: List[str] = field(default_factory=list)
    max_tascs: int = 10
    require_approval: bool = True  # Add manual approval gate?
    
    # Optional: previous work to cite
    prior_tasc_ids: List[str] = field(default_factory=list)


@dataclass
class GeneratedPlan:
    """Result of plan generation."""
    plan: TascPlan
    reasoning: str  # Why this plan was chosen
    confidence: float  # 0-1 confidence score
    citations: List[TascCitation] = field(default_factory=list)
    requires_approval: bool = True


def generate_plan_prompt(request: PlanGenerationRequest) -> str:
    """Generate the prompt for LLM plan generation.
    
    This prompt template guides LLMs to create well-structured,
    validatable TascPlans.
    """
    constraints_text = "\n".join(f"- {c}" for c in request.constraints) if request.constraints else "None specified"
    prior_work = "\n".join(f"- {tid}" for tid in request.prior_tasc_ids) if request.prior_tasc_ids else "None"
    
    return f"""You are a PLANNER creating a TascPlan for the following goal.

## Goal
{request.goal}

## Context
{request.context or "No additional context provided."}

## Constraints
{constraints_text}

## Prior Work (can cite)
{prior_work}

## Requirements
1. Each tasc must have executable `testing_instructions`
2. `testing_instructions` must exit 0 on success, non-zero on failure
3. Use `dependencies` to enforce execution order
4. Add `proof_required: {{proof_type: "manual"}}` for risky operations
5. Maximum {request.max_tascs} tascs
6. Cite prior work if relevant using `citations` field

## Validation Pattern Reference
| Goal | testing_instructions |
|------|---------------------|
| File exists | `test -f path/to/file` |
| Module imports | `python -c "import module"` |
| Tests pass | `pytest tests/` |
| Lint passes | `ruff check .` |
| Output matches | `diff output.txt expected.txt` |

## Output Format (JSON)
```json
{{
  "title": "Plan title",
  "reasoning": "Why this approach",
  "confidence": 0.85,
  "tascs": [
    {{
      "id": "tasc_1",
      "title": "Human readable step",
      "testing_instructions": "command that exits 0 on success",
      "desired_outcome": "What success looks like",
      "dependencies": []
    }}
  ],
  "citations": [
    {{
      "cited_tasc_id": "prior_tasc_id",
      "citation_type": "evidence",
      "description": "Why this prior work is relevant"
    }}
  ]
}}
```

Generate the plan now:"""


def parse_generated_plan(
    response: str,
    request: PlanGenerationRequest,
) -> GeneratedPlan:
    """Parse LLM response into a GeneratedPlan.
    
    Handles JSON extraction and validation.
    """
    # Extract JSON from response (handle markdown code blocks)
    json_str = response
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        json_str = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        json_str = response[start:end].strip()
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {e}")
    
    # Build tascs
    tascs = []
    for t in data.get("tascs", []):
        tasc_dict = {
            "id": t.get("id", f"tasc_{uuid.uuid4().hex[:8]}"),
            "title": t.get("title", "Untitled"),
            "testing_instructions": t.get("testing_instructions", "echo 'no test'"),
            "desired_outcome": t.get("desired_outcome", ""),
            "dependencies": t.get("dependencies", []),
        }
        
        # Handle proof requirements
        if t.get("proof_required"):
            proof_req = t["proof_required"]
            if isinstance(proof_req, dict):
                tasc_dict["proof_required"] = proof_req
            elif proof_req == "manual":
                tasc_dict["proof_required"] = {"proof_type": "manual"}
        
        tascs.append(tasc_dict)
    
    # Add approval gate if requested
    if request.require_approval and tascs:
        # Find the last non-approval tasc
        last_id = tascs[-1]["id"]
        tascs.append({
            "id": "final_review",
            "title": "Human review before completion",
            "testing_instructions": "",
            "proof_required": {"proof_type": "manual"},
            "dependencies": [last_id],
        })
    
    # Create plan
    plan = create_plan(
        title=data.get("title", request.goal[:50]),
        tascs=tascs,
    )
    
    # Parse citations
    citations = []
    for c in data.get("citations", []):
        citations.append(TascCitation(
            source_tasc_id=plan.id,
            cited_tasc_id=c.get("cited_tasc_id", ""),
            citation_type=c.get("citation_type", "related"),
            description=c.get("description", ""),
        ))
    
    return GeneratedPlan(
        plan=plan,
        reasoning=data.get("reasoning", ""),
        confidence=float(data.get("confidence", 0.5)),
        citations=citations,
        requires_approval=request.require_approval,
    )


def calculate_plan_metrics(plan: TascPlan) -> PlanMetrics:
    """Calculate metrics from a completed plan."""
    total = len(plan.tascs)
    successful = 0
    failed = 0
    durations = []
    
    for tasc in plan.tascs:
        val = plan.validations.get(tasc.id)
        if val:
            if val.validated:
                successful += 1
            else:
                failed += 1
            durations.append(val.duration_ms)
    
    total_duration = sum(durations)
    avg_duration = total_duration / len(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    
    return PlanMetrics(
        plan_id=plan.id,
        total_tascs=total,
        successful_tascs=successful,
        failed_tascs=failed,
        total_duration_ms=total_duration,
        avg_tasc_duration_ms=avg_duration,
        max_tasc_duration_ms=max_duration,
        first_pass_success_rate=successful / total if total > 0 else 0,
    )


# ---------------------------------------------------------------------------
# Citation Management
# ---------------------------------------------------------------------------

class CitationStore:
    """Store and retrieve tasc citations."""
    
    def __init__(self, path: str = ".tascer/citations.json"):
        self.path = path
        self._ensure_file()
    
    def _ensure_file(self):
        import os
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._save([])
    
    def _load(self) -> List[Dict]:
        with open(self.path) as f:
            return json.load(f)
    
    def _save(self, data: List[Dict]):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add(self, citation: TascCitation):
        """Add a citation."""
        data = self._load()
        data.append(citation.to_dict())
        self._save(data)
    
    def get_citations_for(self, tasc_id: str) -> List[TascCitation]:
        """Get citations made by a tasc."""
        data = self._load()
        return [
            TascCitation.from_dict(c)
            for c in data
            if c["source_tasc_id"] == tasc_id
        ]
    
    def get_cited_by(self, tasc_id: str) -> List[TascCitation]:
        """Get tascs that cite this tasc."""
        data = self._load()
        return [
            TascCitation.from_dict(c)
            for c in data
            if c["cited_tasc_id"] == tasc_id
        ]
    
    def verify_citation(self, citation: TascCitation, proof_store_path: str = ".tascer/proofs") -> bool:
        """Verify a citation's proof hash matches stored proof."""
        import os
        if not citation.proof_hash:
            return False
        
        # Look for proof file
        proof_file = os.path.join(proof_store_path, f"{citation.cited_tasc_id}.json")
        if not os.path.exists(proof_file):
            return False
        
        with open(proof_file) as f:
            proof = json.load(f)
        
        return proof.get("proof_hash") == citation.proof_hash


def cite_tasc(
    source_tasc_id: str,
    cited_tasc_id: str,
    citation_type: str = "related",
    description: str = "",
    proof_hash: Optional[str] = None,
) -> TascCitation:
    """Create a citation from one tasc to another.

    Example:
        # Cite a prior successful solution
        cite_tasc(
            source_tasc_id="fix_auth_v2",
            cited_tasc_id="fix_auth_v1",
            citation_type="supersedes",
            description="Improved version with better error handling",
            proof_hash="abc123...",
        )
    """
    citation = TascCitation(
        source_tasc_id=source_tasc_id,
        cited_tasc_id=cited_tasc_id,
        citation_type=citation_type,
        description=description,
        proof_hash=proof_hash,
    )

    # Store citation
    store = CitationStore()
    store.add(citation)

    return citation


# ---------------------------------------------------------------------------
# Convenience: Generate plan with Claude (recommended)
# ---------------------------------------------------------------------------

def generate_plan(
    goal: str,
    context: str = "",
    constraints: List[str] = None,
    max_tascs: int = 10,
    require_approval: bool = True,
    prior_tasc_ids: List[str] = None,
    use_claude: bool = True,
    **llm_kwargs,
) -> GeneratedPlan:
    """Generate a TascPlan from a natural language goal.

    Uses Claude (Anthropic) by default for best results.

    Args:
        goal: Natural language description of what to accomplish
        context: Additional context (codebase info, constraints, etc.)
        constraints: List of constraints to enforce
        max_tascs: Maximum number of tascs in the plan
        require_approval: Whether to add a manual approval gate at the end
        prior_tasc_ids: IDs of previous tascs to potentially cite
        use_claude: Whether to use Claude API (requires ANTHROPIC_API_KEY)
        **llm_kwargs: Additional arguments for the LLM (e.g., temperature, api_key, model)

    Returns:
        GeneratedPlan with plan, reasoning, confidence, and citations

    Example:
        >>> from tascer import generate_plan
        >>>
        >>> plan = generate_plan(
        ...     goal="Fix the 500 error on the login endpoint",
        ...     context="FastAPI app with JWT authentication",
        ...     constraints=["Must maintain backwards compatibility"],
        ... )
        >>>
        >>> print(f"Plan: {plan.plan.title}")
        >>> print(f"Confidence: {plan.confidence:.0%}")
        >>> for tasc in plan.plan.tascs:
        ...     print(f"  - {tasc.title}")
    """
    if use_claude:
        try:
            from .claude_planner import generate_plan_with_claude
            return generate_plan_with_claude(
                goal=goal,
                context=context,
                constraints=constraints,
                max_tascs=max_tascs,
                require_approval=require_approval,
                prior_tasc_ids=prior_tasc_ids,
                **llm_kwargs,
            )
        except ImportError:
            raise ImportError(
                "Claude planner not available. Install anthropic: pip install anthropic\n"
                "Or set use_claude=False to use manual plan generation."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate plan with Claude: {e}")
    else:
        # Fall back to manual prompt generation (user provides their own LLM)
        request = PlanGenerationRequest(
            goal=goal,
            context=context,
            constraints=constraints or [],
            max_tascs=max_tascs,
            require_approval=require_approval,
            prior_tasc_ids=prior_tasc_ids or [],
        )

        prompt = generate_plan_prompt(request)
        raise NotImplementedError(
            f"Manual LLM integration not implemented. Use use_claude=True or implement your own.\n\n"
            f"Prompt:\n{prompt}"
        )
