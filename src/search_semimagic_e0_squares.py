# search_semimagic_e0_squares.py

import argparse
import csv
from collections import defaultdict
from functools import reduce
from itertools import combinations
from math import gcd, isqrt


# ============================================================
# OUTILS
# ============================================================

def is_square(n: int) -> bool:
    if n < 0:
        return False
    r = isqrt(n)
    return r * r == n


def square_root_or_none(n: int):
    if n < 0:
        return None
    r = isqrt(n)
    return r if r * r == n else None


def label_square(n: int) -> str:
    if n == 0:
        return "0"
    r = square_root_or_none(n)
    return f"{r}²" if r is not None else str(n)


def gcd_all(values):
    return reduce(gcd, values)


def largest_square_divisor(n: int) -> int:
    """
    Retourne le plus grand carré parfait qui divise n.
    """
    if n <= 1:
        return 1

    square_factor = 1

    exponent = 0
    while n % 2 == 0:
        n //= 2
        exponent += 1

    if exponent >= 2:
        square_factor *= 2 ** (2 * (exponent // 2))

    d = 3
    while d * d <= n:
        exponent = 0

        while n % d == 0:
            n //= d
            exponent += 1

        if exponent >= 2:
            square_factor *= d ** (2 * (exponent // 2))

        d += 2

    return square_factor


def common_square_factor(values):
    g = gcd_all(values)
    return largest_square_divisor(g)


# ============================================================
# SYMÉTRIES POUR ÉVITER LES DOUBLONS
# ============================================================

def rotate_matrix(m):
    return [list(row) for row in zip(*m[::-1])]


def reflect_matrix(m):
    return [row[::-1] for row in m]


def all_symmetries(m):
    current = m

    for _ in range(4):
        yield current
        yield reflect_matrix(current)
        current = rotate_matrix(current)


def matrix_signature(m):
    return min(
        tuple(value for row in sym for value in row)
        for sym in all_symmetries(m)
    )


# ============================================================
# GÉNÉRATION DES PAIRES PYTHAGORICIENNES
# ============================================================

def generate_pythagorean_adjacency(max_root: int):
    """
    Génère un graphe sur les racines 1..max_root.

    Une arête x--y signifie que :

        x² + y²

    est un carré parfait.

    Exemple :
        15--20 car 15² + 20² = 25².
    """

    adjacency = [set() for _ in range(max_root + 1)]
    seen_edges = set()

    max_m = isqrt(max_root) + 2

    for m in range(2, max_m + 1):
        for n in range(1, m):

            if gcd(m, n) != 1:
                continue

            if (m - n) % 2 == 0:
                continue

            leg1 = m * m - n * n
            leg2 = 2 * m * n

            if leg1 <= 0 or leg2 <= 0:
                continue

            max_leg = max(leg1, leg2)

            if max_leg > max_root:
                continue

            max_k = max_root // max_leg

            for k in range(1, max_k + 1):
                x = k * leg1
                y = k * leg2

                if x > max_root or y > max_root or x == y:
                    continue

                u, v = sorted((x, y))

                if (u, v) in seen_edges:
                    continue

                seen_edges.add((u, v))
                adjacency[u].add(v)
                adjacency[v].add(u)

    return adjacency, seen_edges


# ============================================================
# CONSTRUCTION DU CARRÉ SEMI-MAGIQUE e = 0
# ============================================================

def build_semimagic_square(A, C, H, J):
    """
    Carré semi-magique :

        A²        H² + J²      C²
        C² + J²   0            A² + H²
        H²        A² + C²      J²

    Les lignes et colonnes ont toutes la même somme :

        S = A² + C² + H² + J²
    """

    a = A * A
    c = C * C
    h = H * H
    j = J * J

    b = h + j
    d = c + j
    f = a + h
    i = a + c

    matrix = [
        [a, b, c],
        [d, 0, f],
        [h, i, j],
    ]

    magic_sum = a + c + h + j

    return matrix, magic_sum


def count_positive_square_cells(matrix):
    """
    Compte uniquement les carrés positifs.
    Le centre 0 n'est pas compté.
    """
    count = 0
    roots = []

    for row in matrix:
        for value in row:
            if value == 0:
                continue

            r = square_root_or_none(value)

            if r is not None:
                count += 1
                roots.append(r)

    return count, roots


def is_semimagic(matrix, magic_sum):
    rows = [sum(row) for row in matrix]

    cols = [
        matrix[0][0] + matrix[1][0] + matrix[2][0],
        matrix[0][1] + matrix[1][1] + matrix[2][1],
        matrix[0][2] + matrix[1][2] + matrix[2][2],
    ]

    return all(s == magic_sum for s in rows + cols)


def evaluate_candidate(A, C, H, J, min_squares, primitive_only, seen_signatures):
    matrix, magic_sum = build_semimagic_square(A, C, H, J)

    if not is_semimagic(matrix, magic_sum):
        return None

    positive_values = [
        value
        for row in matrix
        for value in row
        if value != 0
    ]

    # On garde des cases positives distinctes.
    if len(set(positive_values)) != len(positive_values):
        return None

    square_count, roots = count_positive_square_cells(matrix)

    if square_count < min_squares:
        return None

    square_factor = common_square_factor(positive_values)

    if primitive_only and square_factor != 1:
        return None

    sig = matrix_signature(matrix)

    if sig in seen_signatures:
        return None

    seen_signatures.add(sig)

    return {
        "square_count": square_count,
        "A": A,
        "C": C,
        "H": H,
        "J": J,
        "magic_sum": magic_sum,
        "magic_sum_root": square_root_or_none(magic_sum),
        "max_root": max(A, C, H, J, *roots),
        "square_factor": square_factor,
        "matrix": matrix,
    }


# ============================================================
# RECHERCHE
# ============================================================

def search(max_root, min_squares, primitive_only, limit):
    adjacency, edges = generate_pythagorean_adjacency(max_root)

    print(f"Paires pythagoriciennes générées : {len(edges)}")

    # pair_to_common[(A,J)] = liste des racines X telles que :
    # A² + X² est carré ET J² + X² est carré.
    pair_to_common = defaultdict(list)

    for common_root in range(1, max_root + 1):
        neighbors = sorted(adjacency[common_root])

        for A, J in combinations(neighbors, 2):
            if A == J:
                continue

            pair_to_common[(A, J)].append(common_root)

    print(f"Paires avec au moins un voisin commun : {len(pair_to_common)}")

    results = []
    seen_signatures = set()

    # Pour avoir 8 carrés positifs, il faut deux voisins communs C,H
    # pour une paire A,J.
    for (A, J), commons in pair_to_common.items():

        if len(commons) < 2:
            continue

        commons = sorted(set(commons))

        for C, H in combinations(commons, 2):

            if len({A, C, H, J}) != 4:
                continue

            result = evaluate_candidate(
                A=A,
                C=C,
                H=H,
                J=J,
                min_squares=min_squares,
                primitive_only=primitive_only,
                seen_signatures=seen_signatures,
            )

            if result is not None:
                results.append(result)

                if len(results) >= limit:
                    results.sort(
                        key=lambda r: (
                            -r["square_count"],
                            r["max_root"],
                            r["magic_sum"],
                        )
                    )
                    return results

    results.sort(
        key=lambda r: (
            -r["square_count"],
            r["max_root"],
            r["magic_sum"],
        )
    )

    return results


# ============================================================
# AFFICHAGE / EXPORT
# ============================================================

def print_result(result):
    print("=" * 80)
    print(f"Nombre de carrés positifs : {result['square_count']}/8")
    print(f"Racines des coins          : A={result['A']}, C={result['C']}, H={result['H']}, J={result['J']}")
    print(f"Somme semi-magique         : {result['magic_sum']}")

    if result["magic_sum_root"] is not None:
        print(f"Somme semi-magique         : {result['magic_sum_root']}²")

    print(f"Racine maximale            : {result['max_root']}")
    print(f"Facteur carré commun       : {result['square_factor']}")
    print()

    for row in result["matrix"]:
        print(" | ".join(f"{label_square(value):>10}" for value in row))

    print()


def export_csv(results, path):
    fieldnames = [
        "square_count",
        "A",
        "C",
        "H",
        "J",
        "magic_sum",
        "magic_sum_root",
        "max_root",
        "square_factor",
        "m11",
        "m12",
        "m13",
        "m21",
        "m22",
        "m23",
        "m31",
        "m32",
        "m33",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            m = result["matrix"]

            writer.writerow({
                "square_count": result["square_count"],
                "A": result["A"],
                "C": result["C"],
                "H": result["H"],
                "J": result["J"],
                "magic_sum": result["magic_sum"],
                "magic_sum_root": result["magic_sum_root"] or "",
                "max_root": result["max_root"],
                "square_factor": result["square_factor"],
                "m11": m[0][0],
                "m12": m[0][1],
                "m13": m[0][2],
                "m21": m[1][0],
                "m22": m[1][1],
                "m23": m[1][2],
                "m31": m[2][0],
                "m32": m[2][1],
                "m33": m[2][2],
            })


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Recherche de carrés semi-magiques 3x3 avec centre 0."
    )

    parser.add_argument(
        "--max-root",
        type=int,
        default=100,
        help="Racine maximale utilisée pour les coins A,C,H,J.",
    )

    parser.add_argument(
        "--min-squares",
        type=int,
        default=7,
        help="Nombre minimal de carrés positifs parmi les 8 cases non nulles.",
    )

    parser.add_argument(
        "--primitive-only",
        action="store_true",
        help="Exclure les dilatations par facteur carré commun.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Nombre maximal de résultats affichés/exportés.",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Chemin CSV optionnel.",
    )

    args = parser.parse_args()

    results = search(
        max_root=args.max_root,
        min_squares=args.min_squares,
        primitive_only=args.primitive_only,
        limit=args.limit,
    )

    print()
    print(f"Résultats trouvés : {len(results)}")
    print()

    for result in results:
        print_result(result)

    if args.csv:
        export_csv(results, args.csv)
        print(f"CSV exporté : {args.csv}")


if __name__ == "__main__":
    main()