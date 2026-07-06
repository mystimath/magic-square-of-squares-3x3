# search_magic_square_of_squares_v2.py

from math import isqrt
import argparse
import csv
import time


def sqrt_if_square(n: int):
    if n <= 0:
        return None
    r = isqrt(n)
    return r if r * r == n else None


def square_label(n: int) -> str:
    r = sqrt_if_square(n)
    return f"{r}²" if r is not None else str(n)


def is_magic_square(m):
    sums = []

    sums.extend([sum(row) for row in m])

    for col in range(3):
        sums.append(m[0][col] + m[1][col] + m[2][col])

    sums.append(m[0][0] + m[1][1] + m[2][2])
    sums.append(m[0][2] + m[1][1] + m[2][0])

    return len(set(sums)) == 1, sums[0]


def offsets_for_square_center(center_root: int):
    """
    Pour e = center_root², cherche tous les couples :

        x², e, y²

    tels que :

        x² + y² = 2e

    Chaque couple donne un écart :

        offset = e - x² = y² - e
    """

    e = center_root * center_root
    offsets = []

    for x in range(1, center_root):
        x2 = x * x
        y2 = 2 * e - x2
        y = sqrt_if_square(y2)

        if y is not None and y > center_root:
            offsets.append({
                "offset": e - x2,
                "low_root": x,
                "high_root": y,
                "low_value": x2,
                "high_value": y2,
            })

    return offsets


def count_square_entries(entries):
    roots = {}

    for name, value in entries.items():
        r = sqrt_if_square(value)
        if r is not None:
            roots[name] = r

    return len(roots), roots


def build_candidate(e, p, q, c, d, f, h):
    """
    Carré magique orienté selon :

        i < c < d < a < e < j < f < h < b

    Forme :

        a  b  c
        d  e  f
        h  i  j
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


def search(max_center_root: int, min_squares: int, limit: int, progress: int | None):
    results = []
    start = time.time()

    for center_root in range(2, max_center_root + 1):
        if progress and center_root % progress == 0:
            elapsed = time.time() - start
            print(
                f"[progress] centre={center_root}/{max_center_root} "
                f"résultats={len(results)} "
                f"temps={elapsed:.1f}s"
            )

        e = center_root * center_root
        offsets = offsets_for_square_center(center_root)

        if len(offsets) < 2:
            continue

        for P in offsets:
            p = P["offset"]
            c = P["low_value"]
            h = P["high_value"]

            for Q in offsets:
                q = Q["offset"]
                d = Q["low_value"]
                f = Q["high_value"]

                # Condition qui donne l'ordre :
                # i < c < d < a < e < j < f < h < b
                if not (0 < q < p < 2 * q):
                    continue

                entries, matrix = build_candidate(e, p, q, c, d, f, h)

                if entries["i"] <= 0:
                    continue

                if len(set(entries.values())) != 9:
                    continue

                if not (
                    entries["i"]
                    < entries["c"]
                    < entries["d"]
                    < entries["a"]
                    < entries["e"]
                    < entries["j"]
                    < entries["f"]
                    < entries["h"]
                    < entries["b"]
                ):
                    continue

                ok_magic, magic_sum = is_magic_square(matrix)

                if not ok_magic:
                    continue

                square_count, roots = count_square_entries(entries)

                if square_count >= min_squares:
                    results.append({
                        "square_count": square_count,
                        "magic_sum": magic_sum,
                        "center_root": center_root,
                        "e": e,
                        "p": p,
                        "q": q,
                        "entries": entries,
                        "roots": roots,
                        "matrix": matrix,
                        "max_entry": max(entries.values()),
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

        for r in results:
            entries = r["entries"]
            roots = r["roots"]

            row = {
                "square_count": r["square_count"],
                "magic_sum": r["magic_sum"],
                "center_root": r["center_root"],
                "e": r["e"],
                "p": r["p"],
                "q": r["q"],
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
            }

            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-center-root",
        type=int,
        default=500,
        help="Racine maximale du centre e = n²",
    )

    parser.add_argument(
        "--min-squares",
        type=int,
        default=7,
        help="Nombre minimal de cases carrées à afficher",
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