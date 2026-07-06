# search_magic_square_of_squares.py

from math import isqrt
import argparse


def sqrt_if_square(n: int):
    """Retourne (True, racine) si n est un carré parfait positif."""
    if n <= 0:
        return False, None
    r = isqrt(n)
    return r * r == n, r


def square_label(n: int) -> str:
    """Affiche n sous forme r² si possible."""
    ok, r = sqrt_if_square(n)
    return f"{r}²" if ok else str(n)


def is_magic_square(m):
    """Vérifie que les 8 sommes valent la même valeur."""
    rows = [sum(row) for row in m]
    cols = [m[0][k] + m[1][k] + m[2][k] for k in range(3)]
    diags = [
        m[0][0] + m[1][1] + m[2][2],
        m[0][2] + m[1][1] + m[2][0],
    ]

    sums = rows + cols + diags
    return len(set(sums)) == 1, sums[0]


def count_square_entries(entries):
    roots = {}
    count = 0

    for name, value in entries.items():
        ok, r = sqrt_if_square(value)
        if ok:
            count += 1
            roots[name] = r

    return count, roots


def search(max_center_root=500, max_entry_root=700, min_squares=7, limit=20):
    """
    Cherche des carrés magiques 3x3 selon la forme :

        e-p+q   e+2p-q   e-p
        e-q     e        e+q
        e+p     e-2p+q   e+p-q

    Conditions d'ordre :
        i < c < d < a < e < j < f < h < b

    Cela revient à :
        0 < q < p < 2q
        e - 2p + q > 0
    """

    square_values = [r * r for r in range(1, max_entry_root + 1)]
    square_set = set(square_values)

    results = []

    for center_root in range(2, max_center_root + 1):
        e = center_root * center_root

        # On construit les offsets t tels que e-t et e+t soient tous les deux carrés.
        offsets = []

        for low in square_values:
            if low >= e:
                break

            high = 2 * e - low

            if high in square_set:
                t = e - low
                offsets.append((t, low, high))

        # p correspond au couple c/h.
        # q correspond au couple d/f.
        for p, c, h in offsets:
            for q, d, f in offsets:

                # Conditions pour respecter l'ordre demandé
                if not (0 < q < p < 2 * q):
                    continue

                a = e - p + q
                b = e + 2 * p - q
                i = e - 2 * p + q
                j = e + p - q

                if i <= 0:
                    continue

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

                # Tous les entiers doivent être distincts.
                if len(set(entries.values())) != 9:
                    continue

                # Vérification stricte de l'ordre choisi
                if not (
                    i < c < d < a < e < j < f < h < b
                ):
                    continue

                m = [
                    [a, b, c],
                    [d, e, f],
                    [h, i, j],
                ]

                ok_magic, magic_sum = is_magic_square(m)

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
                        "matrix": m,
                    })

    results.sort(
        key=lambda r: (
            -r["square_count"],
            max(r["entries"].values()),
            r["magic_sum"],
        )
    )

    return results[:limit]


def print_result(result):
    print("=" * 80)
    print(f"Nombre d'entrées carrées : {result['square_count']}/9")
    print(f"Somme magique            : {result['magic_sum']}")
    print(f"Centre                   : {result['center_root']}² = {result['e']}")
    print(f"p                        : {result['p']}")
    print(f"q                        : {result['q']}")
    print()

    m = result["matrix"]

    for row in m:
        print(" | ".join(f"{square_label(x):>12}" for x in row))

    print()
    print("Entrées carrées :")

    for name, root in sorted(result["roots"].items()):
        value = result["entries"][name]
        print(f"  {name} = {root}² = {value}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--max-center-root",
        type=int,
        default=500,
        help="Racine maximale du centre e = n²",
    )

    parser.add_argument(
        "--max-entry-root",
        type=int,
        default=700,
        help="Racine maximale utilisée pour construire les progressions de carrés",
    )

    parser.add_argument(
        "--min-squares",
        type=int,
        default=7,
        help="Nombre minimal d'entrées carrées à afficher",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Nombre maximal de résultats affichés",
    )

    args = parser.parse_args()

    results = search(
        max_center_root=args.max_center_root,
        max_entry_root=args.max_entry_root,
        min_squares=args.min_squares,
        limit=args.limit,
    )

    print(f"Résultats trouvés : {len(results)}")
    print()

    for result in results:
        print_result(result)


if __name__ == "__main__":
    main()