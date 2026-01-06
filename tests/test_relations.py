"""Tests for typed semantic relations system.

Tests cover:
- Relation creation and serialization
- RelationType properties
- Database storage and retrieval
- Causal chain tracing
- Support networks
- Contradiction detection
- Task dependencies
- Evolution tracking
"""

import pytest
import tempfile
import os
from tasc.relations import (
    Relation,
    RelationType,
    RelationCollection,
    create_causal_chain,
    create_support_network,
    create_dependency_graph,
)
from tasc.relation_storage import (
    store_relation,
    get_relations_from_card,
    get_relations_to_card,
    get_relation_by_id,
    delete_relation,
    count_relations,
    get_causal_chain,
    get_support_network,
    calculate_support_strength,
    find_contradictions,
    get_dependencies,
    check_dependencies_satisfied,
    topological_sort_tasks,
    get_evolution_chain,
)
from ab.abdb import ABMemory
from ab.models import Card, Buffer


@pytest.fixture
def memory():
    """Create a temporary AB Memory instance."""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    mem = ABMemory(path)
    yield mem
    os.unlink(path)


@pytest.fixture
def sample_cards(memory):
    """Create sample cards for testing."""
    cards = {}

    # Create 10 test cards
    for i in range(10):
        card = memory.store_card(
            label=f"Test Card {i}",
            buffers=[Buffer(name="test", payload=f"Card {i} data".encode())],
            track="execution",
        )
        cards[i] = card.id

    return cards


def test_relation_creation():
    """Test basic relation creation."""
    rel = Relation.create(
        relation_id="rel_001",
        relation_type=RelationType.CAUSES,
        source_card_id=1,
        target_card_id=2,
        confidence=0.95,
        metadata={"reason": "test"},
    )

    assert rel.id == "rel_001"
    assert rel.type == RelationType.CAUSES
    assert rel.source_card_id == 1
    assert rel.target_card_id == 2
    assert rel.confidence == 0.95
    assert rel.metadata["reason"] == "test"


def test_relation_atom_serialization():
    """Test Relation to/from Atom conversion."""
    rel = Relation.create(
        relation_id="rel_001",
        relation_type=RelationType.SUPPORTS,
        source_card_id=100,
        target_card_id=200,
        confidence=0.85,
    )

    # Convert to atom
    atom = rel.to_atom()
    assert atom.pindex == 12  # relation pindex

    # Convert back
    rel2 = Relation.from_atom(atom)
    assert rel2.id == rel.id
    assert rel2.type == rel.type
    assert rel2.source_card_id == rel.source_card_id
    assert rel2.target_card_id == rel.target_card_id
    assert rel2.confidence == rel.confidence


def test_relation_type_properties():
    """Test RelationType property methods."""
    causes = Relation.create("r1", RelationType.CAUSES, 1, 2)
    assert causes.is_transitive()
    assert not causes.is_symmetric()

    contradicts = Relation.create("r2", RelationType.CONTRADICTS, 1, 2)
    assert contradicts.is_symmetric()
    assert not contradicts.is_transitive()

    equals = Relation.create("r3", RelationType.EQUALS, 1, 2)
    assert equals.is_transitive()
    assert equals.is_symmetric()


def test_relation_inverse_types():
    """Test inverse relation type lookup."""
    refines = Relation.create("r1", RelationType.REFINES, 1, 2)
    assert refines.get_inverse_type() == RelationType.GENERALIZES

    generalizes = Relation.create("r2", RelationType.GENERALIZES, 1, 2)
    assert generalizes.get_inverse_type() == RelationType.REFINES

    causes = Relation.create("r3", RelationType.CAUSES, 1, 2)
    assert causes.get_inverse_type() is None  # No natural inverse


def test_relation_collection():
    """Test RelationCollection functionality."""
    collection = RelationCollection.create("coll_001", "Test collection")

    rel1 = Relation.create("r1", RelationType.CAUSES, 1, 2)
    rel2 = Relation.create("r2", RelationType.SUPPORTS, 3, 4)
    rel3 = Relation.create("r3", RelationType.CAUSES, 2, 3)

    collection.add_relation(rel1)
    collection.add_relation(rel2)
    collection.add_relation(rel3)

    assert len(collection.relations) == 3

    # Filter by type
    causes_rels = collection.get_by_type(RelationType.CAUSES)
    assert len(causes_rels) == 2

    # Filter by source
    from_card_1 = collection.get_by_source(1)
    assert len(from_card_1) == 1
    assert from_card_1[0].id == "r1"

    # Filter by target
    to_card_3 = collection.get_by_target(3)
    assert len(to_card_3) == 1
    assert to_card_3[0].id == "r3"


def test_store_and_retrieve_relation(memory, sample_cards):
    """Test storing and retrieving relations from database."""
    rel = Relation.create(
        relation_id="rel_001",
        relation_type=RelationType.CAUSES,
        source_card_id=sample_cards[0],
        target_card_id=sample_cards[1],
        confidence=0.95,
    )

    # Store relation
    store_relation(memory, rel)

    # Retrieve by ID
    retrieved = get_relation_by_id(memory, "rel_001")
    assert retrieved is not None
    assert retrieved.id == "rel_001"
    assert retrieved.type == RelationType.CAUSES
    assert retrieved.source_card_id == sample_cards[0]
    assert retrieved.confidence == 0.95


def test_get_relations_from_card(memory, sample_cards):
    """Test getting relations where card is the source."""
    # Create multiple relations from card 0
    rel1 = Relation.create("r1", RelationType.CAUSES, sample_cards[0], sample_cards[1])
    rel2 = Relation.create("r2", RelationType.IMPLIES, sample_cards[0], sample_cards[2])
    rel3 = Relation.create("r3", RelationType.CAUSES, sample_cards[0], sample_cards[3])

    store_relation(memory, rel1)
    store_relation(memory, rel2)
    store_relation(memory, rel3)

    # Get all relations from card 0
    all_from_0 = get_relations_from_card(memory, sample_cards[0])
    assert len(all_from_0) == 3

    # Filter by type
    causes_from_0 = get_relations_from_card(memory, sample_cards[0], RelationType.CAUSES)
    assert len(causes_from_0) == 2


def test_get_relations_to_card(memory, sample_cards):
    """Test getting relations where card is the target."""
    # Create multiple relations to card 5
    rel1 = Relation.create("r1", RelationType.SUPPORTS, sample_cards[0], sample_cards[5])
    rel2 = Relation.create("r2", RelationType.SUPPORTS, sample_cards[1], sample_cards[5])
    rel3 = Relation.create("r3", RelationType.SUPPORTS, sample_cards[2], sample_cards[5])

    store_relation(memory, rel1)
    store_relation(memory, rel2)
    store_relation(memory, rel3)

    # Get all relations to card 5
    all_to_5 = get_relations_to_card(memory, sample_cards[5], RelationType.SUPPORTS)
    assert len(all_to_5) == 3


def test_delete_relation(memory, sample_cards):
    """Test deleting a relation."""
    rel = Relation.create("r1", RelationType.CAUSES, sample_cards[0], sample_cards[1])
    store_relation(memory, rel)

    # Verify it exists
    assert get_relation_by_id(memory, "r1") is not None

    # Delete it
    delete_relation(memory, "r1")

    # Verify it's gone
    assert get_relation_by_id(memory, "r1") is None


def test_count_relations(memory, sample_cards):
    """Test counting relations with filters."""
    # Create various relations
    rel1 = Relation.create("r1", RelationType.CAUSES, sample_cards[0], sample_cards[1])
    rel2 = Relation.create("r2", RelationType.CAUSES, sample_cards[0], sample_cards[2])
    rel3 = Relation.create("r3", RelationType.SUPPORTS, sample_cards[1], sample_cards[3])

    store_relation(memory, rel1)
    store_relation(memory, rel2)
    store_relation(memory, rel3)

    # Count all relations
    assert count_relations(memory) == 3

    # Count from specific source
    assert count_relations(memory, source_card_id=sample_cards[0]) == 2

    # Count specific type
    assert count_relations(memory, relation_type=RelationType.CAUSES) == 2

    # Count with multiple filters
    assert count_relations(
        memory,
        source_card_id=sample_cards[0],
        relation_type=RelationType.CAUSES,
    ) == 2


def test_causal_chain_helper():
    """Test causal chain creation helper."""
    card_ids = [1, 2, 3, 4, 5]
    relations = create_causal_chain(card_ids, "chain", confidence=0.9)

    assert len(relations) == 4  # N-1 relations for N cards
    assert all(r.type == RelationType.CAUSES for r in relations)
    assert all(r.confidence == 0.9 for r in relations)

    # Verify chain structure
    assert relations[0].source_card_id == 1
    assert relations[0].target_card_id == 2
    assert relations[3].source_card_id == 4
    assert relations[3].target_card_id == 5


def test_support_network_helper():
    """Test support network creation helper."""
    evidence_ids = [1, 2, 3, 4]
    belief_id = 100
    confidences = [0.95, 0.9, 0.85, 0.8]

    relations = create_support_network(evidence_ids, belief_id, "support", confidences)

    assert len(relations) == 4
    assert all(r.type == RelationType.SUPPORTS for r in relations)
    assert all(r.target_card_id == belief_id for r in relations)
    assert [r.confidence for r in relations] == confidences


def test_dependency_graph_helper():
    """Test dependency graph creation helper."""
    task_pairs = [(2, 1), (3, 1), (4, 2), (4, 3)]  # (dependent, prerequisite)
    relations = create_dependency_graph(task_pairs, "dep")

    assert len(relations) == 4
    assert all(r.type == RelationType.DEPENDS_ON for r in relations)

    # Verify structure
    assert relations[0].source_card_id == 2
    assert relations[0].target_card_id == 1


def test_get_causal_chain(memory, sample_cards):
    """Test tracing causal chain backwards."""
    # Create chain: 0 -> 1 -> 2 -> 3
    chain = create_causal_chain([sample_cards[i] for i in range(4)], "chain")
    for rel in chain:
        store_relation(memory, rel)

    # Trace backwards from card 3
    traced = get_causal_chain(memory, sample_cards[3], max_depth=10)

    assert len(traced) == 3
    assert traced[0].target_card_id == sample_cards[3]
    assert traced[0].source_card_id == sample_cards[2]
    assert traced[2].source_card_id == sample_cards[0]


def test_get_support_network(memory, sample_cards):
    """Test getting evidence support network."""
    # Create support network: 0, 1, 2 -> 5
    evidence_ids = [sample_cards[i] for i in range(3)]
    belief_id = sample_cards[5]

    network = create_support_network(evidence_ids, belief_id, "support")
    for rel in network:
        store_relation(memory, rel)

    # Get support network
    support = get_support_network(memory, belief_id)

    assert len(support) == 3
    assert all(r.target_card_id == belief_id for r in support)


def test_calculate_support_strength(memory, sample_cards):
    """Test calculating overall support strength."""
    belief_id = sample_cards[5]

    # Create support with varying confidence
    evidence_ids = [sample_cards[i] for i in range(4)]
    confidences = [0.9, 0.85, 0.8, 0.95]

    network = create_support_network(evidence_ids, belief_id, "support", confidences)
    for rel in network:
        store_relation(memory, rel)

    # Calculate strength
    strength = calculate_support_strength(memory, belief_id)

    # Average is 0.875, with 10% bonus for 4 sources
    expected = sum(confidences) / len(confidences) * 1.1
    assert abs(strength - expected) < 0.01


def test_find_contradictions(memory, sample_cards):
    """Test finding contradictions."""
    # Create contradictions involving card 0
    rel1 = Relation.create("c1", RelationType.CONTRADICTS, sample_cards[0], sample_cards[1])
    rel2 = Relation.create("c2", RelationType.CONTRADICTS, sample_cards[2], sample_cards[0])
    rel3 = Relation.create("c3", RelationType.CONTRADICTS, sample_cards[3], sample_cards[4])  # Not involving 0

    store_relation(memory, rel1)
    store_relation(memory, rel2)
    store_relation(memory, rel3)

    # Find contradictions for card 0
    contradictions = find_contradictions(memory, sample_cards[0])

    assert len(contradictions) == 2  # rel1 and rel2


def test_get_dependencies(memory, sample_cards):
    """Test getting task dependencies."""
    # Create dependencies: 5 depends on 0, 1, 2
    deps = create_dependency_graph(
        [
            (sample_cards[5], sample_cards[0]),
            (sample_cards[5], sample_cards[1]),
            (sample_cards[5], sample_cards[2]),
        ],
        "dep",
    )

    for rel in deps:
        store_relation(memory, rel)

    # Get dependencies for card 5
    dependencies = get_dependencies(memory, sample_cards[5])

    assert len(dependencies) == 3
    assert all(r.source_card_id == sample_cards[5] for r in dependencies)


def test_check_dependencies_satisfied(memory, sample_cards):
    """Test checking if dependencies are satisfied."""
    # Create dependency: 5 depends on 0, 1
    deps = create_dependency_graph(
        [
            (sample_cards[5], sample_cards[0]),
            (sample_cards[5], sample_cards[1]),
        ],
        "dep",
    )

    for rel in deps:
        store_relation(memory, rel)

    # Check with all dependencies completed
    assert check_dependencies_satisfied(
        memory,
        sample_cards[5],
        [sample_cards[0], sample_cards[1]],
    )

    # Check with incomplete dependencies
    assert not check_dependencies_satisfied(
        memory,
        sample_cards[5],
        [sample_cards[0]],  # Missing card 1
    )


def test_topological_sort_tasks(memory, sample_cards):
    """Test topological sorting of tasks by dependencies."""
    # Create dependency graph:
    # 0 (no deps) -> 1, 2
    # 1, 2 -> 3
    # 3 -> 4
    deps = create_dependency_graph(
        [
            (sample_cards[1], sample_cards[0]),
            (sample_cards[2], sample_cards[0]),
            (sample_cards[3], sample_cards[1]),
            (sample_cards[3], sample_cards[2]),
            (sample_cards[4], sample_cards[3]),
        ],
        "dep",
    )

    for rel in deps:
        store_relation(memory, rel)

    # Sort tasks
    task_ids = [sample_cards[i] for i in range(5)]
    sorted_ids = topological_sort_tasks(memory, task_ids)

    # Verify ordering
    assert sorted_ids.index(sample_cards[0]) < sorted_ids.index(sample_cards[1])
    assert sorted_ids.index(sample_cards[0]) < sorted_ids.index(sample_cards[2])
    assert sorted_ids.index(sample_cards[1]) < sorted_ids.index(sample_cards[3])
    assert sorted_ids.index(sample_cards[2]) < sorted_ids.index(sample_cards[3])
    assert sorted_ids.index(sample_cards[3]) < sorted_ids.index(sample_cards[4])


def test_topological_sort_circular_dependency(memory, sample_cards):
    """Test that circular dependencies raise an error."""
    # Create circular dependency: 0 -> 1 -> 2 -> 0
    deps = create_dependency_graph(
        [
            (sample_cards[1], sample_cards[0]),
            (sample_cards[2], sample_cards[1]),
            (sample_cards[0], sample_cards[2]),  # Creates cycle
        ],
        "dep",
    )

    for rel in deps:
        store_relation(memory, rel)

    task_ids = [sample_cards[i] for i in range(3)]

    with pytest.raises(ValueError, match="Circular dependency"):
        topological_sort_tasks(memory, task_ids)


def test_get_evolution_chain(memory, sample_cards):
    """Test tracing evolution chain through TRANSFORMS relations."""
    # Create evolution: 0 -> 1 -> 2 -> 3
    chain = []
    for i in range(3):
        rel = Relation.create(
            f"t{i}",
            RelationType.TRANSFORMS,
            sample_cards[i],
            sample_cards[i + 1],
            metadata={"reason": f"evolution step {i}"},
        )
        chain.append(rel)
        store_relation(memory, rel)

    # Trace evolution from card 0
    traced = get_evolution_chain(memory, sample_cards[0])

    assert len(traced) == 3
    assert traced[0].source_card_id == sample_cards[0]
    assert traced[0].target_card_id == sample_cards[1]
    assert traced[2].target_card_id == sample_cards[3]


def test_relation_dict_serialization():
    """Test Relation to/from dict conversion."""
    rel = Relation.create(
        relation_id="rel_001",
        relation_type=RelationType.SUPPORTS,
        source_card_id=100,
        target_card_id=200,
        confidence=0.85,
        metadata={"test": "data"},
    )

    # Convert to dict
    d = rel.to_dict()
    assert d["id"] == "rel_001"
    assert d["type"] == "supports"
    assert d["source_card_id"] == 100
    assert d["confidence"] == 0.85

    # Convert back
    rel2 = Relation.from_dict(d)
    assert rel2.id == rel.id
    assert rel2.type == rel.type
    assert rel2.source_card_id == rel.source_card_id


def test_relation_collection_serialization():
    """Test RelationCollection to/from dict conversion."""
    collection = RelationCollection.create("coll_001", "Test")

    rel1 = Relation.create("r1", RelationType.CAUSES, 1, 2)
    rel2 = Relation.create("r2", RelationType.SUPPORTS, 3, 4)

    collection.add_relation(rel1)
    collection.add_relation(rel2)

    # Convert to dict
    d = collection.to_dict()
    assert d["id"] == "coll_001"
    assert len(d["relations"]) == 2

    # Convert back
    collection2 = RelationCollection.from_dict(d)
    assert collection2.id == collection.id
    assert len(collection2.relations) == 2
