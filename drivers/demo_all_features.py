#!/usr/bin/env python3
"""Comprehensive demonstration of AB and TASC capabilities.

This script showcases every major feature of the system with practical,
real-life usage examples. Run with: python3 demo_all_features.py

Each section demonstrates a feature with:
1. What it does
2. Real-world use case
3. Working code example
"""

import os
import tempfile
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ab import (
    ABMemory, Buffer, CardStats,
    apply_transform, transform_registry,
    decay_formula, apply_decay_to_all, get_stale_cards,
    Self, Proposal, PlannerSelf, ArchitectSelf, ExecutorSelf, self_registry,
    rfs_recall, attention_jump, build_recall_chain, get_connection_graph,
    semantic_search, find_similar_cards, embed_text, cosine_similarity,
    Overlord, LaneManager, search_cards,
    create_awareness_card, subscribe_to_awareness,
)
from ab.recall import recall_cards
from ab.checkpoint import checkpoint_after_planning, checkpoint_after_decision
from tasc.tasc import Tasc
from tasc.ab_integration import store_tasc, load_tasc


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_subheader(title: str) -> None:
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def main():
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    memory = ABMemory(db_path=db_path)

    print_header("AB & TASC FEATURE DEMONSTRATION")
    print(f"Database: {db_path}")

    # =========================================================================
    # SECTION 1: BASIC MEMORY OPERATIONS
    # =========================================================================
    print_header("1. BASIC MEMORY OPERATIONS")
    
    print_subheader("Creating Moments and Cards")
    print("""
REAL-LIFE USE CASE: Logging an AI agent's thinking process
- Each moment represents a point in time when the agent processed something
- Cards store structured information about what was processed
- Buffers hold the actual data (prompts, responses, context)
""")
    
    # Create a moment
    moment = memory.create_moment(master_input="User asked about the weather")
    print(f"Created moment {moment.id} at {moment.timestamp}")
    
    # Store a card with buffers
    card = memory.store_card(
        label="conversation",
        buffers=[
            Buffer(name="user_input", payload=b"What's the weather today?", headers={"type": "question"}),
            Buffer(name="ai_response", payload=b"It's sunny and 72F in your area.", headers={"type": "answer"}),
            Buffer(name="context", payload=b'{"location": "San Francisco", "source": "weather_api"}', headers={"type": "json"}),
        ],
        moment_id=moment.id
    )
    print(f"Created card {card.id} with {len(card.buffers)} buffers")

    # =========================================================================
    # SECTION 2: CARD STATS & MEMORY PHYSICS
    # =========================================================================
    print_header("2. CARD STATS & MEMORY PHYSICS")
    
    print_subheader("Strength-Based Memory")
    print("""
REAL-LIFE USE CASE: Spaced repetition for learning
- Frequently accessed memories become stronger (like flashcards you know well)
- Rarely accessed memories fade over time (like facts you're forgetting)
- System automatically prioritizes important information
""")
    
    # Create some knowledge cards
    facts = [
        ("Python was created by Guido van Rossum", "programming"),
        ("The capital of France is Paris", "geography"),
        ("E = mc² is Einstein's famous equation", "physics"),
    ]
    
    fact_cards = []
    for fact, category in facts:
        card = memory.store_card(
            label="fact",
            buffers=[Buffer(name="content", payload=fact.encode(), headers={"category": category})]
        )
        fact_cards.append(card)
        print(f"Created fact card {card.id}: {fact[:40]}...")
    
    # Simulate "studying" - recall certain facts more often
    python_card = fact_cards[0]
    print(f"\nRecalling Python fact multiple times (simulating study)...")
    for i in range(5):
        stats = memory.recall_card(python_card.id)
        print(f"  Recall {i+1}: strength={stats.strength:.2f}, count={stats.recall_count}")
    
    # Compare strengths
    print("\nComparing memory strengths:")
    for card in fact_cards:
        stats = memory.get_card_stats(card.id)
        print(f"  Card {card.id}: strength={stats.strength:.2f} (recalled {stats.recall_count}x)")
    
    # Show strongest memories
    print("\nTop memories by strength:")
    top_cards = memory.list_cards_by_strength(limit=3)
    for i, stats in enumerate(top_cards, 1):
        print(f"  {i}. Card {stats.card_id}: strength={stats.strength:.2f}")

    print_subheader("Memory Decay")
    print("""
REAL-LIFE USE CASE: Simulating natural forgetting
- Memories weaken if not accessed (like forgetting a phone number)
- Half-life determines how fast forgetting occurs
- Important for keeping memory relevant and preventing overload
""")
    
    # Show decay formula
    print("\nDecay simulation (1 week half-life):")
    initial_strength = 10.0
    for hours in [0, 24, 168, 336, 504]:  # 0, 1 day, 1 week, 2 weeks, 3 weeks
        decayed = decay_formula(initial_strength, hours, half_life_hours=168.0)
        print(f"  After {hours:3d} hours: {decayed:.2f} (was {initial_strength})")

    # =========================================================================
    # SECTION 3: TRANSFORM SYSTEM
    # =========================================================================
    print_header("3. TRANSFORM SYSTEM")
    
    print_subheader("Buffer Transforms")
    print("""
REAL-LIFE USE CASE: Pre-processing text before analysis
- Normalize text (lowercase, strip whitespace)
- Extract features (length, word count)
- Chain multiple operations together
""")
    
    # Show available transforms
    print(f"Available transforms: {transform_registry.list_transforms()}")
    
    # Demonstrate each transform
    test_text = b"  HELLO World! This is a TEST.  "
    print(f"\nOriginal text: {test_text!r}")
    print(f"  identity:    {apply_transform('identity', test_text)!r}")
    print(f"  lower_text:  {apply_transform('lower_text', test_text)!r}")
    print(f"  upper_text:  {apply_transform('upper_text', test_text)!r}")
    print(f"  strip:       {apply_transform('strip', test_text)!r}")
    print(f"  len:         {apply_transform('len', test_text)!r}")
    
    print("\nTransform chaining:")
    print(f"  strip|lower_text: {apply_transform('strip|lower_text', test_text)!r}")
    print(f"  strip|upper_text|len: {apply_transform('strip|upper_text|len', test_text)!r}")

    # =========================================================================
    # SECTION 4: SELF AGENT SYSTEM
    # =========================================================================
    print_header("4. SELF AGENT SYSTEM")
    
    print_subheader("Cognitive Selves")
    print("""
REAL-LIFE USE CASE: Multi-agent AI system with specialized roles
- PlannerSelf: Strategic thinking, task breakdown
- ArchitectSelf: Design patterns, system structure
- ExecutorSelf: Action execution, task completion
- Each self produces proposals that compete for attention
""")
    
    # Create an awareness card with context
    awareness_card = memory.store_card(
        label="awareness",
        buffers=[
            Buffer(name="prompt", payload=b"Implement user authentication with OAuth2", headers={}),
            Buffer(name="context", payload=b"We are building a web application with React frontend", headers={}),
            Buffer(name="files", payload=b"src/auth.py, src/components/Login.tsx", headers={}),
            Buffer(name="tasks", payload=b"TODO: Add login page, TODO: Set up OAuth flow", headers={}),
        ]
    )
    
    # Have each self think about the task
    planner = PlannerSelf()
    architect = ArchitectSelf()
    executor = ExecutorSelf()
    
    print("\nSelf proposals for the authentication task:")
    for self in [planner, architect, executor]:
        proposal = self.think(awareness_card)
        print(f"\n  {self.name.upper()} (strength={proposal.strength:.1f}):")
        print(f"    {proposal.suggestion}")
        if proposal.metadata:
            print(f"    Metadata: {proposal.metadata}")
    
    print_subheader("Recursive Self Calls")
    print("""
REAL-LIFE USE CASE: Delegation between AI agents
- A planner can delegate specific tasks to an executor
- Enables complex multi-step reasoning
""")
    
    # Demonstrate recursive call
    planner.bind_memory(memory)
    delegated = planner.call_subself(executor, awareness_card)
    print(f"\nPlanner delegated to Executor:")
    print(f"  Executor's response: {delegated.suggestion}")

    # =========================================================================
    # SECTION 5: OVERLORD DECISION MAKING
    # =========================================================================
    print_header("5. OVERLORD DECISION MAKING")
    
    print_subheader("Proposal Arbitration")
    print("""
REAL-LIFE USE CASE: AI system making decisions from multiple options
- Multiple selves/agents propose actions
- Overlord selects the best option based on priority/strength
- Decision is persisted for later analysis
""")
    
    overlord = Overlord(memory)
    
    # Add competing proposals
    proposals = [
        {"subself_id": "planner", "action": "Create detailed implementation plan first", "priority": 3.5},
        {"subself_id": "executor", "action": "Start coding immediately", "priority": 5.2},
        {"subself_id": "architect", "action": "Review system design before implementing", "priority": 4.1},
    ]
    
    print("\nProposals submitted:")
    for p in proposals:
        overlord.add_proposal(p)
        print(f"  [{p['subself_id']}] priority={p['priority']}: {p['action'][:50]}")
    
    winner = overlord.decide()
    print(f"\n🏆 WINNER: {winner['subself_id']} with priority {winner['priority']}")
    print(f"   Action: {winner['action']}")

    # =========================================================================
    # SECTION 6: CONNECTIONS & RFS RECALL
    # =========================================================================
    print_header("6. CONNECTIONS & RFS RECALL")
    
    print_subheader("Card Connections")
    print("""
REAL-LIFE USE CASE: Building a knowledge graph
- Connect related pieces of information
- Navigate from one memory to related ones
- Strengthen connections that are frequently used
""")
    
    # Create a knowledge graph
    concept_python = memory.store_card("concept", [Buffer(name="text", payload=b"Python programming language", headers={})])
    concept_guido = memory.store_card("concept", [Buffer(name="text", payload=b"Guido van Rossum, Python creator", headers={})])
    concept_web = memory.store_card("concept", [Buffer(name="text", payload=b"Web development frameworks", headers={})])
    concept_django = memory.store_card("concept", [Buffer(name="text", payload=b"Django web framework", headers={})])
    concept_flask = memory.store_card("concept", [Buffer(name="text", payload=b"Flask microframework", headers={})])
    
    # Create connections
    memory.create_connection(concept_python.id, concept_guido.id, "created_by", strength=2.0)
    memory.create_connection(concept_python.id, concept_web.id, "used_for", strength=1.5)
    memory.create_connection(concept_web.id, concept_django.id, "includes", strength=1.8)
    memory.create_connection(concept_web.id, concept_flask.id, "includes", strength=1.6)
    memory.create_connection(concept_django.id, concept_python.id, "written_in", strength=2.0)
    
    print("Knowledge graph created:")
    print("  Python -> Guido (created_by)")
    print("  Python -> Web Dev (used_for)")
    print("  Web Dev -> Django (includes)")
    print("  Web Dev -> Flask (includes)")
    print("  Django -> Python (written_in)")
    
    print_subheader("Multi-Hop Traversal (RFS Recall)")
    print("""
REAL-LIFE USE CASE: Finding related information through chains
- Start from one concept and find all related concepts
- Discover indirect connections (friend of a friend)
- Score results by path strength
""")
    
    # Perform RFS recall from Python
    results = rfs_recall(memory, concept_python.id, max_hops=3, strengthen_path=False)
    
    print(f"\nStarting from 'Python', found {len(results)} related concepts:")
    for card, score, path in results:
        buf_text = card.buffers[0].payload.decode() if card.buffers else "?"
        path_str = " -> ".join(map(str, path))
        print(f"  Score {score:.3f}: {buf_text[:40]} (path: {path_str})")

    # =========================================================================
    # SECTION 7: SEMANTIC SEARCH
    # =========================================================================
    print_header("7. SEMANTIC SEARCH")
    
    print_subheader("Bag-of-Words Similarity")
    print("""
REAL-LIFE USE CASE: Finding relevant documents by meaning
- Search for concepts, not just exact keywords
- Rank results by semantic similarity
- Works without external ML models
""")
    
    # Create some documents
    docs = [
        "Machine learning is a subset of artificial intelligence",
        "Python is great for data science and AI applications",
        "JavaScript is popular for web development",
        "Deep learning uses neural networks for pattern recognition",
        "React is a JavaScript library for building UIs",
    ]
    
    doc_cards = []
    for doc in docs:
        card = memory.store_card("document", [Buffer(name="content", payload=doc.encode(), headers={})])
        doc_cards.append(card)
    
    # Search for AI-related documents
    query = "artificial intelligence machine learning"
    print(f"\nSearching for: '{query}'")
    results = semantic_search(memory, query, top_k=3, label_filter="document")
    
    print("\nTop matching documents:")
    for card, score in results:
        text = card.buffers[0].payload.decode()
        print(f"  Score {score:.3f}: {text[:60]}...")
    
    # Show embedding vectors
    print("\nEmbedding comparison:")
    vec1 = embed_text("machine learning")
    vec2 = embed_text("artificial intelligence")
    vec3 = embed_text("web development")
    
    print(f"  'machine learning' vs 'artificial intelligence': {cosine_similarity(vec1, vec2):.3f}")
    print(f"  'machine learning' vs 'web development': {cosine_similarity(vec1, vec3):.3f}")

    # =========================================================================
    # SECTION 8: TASC (Task Atoms)
    # =========================================================================
    print_header("8. TASC - TASK ATOMS")
    
    print_subheader("Task Management")
    print("""
REAL-LIFE USE CASE: AI-native task tracking
- Binary-efficient task storage
- Dependencies between tasks
- Integration with AB memory for persistence
""")
    
    # Create tasks
    task1 = Tasc(
        id="TASK-001",
        status="queued",
        title="Implement user authentication",
        additional_notes="Use OAuth2 with Google provider",
        testing_instructions="Test login flow with test accounts",
        desired_outcome="Users can log in with Google",
        dependencies=[]
    )
    
    task2 = Tasc(
        id="TASK-002",
        status="queued",
        title="Add user profile page",
        additional_notes="Display user info from OAuth",
        testing_instructions="Verify profile shows correct data",
        desired_outcome="Users see their profile after login",
        dependencies=["TASK-001"]  # Depends on auth
    )
    
    print("Tasks created:")
    print(f"  {task1.id}: {task1.title} (deps: {task1.dependencies})")
    print(f"  {task2.id}: {task2.title} (deps: {task2.dependencies})")
    
    # Store in AB memory
    card1_id = store_tasc(memory, task1)
    card2_id = store_tasc(memory, task2)
    print(f"\nStored as AB cards: {card1_id}, {card2_id}")
    
    # Load back
    loaded = load_tasc(memory, card1_id)
    print(f"Loaded back: {loaded.id} - {loaded.title}")

    # =========================================================================
    # SECTION 9: CHECKPOINTS
    # =========================================================================
    print_header("9. CHECKPOINTS")
    
    print_subheader("Development Workflow Cards")
    print("""
REAL-LIFE USE CASE: Documenting development decisions
- Spec cards: What we're building
- Plan cards: How we'll build it
- Decision cards: Why we chose this approach
""")
    
    # Use a task card as the anchor for checkpoints
    # (Checkpoints link back to a TASC card)
    print("Using TASC-001 as base for checkpoints...")
    
    # Create spec and plan checkpoint
    checkpoint_ids = checkpoint_after_planning(
        memory,
        tasc_card_id=card1_id,
        spec="Implement OAuth2 authentication with Google as the identity provider.",
        plan="1. Set up OAuth client\n2. Create login endpoint\n3. Handle callback\n4. Store sessions",
        known_pitfalls=["Token refresh handling", "CSRF protection"],
        definition_of_done=["User can log in", "Session persists", "Logout works"],
    )
    print(f"Created checkpoint: spec_id={checkpoint_ids['spec_id']}, plan_id={checkpoint_ids['plan_id']}")
    
    # Create a decision checkpoint
    decision_id = checkpoint_after_decision(
        memory,
        tasc_card_id=card1_id,
        decision="Use JWT for sessions",
        reasoning="Better scalability, works with microservices",
    )
    print(f"Created decision checkpoint: card_id={decision_id}")

    # =========================================================================
    # SECTION 10: AWARENESS & SUBSCRIPTIONS
    # =========================================================================
    print_header("10. AWARENESS & SUBSCRIPTIONS")
    
    print_subheader("Context Awareness")
    print("""
REAL-LIFE USE CASE: AI agent awareness of its environment
- Track what files are open, what errors occurred
- Subscribe to specific types of information
- React to changes in context
""")
    
    # Create awareness card
    awareness_id = create_awareness_card(
        memory,
        name="agent_context",
        buffers=[
            Buffer(name="current_file", payload=b"src/auth.py", headers={"type": "file"}),
            Buffer(name="open_tabs", payload=b'["auth.py", "test_auth.py", "README.md"]', headers={"type": "json"}),
            Buffer(name="last_error", payload=b"", headers={"type": "error"}),
        ]
    )
    print(f"Created awareness card {awareness_id}")
    
    # Create a subscriber card
    subscriber_card = memory.store_card("subscriber", [Buffer(name="inbox", payload=b"", headers={})])
    
    # Subscribe to specific buffers
    sub_ids = subscribe_to_awareness(
        memory,
        awareness_card_id=awareness_id,
        subscriber_card_id=subscriber_card.id,
        buffer_names=["last_error", "current_file"]
    )
    print(f"Subscribed to {len(sub_ids)} buffers (subscription ids: {sub_ids})")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("DEMONSTRATION COMPLETE")
    
    # Clean up
    memory.close()
    os.unlink(db_path)
    
    print("""
This demonstration covered all major features of the AB system:

1. BASIC MEMORY - Moments, cards, and buffers for structured storage
2. MEMORY PHYSICS - Strength-based recall and natural decay
3. TRANSFORMS - Text processing and chaining
4. SELF AGENTS - Specialized cognitive agents with think() interface
5. OVERLORD - Decision making from competing proposals
6. CONNECTIONS - Knowledge graph and RFS multi-hop recall
7. SEMANTIC SEARCH - Bag-of-words similarity matching
8. TASC - Binary-efficient task management
9. CHECKPOINTS - Development workflow documentation
10. AWARENESS - Context tracking and subscriptions

For more details, see the source code in the `ab/` and `tasc/` directories.
""")


if __name__ == "__main__":
    main()
