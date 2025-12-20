"""
Mathematical Discovery: Linear Algebra - Vectors, Matrices, and Transformations ⃗

Linear algebra is the mathematics of linear transformations and vector spaces!

Core Concepts:
    • Vectors: Directed quantities with magnitude and direction
    • Matrices: Rectangular arrays representing linear transformations
    • Linear combinations: a·v + b·w
    • Dot product: v·w = |v||w|cos(θ)
    • Matrix multiplication: (AB)ᵢⱼ = Σₖ AᵢₖBₖⱼ

Fundamental Operations:
    Vector addition: [a,b] + [c,d] = [a+c, b+d]
    Scalar multiplication: k[a,b] = [ka, kb]
    Dot product: [a,b]·[c,d] = ac + bd
    Matrix multiplication: Apply transformation after transformation

Key Properties:
    • Matrix multiplication is associative: (AB)C = A(BC)
    • Distributive: A(B+C) = AB + AC
    • Identity matrix: I·A = A·I = A
    • Transpose: (AB)ᵀ = BᵀAᵀ (order reverses!)
    • Determinant: det(AB) = det(A)det(B)

Applications:
    • Computer Graphics: Rotations, scaling, projections
    • Machine Learning: Neural networks, SVD, PCA
    • Physics: Quantum mechanics (state vectors)
    • Engineering: Control systems, signal processing
    • Economics: Input-output models, optimization

Let's LEARN linear algebra through exploration! ⃗✨
"""

import asyncio
from supe import Supe
from ab.models import Buffer


def draw_2d_vector():
    """ASCII art of 2D vector."""
    return """
    2D Vector: v = [3, 2]

           ↑ y
           |
         2 •---->• (3,2)
           |    /
         1 |   /
           |  /
         0 +--------→ x
           0  1  2  3

    Components: vₓ = 3, vᵧ = 2
    Magnitude: |v| = √(3² + 2²) = √13 ≈ 3.606
    Direction: tan⁻¹(2/3) ≈ 33.7°
    """


def draw_vector_addition():
    """ASCII art of vector addition."""
    return """
    Vector Addition: u + v

           ↑
           |      • (u+v)
         3 |     /|
           |    / |
         2 |   /  • v
           |  /  /
         1 | /  /
           |/  /
         0 •--•------→
           u

    Parallelogram rule:
    u + v is the diagonal from origin to opposite corner

    Component-wise:
    [2,1] + [1,2] = [2+1, 1+2] = [3,3]
    """


def draw_dot_product():
    """ASCII art of dot product geometric interpretation."""
    return """
    Dot Product: v·w = |v||w|cos(θ)

           w
          /|
         / |
        /  | projection
       /   |
      /  θ |
     v     |

    v·w = (projection of v onto w) × |w|

    Also: v·w = vₓwₓ + vᵧwᵧ

    Special cases:
    • v·w = 0  ⟹  v ⊥ w (perpendicular)
    • v·v = |v|² (magnitude squared)
    • v·w = |v||w|  ⟹  v ∥ w (parallel)
    """


def draw_matrix_2x2():
    """ASCII art of 2×2 matrix."""
    return """
    2×2 Matrix: A = [a b]
                    [c d]

    ┌       ┐
    │ a  b  │
    │ c  d  │
    └       ┘

    As linear transformation:
    • First column: where [1,0] goes
    • Second column: where [0,1] goes

    Example: Rotation by 90°
    R = [ 0 -1]  ⟹  [1,0] → [0,1]
        [ 1  0]      [0,1] → [-1,0]
    """


def draw_matrix_multiplication():
    """ASCII art of matrix multiplication."""
    return """
    Matrix Multiplication: C = A × B

        B
      ┌───┐
      │ b │
    A │ i │  →  C
    ┌─│ j │─┐   ┌───┐
    │ │   │ │   │ c │
    │ aᵢ  │ │ = │ i │
    │ k   │ │   │ j │
    └─────┘─┘   └───┘

    Rule: cᵢⱼ = Σₖ aᵢₖ·bₖⱼ

    Row of A × Column of B:
    [a b] [e] = ae + bf
          [f]

    Example:
    [1 2] [5 6]   [1·5+2·7  1·6+2·8]   [19 22]
    [3 4] [7 8] = [3·5+4·7  3·6+4·8] = [43 50]
    """


def draw_identity_matrix():
    """ASCII art of identity matrix."""
    return """
    Identity Matrix: I

    2×2:  [ 1  0 ]
          [ 0  1 ]

    3×3:  [ 1  0  0 ]
          [ 0  1  0 ]
          [ 0  0  1 ]

    Property: I·A = A·I = A

    Diagonal of 1s, everything else 0
    Like multiplying by 1 in regular arithmetic!
    """


def draw_rotation_matrix():
    """ASCII art of rotation transformation."""
    return """
    Rotation Matrix: Rotate by angle θ

    R(θ) = [ cos θ  -sin θ ]
           [ sin θ   cos θ ]

    Example: Rotate 90° counterclockwise
    R(90°) = [ 0  -1 ]
             [ 1   0 ]

    Apply to point [1,0]:
    [ 0  -1 ] [ 1 ]   [ 0 ]
    [ 1   0 ] [ 0 ] = [ 1 ]

    [1,0] → [0,1]  (rotated 90°!)

    Visual:
         ↑ [0,1]
         |
    -----+----→ [1,0]
         |
    """


def draw_determinant():
    """ASCII art of determinant as area."""
    return """
    Determinant: Area/Volume Scaling Factor

    2×2 Matrix: A = [a b]
                    [c d]

    det(A) = ad - bc

    Geometric meaning:
    • det(A) = area of parallelogram formed by columns
    • det(A) = 0  ⟹  columns are parallel (no area)
    • det(A) < 0  ⟹  orientation reversed

    Example:
    [2 0]   det = 2·3 - 0·0 = 6
    [0 3]   (rectangle with area 6)

    [1 2]   det = 1·4 - 2·3 = -2
    [3 4]   (area 2, orientation flipped)
    """


def draw_eigenvalue():
    """ASCII art of eigenvector concept."""
    return """
    Eigenvectors: Vectors that don't change direction!

    Definition: Av = λv
    • v is eigenvector
    • λ is eigenvalue (scaling factor)

    Visual:
         v
         |
         ↓
      Matrix A
         ↓
        λv  (same direction, scaled!)
         |
         ↓

    Example: Diagonal matrix
    [3 0] [1]   [3]
    [0 5] [0] = [0] = 3[1,0]

    Eigenvector: [1,0], Eigenvalue: 3
    Eigenvector: [0,1], Eigenvalue: 5
    """


async def main():
    print("=" * 80)
    print("⃗  MATHEMATICAL DISCOVERY: Linear Algebra - Vectors and Transformations")
    print("=" * 80)
    print()
    print("Using EXPLORE mode to discover linear algebra properties!")
    print("The mathematics that powers computer graphics and machine learning")
    print()

    supe = Supe(db_path=":memory:")

    # Seed linear algebra knowledge
    print("📚 Seeding linear algebra definitions...")

    linalg_def = """Linear Algebra: Mathematics of Vectors and Matrices

Vectors:
- Directed quantities with magnitude and direction
- Notation: v = [v₁, v₂, ..., vₙ]
- Operations: addition, scalar multiplication

Vector Operations:
- Addition: u + v = [u₁+v₁, u₂+v₂, ...]
- Scalar mult: k·v = [k·v₁, k·v₂, ...]
- Dot product: u·v = u₁v₁ + u₂v₂ + ...
- Magnitude: |v| = √(v₁² + v₂² + ...)

Matrices:
- Rectangular arrays of numbers
- Represent linear transformations
- Notation: A = [aᵢⱼ] where i=row, j=column

Matrix Operations:
- Addition: (A+B)ᵢⱼ = Aᵢⱼ + Bᵢⱼ
- Scalar mult: (kA)ᵢⱼ = k·Aᵢⱼ
- Multiplication: (AB)ᵢⱼ = Σₖ AᵢₖBₖⱼ

Properties:
- Matrix mult is associative: (AB)C = A(BC)
- Distributive: A(B+C) = AB + AC
- NOT commutative: AB ≠ BA (usually)
- Identity: I·A = A·I = A

Transpose:
- Swap rows and columns: (Aᵀ)ᵢⱼ = Aⱼᵢ
- (AB)ᵀ = BᵀAᵀ (order reverses!)
- (Aᵀ)ᵀ = A

Determinant (2×2):
- det([a b; c d]) = ad - bc
- Geometric: area scaling factor
- det(AB) = det(A)·det(B)

Eigenvectors and Eigenvalues:
- Av = λv
- v doesn't change direction, only scales by λ
- Fundamental in: PCA, quantum mechanics, stability analysis"""

    supe.memory.store_card(
        label="linalg_definitions",
        buffers=[Buffer(name="content", payload=linalg_def.encode('utf-8'))],
        master_output="Linear algebra definitions and operations",
        track="awareness",
    )
    print("✓ Linear algebra concepts defined\n")

    # Discovery 1: Vector addition is commutative
    print("🔍 DISCOVERY 1: Vector Addition is Commutative")
    print("-" * 80)
    print(draw_vector_addition())
    print("Question: Is u + v = v + u?")
    print()
    print("Test: u = [2,1], v = [1,2]")
    print("  u + v = [2+1, 1+2] = [3,3]")
    print("  v + u = [1+2, 2+1] = [3,3] ✓")
    print()

    result1 = await supe.learn(
        "Is vector addition commutative? Test: [2,1] + [1,2] = [1,2] + [2,1] = [3,3]",
        mode="explore"
    )

    if result1['beliefs_count'] > 0:
        status = result1['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result1['confidence']:.2f}")
        print(f"Proof Hash: {result1['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Vector addition is commutative!")
            print("⟹ This mirrors regular addition commutativity")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 2: Dot product
    print("🔍 DISCOVERY 2: Dot Product Formula")
    print("-" * 80)
    print(draw_dot_product())
    print("Question: Is [3,4]·[1,2] = 3·1 + 4·2 = 11?")
    print()
    print("Calculation:")
    print("  u·v = uₓvₓ + uᵧvᵧ")
    print("      = 3·1 + 4·2")
    print("      = 3 + 8 = 11 ✓")
    print()

    result2 = await supe.learn(
        "For vectors [3,4] and [1,2], is the dot product equal to 11? (3·1 + 4·2)",
        mode="explore"
    )

    if result2['beliefs_count'] > 0:
        status = result2['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result2['confidence']:.2f}")
        print(f"Proof Hash: {result2['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Dot product formula VERIFIED!")
            print("⟹ Component-wise multiplication and sum!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 3: Matrix multiplication
    print("🔍 DISCOVERY 3: Matrix Multiplication")
    print("-" * 80)
    print(draw_matrix_multiplication())
    print("Question: Is [[1,2],[3,4]] × [[5,6],[7,8]] = [[19,22],[43,50]]?")
    print()
    print("Calculation:")
    print("  (1,1) entry: 1·5 + 2·7 = 5 + 14 = 19 ✓")
    print("  (1,2) entry: 1·6 + 2·8 = 6 + 16 = 22 ✓")
    print("  (2,1) entry: 3·5 + 4·7 = 15 + 28 = 43 ✓")
    print("  (2,2) entry: 3·6 + 4·8 = 18 + 32 = 50 ✓")
    print()

    result3 = await supe.learn(
        "Is [[1,2],[3,4]] × [[5,6],[7,8]] = [[19,22],[43,50]]? (Matrix multiplication)",
        mode="explore"
    )

    if result3['beliefs_count'] > 0:
        status = result3['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result3['confidence']:.2f}")
        print(f"Proof Hash: {result3['proof_hash'][:16]}...")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 4: Identity matrix
    print("🔍 DISCOVERY 4: Identity Matrix Property")
    print("-" * 80)
    print(draw_identity_matrix())
    print("Question: Is I·A = A where I = [[1,0],[0,1]] and A = [[2,3],[4,5]]?")
    print()
    print("Calculation:")
    print("  [[1,0],[0,1]] × [[2,3],[4,5]]")
    print("  = [[1·2+0·4, 1·3+0·5], [0·2+1·4, 0·3+1·5]]")
    print("  = [[2,3], [4,5]] ✓")
    print()

    result4 = await supe.learn(
        "Is I·A = A for I=[[1,0],[0,1]] and A=[[2,3],[4,5]]? (Identity property)",
        mode="explore"
    )

    if result4['beliefs_count'] > 0:
        status = result4['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result4['confidence']:.2f}")
        print(f"Proof Hash: {result4['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Identity matrix VERIFIED!")
            print("⟹ I acts like 1 in matrix multiplication!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 5: Matrix multiplication is associative
    print("🔍 DISCOVERY 5: Matrix Multiplication is Associative")
    print("-" * 80)
    print("Question: Is (AB)C = A(BC)?")
    print()
    print("Test: A = [[1,2]], B = [[3],[4]], C = [[5,6]]")
    print("  (AB)C = ([[1,2]]·[[3],[4]])·[[5,6]]")
    print("        = [[11]]·[[5,6]] = [[55,66]]")
    print()
    print("  A(BC) = [[1,2]]·([[3],[4]]·[[5,6]])")
    print("        = [[1,2]]·[[15,18],[20,24]]")
    print("        = [[55,66]] ✓")
    print()

    result5 = await supe.learn(
        "Is matrix multiplication associative? Test: (AB)C = A(BC) = [[55,66]]",
        mode="explore"
    )

    if result5['beliefs_count'] > 0:
        status = result5['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result5['confidence']:.2f}")
        print(f"Proof Hash: {result5['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Matrix multiplication is associative!")
            print("⟹ Grouping doesn't matter: (AB)C = A(BC)")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Discovery 6: Determinant
    print("🔍 DISCOVERY 6: Determinant Formula")
    print("-" * 80)
    print(draw_determinant())
    print("Question: For A = [[2,0],[0,3]], is det(A) = 6?")
    print()
    print("Formula: det([[a,b],[c,d]]) = ad - bc")
    print("  det([[2,0],[0,3]]) = 2·3 - 0·0 = 6 ✓")
    print()
    print("Geometric: This matrix scales area by factor of 6")
    print()

    result6 = await supe.learn(
        "For matrix [[2,0],[0,3]], is the determinant equal to 6? (2·3 - 0·0)",
        mode="explore"
    )

    if result6['beliefs_count'] > 0:
        status = result6['beliefs'][0]['content']['status']
        print(f"Result: {status} {'✅' if status == 'PROVEN' else '❌'}")
        print(f"Confidence: {result6['confidence']:.2f}")
        print(f"Proof Hash: {result6['proof_hash'][:16]}...")

        if status == 'PROVEN':
            print("\n⟹ Determinant formula VERIFIED!")
            print("⟹ det = ad - bc for 2×2 matrices")
            print("⟹ Represents area scaling factor!")
    else:
        print("Result: NO BELIEF ⚠️")
    print()

    # Display visualizations
    print("=" * 80)
    print("🎨 LINEAR ALGEBRA VISUALIZATIONS")
    print("=" * 80)
    print()
    print("⃗ 2D Vector:")
    print(draw_2d_vector())
    print()
    print("➕ Vector Addition:")
    print(draw_vector_addition())
    print()
    print("⊙ Dot Product:")
    print(draw_dot_product())
    print()
    print("▦ 2×2 Matrix:")
    print(draw_matrix_2x2())
    print()
    print("✖️ Matrix Multiplication:")
    print(draw_matrix_multiplication())
    print()
    print("𝟙 Identity Matrix:")
    print(draw_identity_matrix())
    print()
    print("↻ Rotation Matrix:")
    print(draw_rotation_matrix())
    print()
    print("▱ Determinant:")
    print(draw_determinant())
    print()
    print("λ Eigenvector:")
    print(draw_eigenvalue())
    print()

    # Summary
    print("=" * 80)
    print("🎓 LINEAR ALGEBRA DISCOVERIES")
    print("=" * 80)
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    LINEAR ALGEBRA FUNDAMENTALS                       ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║                                                                      ║")
    print("║  Vector Operations:                                                  ║")
    print("║    • Addition: u + v = [u₁+v₁, u₂+v₂] (commutative)                ║")
    print("║    • Scalar mult: k·v = [k·v₁, k·v₂]                                ║")
    print("║    • Dot product: u·v = u₁v₁ + u₂v₂                                 ║")
    print("║    • Magnitude: |v| = √(v₁² + v₂²)                                  ║")
    print("║                                                                      ║")
    print("║  Matrix Operations:                                                  ║")
    print("║    • Multiplication: (AB)ᵢⱼ = Σₖ AᵢₖBₖⱼ                             ║")
    print("║    • Associative: (AB)C = A(BC)                                     ║")
    print("║    • Identity: I·A = A·I = A                                        ║")
    print("║    • NOT commutative: AB ≠ BA (usually)                             ║")
    print("║                                                                      ║")
    print("║  Determinant (2×2):                                                  ║")
    print("║    • det([a b; c d]) = ad - bc                                      ║")
    print("║    • Geometric: area scaling factor                                 ║")
    print("║    • det(AB) = det(A)·det(B)                                        ║")
    print("║                                                                      ║")
    print("║  Eigenvectors:                                                       ║")
    print("║    • Av = λv (direction unchanged, scaled by λ)                     ║")
    print("║    • Fundamental in PCA, stability, quantum mechanics               ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    print("🌟 What We Learned:")
    print(f"   • Total beliefs formed: {sum(1 for r in [result1, result2, result3, result4, result5, result6] if r['beliefs_count'] > 0)}")
    print("   • Each discovery stored with proof hash")
    print("   • Linked to Tasc execution for traceability")
    print()
    print("🔗 Connections:")
    print("   Linear Algebra ──→ Computer Graphics (transformations, 3D rendering)")
    print("                  ──→ Machine Learning (neural networks, PCA, SVD)")
    print("                  ──→ Physics (quantum states, mechanics)")
    print("                  ──→ Engineering (control systems, vibrations)")
    print("                  ──→ Economics (input-output models, optimization)")
    print()
    print("💡 Next Linear Algebra Horizons:")
    print("   • Matrix inverse and solving Ax = b")
    print("   • Transpose properties: (AB)ᵀ = BᵀAᵀ")
    print("   • Orthogonal matrices: QᵀQ = I")
    print("   • Eigenvalue decomposition: A = PΛP⁻¹")
    print("   • Singular Value Decomposition (SVD)")
    print("   • Vector spaces and subspaces")
    print()
    print("🎭 Philosophy:")
    print("   Linear algebra reveals that transformations are fundamental!")
    print("   Matrices represent change, eigenvectors show what stays aligned.")
    print("   This is the language of: AI, graphics, physics, and modern tech.")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
