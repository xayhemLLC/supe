"""
Mathematical Discovery: Information Theory - The Mathematics of Communication 📡

Information theory quantifies uncertainty, compression, and communication!

Core Concepts:
    • Entropy H(X): Average information content (bits)
    • Mutual Information I(X;Y): Shared information between variables
    • Channel Capacity: Maximum reliable transmission rate
    • Kolmogorov Complexity: Shortest program to generate data
    • Source Coding: Optimal compression (Huffman, Shannon)

Properties to Discover:
    • Shannon Entropy: H(X) = -Σ p(x) log₂ p(x)
    • Non-negativity: H(X) ≥ 0
    • Maximum entropy: H(X) ≤ log₂|X| (uniform distribution)
    • Conditioning reduces entropy: H(X|Y) ≤ H(X)
    • Data Processing Inequality: I(X;Y) ≥ I(X;Z) if X→Y→Z

Let's DISCOVER information theory through exploration! 💾
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_entropy_concept():
    return """
    Shannon Entropy: H(X) = -Σ p(x) log₂ p(x)

    "Average information content in bits"

    Example: Fair coin flip

         H        T
        ╱ ╲      ╱ ╲
       ╱   ╲    ╱   ╲
      p=0.5  p=0.5

    H(X) = -[0.5 log₂(0.5) + 0.5 log₂(0.5)]
         = -[0.5(-1) + 0.5(-1)]
         = -[-0.5 - 0.5]
         = 1 bit ✓

    Intuition: Need 1 bit to encode each outcome!

    Example: Biased coin (p=0.9 heads, p=0.1 tails)

         H              T
        ╱ ╲            ╱ ╲
       ╱   ╲          ╱   ╲
      p=0.9         p=0.1

    H(X) = -[0.9 log₂(0.9) + 0.1 log₂(0.1)]
         = -[0.9(-0.152) + 0.1(-3.322)]
         = -[-0.137 - 0.332]
         = 0.469 bits

    Less entropy! More predictable → less information!

    Extremes:
    • Deterministic (p=1): H = 0 bits (no surprise!)
    • Uniform: H = log₂n bits (maximum surprise!)
    """


def draw_mutual_information():
    return """
    Mutual Information: I(X;Y) = H(X) + H(Y) - H(X,Y)

    "How much information X and Y share"

           H(X)          H(Y)
         ┌─────┐      ┌─────┐
         │     │      │     │
         │  ┌──┼──────┼──┐  │
         │  │  │      │  │  │
         └──┼──┘      └──┼──┘
            │  I(X;Y)    │
            └────────────┘

    I(X;Y) = overlap between X and Y

    Properties:
    • I(X;Y) ≥ 0 (non-negative)
    • I(X;Y) = 0 ⟺ X and Y independent
    • I(X;Y) = H(X) ⟺ Y determines X
    • I(X;Y) = I(Y;X) (symmetric)

    Example: Weather and Ice Cream Sales

    X = {sunny, rainy}
    Y = {high_sales, low_sales}

    If weather affects sales:
    • I(X;Y) > 0 (shared information)
    • Knowing weather reduces uncertainty about sales

    If independent:
    • I(X;Y) = 0 (no shared information)
    • Weather tells nothing about sales
    """


def draw_channel_capacity():
    return """
    Channel Capacity: Maximum reliable transmission rate

    Binary Symmetric Channel (BSC):

    Input X        Channel        Output Y
      0 ──────────(1-p)─────────→ 0
      │                          ╱
      │          ╱             ╱
      └────────╱──(p)──────────→ 1
              ╱                │
            ╱                  │
      1 ──────────(1-p)─────────→ 1
      │                        ╱
      │        ╱             ╱
      └──────╱──(p)────────→ 0

    Bit flips with probability p (crossover probability)

    Capacity: C = 1 - H(p)
            = 1 - [-p log₂ p - (1-p) log₂(1-p)]

    Examples:
    • p = 0 (no errors): C = 1 bit per use ✓
    • p = 0.5 (random flips): C = 0 bits (useless!)
    • p = 0.1 (10% errors): C ≈ 0.53 bits

    Shannon's Channel Coding Theorem:
    • Can transmit at rate R < C with arbitrary reliability
    • Cannot transmit reliably at R > C
    """


def draw_huffman_coding():
    return """
    Huffman Coding: Optimal prefix-free compression

    Example: Encode {A, B, C, D} with probabilities

    Symbol | Probability | Huffman Code
    ───────┼─────────────┼─────────────
       A   |    0.5      |     0
       B   |    0.25     |    10
       C   |    0.15     |   110
       D   |    0.10     |   111

    Binary tree construction:

              Root
             ╱    ╲
            ╱      ╲
           0        1
          ╱        ╱ ╲
         A        ╱   ╲
                 0     1
                ╱     ╱ ╲
               B     ╱   ╲
                    0     1
                   ╱     ╱
                  C     D

    Average code length:
    L = 0.5(1) + 0.25(2) + 0.15(3) + 0.10(3)
      = 0.5 + 0.5 + 0.45 + 0.3
      = 1.75 bits per symbol

    Entropy:
    H = -[0.5 log₂ 0.5 + 0.25 log₂ 0.25 + 0.15 log₂ 0.15 + 0.10 log₂ 0.10]
      ≈ 1.68 bits

    Efficiency: L/H = 1.75/1.68 ≈ 104% (near optimal!)

    Key: Frequent symbols get shorter codes!
    """


def draw_source_coding_theorem():
    return """
    Shannon's Source Coding Theorem

    "Can compress to entropy, but no further"

    For source with entropy H(X):
    • Average code length L ≥ H(X) (lower bound)
    • Can achieve L < H(X) + ε for any ε > 0

    Visual:

    Compression Limit
         │
         │    ╱
         │   ╱ Possible region
         │  ╱  (L ≥ H)
         │ ╱
         │╱_____________
         H(X)      Code length L

    Cannot compress below entropy!

    Examples:
    • English text: H ≈ 1.5 bits/char
      (ASCII uses 8 bits → 5.3× compression possible!)

    • DNA sequence: H ≈ 2 bits/base
      (Already optimal with {A,C,G,T})

    • Random data: H = 8 bits/byte
      (Cannot compress!)

    Practical implications:
    • ZIP, gzip compress to ~H(X)
    • Already-compressed files cannot compress further
    • Encryption should produce H = 8 bits/byte (random)
    """


def draw_kolmogorov_complexity():
    return """
    Kolmogorov Complexity: K(x) = length of shortest program that outputs x

    "Algorithmic information content"

    Example strings (both length 32):

    String 1: "01010101010101010101010101010101"
    String 2: "10110010011101010111001010110101"

    String 1 program:
        for i in range(16):
            print("01")

    K(String 1) ≈ 20 bytes (compressible!)

    String 2 program:
        print("10110010011101010111001010110101")

    K(String 2) ≈ 32 bytes (incompressible!)

    Properties:
    • K(x) ≤ |x| + c (can always print x)
    • K(x) is incomputable (halting problem)
    • Random strings: K(x) ≈ |x|
    • Patterned strings: K(x) << |x|

    Connection to entropy:
    • H(X) ≈ E[K(X)] / length
    • Low entropy → compressible
    • High entropy → incompressible

    Philosophical: "What is randomness?"
    → String is random if K(x) ≈ |x|
    → Cannot be described more concisely
    """


def draw_data_processing_inequality():
    return """
    Data Processing Inequality

    "Processing cannot increase information"

    Markov chain: X → Y → Z

        X ──→ Y ──→ Z
     (Data) (Process) (Output)

    Theorem: I(X;Z) ≤ I(X;Y)

    "Z cannot contain more info about X than Y does"

    Visual:

        I(X;Y)         I(Y;Z)
      ┌────────┐     ┌────────┐
      │   ┌────┼─────┼────┐   │
      │   │ I(X;Z) │ │   │   │
      │   └────┼─────┼────┘   │
      └────────┘     └────────┘

    I(X;Z) ≤ min(I(X;Y), I(Y;Z))

    Example: Noisy communication

    Message X → Channel Y → Received Z

    • Original message X
    • Transmitted with noise → Y
    • Further noise → Z
    • I(X;Z) ≤ I(X;Y) (info loss!)

    Implications:
    • Cannot recover lost information
    • Each processing step loses info
    • Compression is irreversible
    • Cryptography relies on info loss

    "Information is destroyed, never created"
    """


def draw_entropy_properties():
    return """
    Entropy Properties

    1. Non-negativity: H(X) ≥ 0

       Proof: p(x) ∈ [0,1]
              log₂ p(x) ≤ 0
              -p(x) log₂ p(x) ≥ 0
              Sum of non-negative terms ≥ 0 ✓

    2. Maximum entropy (uniform distribution)

       H(X) ≤ log₂ |X|

       Achieved when p(x) = 1/|X| for all x

       Example: Fair die
       H = -Σ (1/6) log₂(1/6) = log₂ 6 ≈ 2.58 bits

    3. Conditioning reduces entropy

       H(X|Y) ≤ H(X)

       "Knowing Y cannot increase uncertainty about X"

       Example:
       X = suit of card (4 options)
       Y = color of card (2 options)

       H(X) = log₂ 4 = 2 bits
       H(X|Y) = log₂ 2 = 1 bit ✓

       Knowing color reduces uncertainty!

    4. Chain rule

       H(X,Y) = H(X) + H(Y|X)

       Joint entropy = marginal + conditional

    5. Additivity (independent)

       If X ⊥ Y: H(X,Y) = H(X) + H(Y)

       Independent → entropies add
    """


async def main():
    print("=" * 80)
    print("📡 MATHEMATICAL DISCOVERY: Information Theory - Mathematics of Communication")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover information theory fundamentals!")
    print("From entropy to compression to communication!")
    print()

    # Use in-memory database
    supe = Supe(db_path=":memory:")

    # Seed information theory knowledge
    print("📚 Seeding information theory definitions...")

    info_defs = """Information Theory: The Mathematics of Communication

Core Definitions:

    Shannon Entropy:
        H(X) = -Σ p(x) log₂ p(x)

        Interpretation: Average information content in bits
        Properties:
            • H(X) ≥ 0 (non-negative)
            • H(X) ≤ log₂|X| (maximum for uniform distribution)
            • H(X) = 0 ⟺ X is deterministic

    Mutual Information:
        I(X;Y) = H(X) + H(Y) - H(X,Y)
              = Σ p(x,y) log₂[p(x,y)/(p(x)p(y))]

        Interpretation: Information shared between X and Y
        Properties:
            • I(X;Y) ≥ 0
            • I(X;Y) = 0 ⟺ X ⊥ Y (independent)
            • I(X;Y) = I(Y;X) (symmetric)

    Conditional Entropy:
        H(X|Y) = H(X,Y) - H(Y)

        Interpretation: Uncertainty about X given Y
        Property: H(X|Y) ≤ H(X) (conditioning reduces entropy)

    Channel Capacity:
        C = max I(X;Y)

        For Binary Symmetric Channel with error probability p:
        C = 1 - H(p) = 1 - [-p log₂ p - (1-p) log₂(1-p)]

Fundamental Theorems:

    Source Coding Theorem (Shannon):
        Can compress data to entropy: L ≥ H(X)
        Cannot compress below entropy!

        Optimal codes (Huffman) achieve L < H(X) + 1

    Channel Coding Theorem (Shannon):
        Can transmit reliably at rate R < C
        Cannot transmit reliably at R > C

        Error-correcting codes achieve capacity!

    Data Processing Inequality:
        For Markov chain X → Y → Z:
        I(X;Z) ≤ I(X;Y)

        Processing cannot increase information!

Applications:
    • Data compression (ZIP, JPEG, MP3)
    • Error correction (CD, DVD, satellite communication)
    • Cryptography (entropy = security)
    • Machine learning (KL divergence, cross-entropy)
    • Neuroscience (neural coding, information processing)
    • Thermodynamics (connection to physical entropy)

Key Insights:
    • Information is quantifiable (bits)
    • Compression has fundamental limits (entropy)
    • Communication has fundamental limits (capacity)
    • Information processing is irreversible (data processing inequality)
    • Randomness = incompressibility (Kolmogorov complexity)"""

    supe.memory.store_card(
        label="information_theory_fundamentals",
        buffers=[Buffer(name="content", payload=info_defs.encode('utf-8'))],
        master_output="Information theory: entropy, compression, communication",
        track="awareness",
    )
    print("✓ Information theory concepts defined\n")

    # Discovery 1: Non-negativity of Entropy
    print("🔍 DISCOVERY 1: Non-negativity of Entropy")
    print("-" * 80)
    print(draw_entropy_properties())

    result1 = await supe.learn(
        "Is H(X) ≥ 0? (Entropy is non-negative)",
        mode="explore"
    )

    print(f"Question: Is H(X) ≥ 0?")
    print()
    print("Example: Fair coin")
    print("  H(X) = -[0.5 log₂ 0.5 + 0.5 log₂ 0.5]")
    print("       = -[0.5(-1) + 0.5(-1)] = 1 ≥ 0 ✓")
    print()

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Maximum Entropy
    print("🔍 DISCOVERY 2: Maximum Entropy (Uniform Distribution)")
    print("-" * 80)
    print(draw_entropy_concept())

    result2 = await supe.learn(
        "Is H(X) ≤ log₂|X|? (Maximum entropy for uniform distribution)",
        mode="explore"
    )

    print(f"Question: Is H(X) ≤ log₂|X|?")
    print()
    print("Example: Fair 6-sided die")
    print("  H(X) = log₂ 6 ≈ 2.58 bits")
    print("  Max: log₂|X| = log₂ 6 ≈ 2.58 bits")
    print("  Check: 2.58 ≤ 2.58 ✓")
    print()

    if result2['beliefs_count'] > 0:
        belief = result2['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Conditioning Reduces Entropy
    print("🔍 DISCOVERY 3: Conditioning Reduces Entropy")
    print("-" * 80)
    print("""
    Theorem: H(X|Y) ≤ H(X)

    "Knowing Y cannot increase uncertainty about X"

    Proof sketch:
    I(X;Y) = H(X) - H(X|Y) ≥ 0
    Therefore: H(X|Y) ≤ H(X) ✓

    Example: Card suit given color
    • H(Suit) = log₂ 4 = 2 bits
    • H(Suit|Color) = log₂ 2 = 1 bit
    • 1 ≤ 2 ✓
    """)

    result3 = await supe.learn(
        "Is H(X|Y) ≤ H(X)? (Conditioning reduces entropy)",
        mode="explore"
    )

    print(f"Question: Is H(X|Y) ≤ H(X)?")
    print()
    print("Example: Knowing card color reduces suit uncertainty")
    print("  H(Suit) = 2 bits")
    print("  H(Suit|Color) = 1 bit")
    print("  Check: 1 ≤ 2 ✓")
    print()

    if result3['beliefs_count'] > 0:
        belief = result3['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Data Processing Inequality
    print("🔍 DISCOVERY 4: Data Processing Inequality")
    print("-" * 80)
    print(draw_data_processing_inequality())

    result4 = await supe.learn(
        "For X → Y → Z, is I(X;Z) ≤ I(X;Y)? (Data processing inequality)",
        mode="explore"
    )

    print(f"Question: For Markov chain X → Y → Z, is I(X;Z) ≤ I(X;Y)?")
    print()
    print("Meaning: Processing cannot increase information")
    print("  Each step loses information")
    print("  Cannot recover what's lost ✓")
    print()

    if result4['beliefs_count'] > 0:
        belief = result4['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Source Coding Theorem
    print("🔍 DISCOVERY 5: Source Coding Theorem")
    print("-" * 80)
    print(draw_source_coding_theorem())

    result5 = await supe.learn(
        "Is L ≥ H(X) for any code? (Source coding theorem - cannot compress below entropy)",
        mode="explore"
    )

    print(f"Question: Is average code length L ≥ H(X)?")
    print()
    print("Meaning: Cannot compress below entropy")
    print("  Huffman coding achieves L < H(X) + 1")
    print("  Entropy is the compression limit ✓")
    print()

    if result5['beliefs_count'] > 0:
        belief = result5['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Visualizations
    print("=" * 80)
    print("🎨 INFORMATION THEORY VISUALIZATIONS")
    print("=" * 80)
    print()

    print("📊 Mutual Information:")
    print(draw_mutual_information())
    print()

    print("📡 Channel Capacity:")
    print(draw_channel_capacity())
    print()

    print("🗜️  Huffman Coding:")
    print(draw_huffman_coding())
    print()

    print("🔢 Kolmogorov Complexity:")
    print(draw_kolmogorov_complexity())
    print()

    # Summary
    print("=" * 80)
    print("🎓 INFORMATION THEORY DISCOVERIES")
    print("=" * 80)
    print()

    total_beliefs = sum(r['beliefs_count'] for r in [result1, result2, result3, result4, result5])

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                  INFORMATION THEORY FUNDAMENTALS                     ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Shannon Entropy:                                                    ║")
    print("║    H(X) = -Σ p(x) log₂ p(x)                                         ║")
    print("║    • H(X) ≥ 0 (non-negative)                                        ║")
    print("║    • H(X) ≤ log₂|X| (max for uniform)                               ║")
    print("║                                                                      ║")
    print("║  Conditional Entropy:                                                ║")
    print("║    H(X|Y) ≤ H(X)                                                    ║")
    print("║    (Conditioning reduces entropy)                                    ║")
    print("║                                                                      ║")
    print("║  Data Processing Inequality:                                         ║")
    print("║    X → Y → Z: I(X;Z) ≤ I(X;Y)                                       ║")
    print("║    (Processing loses information)                                    ║")
    print("║                                                                      ║")
    print("║  Source Coding Theorem:                                              ║")
    print("║    L ≥ H(X)                                                         ║")
    print("║    (Cannot compress below entropy)                                   ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print(f"🌟 What We Learned:")
    print(f"   • Total beliefs formed: {total_beliefs}")
    print(f"   • Each discovery stored with proof hash")
    print(f"   • Linked to Tasc execution for traceability")
    print()

    print("🔗 Connections:")
    print("   Information Theory ──→ Computer Science (compression, encoding)")
    print("                      ──→ Communications (error correction, capacity)")
    print("                      ──→ Machine Learning (cross-entropy, KL divergence)")
    print("                      ──→ Cryptography (entropy = security)")
    print("                      ──→ Physics (thermodynamic entropy)")
    print("                      ──→ Neuroscience (neural coding)")
    print()

    print("💡 Next Information Theory Horizons:")
    print("   • Rate-distortion theory (lossy compression)")
    print("   • Channel coding (error-correcting codes)")
    print("   • Network information theory (multiple users)")
    print("   • Quantum information theory")
    print("   • Algorithmic information theory (Kolmogorov)")
    print()

    print("🎭 Philosophy:")
    print("   Information is physical!")
    print("   Entropy quantifies surprise and uncertainty.")
    print("   Communication has fundamental limits.")
    print("   Cannot create information from noise.")
    print("   Compression reveals structure vs randomness.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
