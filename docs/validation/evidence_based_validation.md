# Evidence-Based Validation for Tascs

## Overview

This document describes the evidence-based validation system for tascs, which replaces binary pass/fail validation with a probabilistic, confidence-scored approach based on collected evidence artifacts.

**Core Principle**: Validation quality is determined by the quality and completeness of evidence, not by arbitrary binary gates.

## The Problem

Traditional task validation struggles with:
- **Binary pass/fail**: Too rigid for complex, creative work
- **Perfect validators don't exist**: Most real-world tasks are fuzzy
- **Missing context**: No audit trail of reasoning and process
- **No retrospective learning**: Can't improve confidence over time

For developers, designers, researchers, and problem-solvers, perfect validators are impossible to create. We needed a better approach.

## The Solution: Evidence as Validation

Instead of asking "did the task succeed?", we ask **"what evidence exists that the work was done rigorously?"**

This shifts validation from binary outcomes to evidence quality assessment:

```python
# Traditional validation
def validate(task) -> bool:
    return task.tests_pass and task.bug_fixed  # Binary

# Evidence-based validation
def validate(task, evidence_collection) -> ValidationResult:
    confidence = evaluate_evidence_quality(evidence_collection)
    return ValidationResult(confidence=confidence)  # 0.0-1.0
```

## Architecture

### 1. Evidence (Atomic Unit)

Evidence is the fundamental unit of validation, built on the Atom foundation:

```python
@dataclass
class Evidence:
    """Evidence supporting task completion."""
    id: str
    text: str
    source: EvidenceSource  # Where it came from
    citations: List[str]    # Traceable references
    validated: bool         # Has it been validated?
    validation_method: str  # How was it validated?
    confidence: float       # 0.0-1.0
```

**Evidence Sources** (17 types):
- `DOC`: Documentation, design docs, comments
- `CODE`: Source code, implementation
- `TEST`: Test results, test cases
- `EXPERIMENT`: Experimental validation, reproductions
- `REASONING`: Logical analysis, hypotheses, trade-offs
- `PEER_REVIEW`: Code reviews, human feedback
- `CODE_ANALYSIS`: Static analysis, linting
- `PROFILING`: Performance measurements
- `SECURITY_SCAN`: Security analysis results
- `REGRESSION_TEST`: Tests added to prevent recurrence
- And 7 more specialized types...

Evidence is serializable to Atoms (pindex=10) for storage in the Tasc system.

### 2. Evidence Collections

Groups related evidence for a single tasc:

```python
collection = EvidenceCollection.create(tasc_id="debug-001")
collection.add_evidence(hypothesis_evidence)
collection.add_evidence(reproduction_evidence)
collection.add_evidence(fix_evidence)
```

**Metrics**:
- Evidence count
- Source diversity (# of different evidence types)
- Validated evidence count
- Citation quality

### 3. Unified Validator

Validates tascs using multi-factor confidence scoring:

```python
validator = UnifiedValidator()
result = await validator.validate(tasc, evidence_collection)

# Result includes:
# - overall_confidence: 0.0-1.0
# - evidence_factor: Quality of evidence
# - process_factor: Process adherence
# - objective_factor: Objective checks (tests, builds)
# - requires_human_review: bool
# - review_reasons: List[str]
```

**Validation Formula** (from learning system):

```python
confidence = base * evidence_factor * process_factor * objective_factor

where:
  evidence_factor = f(count, diversity, validation, citations) ∈ [0.8, 1.2]
  process_factor = f(required_steps_completed) ∈ [0.8, 1.0]
  objective_factor = f(tests_pass, builds_work) ∈ [0.0, 1.0]
```

**Evidence Quality Evaluation** (identical to `supe/learning/states/evaluate.py:101-151`):

```python
def _evaluate_evidence_quality(evidence_list):
    """Multi-factor evidence scoring."""

    # 1. Count factor (optimal: 5 items)
    count_factor = min(1.0, len(evidence_list) / 5.0)

    # 2. Source diversity (optimal: 3 types)
    diversity_factor = min(1.0, len(unique_sources) / 3.0)

    # 3. Validation status (validated > unvalidated)
    validation_factor = validated_count / total_count

    # 4. Citation quality (cited > uncited)
    citation_factor = cited_count / total_count

    # 5. Quality bonuses
    if experiment.validated: bonus += 0.1
    if test.validated: bonus += 0.1
    if doc.has_citations: bonus += 0.05

    # Weighted average + bonus
    quality = (
        count_factor * 0.3 +
        diversity_factor * 0.2 +
        validation_factor * 0.3 +
        citation_factor * 0.2
    ) + bonus

    return min(1.2, quality)  # Can boost above 1.0
```

### 4. Domain-Specific Requirements

Different task types have different evidence requirements:

```python
# Debugging requires:
- REASONING (hypothesis)
- EXPERIMENT (reproduction)
- CODE_ANALYSIS (root cause)
- CODE (fix)
- REGRESSION_TEST (prevent recurrence)

# Design requires:
- DOC (requirements)
- REASONING (alternatives + trade-offs)
- CODE (prototype)

# Research requires:
- DOC (questions + sources + notes)
- CODE (working examples)

# And 4 more domains...
```

**Domain Inference**:

```python
tasc = Tasc(title="Fix crash when user clicks logout")
domain = infer_domain_from_title(tasc.title)  # → DEBUGGING
apply_domain_to_tasc(tasc, domain)
# Sets tasc.required_evidence_types automatically
```

### 5. AB Memory Integration

Evidence and validation results persist in AB Memory:

```python
# Store evidence
evidence_card_id = store_evidence(memory, evidence, moment_id)

# Store entire collection
collection_card_id = store_evidence_collection(memory, collection, moment_id)

# Store validation result
validation_card_id = store_validation_result(memory, result, tasc_id, moment_id)

# Enables:
# - Retrospective validation (confidence updates)
# - Evidence search and reuse
# - Validation history and audit trails
```

### 6. Self-Testing Tascs (Advanced)

Tascs can generate and execute their own validation experiments:

```python
self_val = SelfValidatingTaskc(tasc, domain=TaskDomain.DEBUGGING)

# 1. Generate experiments
experiments = await self_val.synthesize_validation_experiments()
# → Generates hypothesis tests, regression tests, etc.

# 2. Execute experiments
results = await self_val.execute_validation_experiments()
# → Runs experiments in parallel

# 3. Generate evidence
evidence_collection = self_val.generate_evidence_collection()
# → Converts experiment results to evidence

# 4. Validate
result = await validate_tasc_with_evidence(tasc, evidence_collection)
```

This directly applies the learning system's EXPLORE mode experimental methodology to task validation.

## Usage Examples

### Example 1: Debugging with Evidence

```python
# 1. Create tasc
tasc = Tasc(
    id="debug-001",
    title="Fix crash when user clicks logout",
    testing_instructions="pytest tests/auth/test_logout.py",
)
apply_domain_to_tasc(tasc, TaskDomain.DEBUGGING)

# 2. Collect evidence during debugging
collection = EvidenceCollection.create(tasc.id)

# Hypothesis
collection.add_evidence(Evidence.create(
    text="Hypothesis: Null pointer in SessionManager.cleanup()",
    source=EvidenceSource.REASONING,
    citations=["debugger_analysis"],
))

# Reproduction
reproduction = Evidence.create(
    text="Reproduced bug in 4 steps...",
    source=EvidenceSource.EXPERIMENT,
    citations=["reproduction_script.sh"],
)
reproduction.validated = True
collection.add_evidence(reproduction)

# Root cause
collection.add_evidence(Evidence.create(
    text="Root cause: Missing null check on user.session",
    source=EvidenceSource.CODE_ANALYSIS,
    citations=["src/auth/session_manager.py:142"],
))

# Fix
collection.add_evidence(Evidence.create(
    text="Added null check before accessing user.session",
    source=EvidenceSource.CODE,
    citations=["commit:abc123"],
))

# Regression test
regression_test = Evidence.create(
    text="Added test_logout_with_expired_session()",
    source=EvidenceSource.REGRESSION_TEST,
    citations=["tests/auth/test_logout.py"],
)
regression_test.validated = True
collection.add_evidence(regression_test)

# 3. Validate
result = await validate_tasc_with_evidence(tasc, collection)

print(f"Confidence: {result.overall_confidence:.1%}")
# → 95% (all required evidence present, 2 validated, all cited)

print(f"Status: {result.validation_status}")
# → "complete"

print(f"Requires Review: {result.requires_human_review}")
# → False
```

### Example 2: Self-Testing Tasc

```python
# 1. Create tasc
tasc = Tasc(
    id="auto-001",
    title="Fix memory leak in WebSocket handler",
)

# 2. Self-validate
self_val = SelfValidatingTaskc(tasc, TaskDomain.DEBUGGING)
evidence_collection = await self_val.self_validate()

# Automatically:
# - Generated 3 experiments (bug reproduction, regression test, no breakage)
# - Executed experiments in parallel
# - Created evidence from results

# 3. Validate
result = await validate_tasc_with_evidence(tasc, evidence_collection)
```

### Example 3: Design Validation

```python
tasc = Tasc(title="Design caching layer for API")
apply_domain_to_tasc(tasc, TaskDomain.DESIGN)

collection = EvidenceCollection.create(tasc.id)

# Requirements
collection.add_evidence(Evidence.create(
    text="Requirements: Reduce latency 50%, support 10k req/sec...",
    source=EvidenceSource.DOC,
    citations=["docs/cache_requirements.md"],
))

# Alternatives
collection.add_evidence(Evidence.create(
    text="Evaluated 3 options: Redis, in-process LRU, CDN. Selected Redis + L1 cache.",
    source=EvidenceSource.REASONING,
    citations=["docs/cache_alternatives.md"],
))

# Trade-offs
collection.add_evidence(Evidence.create(
    text="Trade-off: Consistency vs Performance. Chose eventual consistency (5min TTL).",
    source=EvidenceSource.REASONING,
    citations=["docs/cache_tradeoffs.md"],
))

# Prototype
prototype = Evidence.create(
    text="Prototype shows 60% latency reduction (exceeds target)",
    source=EvidenceSource.CODE,
    citations=["benchmarks/results.json"],
)
prototype.validated = True
collection.add_evidence(prototype)

result = await validate_tasc_with_evidence(tasc, collection)
# High confidence due to thorough reasoning and validated prototype
```

## Validation Decision Tree

```
Start: Validate task
│
├─ Collect evidence during work
│  ├─ Documentation (requirements, notes)
│  ├─ Reasoning (hypotheses, trade-offs)
│  ├─ Code (implementation, fixes)
│  ├─ Tests (results, coverage)
│  └─ Experiments (reproductions, validations)
│
├─ Run validation
│  ├─ Evidence quality evaluation
│  │  ├─ Count: 5 items → 100% factor
│  │  ├─ Diversity: 3+ sources → 100% factor
│  │  ├─ Validation: 80%+ validated → 80% factor
│  │  └─ Citations: 100% cited → 100% factor
│  │  └─ Bonuses: validated experiments/tests → +20%
│  │
│  ├─ Process adherence
│  │  └─ All required evidence types present → 100% factor
│  │
│  └─ Objective checks
│     └─ Tests pass, builds work → 100% factor
│
└─ Determine outcome
   ├─ Confidence ≥ 80% & complete → "complete" ✅
   ├─ Confidence ≥ 60% → "partial" ⚠️
   ├─ Confidence < 60% → "failed" ❌
   └─ Missing evidence or low confidence → Human review required
```

## Benefits

### 1. Auditable Work
Every decision, hypothesis, and change is documented with evidence. You can trace why something was done.

### 2. Confidence Scoring
Instead of binary pass/fail, get nuanced confidence levels:
- 90-100%: Very high confidence, complete evidence
- 70-90%: Good confidence, may have minor gaps
- 50-70%: Uncertain, missing key evidence
- <50%: Low confidence, requires review

### 3. Domain-Specific Validation
Different task types get appropriate validation requirements automatically:
- Debugging: Must have hypothesis, reproduction, root cause, fix, regression test
- Design: Must have requirements, alternatives, trade-offs, prototype
- Security: Must have threat model, scans, mitigations, tests (95% confidence threshold)

### 4. Retrospective Validation
Confidence can be updated as new evidence emerges:
```python
# New evidence discovered after validation
new_evidence = [Evidence.create(...), Evidence.create(...)]
updated_result = update_validation_confidence(memory, tasc_id, new_evidence)
```

### 5. Evidence Reuse
Evidence is searchable and reusable:
```python
# Find past evidence of similar bugs
similar_evidence = search_evidence_by_text(memory, "null pointer")

# Learn from past validations
similar_cases = find_similar_validation_cases(memory, current_tasc)
```

### 6. Human Review Gates
Automatically triggers human review when:
- Confidence < 70%
- Missing required evidence
- Objective checks fail
- Evidence quality insufficient

## Integration with Learning System

The validation system directly applies the learning system's proven methodology:

| Learning System (EXPLORE mode) | Validation System |
|--------------------------------|-------------------|
| Theorem to prove | Task to validate |
| Experiments | Validation experiments |
| Evidence from experiments | Evidence from work |
| Confidence scoring | Validation confidence |
| Multi-factor evaluation | Multi-factor validation |
| Self-testing beliefs | Self-testing tascs |

**Same confidence formula**, **same evidence evaluation**, **same methodology** - but applied to task validation instead of knowledge acquisition.

## File Structure

```
tasc/
├── evidence.py              # Evidence and EvidenceCollection
├── validation.py            # UnifiedValidator
├── domains.py              # Domain-specific requirements
├── self_validation.py      # Self-testing tascs
├── ab_storage.py           # AB Memory integration
└── atomtypes.py            # Evidence atom types (pindex=10,11)

examples/
├── validation_debugging_example.py
├── validation_design_example.py
└── validation_self_testing_example.py

tests/
└── test_evidence_based_validation.py
```

## Running Examples

```bash
# Debugging validation example
python3 examples/validation_debugging_example.py

# Design validation example
python3 examples/validation_design_example.py

# Self-testing tasc example
python3 examples/validation_self_testing_example.py

# Run tests
pytest tests/test_evidence_based_validation.py -v
```

## Future Enhancements

1. **Machine Learning on Evidence Patterns**
   - Learn which evidence combinations predict success
   - Adjust weights based on historical validation outcomes

2. **Automated Evidence Collection**
   - Git hooks to automatically collect code evidence
   - Test framework integration for automatic test evidence
   - IDE plugins for inline evidence collection

3. **Evidence Visualization**
   - Evidence graphs showing relationships
   - Confidence evolution over time
   - Missing evidence highlighting

4. **Cross-Task Evidence Linking**
   - Reference evidence from related tasks
   - Build evidence libraries by domain
   - Evidence reuse recommendations

5. **Integration with Proof-of-Work**
   - Evidence as proof artifacts
   - Cryptographic validation of evidence
   - Evidence-based task reputation scores

## Conclusion

Evidence-based validation replaces binary pass/fail with a principled, probabilistic approach based on collected artifacts. This makes validation more appropriate for real-world problem-solving where perfect validators don't exist.

By building on the learning system's proven confidence-scoring methodology and the Atom foundation, we've created a validation system that is:
- **Rigorous**: Multi-factor evidence evaluation
- **Flexible**: Works for any task domain
- **Auditable**: Complete evidence trails
- **Improvable**: Confidence updates over time
- **Automated**: Self-testing capabilities

The result: validation that actually matches how experts assess work quality - through evidence, not arbitrary gates.
