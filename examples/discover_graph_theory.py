"""
Mathematical Discovery: Graph Theory - The Mathematics of Networks 🕸️

Graph theory studies networks of vertices (nodes) connected by edges!

Core Concepts:
    • Graph G = (V, E): Set of vertices and edges
    • Degree: Number of edges connected to a vertex
    • Path: Sequence of edges connecting vertices
    • Cycle: Path that starts and ends at same vertex
    • Connected: Path exists between any two vertices

Properties to Discover:
    • Handshaking Lemma: Σ deg(v) = 2|E|
    • Euler's Formula: V - E + F = 2 (planar graphs)
    • Complete graph: K_n has n(n-1)/2 edges
    • Tree property: Connected graph with n vertices has n-1 edges
    • Bipartite: Can color vertices with 2 colors (no adjacent same color)

Let's DISCOVER graph theory through exploration! 🎨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_basic_graph():
    return """
    Basic Graph: G = (V, E)

    Vertices (V): {A, B, C, D}
    Edges (E): {AB, AC, BD, CD}

           A ───── B
           │       │
           │       │
           C ───── D

    Degree of each vertex:
    • deg(A) = 2 (connected to B, C)
    • deg(B) = 2 (connected to A, D)
    • deg(C) = 2 (connected to A, D)
    • deg(D) = 2 (connected to B, C)

    Sum of degrees: 2+2+2+2 = 8
    Number of edges: 4
    Notice: Σ deg(v) = 2|E| ✓ (Handshaking Lemma!)
    """


def draw_handshaking_lemma():
    return """
    Handshaking Lemma: Σ deg(v) = 2|E|

    "The sum of all degrees equals twice the number of edges"

    Why? Each edge contributes 2 to the degree sum:

        A ──── B    Edge AB contributes:
                    • +1 to deg(A)
                    • +1 to deg(B)
                    Total: +2

    Example graph:

           1
          ╱ ╲
         ╱   ╲
        2─────3
         ╲   ╱
          ╲ ╱
           4

    Degrees: deg(1)=2, deg(2)=3, deg(3)=3, deg(4)=2
    Sum: 2+3+3+2 = 10
    Edges: |E| = 5
    Check: 10 = 2×5 ✓

    Corollary: Number of odd-degree vertices is EVEN!
    (Because sum is even, parity must balance)
    """


def draw_complete_graph():
    return """
    Complete Graph K_n: Every vertex connected to every other

    K₃ (triangle):        K₄ (tetrahedron):

           1                    1
          ╱ ╲                  ╱│╲
         ╱   ╲                ╱ │ ╲
        2─────3              2──┼──3
                              ╲ │ ╱
    Edges: 3                   ╲│╱
                                4

                             Edges: 6

    Formula: K_n has n(n-1)/2 edges

    Why? Each vertex connects to (n-1) others.
         Total connections: n(n-1)
         But each edge counted twice: n(n-1)/2

    Examples:
    • K₃: 3(2)/2 = 3 edges ✓
    • K₄: 4(3)/2 = 6 edges ✓
    • K₅: 5(4)/2 = 10 edges
    • K₁₀: 10(9)/2 = 45 edges

    Maximum edges in simple graph!
    """


def draw_tree():
    return """
    Tree: Connected graph with NO cycles

    Example tree with 5 vertices:

              1
             ╱ ╲
            ╱   ╲
           2     3
          ╱ ╲
         4   5

    Properties:
    • Connected: Path exists between any two vertices
    • Acyclic: No cycles
    • |V| = 5 vertices
    • |E| = 4 edges
    • Notice: |E| = |V| - 1 ✓

    Theorem: A tree with n vertices has exactly n-1 edges.

    Proof idea:
    1. Start with n isolated vertices (0 edges)
    2. To connect them, need at least n-1 edges
    3. If we add more, we create a cycle
    4. Therefore: tree has exactly n-1 edges ✓

    Binary tree (each node ≤2 children):

              1
             ╱ ╲
            2   3
           ╱ ╲
          4   5

    Used in: Data structures, parsing, decision trees
    """


def draw_eulers_formula():
    return """
    Euler's Formula for Planar Graphs: V - E + F = 2

    "Vertices minus Edges plus Faces equals 2"

    Example: Cube graph

         A ────── B
        ╱│      ╱│
       ╱ │     ╱ │
      D ─┼──── C │
      │  E ────│─ F
      │ ╱      │╱
      │╱       │
      H ────── G

    Count:
    • Vertices (V): 8 (corners A-H)
    • Edges (E): 12 (sides of cube)
    • Faces (F): 6 (squares) + 1 (outer face) = 7???

    Wait, correct counting:
    • Faces (F): 6 faces of cube
    • But F includes the "outside" face!
    • Total: 6 interior faces

    Actually for cube:
    V = 8, E = 12, F = 6
    Check: 8 - 12 + 6 = 2 ✓

    Simpler example - Square:

        A ──── B
        │      │
        │      │
        D ──── C

    V = 4, E = 4, F = 2 (inside + outside)
    Check: 4 - 4 + 2 = 2 ✓

    Triangle:
        1
       ╱ ╲
      2───3

    V = 3, E = 3, F = 2 (inside + outside)
    Check: 3 - 3 + 2 = 2 ✓
    """


def draw_bipartite_graph():
    return """
    Bipartite Graph: Vertices can be split into two sets
                     with NO edges within each set

    Example: K₂,₃ (complete bipartite)

    Set A: {1, 2}        Set B: {a, b, c}

           1 ─────────── a
           │ ╲       ╱   │
           │  ╲     ╱    │
           │   ╲   ╱     │
           │    ╲ ╱      │
           │     ╳       │
           │    ╱ ╲      │
           │   ╱   ╲     │
           │  ╱     ╲    │
           │ ╱       ╲   │
           2 ─────────── b
            ╲           ╱
             ╲         ╱
              ╲       ╱
               ╲     ╱
                ╲   ╱
                 ╲ ╱
                  c

    Every edge connects A to B (never within A or within B)

    2-Colorable Test: Can we color vertices with 2 colors
                      so no edge connects same colors?

           1 (red) ─── a (blue)
           │           │
           │           │
           2 (red) ─── b (blue)

    YES! → Bipartite ✓

    Non-bipartite example - Triangle:

           1
          ╱ ╲
         ╱   ╲
        2─────3

    Try 2-coloring:
    • Color 1 red
    • Color 2 blue (edge 1-2)
    • Color 3 red (edge 2-3)
    • But edge 1-3 connects two reds! ✗

    Theorem: A graph is bipartite ⟺ it has no odd cycles!
    """


def draw_graph_coloring():
    return """
    Graph Coloring: Assign colors to vertices so
                    adjacent vertices have different colors

    Example: Map coloring

           A
          ╱│╲
         ╱ │ ╲
        B──┼──C
         ╲ │ ╱
          ╲│╱
           D

    Chromatic number χ(G): Minimum colors needed

    Try 3 colors {red, blue, green}:
    • A: red
    • B: blue (adj to A)
    • C: green (adj to A, B)
    • D: blue (adj to A, C; can reuse blue!)

    χ(G) = 3 ✓

    Special cases:
    • Path: χ = 2 (alternate colors)
    • Cycle (even): χ = 2
    • Cycle (odd): χ = 3
    • Complete K_n: χ = n (all different!)
    • Tree: χ = 2 (bipartite)

    Four Color Theorem: Any planar graph can be colored
                        with at most 4 colors!

    (Proven in 1976 with computer assistance)

    Applications:
    • Map coloring
    • Register allocation (compilers)
    • Scheduling (no conflicts)
    • Frequency assignment (wireless networks)
    """


def draw_eulerian_path():
    return """
    Eulerian Path: Path that uses every EDGE exactly once

    Example: Königsberg bridges problem

    Can you walk through all 7 bridges exactly once?

        Land A
          │
       Bridge 1
          │
    ──Bridge 2── Island ──Bridge 3──
          │         │
       Bridge 4  Bridge 5
          │         │
        Land C   Bridge 6
                    │
                 Bridge 7
                    │
                 Land D

    Graph representation:

           A
          ╱│╲
         ╱ │ ╲
        B──┼──C
         ╲ │ ╱
          ╲│╱
           D

    Degree count:
    • deg(A) = 5 (bridges to B: 2, C: 2, D: 1)

    Actual Königsberg:
    • deg(A) = 3 (odd)
    • deg(B) = 5 (odd)
    • deg(C) = 3 (odd)
    • deg(D) = 3 (odd)

    Four odd-degree vertices!

    Theorem: Eulerian path exists ⟺
             Graph has 0 or 2 odd-degree vertices

    Königsberg: 4 odd vertices → NO Eulerian path! ✗

    Valid example:

        A ──── B
        │      │
        │      │
        C ──── D
         ╲    ╱
          ╲  ╱
           E

    Degrees: A(2), B(2), C(3), D(3), E(2)
    Two odd vertices (C, D) → Eulerian path EXISTS! ✓
    Path: C → A → B → D → E → C (start/end at odd vertices)
    """


async def main():
    print("=" * 80)
    print("🕸️  MATHEMATICAL DISCOVERY: Graph Theory - Mathematics of Networks")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover graph theory fundamentals!")
    print("From handshaking lemma to Euler's formula!")
    print()

    # Use in-memory database
    supe = Supe(db_path=":memory:")

    # Seed graph theory knowledge
    print("📚 Seeding graph theory definitions...")

    graph_defs = """Graph Theory: The Mathematics of Networks

Definitions:
    Graph G = (V, E):
        • V: Set of vertices (nodes)
        • E: Set of edges (connections)
        • Example: V = {1,2,3}, E = {12, 23, 13}

    Types:
        • Simple graph: No loops, no multiple edges
        • Directed graph: Edges have direction (arrows)
        • Weighted graph: Edges have values
        • Complete graph K_n: Every pair of vertices connected
        • Bipartite: Vertices split into two sets, edges only between sets
        • Tree: Connected acyclic graph

    Properties:
        • Degree deg(v): Number of edges incident to v
        • Path: Sequence of vertices connected by edges
        • Cycle: Path that starts and ends at same vertex
        • Connected: Path exists between any two vertices
        • Planar: Can be drawn without edge crossings

Fundamental Theorems:

    Handshaking Lemma:
        Σ deg(v) = 2|E|
        "Sum of all degrees equals twice the number of edges"
        Corollary: Number of odd-degree vertices is even

    Tree Characterization:
        For connected graph: Tree ⟺ |E| = |V| - 1
        "Tree with n vertices has exactly n-1 edges"

    Euler's Formula (planar graphs):
        V - E + F = 2
        "Vertices minus Edges plus Faces equals 2"

    Complete Graph:
        K_n has n(n-1)/2 edges
        "Each vertex connects to n-1 others, divide by 2"

    Bipartite Characterization:
        G is bipartite ⟺ G has no odd cycles
        "Can 2-color ⟺ no triangles, pentagons, etc."

    Eulerian Path:
        Eulerian path exists ⟺ 0 or 2 odd-degree vertices
        "Can traverse all edges once ⟺ at most 2 odd vertices"

    Four Color Theorem:
        Any planar graph can be colored with ≤ 4 colors
        (Proven 1976, computer-assisted proof)

Applications:
    • Social networks (friendships, followers)
    • Transportation (roads, flights, routes)
    • Internet (routers, connections)
    • Biology (protein interactions, neural networks)
    • Scheduling (dependencies, conflicts)
    • Compilers (register allocation, dataflow)
    • Chemistry (molecular structure)

Classic Problems:
    • Königsberg bridges (Eulerian path)
    • Traveling salesman (Hamiltonian cycle)
    • Graph coloring (chromatic number)
    • Shortest path (Dijkstra, Bellman-Ford)
    • Maximum flow (Ford-Fulkerson)
    • Matching (bipartite matching, marriage problem)"""

    supe.memory.store_card(
        label="graph_theory_fundamentals",
        buffers=[Buffer(name="content", payload=graph_defs.encode('utf-8'))],
        master_output="Graph theory fundamentals: graphs, paths, cycles",
        track="awareness",
    )
    print("✓ Graph theory concepts defined\n")

    # Discovery 1: Handshaking Lemma
    print("🔍 DISCOVERY 1: Handshaking Lemma")
    print("-" * 80)
    print(draw_handshaking_lemma())

    result1 = await supe.learn(
        "Is Σ deg(v) = 2|E|? (Handshaking lemma: sum of degrees = 2 × edges)",
        mode="explore"
    )

    print(f"Question: Is Σ deg(v) = 2|E|?")
    print()
    print("Example: Square graph")
    print("  Vertices: 4, Edges: 4")
    print("  Each vertex has degree 2")
    print("  Σ deg = 2+2+2+2 = 8")
    print("  2|E| = 2×4 = 8 ✓")
    print()

    if result1['beliefs_count'] > 0:
        belief = result1['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Complete Graph Formula
    print("🔍 DISCOVERY 2: Complete Graph Edges")
    print("-" * 80)
    print(draw_complete_graph())

    result2 = await supe.learn(
        "Does K_n have n(n-1)/2 edges? (Complete graph edge count)",
        mode="explore"
    )

    print(f"Question: Does K_n have n(n-1)/2 edges?")
    print()
    print("Example: K₄ (4 vertices, all connected)")
    print("  Each vertex connects to 3 others")
    print("  Total: 4×3 = 12 connections")
    print("  Each edge counted twice: 12/2 = 6 edges")
    print("  Formula: 4(3)/2 = 6 ✓")
    print()

    if result2['beliefs_count'] > 0:
        belief = result2['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Tree Property
    print("🔍 DISCOVERY 3: Tree Edge Count")
    print("-" * 80)
    print(draw_tree())

    result3 = await supe.learn(
        "Does a tree with n vertices have n-1 edges? (Tree characterization)",
        mode="explore"
    )

    print(f"Question: Does a tree with n vertices have n-1 edges?")
    print()
    print("Example: Binary tree with 5 vertices")
    print("  Vertices: 5")
    print("  Edges: 4")
    print("  Check: 5 - 1 = 4 ✓")
    print()

    if result3['beliefs_count'] > 0:
        belief = result3['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Euler's Formula
    print("🔍 DISCOVERY 4: Euler's Formula for Planar Graphs")
    print("-" * 80)
    print(draw_eulers_formula())

    result4 = await supe.learn(
        "Is V - E + F = 2 for planar graphs? (Euler's formula)",
        mode="explore"
    )

    print(f"Question: Is V - E + F = 2?")
    print()
    print("Example: Triangle")
    print("  V = 3 (vertices)")
    print("  E = 3 (edges)")
    print("  F = 2 (inside + outside)")
    print("  Check: 3 - 3 + 2 = 2 ✓")
    print()

    if result4['beliefs_count'] > 0:
        belief = result4['beliefs'][0]['content']
        print(f"Result: {belief['status']} ✓")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Bipartite = No Odd Cycles
    print("🔍 DISCOVERY 5: Bipartite Graph Characterization")
    print("-" * 80)
    print(draw_bipartite_graph())

    result5 = await supe.learn(
        "Is a graph bipartite if and only if it has no odd cycles? (Bipartite characterization)",
        mode="explore"
    )

    print(f"Question: Is G bipartite ⟺ G has no odd cycles?")
    print()
    print("Example: Even cycle (square)")
    print("  Can 2-color: 1(red) - 2(blue) - 3(red) - 4(blue) - 1")
    print("  No odd cycles → bipartite ✓")
    print()
    print("Counter-example: Triangle (odd cycle)")
    print("  Cannot 2-color: 1(red) - 2(blue) - 3(?) - 1")
    print("  Has odd cycle → NOT bipartite ✓")
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
    print("🎨 GRAPH THEORY VISUALIZATIONS")
    print("=" * 80)
    print()

    print("📊 Basic Graph:")
    print(draw_basic_graph())
    print()

    print("🔗 Eulerian Path:")
    print(draw_eulerian_path())
    print()

    print("🎨 Graph Coloring:")
    print(draw_graph_coloring())
    print()

    # Summary
    print("=" * 80)
    print("🎓 GRAPH THEORY DISCOVERIES")
    print("=" * 80)
    print()

    total_beliefs = sum(r['beliefs_count'] for r in [result1, result2, result3, result4, result5])

    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    GRAPH THEORY FUNDAMENTALS                         ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Handshaking Lemma:                                                  ║")
    print("║    Σ deg(v) = 2|E|                                                  ║")
    print("║    (Sum of degrees = twice number of edges)                          ║")
    print("║                                                                      ║")
    print("║  Complete Graph:                                                     ║")
    print("║    K_n has n(n-1)/2 edges                                           ║")
    print("║                                                                      ║")
    print("║  Tree Property:                                                      ║")
    print("║    Tree with n vertices has n-1 edges                               ║")
    print("║                                                                      ║")
    print("║  Euler's Formula (planar):                                           ║")
    print("║    V - E + F = 2                                                    ║")
    print("║                                                                      ║")
    print("║  Bipartite:                                                          ║")
    print("║    G is bipartite ⟺ no odd cycles                                  ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    print(f"🌟 What We Learned:")
    print(f"   • Total beliefs formed: {total_beliefs}")
    print(f"   • Each discovery stored with proof hash")
    print(f"   • Linked to Tasc execution for traceability")
    print()

    print("🔗 Connections:")
    print("   Graph Theory ──→ Computer Science (algorithms, data structures)")
    print("                ──→ Social Networks (influence, communities)")
    print("                ──→ Biology (protein interactions, neural nets)")
    print("                ──→ Transportation (shortest paths, routing)")
    print("                ──→ Scheduling (dependencies, conflicts)")
    print()

    print("💡 Next Graph Theory Horizons:")
    print("   • Directed graphs (DAGs, topological sort)")
    print("   • Weighted graphs (Dijkstra, Bellman-Ford)")
    print("   • Network flow (max-flow min-cut)")
    print("   • Matching (bipartite matching)")
    print("   • Planarity testing")
    print("   • Spectral graph theory")
    print()

    print("🎭 Philosophy:")
    print("   Graphs model relationships and structure!")
    print("   Discrete mathematics meets continuous (eigenvalues).")
    print("   Local properties → global structure (connectivity).")
    print("   Algorithms + Theory = powerful problem-solving.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
