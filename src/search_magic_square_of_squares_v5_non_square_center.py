from collections import defaultdict
from functools import reduce
from math import gcd, isqrt
import argparse
import csv
import time


# ============================================================
# OUTILS ARITHMÉTIQUES
# ============================================================

def sqrt_if_square(n):
    """
    Retourne la racine carrée entière si n est un carré parfait positif.
    Sinon retourne None.
    """
    if n <= 0:
        return None

    r = isqrt(n)
    return r if r * r == n else None


def square_label(n):
    """
    Affiche n sous forme r² si possible.
    Sinon affiche n tel quel.
    """
    r = sqrt_if_square(n)
    return f"{r}²" if r is not None else str(n)


def gcd_all(values):
    """
    PGCD d'une liste d'entiers.
    """
    return reduce(gcd, values)


def largest_square_divisor(n):
    """
    Retourne le plus grand carré parfait qui divise n.

    Exemples :
        72 -> 36
        48 -> 16
        12 -> 4
        10 -> 1
    """
    if n <= 1:
        return 1

    square_divisor = 1

    exponent = 0
    while n % 2 == 0:
        n //= 2
        exponent += 1

    if exponent >= 2:
        square_divisor *= 2 ** (2 * (exponent // 2))

    d = 3

    while d * d <= n:
        exponent = 0

        while n % d == 0:
            n //= d
            exponent += 1

        if exponent >= 2:
            square_divisor *= d ** (2 * (exponent // 2))

        d += 2

    return square_divisor


def common_square_factor(values):
    """
    Retourne le plus grand facteur carré parfait commun aux entrées.
    """
    g = gcd_all(values)
    return largest_square_divisor(g)


# ============================================================
# SYMÉTRIES
# ============================================================

def rotate_matrix(m):
    return [list(row) for row in zip(*m[::-1])]


def reflect_matrix(m):
    return [row[::-1] for row in m]


def all_symmetries(m):
    """
    Génère les 8 symétries : 4 rotations et leurs réflexions.
    """
    current = m

    for _ in range(4):
        yield current
        yield reflect_matrix(current)
        current = rotate_matrix(current)


def matrix_signature(m):
    """
    Signature canonique pour éviter les doublons par rotation / symétrie.
    """
    return min(
        tuple(value for row in sym for value in row)
        for sym in all_symmetries(m)
    )


# ============================================================
# VÉRIFICATIONS
# ============================================================

def is_magic_square(m):
    """
    Vérifie les 3 lignes, 3 colonnes et 2 diagonales.
    """
    sums = []

    sums.extend(sum(row) for row in m)

    for col in range(3):
        sums.append(m[0][col] + m[1][col] + m[2][col])

    sums.append(m[0][0] + m[1][1] + m[2][2])
    sums.append(m[0][2] + m[1][1] + m[2][0])

    return len(set(sums)) == 1, sums[0]


def count_square_entries(entries):
    """
    Compte les cases carrées et retourne leurs racines.
    """
    roots = {}

    for name, value in entries.items():
        root = sqrt_if_square(value)

        if root is not None:
            roots[name] = root

    return len(roots), roots


# ============================================================
# GÉNÉRATION DES CENTRES NON CARRÉS
# ============================================================

def generate_offsets_by_center(max_outer_root, progress_root=None):
    """
    Génère toutes les paires de carrés :

        x² et y²

    ayant un même centre entier :

        e = (x² + y²) / 2

    Pour que e soit entier, x et y doivent avoir la même parité.

    Chaque paire donne un offset :

        offset = (y² - x²) / 2

    donc :

        e - offset = x²
        e + offset = y²

    Contrairement à la v4, ici e n'est pas imposé comme carré.
    """

    offsets_by_center = defaultdict(dict)
    start = time.time()

    pair_count = 0

    for y in range(2, max_outer_root + 1):

        if progress_root and y % progress_root == 0:
            elapsed = time.time() - start
            print(
                f"[generation] outer_root={y}/{max_outer_root} "
                f"paires={pair_count} "
                f"centres={len(offsets_by_center)} "
                f"temps={elapsed:.1f}s"
            )

        y2 = y * y

        # x doit avoir la même parité que y.
        x_start = 1 if y % 2 == 1 else 2

        for x in range(x_start, y, 2):
            x2 = x * x

            e = (x2 + y2) // 2
            offset = (y2 - x2) // 2

            pair_count += 1

            # Pour un centre donné, un offset correspond à une paire opposée.
            if offset not in offsets_by_center[e]:
                offsets_by_center[e][offset] = {
                    "low_root": x,
                    "high_root": y,
                    "low_value": x2,
                    "high_value": y2,
                }

    return offsets_by_center, pair_count


# ============================================================
# CONSTRUCTION DU CARRÉ MAGIQUE
# ============================================================

def build_candidate(e, p, q):
    """
    Carré magique 3x3 :

        a b c
        d e f
        h i j

    On choisit deux offsets p et q :

        c = e - p
        h = e + p

        d = e - q
        f = e + q

    Les contraintes magiques imposent :

        a = e - p + q
        b = e + 2p - q
        i = e - 2p + q
        j = e + p - q

    Pour avoir 8 cases extérieures carrées, il faut que les offsets :

        p
        q
        |p - q|
        |2p - q|

    correspondent tous à des paires de carrés autour du même centre e.
    """

    a = e - p + q
    b = e + 2 * p - q
    c = e - p

    d = e - q
    f = e + q

    h = e + p
    i = e - 2 * p + q
    j = e + p - q

    entries = {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "e": e,
        "f": f,
        "h": h,
        "i": i,
        "j": j,
    }

    matrix = [
        [a, b, c],
        [d, e, f],
        [h, i, j],
    ]

    return entries, matrix


# ============================================================
# RECHERCHE PRINCIPALE
# ============================================================

def search(
    max_outer_root,
    include_square_center,
    primitive_only,
    limit,
    progress_root,
    progress_center,
):
    start = time.time()

    print("Génération des paires de carrés autour de centres entiers...")
    offsets_by_center, pair_count = generate_offsets_by_center(
        max_outer_root=max_outer_root,
        progress_root=progress_root,
    )

    print("Filtrage des centres ayant au moins 4 paires opposées...")
    candidate_centers = {
        e: offset_map
        for e, offset_map in offsets_by_center.items()
        if len(offset_map) >= 4
    }

    print(f"Nombre total de paires générées     : {pair_count}")
    print(f"Nombre total de centres rencontrés  : {len(offsets_by_center)}")
    print(f"Centres avec au moins 4 offsets     : {len(candidate_centers)}")
    print("Recherche des carrés magiques 8/9...")

    results = []
    seen_signatures = set()

    tested_offset_pairs = 0
    rejected_square_center = 0
    rejected_not_magic = 0
    rejected_not_distinct = 0
    rejected_not_primitive = 0

    centers_items = list(candidate_centers.items())

    for idx, (e, offset_map) in enumerate(centers_items, start=1):

        if progress_center and idx % progress_center == 0:
            elapsed = time.time() - start
            print(
                f"[search] centre_index={idx}/{len(centers_items)} "
                f"résultats={len(results)} "
                f"temps={elapsed:.1f}s"
            )

        center_root = sqrt_if_square(e)

        if center_root is not None and not include_square_center:
            rejected_square_center += 1
            continue

        offsets = sorted(offset_map.keys())
        offset_set = set(offsets)

        for p in offsets:
            for q in offsets:

                if p == q:
                    continue

                tested_offset_pairs += 1

                r = abs(p - q)
                s = abs(2 * p - q)

                if r == 0 or s == 0:
                    continue

                # Les quatre offsets nécessaires doivent exister.
                if r not in offset_set:
                    continue

                if s not in offset_set:
                    continue

                entries, matrix = build_candidate(e, p, q)
                values = list(entries.values())

                # Toutes les cases doivent être positives.
                if min(values) <= 0:
                    continue

                # Les 9 cases doivent être distinctes.
                if len(set(values)) != 9:
                    rejected_not_distinct += 1
                    continue

                ok_magic, magic_sum = is_magic_square(matrix)

                if not ok_magic:
                    rejected_not_magic += 1
                    continue

                square_count, roots = count_square_entries(entries)

                # En mode centre non carré, on attend 8/9.
                # Si include_square_center est actif, un 9/9 serait également possible.
                if square_count < 8:
                    continue

                g = gcd_all(values)
                square_factor = common_square_factor(values)

                if primitive_only and square_factor != 1:
                    rejected_not_primitive += 1
                    continue

                sig = matrix_signature(matrix)

                if sig in seen_signatures:
                    continue

                seen_signatures.add(sig)

                results.append({
                    "square_count": square_count,
                    "magic_sum": magic_sum,
                    "center": e,
                    "center_root": center_root if center_root is not None else "",
                    "p": p,
                    "q": q,
                    "gcd": g,
                    "square_factor": square_factor,
                    "entries": entries,
                    "roots": roots,
                    "matrix": matrix,
                    "max_entry": max(values),
                    "max_square_root": max(root for root in roots.values()),
                })

    results.sort(
        key=lambda item: (
            -item["square_count"],
            item["max_square_root"],
            item["max_entry"],
            item["magic_sum"],
        )
    )

    stats = {
        "max_outer_root": max_outer_root,
        "pair_count": pair_count,
        "all_centers_count": len(offsets_by_center),
        "candidate_centers_count": len(candidate_centers),
        "tested_offset_pairs": tested_offset_pairs,
        "rejected_square_center": rejected_square_center,
        "rejected_not_magic": rejected_not_magic,
        "rejected_not_distinct": rejected_not_distinct,
        "rejected_not_primitive": rejected_not_primitive,
        "results_count": len(results),
        "elapsed_seconds": time.time() - start,
    }

    return results[:limit], results, stats


# ============================================================
# AFFICHAGE
# ============================================================

def print_result(result):
    print("=" * 80)
    print(f"Nombre d'entrées carrées : {result['square_count']}/9")
    print(f"Somme magique            : {result['magic_sum']}")
    print(f"Centre                   : {result['center']}")
    print(f"Racine du centre          : {result['center_root'] or 'non carré'}")
    print(f"p                        : {result['p']}")
    print(f"q                        : {result['q']}")
    print(f"gcd des 9 entrées         : {result['gcd']}")
    print(f"facteur carré commun      : {result['square_factor']}")
    print(f"racine carrée max         : {result['max_square_root']}")
    print()

    for row in result["matrix"]:
        print(" | ".join(f"{square_label(value):>14}" for value in row))

    print()
    print("Entrées carrées :")

    for name in ["a", "b", "c", "d", "e", "f", "h", "i", "j"]:
        value = result["entries"][name]
        root = result["roots"].get(name)

        if root is not None:
            print(f"  {name} = {root}² = {value}")
        else:
            print(f"  {name} = {value}  non carré")

    print()


def print_stats(stats):
    print("=" * 80)
    print("STATISTIQUES")
    print("=" * 80)

    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key:30s}: {value:.2f}")
        else:
            print(f"{key:30s}: {value}")

    print()


# ============================================================
# EXPORT CSV
# ============================================================

def export_csv(results, path):
    fieldnames = [
        "square_count",
        "magic_sum",
        "center",
        "center_root",
        "p",
        "q",
        "gcd",
        "square_factor",
        "max_square_root",
        "a",
        "b",
        "c",
        "d",
        "e_entry",
        "f",
        "h",
        "i",
        "j",
        "a_root",
        "b_root",
        "c_root",
        "d_root",
        "e_root",
        "f_root",
        "h_root",
        "i_root",
        "j_root",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            entries = result["entries"]
            roots = result["roots"]

            writer.writerow({
                "square_count": result["square_count"],
                "magic_sum": result["magic_sum"],
                "center": result["center"],
                "center_root": result["center_root"],
                "p": result["p"],
                "q": result["q"],
                "gcd": result["gcd"],
                "square_factor": result["square_factor"],
                "max_square_root": result["max_square_root"],
                "a": entries["a"],
                "b": entries["b"],
                "c": entries["c"],
                "d": entries["d"],
                "e_entry": entries["e"],
                "f": entries["f"],
                "h": entries["h"],
                "i": entries["i"],
                "j": entries["j"],
                "a_root": roots.get("a", ""),
                "b_root": roots.get("b", ""),
                "c_root": roots.get("c", ""),
                "d_root": roots.get("d", ""),
                "e_root": roots.get("e", ""),
                "f_root": roots.get("f", ""),
                "h_root": roots.get("h", ""),
                "i_root": roots.get("i", ""),
                "j_root": roots.get("j", ""),
            })


# ============================================================
# POINT D'ENTRÉE
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Recherche de carrés magiques 3x3 avec 8 cases carrées "
            "et centre non nécessairement carré."
        )
    )

    parser.add_argument(
        "--max-outer-root",
        type=int,
        default=5000,
        help=(
            "Racine maximale des carrés extérieurs. "
            "Toutes les cases carrées extérieures seront <= max_outer_root²."
        ),
    )

    parser.add_argument(
        "--include-square-center",
        action="store_true",
        help=(
            "Inclure aussi les centres carrés. "
            "Par défaut, ils sont exclus pour cibler les vrais centres non carrés."
        ),
    )

    parser.add_argument(
        "--primitive-only",
        action="store_true",
        help=(
            "Exclure les candidats ayant un facteur carré parfait commun "
            "aux 9 entrées."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Nombre maximal de résultats affichés.",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Chemin du fichier CSV d'export.",
    )

    parser.add_argument(
        "--progress-root",
        type=int,
        default=None,
        help="Afficher la progression de génération tous les N roots extérieurs.",
    )

    parser.add_argument(
        "--progress-center",
        type=int,
        default=None,
        help="Afficher la progression de recherche tous les N centres candidats.",
    )

    args = parser.parse_args()

    displayed_results, all_results, stats = search(
        max_outer_root=args.max_outer_root,
        include_square_center=args.include_square_center,
        primitive_only=args.primitive_only,
        limit=args.limit,
        progress_root=args.progress_root,
        progress_center=args.progress_center,
    )

    print()
    print(f"Résultats trouvés : {len(all_results)}")
    print()

    for result in displayed_results:
        print_result(result)

    print_stats(stats)

    if args.csv:
        export_csv(all_results, args.csv)
        print(f"CSV exporté : {args.csv}")


if __name__ == "__main__":
    main()