"""
Mathematical Discovery: Probability Theory - The Mathematics of Uncertainty 🎲

Probability quantifies uncertainty and connects set theory to real-world randomness!

Core Concepts:
    • Sample space Ω: Set of all possible outcomes
    • Event: Subset of sample space (A ⊆ Ω)
    • Probability P(A): Number between 0 and 1
    • P(Ω) = 1 (something must happen)
    • P(∅) = 0 (impossible event)

Axioms (Kolmogorov):
    1. 0 ≤ P(A) ≤ 1 for all events A
    2. P(Ω) = 1
    3. P(A ∪ B) = P(A) + P(B) if A ∩ B = ∅ (disjoint)

Key Formulas:
    • Complement: P(A') = 1 - P(A)
    • Inclusion-Exclusion: P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
    • Conditional: P(A|B) = P(A ∩ B) / P(B)
    • Independence: P(A ∩ B) = P(A) × P(B)
    • Bayes' Theorem: P(A|B) = P(B|A) × P(A) / P(B)

Applications:
    • Statistics and data science
    • Machine learning (Bayesian inference)
    • Risk assessment and insurance
    • Quantum mechanics (probability amplitudes)
    • Game theory and decision making

Let's LEARN probability through exploration! 🎲✨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_sample_space():
    """Visualize sample space for coin flip."""
    return """
    Sample Space for Coin Flip: Ω = {H, T}

         Ω
      ┌──────┐
      │  H   │  ← Heads
      │      │
      │  T   │  ← Tails
      └──────┘

    Events:
    • A = {H}: Get heads
    • B = {T}: Get tails
    • Ω = {H, T}: Get something
    • ∅: Impossible

    Probabilities:
    P(H) = 1/2
    P(T) = 1/2
    P(Ω) = 1
    P(∅) = 0
    """


def draw_dice_sample_space():
    """Visualize sample space for die roll."""
    return """
    Sample Space for Die Roll: Ω = {1, 2, 3, 4, 5, 6}

         ┌───┬───┬───┬───┬───┬───┐
      Ω  │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │
         └───┴───┴───┴───┴───┴───┘

    Events:
    • A = {2, 4, 6}: Even number
    • B = {1, 3, 5}: Odd number
    • C = {5, 6}: Greater than 4
    • D = {1}: Roll a one

    Probabilities (fair die):
    P(A) = 3/6 = 1/2
    P(B) = 3/6 = 1/2
    P(C) = 2/6 = 1/3
    P(D) = 1/6
    """


def draw_venn_probability():
    """Venn diagram for probability."""
    return """
    Probability Venn Diagram: P(A ∪ B)

           A         B
         •••••     •••••
        •• 1 ••   •• 2 ••
       ••  4  •••••  5  ••
       •       ███       •
       •       ███       •
       ••     •••••     ••
        ••   ••   ••   ••
         •••••     •••••

    Regions (probabilities):
    1. A only: P(A \ B) = 0.2
    2. B only: P(B \ A) = 0.3
    3. Both: P(A ∩ B) = 0.1
    4. Neither: P((A ∪ B)') = 0.4

    Inclusion-Exclusion:
    P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
             = 0.3 + 0.4 - 0.1
             = 0.6
    """


def draw_conditional_probability():
    """Visualize conditional probability."""
    return """
    Conditional Probability: P(A|B)

    "Probability of A given B has occurred"

    Original space:          Restricted to B:
         Ω                        B
      ┌──────┐                ┌─────┐
      │  B   │                │ A∩B │
      │┌────┐│                │ ▓▓▓ │
      ││A∩B ││  ────────→     │ ▓▓▓ │
      ││ ▓▓ ││                └─────┘
      │└────┘│
      └──────┘

    Formula: P(A|B) = P(A ∩ B) / P(B)

    Example:
    • P(roll 6 | even number)
    • P(A ∩ B) = P({6}) = 1/6
    • P(B) = P({2,4,6}) = 1/2
    • P(A|B) = (1/6) / (1/2) = 1/3
    """


def draw_independence():
    """Visualize independent events."""
    return """
    Independent Events: P(A ∩ B) = P(A) × P(B)

    Two coin flips (independent):

    First flip:    H     T
                 ─┴─   ─┴─

    Second flip:
         H      HH    TH
         T      HT    TT

    P(HH) = P(H on 1st) × P(H on 2nd)
          = 1/2 × 1/2
          = 1/4

    All outcomes:
    • P(HH) = 1/4
    • P(HT) = 1/4
    • P(TH) = 1/4
    • P(TT) = 1/4

    Events don't influence each other!
    """


def draw_bayes_theorem():
    """Visualize Bayes' theorem."""
    return """
    Bayes' Theorem: P(A|B) = P(B|A) × P(A) / P(B)

    "Reverse" conditional probabilities!

    Example: Medical test
    • Disease (D): 1% of population
    • Test positive (T+): 99% if have disease
    • False positive: 5% if healthy

    Question: P(D | T+)?

           D               H
         1%               99%
        ┌──┐           ┌────────┐
        │99│ T+        │  5%    │ T+
        │  │           │        │
        └──┘           └────────┘

    P(D | T+) = P(T+ | D) × P(D) / P(T+)
              = 0.99 × 0.01 / P(T+)

    P(T+) = P(T+ | D) × P(D) + P(T+ | H) × P(H)
          = 0.99 × 0.01 + 0.05 × 0.99
          = 0.0099 + 0.0495 = 0.0594

    P(D | T+) = 0.0099 / 0.0594 ≈ 0.17 (17%!)

    Surprising: Positive test → only 17% chance of disease!
    """


def draw_law_total_probability():
    """Visualize law of total probability."""
    return """
    Law of Total Probability

    Partition sample space: B₁, B₂, ..., Bₙ
    (disjoint and cover Ω)

         Ω
      ┌─────────┐
      │  B₁  B₂ │
      │ ┌──┬──┐ │
      │ │A │A │ │
      │ └──┴──┘ │
      │  B₃     │
      │ ┌────┐  │
      │ │ A  │  │
      │ └────┘  │
      └─────────┘

    P(A) = Σᵢ P(A ∩ Bᵢ)
         = Σᵢ P(A | Bᵢ) × P(Bᵢ)

    Example: Manufacturing from 3 factories
    • Factory 1: 50% of products, 1% defective
    • Factory 2: 30% of products, 2% defective
    • Factory 3: 20% of products, 3% defective

    P(defective) = 0.01×0.5 + 0.02×0.3 + 0.03×0.2
                 = 0.005 + 0.006 + 0.006
                 = 0.017 (1.7%)
    """


async def main():
    print("=" * 80)
    print("🎲 MATHEMATICAL DISCOVERY: Probability Theory - Mathematics of Uncertainty")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover probability properties!")
    print("From set theory to chance: events, independence, and Bayes!")
    print()

    supe = Supe(db_path=":memory:")

    # Seed probability knowledge
    print("📚 Seeding probability definitions...")

    prob_def = """Probability Theory: Mathematics of Uncertainty

Sample Space (Ω): Set of all possible outcomes
Event: Subset A ⊆ Ω
Probability Function P: Maps events to [0,1]

Kolmogorov Axioms:
1. 0 ≤ P(A) ≤ 1 for all events A
2. P(Ω) = 1 (certainty)
3. P(A ∪ B) = P(A) + P(B) if A ∩ B = ∅ (additivity)

Basic Properties:
- Complement: P(A') = 1 - P(A)
- Inclusion-Exclusion: P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
- Monotonicity: If A ⊆ B then P(A) ≤ P(B)

Conditional Probability:
P(A|B) = P(A ∩ B) / P(B)  when P(B) > 0
"Probability of A given B occurred"

Independence:
Events A and B are independent if:
P(A ∩ B) = P(A) × P(B)
Equivalently: P(A|B) = P(A)

Bayes' Theorem:
P(A|B) = P(B|A) × P(A) / P(B)
Allows "reversing" conditional probabilities

Law of Total Probability:
If B₁, ..., Bₙ partition Ω:
P(A) = Σᵢ P(A|Bᵢ) × P(Bᵢ)"""

    supe.memory.store_card(
        label="probability_definitions",
        buffers=[Buffer(name="content", payload=prob_def.encode('utf-8'))],
        master_output="Probability theory definitions and axioms",
        track="awareness",
    )
    print("✓ Probability concepts defined\n")

    # Discovery 1: Complement rule
    print("🔍 DISCOVERY 1: Complement Rule")
    print("-" * 80)
    print(draw_sample_space())
    print("Question: Is P(A) + P(A') = 1?")
    print()
    print("Example: Coin flip")
    print("  P(Heads) = 1/2")
    print("  P(Tails) = P(Heads') = 1/2")
    print("  P(H) + P(T) = 1/2 + 1/2 = 1 ✓")
    print()

    result1 = await supe.learn(
        "Is P(A) + P(A') = 1? (Complement rule: probabilities sum to 1)",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Complement rule VERIFIED!")
            print("⟹ P(A) + P(A') = 1 always holds!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Inclusion-exclusion for probability
    print("🔍 DISCOVERY 2: Inclusion-Exclusion Principle")
    print("-" * 80)
    print(draw_venn_probability())
    print("Question: Is P(A ∪ B) = P(A) + P(B) - P(A ∩ B)?")
    print()
    print("Example: P(A) = 0.3, P(B) = 0.4, P(A ∩ B) = 0.1")
    print("  P(A ∪ B) = 0.3 + 0.4 - 0.1 = 0.6 ✓")
    print()

    result2 = await supe.learn(
        "Is P(A∪B) = P(A) + P(B) - P(A∩B)? (Test: 0.3 + 0.4 - 0.1 = 0.6)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Inclusion-exclusion VERIFIED!")
            print("⟹ Subtract overlap to avoid double-counting!")
            print("⟹ Mirrors set theory formula!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Independence
    print("🔍 DISCOVERY 3: Independence Property")
    print("-" * 80)
    print(draw_independence())
    print("Question: For independent events, is P(A ∩ B) = P(A) × P(B)?")
    print()
    print("Example: Two coin flips")
    print("  P(H on 1st) = 1/2")
    print("  P(H on 2nd) = 1/2")
    print("  P(HH) = 1/2 × 1/2 = 1/4 ✓")
    print()

    result3 = await supe.learn(
        "For independent coin flips, is P(HH) = 1/2 × 1/2 = 1/4? (Independence)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Independence VERIFIED!")
            print("⟹ P(A ∩ B) = P(A) × P(B) for independent events!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Conditional probability
    print("🔍 DISCOVERY 4: Conditional Probability Formula")
    print("-" * 80)
    print(draw_conditional_probability())
    print("Question: Is P(A|B) = P(A ∩ B) / P(B)?")
    print()
    print("Example: P(roll 6 | even)")
    print("  P(A ∩ B) = P({6}) = 1/6")
    print("  P(B) = P({2,4,6}) = 1/2")
    print("  P(A|B) = (1/6) / (1/2) = 1/3 ✓")
    print()

    result4 = await supe.learn(
        "Is P(6|even) = (1/6)/(1/2) = 1/3? (Conditional probability formula)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Conditional probability VERIFIED!")
            print("⟹ P(A|B) = P(A ∩ B) / P(B)")
            print("⟹ Foundation for Bayes' theorem!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Probability sum for disjoint events
    print("🔍 DISCOVERY 5: Additivity for Disjoint Events")
    print("-" * 80)
    print(draw_dice_sample_space())
    print("Question: For disjoint A and B, is P(A ∪ B) = P(A) + P(B)?")
    print()
    print("Example: Even (E) and Odd (O) on die")
    print("  P(E) = P({2,4,6}) = 3/6")
    print("  P(O) = P({1,3,5}) = 3/6")
    print("  P(E ∪ O) = P(Ω) = 1")
    print("  P(E) + P(O) = 3/6 + 3/6 = 1 ✓")
    print()

    result5 = await supe.learn(
        "For disjoint events, is P(E∪O) = P(E) + P(O) = 1? (Additivity axiom)",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Additivity axiom VERIFIED!")
            print("⟹ Core Kolmogorov axiom!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Display visualizations
    print("=" * 80)
    print("🎨 PROBABILITY VISUALIZATIONS")
    print("=" * 80)
    print()
    print("🪙 Sample Space (Coin):")
    print(draw_sample_space())
    print()
    print("🎲 Sample Space (Die):")
    print(draw_dice_sample_space())
    print()
    print("⊕ Venn Diagram (Probability):")
    print(draw_venn_probability())
    print()
    print("│ Conditional Probability:")
    print(draw_conditional_probability())
    print()
    print("⊥ Independence:")
    print(draw_independence())
    print()
    print("⟲ Bayes' Theorem:")
    print(draw_bayes_theorem())
    print()
    print("Σ Law of Total Probability:")
    print(draw_law_total_probability())
    print()

    # Summary
    print("=" * 80)
    print("🎓 PROBABILITY THEORY DISCOVERIES")
    print("=" * 80)
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    PROBABILITY FUNDAMENTALS                          ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Axioms (Kolmogorov):                                                ║")
    print("║    • 0 ≤ P(A) ≤ 1                                                    ║")
    print("║    • P(Ω) = 1                                                        ║")
    print("║    • P(A ∪ B) = P(A) + P(B) if A ∩ B = ∅                            ║")
    print("║                                                                      ║")
    print("║  Key Formulas:                                                       ║")
    print("║    • Complement: P(A') = 1 - P(A)                                   ║")
    print("║    • Inclusion-Exclusion: P(A ∪ B) = P(A) + P(B) - P(A ∩ B)         ║")
    print("║    • Conditional: P(A|B) = P(A ∩ B) / P(B)                          ║")
    print("║    • Independence: P(A ∩ B) = P(A) × P(B)                           ║")
    print("║    • Bayes': P(A|B) = P(B|A) × P(A) / P(B)                          ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🌟 What We Learned:")
    print(f"   • Total beliefs formed: {sum(1 for r in [result1, result2, result3, result4, result5] if r['beliefs_count'] > 0)}")
    print("   • Each discovery stored with proof hash")
    print("   • Linked to Tasc execution for traceability")
    print()
    print("🔗 Connections:")
    print("   Probability ──→ Set Theory (events as sets)")
    print("               ──→ Statistics (inference, estimation)")
    print("               ──→ Machine Learning (Bayesian methods)")
    print("               ──→ Physics (statistical mechanics, quantum)")
    print("               ──→ Economics (risk, decision theory)")
    print()
    print("💡 Next Probability Horizons:")
    print("   • Random variables and distributions")
    print("   • Expected value and variance")
    print("   • Law of large numbers")
    print("   • Central limit theorem")
    print("   • Markov chains")
    print("   • Stochastic processes")
    print()
    print("🎭 Philosophy:")
    print("   Probability bridges the deterministic and random!")
    print("   Set theory + measure theory = rigorous probability.")
    print("   Bayes' theorem: update beliefs with evidence.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
