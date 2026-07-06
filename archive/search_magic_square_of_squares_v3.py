from collections import defaultdict
from functools import reduce
from math import gcd, isqrt
import argparse
import csv
import time


def sqrt_if_square(n):
    if n <= 0:
        return None
    r = isqrt(n)
    return r if r * r == n else None


def square_label(n):
    r = sqrt_if_square(n)
    return f"{r}²" if r is not None else str(n)


def gcd_all(values):
    return reduce(gcd, values)


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


def is_magic_square(m):
    sums = []

    sums.extend(sum(row) for row in m)

    for col in range(3):
        sums.append(m[0][col] + m[1][col] + m[2][col])

    sums.append(m[0][0] + m[1][1] + m[2][2])
    sums.append(m[0][2] + m[1][1] + m[2][0])

    return len(set(sums)) == 1, sums[0]


def count_square_entries(entries):
    roots = {}

    for name, value in entries.items():
        root = sqrt_if_square(value)
        if root is not None:
            roots[name] = root

    return len(roots), roots


def generate_offsets_by_center(max_center_root):
    """
    Génère toutes les progressions arithmétiques de carrés :

        x², z², y²

    via les triangles pythagoriciens :

        u² + v² = z²

    avec :

        x = |u - v|
        y = u + v
        offset = z² - x² = y² - z² = 2uv
    """

    offsets_by_center = defaultdict(list)
    seen = set()

    max_m = isqrt(max_center_root) + 2

    for m in range(2, max_m + 1):
        for n in range(1, m):

            # Génération des triplets pythagoriciens primitifs
            if gcd(m, n) != 1:
                continue

            if (m - n) % 2 == 0:
                continue

            hyp0 = m * m + n * n

            if hyp0 > max_center_root:
                continue

            leg1_0 = m * m - n * n
            leg2_0 = 2 * m * n

            max_k = max_center_root // hyp0

            for k in range(1, max_k + 1):
                z = k * hyp0
                u = k * leg1_0
                v = k * leg2_0

                x = abs(u - v)
                y = u + v

                if x <= 0:
                    continue

                offset = 2 * u * v

                key = (z, offset)

                if key in seen:
                    continue

                seen.add(key)

                offsets_by_center[z].append({
                    "offset": offset,
                    "low_root": x,
                    "high_root": y,
                    "low_value": x * x,
                    "high_value": y * y,
                    "u": u,
                    "v": v,
                })

    return offsets_by_center


def build_candidate(e, p, q, c, d, f, h):
    """
    Carré magique :

        a  b  c
        d  e  f
        h  i  j

    avec :

        c = e - p
        h = e + p
        d = e - q
        f = e + q

    Les autres cases sont forcées par la magie.
    """

    a = e - p + q
    b = e + 2 * p - q
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


def search(max_center_root, min_squares, primitive_only, limit, progress):
    start = time.time()

    print("Génération des progressions de carrés...")
    offsets_by_center = generate_offsets_by_center(max_center_root)

    print("Recherche des carrés magiques...")
    results = []
    seen_signatures = set()

    for center_root in range(2, max_center_root + 1):
        if progress and center_root % progress == 0:
            elapsed = time.time() - start
            print(
                f"[progress] centre={center_root}/{max_center_root} "
                f"résultats={len(results)} "
                f"temps={elapsed:.1f}s"
            )

        offsets = offsets_by_center.get(center_root, [])

        if len(offsets) < 2:
            continue

        e = center_root * center_root

        for P in offsets:
            p = P["offset"]
            c = P["low_value"]
            h = P["high_value"]

            for Q in offsets:
                q = Q["offset"]

                if p == q:
                    continue

                d = Q["low_value"]
                f = Q["high_value"]

                entries, matrix = build_candidate(e, p, q, c, d, f, h)

                values = list(entries.values())

                if min(values) <= 0:
                    continue

                if len(set(values)) != 9:
                    continue

                ok_magic, magic_sum = is_magic_square(matrix)

                if not ok_magic:
                    continue

                square_count, roots = count_square_entries(entries)

                if square_count < min_squares:
                    continue

                g = gcd_all(values)

                if primitive_only and g != 1:
                    continue

                sig = matrix_signature(matrix)

                if sig in seen_signatures:
                    continue

                seen_signatures.add(sig)

                results.append({
                    "square_count": square_count,
                    "magic_sum": magic_sum,
                    "center_root": center_root,
                    "e": e,
                    "p": p,
                    "q": q,
                    "gcd": g,
                    "entries": entries,
                    "roots": roots,
                    "matrix": matrix,
                    "max_entry": max(values),
                })

    results.sort(
        key=lambda r: (
            -r["square_count"],
            r["max_entry"],
            r["magic_sum"],
        )
    )

    return results[:limit], results


def print_result(result):
    print("=" * 80)
    print(f"Nombre d'entrées carrées : {result['square_count']}/9")
    print(f"Somme magique            : {result['magic_sum']}")
    print(f"Centre                   : {result['center_root']}² = {result['e']}")
    print(f"p                        : {result['p']}")
    print(f"q                        : {result['q']}")
    print(f"gcd des 9 entrées         : {result['gcd']}")
    print()

    for row in result["matrix"]:
        print(" | ".join(f"{square_label(x):>12}" for x in row))

    print()
    print("Entrées carrées :")

    for name in ["a", "b", "c", "d", "e", "f", "h", "i", "j"]:
        value = result["entries"][name]
        root = result["roots"].get(name)

        if root is not None:
            print(f"  {name} = {root}² = {value}")

    print()


def export_csv(results, path):
    fieldnames = [
        "square_count",
        "magic_sum",
        "center_root",
        "e",
        "p",
        "q",
        "gcd",
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
                "center_root": result["center_root"],
                "e": result["e"],
                "p": result["p"],
                "q": result["q"],
                "gcd": result["gcd"],
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


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-center-root",
        type=int,
        default=1000,
        help="Racine maximale du centre e = n²",
    )

    parser.add_argument(
        "--min-squares",
        type=int,
        default=7,
        help="Nombre minimal d'entrées carrées",
    )

    parser.add_argument(
        "--primitive-only",
        action="store_true",
        help="Exclure les multiples triviaux k² du même carré",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Nombre maximal de résultats affichés",
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Chemin du fichier CSV d'export",
    )

    parser.add_argument(
        "--progress",
        type=int,
        default=None,
        help="Afficher l'avancement tous les N centres",
    )

    args = parser.parse_args()

    displayed_results, all_results = search(
        max_center_root=args.max_center_root,
        min_squares=args.min_squares,
        primitive_only=args.primitive_only,
        limit=args.limit,
        progress=args.progress,
    )

    print()
    print(f"Résultats trouvés : {len(all_results)}")
    print()

    for result in displayed_results:
        print_result(result)

    if args.csv:
        export_csv(all_results, args.csv)
        print(f"CSV exporté : {args.csv}")


if __name__ == "__main__":
    main()