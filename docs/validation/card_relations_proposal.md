# Card Relations: Semantic Networks in AB Memory

## 🎯 The Opportunity

Currently, AB Memory stores **cards as isolated units**. We can search for similar cards via embeddings, but there's no explicit representation of **how cards relate to each other**.

Adding **typed relations** between cards would transform AB Memory from a flat store into a **rich semantic network**, enabling:
- Causal reasoning ("What caused this bug?")
- Logical inference ("If A implies B, and B implies C...")
- Contradiction detection ("This belief contradicts that observation")
- Transformation tracking ("How did this evolve into that?")
- Dependency graphs ("This task depends on those results")

## 🔗 Proposed Relation Types

### 1. **CAUSES** (Causal Relationship)
**Semantics**: Card A caused card B to exist or occur.

**Examples**:
```python
# Bug causes crash
bug_card CAUSES crash_report_card

# Code change causes test failure
commit_card CAUSES test_failure_card

# Hypothesis causes experiment
hypothesis_card CAUSES experiment_card

# Decision causes implementation
design_decision_card CAUSES implementation_card
```

**Use Cases**:
- Root cause analysis (trace back from effect to cause)
- Impact analysis (trace forward from cause to effects)
- Debugging (find what caused the bug)
- Causal inference (understanding system behavior)

**Properties**:
- **Transitive**: If A CAUSES B and B CAUSES C, then A indirectly causes C
- **Time-ordered**: Cause must precede effect temporally
- **Many-to-many**: Multiple causes for one effect, one cause for multiple effects

### 2. **IMPLIES** (Logical Implication)
**Semantics**: If card A is true, then card B must be true.

**Examples**:
```python
# Theorem implication
theorem_card("addition is commutative") IMPLIES belief_card("order doesn't matter")

# Requirement implication
requirement_card("must support 10k users") IMPLIES architecture_card("need load balancer")

# Evidence implication
evidence_card("all tests pass") IMPLIES belief_card("system is working")

# Constraint implication
constraint_card("must be < 100ms") IMPLIES design_card("use caching")
```

**Use Cases**:
- Logical inference chains
- Requirement traceability
- Proof validation
- Constraint propagation

**Properties**:
- **Transitive**: If A IMPLIES B and B IMPLIES C, then A IMPLIES C
- **Logical**: Based on formal or informal logic
- **Unidirectional**: A → B doesn't mean B → A

### 3. **CONTRADICTS** (Logical Contradiction)
**Semantics**: Card A and card B cannot both be true.

**Examples**:
```python
# Belief contradiction
belief_card("API latency is 50ms") CONTRADICTS measurement_card("actual latency 200ms")

# Hypothesis contradiction
hypothesis_card("bug is in parser") CONTRADICTS evidence_card("parser tests all pass")

# Design contradiction
design_card("synchronous processing") CONTRADICTS requirement_card("must handle 1M req/sec")

# Evidence contradiction
witness_A("system was down") CONTRADICTS witness_B("system was up")
```

**Use Cases**:
- Consistency checking
- Belief revision (when new evidence contradicts old belief)
- Conflict detection in requirements
- Debugging (eliminate contradicted hypotheses)

**Properties**:
- **Symmetric**: If A CONTRADICTS B, then B CONTRADICTS A
- **Requires resolution**: System should flag contradictions for human review
- **Context-dependent**: May contradict in one context but not another

### 4. **EQUALS** (Equivalence)
**Semantics**: Card A and card B represent the same thing.

**Examples**:
```python
# Same entity, different representations
card("user_123") EQUALS card("john.doe@example.com")

# Duplicate observations
observation_A("bug in login") EQUALS observation_B("authentication failure")

# Equivalent solutions
solution_A("use Redis") EQUALS solution_B("use in-memory cache")

# Synonym concepts
concept("ML") EQUALS concept("Machine Learning")
```

**Use Cases**:
- Deduplication
- Entity resolution
- Concept mapping
- Knowledge fusion

**Properties**:
- **Symmetric**: If A EQUALS B, then B EQUALS A
- **Transitive**: If A EQUALS B and B EQUALS C, then A EQUALS C
- **Reflexive**: A EQUALS A (every card equals itself)

### 5. **TRANSFORMS** (State Transformation)
**Semantics**: Card A evolved or transformed into card B.

**Examples**:
```python
# Code evolution
version_1_card TRANSFORMS version_2_card

# Belief update
initial_hypothesis TRANSFORMS revised_hypothesis

# Design iteration
rough_design TRANSFORMS detailed_design

# Learning progression
basic_understanding TRANSFORMS advanced_understanding
```

**Use Cases**:
- Version history tracking
- Belief evolution tracking
- Design iteration history
- Learning progression

**Properties**:
- **Time-ordered**: Transformation has temporal direction
- **Chain-able**: A → B → C → D (evolution chain)
- **Not reversible**: Transformation is one-way

### 6. **SUPPORTS** (Evidential Support)
**Semantics**: Card A provides evidence supporting card B.

**Examples**:
```python
# Evidence supports belief
test_result_card SUPPORTS belief_card("feature works correctly")

# Experiment supports theorem
experiment_card SUPPORTS theorem_card("addition is commutative")

# Documentation supports decision
doc_card("API comparison") SUPPORTS decision_card("chose REST over GraphQL")

# Measurement supports claim
benchmark_card SUPPORTS claim_card("50% faster")
```

**Use Cases**:
- Evidence tracking (what supports this belief?)
- Confidence scoring (more support = higher confidence)
- Justification chains (why do we believe this?)
- Validation (is there enough support?)

**Properties**:
- **Asymmetric**: A supports B doesn't mean B supports A
- **Degree**: Support can be strong or weak (weighted relation)
- **Accumulative**: Multiple support relations increase confidence

### 7. **DEPENDS_ON** (Dependency)
**Semantics**: Card B depends on card A (B cannot exist/complete without A).

**Examples**:
```python
# Task dependency
task_B("deploy to prod") DEPENDS_ON task_A("pass all tests")

# Knowledge dependency
understanding_B("calculus") DEPENDS_ON understanding_A("algebra")

# Implementation dependency
feature_B("user profiles") DEPENDS_ON feature_A("authentication")

# Evidence dependency
conclusion DEPENDS_ON premise
```

**Use Cases**:
- Task ordering (topological sort of dependencies)
- Prerequisite checking (can we do B yet?)
- Impact analysis (what breaks if A fails?)
- Learning paths (what should I learn first?)

**Properties**:
- **Asymmetric**: A depends on B doesn't mean B depends on A
- **Creates order**: Defines partial ordering
- **Transitive**: If B depends on A and C depends on B, then C depends on A
- **Critical**: Circular dependencies should be detected and flagged

### 8. **REFINES** (Refinement)
**Semantics**: Card B is a more detailed/precise version of card A.

**Examples**:
```python
# Requirement refinement
high_level_req("system must be fast") REFINES detailed_req("API < 100ms p99")

# Design refinement
abstract_design("use caching") REFINES concrete_design("Redis cluster with L1 cache")

# Concept refinement
general_concept("bug") REFINES specific_concept("null pointer dereference")

# Question refinement
broad_question("How does auth work?") REFINES specific_question("What is the JWT expiry time?")
```

**Use Cases**:
- Progressive elaboration
- Hierarchical knowledge structures
- Concept taxonomies
- Question decomposition

**Properties**:
- **Asymmetric**: Refinement goes from general → specific
- **Preserves semantics**: Refinement doesn't change meaning, just adds detail
- **Chain-able**: Can have multiple levels of refinement

### 9. **INVALIDATES** (Invalidation)
**Semantics**: Card B invalidates or supersedes card A (A is no longer valid).

**Examples**:
```python
# New evidence invalidates old belief
new_measurement INVALIDATES old_hypothesis

# Bug fix invalidates bug report
fix_commit INVALIDATES bug_report

# Updated requirement invalidates old design
new_requirement INVALIDATES outdated_design

# Counterexample invalidates conjecture
counterexample INVALIDATES proposed_theorem
```

**Use Cases**:
- Belief revision
- Deprecation tracking
- Knowledge updates
- Temporal reasoning

**Properties**:
- **Time-ordered**: Invalidation has temporal direction
- **Asymmetric**: A invalidates B doesn't mean B invalidates A
- **Strong**: Invalidated cards should be marked as obsolete

### 10. **GENERALIZES** (Generalization)
**Semantics**: Card B is a generalization of card A (A is a special case of B).

**Examples**:
```python
# Specific to general
case_study("bug in login") GENERALIZES pattern("authentication errors")

# Instance to class
instance("Redis v7.0") GENERALIZES category("in-memory databases")

# Example to principle
example("sorted array search") GENERALIZES principle("binary search")

# Specific theorem to general theorem
specific("addition of integers is commutative") GENERALIZES general("addition in Abelian groups is commutative")
```

**Use Cases**:
- Pattern discovery
- Concept hierarchy construction
- Learning transfer (apply general principle to new case)
- Abstraction

**Properties**:
- **Inverse of REFINES**: If A REFINES B, then B GENERALIZES A
- **Asymmetric**: Generalization has direction
- **Enables transfer**: Learn from specific → apply generally

## 🏗️ Implementation Architecture

### Relation Storage

**Option 1: Relation as Buffer** (Lightweight)
```python
# Store relations as special buffers in cards
relation_buffer = Buffer(
    name="relations",
    headers={"type": "relation"},
    payload=json.dumps({
        "relations": [
            {"type": "CAUSES", "target_card_id": 456, "confidence": 0.9},
            {"type": "IMPLIES", "target_card_id": 789, "confidence": 1.0},
        ]
    }).encode("utf-8"),
)
```

**Option 2: Relation as Atom** (First-class)
```python
# Register relation as Atom type (pindex=12)
@dataclass
class Relation:
    id: str
    type: RelationType  # CAUSES, IMPLIES, etc.
    source_card_id: int
    target_card_id: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))

    def to_atom(self) -> Atom:
        """Encode as Atom of type 'relation'."""
        # ... serialize to UObject → Atom
```

**Option 3: Relation as Card** (Full entity)
```python
# Relations are themselves cards (enables meta-relations)
relation_card = Card(
    label="CAUSES relation",
    buffers=[
        Buffer(name="source", payload=encode_int(source_card_id)),
        Buffer(name="target", payload=encode_int(target_card_id)),
        Buffer(name="type", payload="CAUSES".encode("utf-8")),
        Buffer(name="confidence", payload=encode_float(0.9)),
    ],
    track="execution",
)
```

**Recommendation**: **Option 2 (Relation as Atom)** provides the best balance:
- First-class type (pindex=12)
- Efficient storage
- Enables relation queries
- Maintains Atom architecture

### Relation Queries

```python
# Query API
class ABMemory:
    def get_relations(
        self,
        source_card_id: int,
        relation_type: Optional[RelationType] = None,
    ) -> List[Relation]:
        """Get all relations from a card."""

    def get_inverse_relations(
        self,
        target_card_id: int,
        relation_type: Optional[RelationType] = None,
    ) -> List[Relation]:
        """Get all relations pointing to a card."""

    def find_transitive_closure(
        self,
        start_card_id: int,
        relation_type: RelationType,
        max_depth: int = 10,
    ) -> List[int]:
        """Find all cards reachable via transitive relation."""

    def detect_contradictions(
        self,
        card_id: int,
    ) -> List[Tuple[int, int]]:
        """Find contradicting card pairs."""

    def get_causal_chain(
        self,
        effect_card_id: int,
    ) -> List[int]:
        """Trace back causal chain to root causes."""
```

### Relation Schema

```sql
-- If using SQL backend for relations
CREATE TABLE relations (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- CAUSES, IMPLIES, etc.
    source_card_id INTEGER NOT NULL,
    target_card_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0,
    metadata TEXT,  -- JSON
    created_at INTEGER NOT NULL,
    FOREIGN KEY (source_card_id) REFERENCES cards(id),
    FOREIGN KEY (target_card_id) REFERENCES cards(id)
);

-- Indices for efficient queries
CREATE INDEX idx_relations_source ON relations(source_card_id, type);
CREATE INDEX idx_relations_target ON relations(target_card_id, type);
CREATE INDEX idx_relations_type ON relations(type);
```

## 🧠 Use Cases & Examples

### Use Case 1: Root Cause Analysis

```python
# Find what caused a bug
crash_card = memory.search_cards("application crash", limit=1)[0]

# Trace causal chain backward
causes = memory.get_causal_chain(crash_card.id)
# Returns: [code_change_card, merge_card, deploy_card, crash_card]

# Identify root cause
root_cause = causes[0]
print(f"Root cause: {root_cause.label}")
# → "Root cause: Merged PR #123 without null check"
```

### Use Case 2: Logical Inference

```python
# Forward inference
if memory.has_relation(card_A, card_B, RelationType.IMPLIES):
    if card_A.is_true():
        # Infer card_B must also be true
        card_B.mark_inferred()

# Transitive inference
axiom = "If A and B, then C"
if card_A.is_true() and card_B.is_true():
    # Find all transitive implications
    implications = memory.find_transitive_closure(
        card_A.id, RelationType.IMPLIES
    )
    # Automatically derive conclusions
```

### Use Case 3: Contradiction Detection

```python
# Detect belief contradictions
new_measurement = Evidence.create(
    text="Measured latency: 200ms",
    source=EvidenceSource.METRIC,
)

# Check for contradictions with existing beliefs
contradictions = memory.detect_contradictions(new_measurement_card.id)

for existing_card_id, new_card_id in contradictions:
    existing = memory.fetch_card(existing_card_id)
    print(f"⚠️  Contradiction detected:")
    print(f"   Existing belief: {existing.label}")
    print(f"   New evidence: {new_measurement.text}")
    print(f"   → Requires belief revision")
```

### Use Case 4: Task Dependency Resolution

```python
# Build dependency graph
task_A = create_task("Write tests")
task_B = create_task("Deploy to staging")
task_C = create_task("Deploy to production")

# Define dependencies
memory.add_relation(Relation(
    type=RelationType.DEPENDS_ON,
    source_card_id=task_B.id,
    target_card_id=task_A.id,
))
memory.add_relation(Relation(
    type=RelationType.DEPENDS_ON,
    source_card_id=task_C.id,
    target_card_id=task_B.id,
))

# Topological sort for execution order
execution_order = memory.topological_sort([task_A.id, task_B.id, task_C.id])
# Returns: [task_A, task_B, task_C]

# Check if ready to execute
can_execute = memory.check_dependencies_satisfied(task_C.id)
# Returns: False (task_A not complete yet)
```

### Use Case 5: Evidence-Based Belief Validation

```python
# Build support network
belief = Belief("System performance is acceptable")

# Add supporting evidence
evidence_1 = Evidence("Benchmark: 95ms p99 latency")
evidence_2 = Evidence("User survey: 85% satisfied")
evidence_3 = Evidence("Load test: Handles 50k req/sec")

memory.add_relation(Relation(
    type=RelationType.SUPPORTS,
    source_card_id=evidence_1.id,
    target_card_id=belief.id,
    confidence=0.9,
))
# ... add more support relations

# Calculate belief confidence from support network
support_strength = memory.calculate_support_strength(belief.id)
# Returns: 0.88 (strong support from 3 evidence sources)
```

### Use Case 6: Learning Path Construction

```python
# Define prerequisite relationships
algebra = Concept("Algebra")
calculus = Concept("Calculus")
linear_algebra = Concept("Linear Algebra")
machine_learning = Concept("Machine Learning")

memory.add_relation(Relation(type=RelationType.DEPENDS_ON, source=calculus, target=algebra))
memory.add_relation(Relation(type=RelationType.DEPENDS_ON, source=linear_algebra, target=algebra))
memory.add_relation(Relation(type=RelationType.DEPENDS_ON, source=machine_learning, target=calculus))
memory.add_relation(Relation(type=RelationType.DEPENDS_ON, source=machine_learning, target=linear_algebra))

# Generate learning path
learning_path = memory.generate_learning_path(
    goal=machine_learning.id,
    current_knowledge=[algebra.id],
)
# Returns: [algebra, calculus, linear_algebra, machine_learning]
```

## 🎨 Visualization

Relations enable powerful knowledge graph visualizations:

```
         [Bug Report #123]
                ↓ CAUSES
         [Crash in Production]
                ↓ CAUSES
         [Investigation Task]
                ↓ CAUSES
         [Hypothesis: Null Pointer]
                ↓ TRANSFORMS
         [Root Cause: Missing Check]
                ↓ CAUSES
         [Fix Commit abc123]
                ↓ CAUSES
         [Regression Test]
                ↓ INVALIDATES
         [Bug Report #123]
```

## ⚖️ Trade-offs

### Pros:
✅ **Rich semantics**: Capture how knowledge relates
✅ **Inference**: Derive new knowledge from existing relations
✅ **Reasoning**: Causal chains, logical inference, contradiction detection
✅ **Provenance**: Track where beliefs come from
✅ **Dependencies**: Model prerequisites and dependencies explicitly
✅ **Evolution**: Track how knowledge transforms over time

### Cons:
❌ **Complexity**: More complex data model
❌ **Storage**: Additional storage for relations
❌ **Query overhead**: Relation queries add latency
❌ **Maintenance**: Relations need to be created and maintained
❌ **Ambiguity**: Relation semantics can be ambiguous
❌ **Consistency**: Ensuring relation consistency (no circular DEPENDS_ON, etc.)

## 🚀 Implementation Roadmap

### Phase 1: Foundation (2-3 days)
1. Define `RelationType` enum (10 relation types)
2. Create `Relation` dataclass with Atom serialization
3. Register `relation` atom type (pindex=12)
4. Add relation storage to `ABMemory`:
   - `add_relation(relation)`
   - `get_relations(source_id)`
   - `get_inverse_relations(target_id)`

### Phase 2: Core Queries (2-3 days)
1. Implement basic queries:
   - `find_by_type(relation_type)`
   - `find_path(source, target, relation_type)`
   - `find_transitive_closure(source, relation_type)`
2. Add relation indices for performance
3. Write comprehensive tests

### Phase 3: Advanced Reasoning (3-5 days)
1. Implement domain-specific algorithms:
   - `detect_contradictions(card_id)`
   - `calculate_support_strength(belief_id)`
   - `get_causal_chain(effect_id)`
   - `topological_sort(card_ids)` for DEPENDS_ON
2. Add consistency checking (detect cycles in DEPENDS_ON)
3. Implement inference rules

### Phase 4: Integration (2-3 days)
1. Integrate with evidence-based validation:
   - Evidence SUPPORTS beliefs automatically
   - Failed validations INVALIDATE previous beliefs
   - Root causes CAUSE bugs
2. Integrate with learning system:
   - Experiments SUPPORT theorems
   - Counterexamples INVALIDATE conjectures
3. Integration with Tasc system:
   - Tasks DEPEND_ON each other
   - Completed tasks CAUSE new tasks

### Phase 5: Visualization (3-5 days)
1. Graph export (GraphML, DOT)
2. Interactive graph viewer
3. Causal chain visualization
4. Dependency graph visualization

## 📊 Comparison to Existing Systems

| System | Relations | Notes |
|--------|-----------|-------|
| **Neo4j** | First-class relations | Graph database, rich query language |
| **RDF/OWL** | Triples (subject-predicate-object) | Semantic web standard |
| **Property Graphs** | Labeled, weighted edges | Common in knowledge graphs |
| **Roam Research** | Bidirectional links | Simple backlink model |
| **Notion** | Relations (databases) | Limited to database relations |
| **AB Memory (current)** | None (embeddings only) | Similarity-based, no explicit relations |
| **AB Memory (proposed)** | Typed relations as Atoms | Hybrid: embeddings + explicit relations |

## 🎯 Conclusion

Adding typed relations to AB Memory would **transform it from a document store into a knowledge graph**, enabling:

1. **Causal reasoning**: Trace causes and effects
2. **Logical inference**: Derive new knowledge
3. **Contradiction detection**: Find inconsistencies
4. **Dependency management**: Model prerequisites
5. **Provenance tracking**: Know where beliefs come from
6. **Evolution tracking**: See how knowledge changes

**Recommendation**: Implement relations as **Atom type (pindex=12)**, starting with core relation types (CAUSES, IMPLIES, SUPPORTS, DEPENDS_ON, CONTRADICTS) and gradually expanding based on use cases.

This would make AB Memory a **true semantic memory system** capable of sophisticated reasoning, not just retrieval.
