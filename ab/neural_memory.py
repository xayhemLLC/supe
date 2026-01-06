"""Neural Memory - Hebbian learning for card connections.

Implements biological memory principles:
1. Strengthening: Links used together grow stronger
2. Decay: Unused links weaken over time
3. Spreading Activation: Recall propagates through network
4. Hub Formation: Frequently accessed cards become central
5. Consolidation: Strong patterns become "fundamental branches"

Like neurons:
- Each card can have infinite connections
- Connection strength varies (synaptic weight)
- Activation spreads through the network
- Repeated patterns become highways
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


@dataclass
class NeuralLink:
    """A synapse-like connection between cards."""
    source_id: int
    target_id: int

    # Synaptic properties
    strength: float = 0.1          # Initial weak connection
    activation_count: int = 0      # Times co-activated
    last_activated: datetime = field(default_factory=datetime.utcnow)

    # Learning rates
    potentiation_rate: float = 0.15   # How fast links strengthen (LTP)
    depression_rate: float = 0.02     # How fast unused links weaken (LTD)

    def activate(self):
        """Strengthen this link (Hebbian learning)."""
        self.activation_count += 1
        self.last_activated = datetime.utcnow()

        # Long-term potentiation: strength increases with use
        # Diminishing returns as strength approaches 1.0
        growth = self.potentiation_rate * (1.0 - self.strength)
        self.strength = min(1.0, self.strength + growth)

    def decay(self, current_time: datetime = None):
        """Weaken from disuse (synaptic depression)."""
        current_time = current_time or datetime.utcnow()
        days_inactive = (current_time - self.last_activated).days

        if days_inactive > 0:
            # Exponential decay, but never below minimum
            decay_factor = math.exp(-self.depression_rate * days_inactive)
            self.strength = max(0.01, self.strength * decay_factor)

    @property
    def is_strong(self) -> bool:
        """Is this a well-established connection?"""
        return self.strength > 0.5 and self.activation_count > 5


@dataclass
class NeuralCard:
    """A neuron-like memory card."""
    card_id: int
    buffers: Dict

    # Neural properties
    activation: float = 0.0           # Current activation level (0-1)
    resting_potential: float = 0.0    # Baseline activation
    activation_threshold: float = 0.3  # Min activation to fire

    # Connections (can be infinite, like dendrites)
    outgoing: Dict[int, NeuralLink] = field(default_factory=dict)
    incoming: Dict[int, NeuralLink] = field(default_factory=dict)

    # Statistics
    recall_count: int = 0
    last_recalled: datetime = field(default_factory=datetime.utcnow)

    # Hub detection
    @property
    def connectivity(self) -> int:
        """Total connections (in + out)."""
        return len(self.outgoing) + len(self.incoming)

    @property
    def is_hub(self) -> bool:
        """Is this a highly-connected hub card?"""
        return self.connectivity > 20 and self.recall_count > 10

    def receive_activation(self, amount: float, from_card: int):
        """Receive activation from another card."""
        # Activation weighted by link strength
        if from_card in self.incoming:
            link = self.incoming[from_card]
            weighted = amount * link.strength
            self.activation = min(1.0, self.activation + weighted)

    def fire(self) -> bool:
        """Check if activation exceeds threshold."""
        return self.activation >= self.activation_threshold

    def reset(self):
        """Reset activation to resting potential."""
        self.activation = self.resting_potential


class NeuralMemory:
    """Memory system with neural dynamics.

    Key behaviors:
    - Queries strengthen pathways (learning)
    - Unused pathways weaken (forgetting)
    - Activation spreads through network (association)
    - Hubs emerge from repeated access (consolidation)
    """

    def __init__(self):
        self.cards: Dict[int, NeuralCard] = {}
        self.links: Dict[Tuple[int, int], NeuralLink] = {}

        # Query history for pattern detection
        self.query_history: List[Tuple[str, List[int], datetime]] = []

        # Concept index (word → card_ids)
        self.concept_index: Dict[str, Set[int]] = defaultdict(set)

    def add_card(self, card_id: int, buffers: Dict) -> NeuralCard:
        """Add a card to the network."""
        card = NeuralCard(card_id=card_id, buffers=buffers)
        self.cards[card_id] = card

        # Index concepts
        self._index_concepts(card)

        return card

    def _index_concepts(self, card: NeuralCard):
        """Extract and index concepts from card."""
        text = " ".join(str(v) for v in card.buffers.values())
        words = set(w.lower() for w in text.split() if len(w) > 3)

        for word in words:
            self.concept_index[word].add(card.card_id)

    def connect(self, source_id: int, target_id: int,
                initial_strength: float = 0.1) -> NeuralLink:
        """Create or strengthen a connection."""
        key = (source_id, target_id)

        if key in self.links:
            # Existing link - strengthen it
            self.links[key].activate()
        else:
            # New link
            link = NeuralLink(
                source_id=source_id,
                target_id=target_id,
                strength=initial_strength
            )
            self.links[key] = link

            # Add to card's connection lists
            if source_id in self.cards:
                self.cards[source_id].outgoing[target_id] = link
            if target_id in self.cards:
                self.cards[target_id].incoming[source_id] = link

        return self.links[key]

    def recall(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Recall memories using spreading activation.

        This is how biological recall works:
        1. Query activates matching cards
        2. Activation spreads through strong links
        3. Most activated cards are recalled
        4. Pathways used get strengthened
        """
        # Reset all activations
        for card in self.cards.values():
            card.reset()

        # Phase 1: Initial activation from query
        query_words = set(w.lower() for w in query.split() if len(w) > 3)
        initially_activated = set()

        for word in query_words:
            for card_id in self.concept_index.get(word, []):
                if card_id in self.cards:
                    self.cards[card_id].activation += 0.3
                    initially_activated.add(card_id)

        # Phase 2: Spreading activation (multiple waves)
        for wave in range(3):
            wave_strength = 0.7 ** wave  # Diminishing waves

            activated_this_wave = []
            for card_id in list(self.cards.keys()):
                card = self.cards[card_id]
                if card.fire():
                    activated_this_wave.append(card_id)

            # Spread to neighbors
            for card_id in activated_this_wave:
                card = self.cards[card_id]
                for target_id, link in card.outgoing.items():
                    if target_id in self.cards:
                        spread_amount = card.activation * wave_strength
                        self.cards[target_id].receive_activation(
                            spread_amount, card_id
                        )

        # Phase 3: Collect results
        results = [
            (card_id, card.activation)
            for card_id, card in self.cards.items()
            if card.activation > 0.1
        ]
        results.sort(key=lambda x: x[1], reverse=True)

        # Phase 4: Hebbian learning - strengthen used pathways
        recalled_ids = {r[0] for r in results[:top_k]}
        self._strengthen_pathways(recalled_ids)

        # Track query
        self.query_history.append((
            query,
            [r[0] for r in results[:top_k]],
            datetime.utcnow()
        ))

        return results[:top_k]

    def _strengthen_pathways(self, activated_ids: Set[int]):
        """Strengthen links between co-activated cards (Hebbian learning)."""
        activated_list = list(activated_ids)

        for i, id1 in enumerate(activated_list):
            for id2 in activated_list[i+1:]:
                # Strengthen bidirectional connections
                self.connect(id1, id2)
                self.connect(id2, id1)

                # Update recall stats
                if id1 in self.cards:
                    self.cards[id1].recall_count += 1
                    self.cards[id1].last_recalled = datetime.utcnow()
                if id2 in self.cards:
                    self.cards[id2].recall_count += 1
                    self.cards[id2].last_recalled = datetime.utcnow()

    def decay_all(self):
        """Apply decay to all links (call periodically)."""
        now = datetime.utcnow()
        for link in self.links.values():
            link.decay(now)

    def get_hubs(self, top_k: int = 10) -> List[Tuple[int, NeuralCard]]:
        """Get the most connected hub cards."""
        cards_by_connectivity = sorted(
            self.cards.items(),
            key=lambda x: (x[1].connectivity, x[1].recall_count),
            reverse=True
        )
        return cards_by_connectivity[:top_k]

    def get_strongest_paths(self, card_id: int, depth: int = 2) -> Dict:
        """Get strongest connection paths from a card."""
        if card_id not in self.cards:
            return {}

        paths = {"card_id": card_id, "connections": []}
        card = self.cards[card_id]

        # Get strongest outgoing links
        strong_links = sorted(
            card.outgoing.items(),
            key=lambda x: x[1].strength,
            reverse=True
        )[:5]

        for target_id, link in strong_links:
            target = self.cards.get(target_id)
            if target:
                conn = {
                    "target_id": target_id,
                    "title": target.buffers.get("title", "?")[:40],
                    "strength": link.strength,
                    "activations": link.activation_count,
                }

                # Recurse for deeper paths
                if depth > 1:
                    conn["paths"] = self.get_strongest_paths(target_id, depth-1)

                paths["connections"].append(conn)

        return paths

    def find_fundamental_branches(self) -> List[Dict]:
        """Find the most established pathways (language-like structures).

        These are the "highways" of memory - frequently traveled,
        strongly connected paths that form the backbone of recall.
        """
        # Find links that are both strong and frequently used
        fundamental = []

        for (src, tgt), link in self.links.items():
            if link.is_strong:
                src_card = self.cards.get(src)
                tgt_card = self.cards.get(tgt)

                if src_card and tgt_card:
                    fundamental.append({
                        "from": src_card.buffers.get("title", "?")[:30],
                        "to": tgt_card.buffers.get("title", "?")[:30],
                        "strength": link.strength,
                        "activations": link.activation_count,
                        "is_hub_connection": src_card.is_hub or tgt_card.is_hub,
                    })

        # Sort by combined strength and usage
        fundamental.sort(
            key=lambda x: x["strength"] * math.log1p(x["activations"]),
            reverse=True
        )

        return fundamental[:20]

    def consolidate(self):
        """Consolidate memories (like sleep does for brains).

        - Prune very weak connections
        - Strengthen hub connections
        - Create shortcuts between frequently co-recalled cards
        """
        # Prune weak, unused links
        to_remove = []
        for key, link in self.links.items():
            if link.strength < 0.05 and link.activation_count < 2:
                to_remove.append(key)

        for key in to_remove:
            src, tgt = key
            del self.links[key]
            if src in self.cards and tgt in self.cards[src].outgoing:
                del self.cards[src].outgoing[tgt]
            if tgt in self.cards and src in self.cards[tgt].incoming:
                del self.cards[tgt].incoming[src]

        # Analyze query history for patterns
        if len(self.query_history) > 10:
            # Find cards that are frequently co-recalled
            cooccurrence: Dict[Tuple[int, int], int] = defaultdict(int)

            for _, recalled_ids, _ in self.query_history[-100:]:
                for i, id1 in enumerate(recalled_ids):
                    for id2 in recalled_ids[i+1:]:
                        key = (min(id1, id2), max(id1, id2))
                        cooccurrence[key] += 1

            # Create/strengthen shortcuts for frequent pairs
            for (id1, id2), count in cooccurrence.items():
                if count >= 5:  # Threshold for "fundamental"
                    self.connect(id1, id2, initial_strength=0.3)
                    self.connect(id2, id1, initial_strength=0.3)

        return {
            "pruned_links": len(to_remove),
            "total_links": len(self.links),
            "total_cards": len(self.cards),
        }


# =============================================================================
# Example Usage
# =============================================================================

def demo():
    """Demonstrate neural memory dynamics."""
    mem = NeuralMemory()

    # Add some cards
    cards_data = [
        {"title": "OAuth Authentication", "type": "feature"},
        {"title": "Login Page", "type": "feature"},
        {"title": "Token Refresh", "type": "feature"},
        {"title": "Session Management", "type": "feature"},
        {"title": "User Profile", "type": "feature"},
        {"title": "API Security", "type": "feature"},
        {"title": "Database Schema", "type": "feature"},
        {"title": "Error Handling", "type": "bugfix"},
    ]

    for i, data in enumerate(cards_data):
        mem.add_card(i, data)

    # Simulate queries over time
    queries = [
        "OAuth authentication login",
        "OAuth token refresh",
        "authentication session",
        "OAuth authentication",  # Repeated
        "login authentication",
        "OAuth authentication",  # Repeated again
        "user profile session",
        "OAuth token",
        "authentication security",
        "OAuth authentication",  # Third time - should be strong now
    ]

    print("=== Simulating Queries ===")
    for q in queries:
        results = mem.recall(q, top_k=3)
        print(f"Query: '{q}'")
        for card_id, activation in results:
            title = mem.cards[card_id].buffers["title"]
            print(f"  {activation:.2f} | {title}")
        print()

    # Show what emerged
    print("=== Fundamental Branches (Highways) ===")
    for branch in mem.find_fundamental_branches()[:5]:
        print(f"  {branch['from']} → {branch['to']}")
        print(f"    strength={branch['strength']:.2f}, activations={branch['activations']}")

    print()
    print("=== Hub Cards ===")
    for card_id, card in mem.get_hubs(3):
        print(f"  [{card_id}] {card.buffers['title']}")
        print(f"    connections={card.connectivity}, recalls={card.recall_count}")

    print()
    print("=== Consolidation ===")
    result = mem.consolidate()
    print(f"  Pruned {result['pruned_links']} weak links")
    print(f"  Remaining: {result['total_links']} links, {result['total_cards']} cards")


if __name__ == "__main__":
    demo()
