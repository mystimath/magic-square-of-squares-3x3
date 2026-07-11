import csv
import math
import argparse
from pathlib import Path


def is_square(n: int) -> bool:
    if n < 0:
        return False
    r = math.isqrt(n)
    return r * r == n


def fmt_cell(n: int) -> str:
    if is_square(n):
        return f"{math.isqrt(n)}²"
    return str(n)


def fmt_value(n: int) -> str:
    if is_square(n):
        return f"{math.isqrt(n)}² = {n}"
    return f"{n}  [non carré]"


def magic_sums(vals):
    a, b, c, d, e, f, g, h, i = vals
    return {
        "ligne 1": a + b + c,
        "ligne 2": d + e + f,
        "ligne 3": g + h + i,
        "colonne 1": a + d + g,
        "colonne 2": b + e + h,
        "colonne 3": c + f + i,
        "diagonale 1": a + e + i,
        "diagonale 2": c + e + g,
    }


def print_grid(row, index):
    vals = [int(row[k]) for k in ["a", "b", "c", "d", "e", "f", "g", "h", "i"]]
    a, b, c, d, e, f, g, h, i = vals

    total_squares = sum(is_square(x) for x in vals)
    center = int(row["center"])
    u = int(row["u"])
    v = int(row["v"])

    labels = [fmt_cell(x) for x in vals]
    width = max(len(x) for x in labels) + 2

    print("=" * 90)
    print(f"Carré #{index}")
    print("=" * 90)
    print(f"mode           : {row.get('mode', '')}")
    print(f"centre e       : {center} {'[carré]' if is_square(center) else '[non carré]'}")
    print(f"u / v          : {u} / {v}")
    print(f"total carrés   : {total_squares}/9")
    print(f"positions      : {row.get('square_positions', '')}")
    print(f"gcd racines    : {row.get('primitive_root_gcd', '')}")
    print()

    print("Grille en puissances :")
    print()
    print(f"{labels[0]:>{width}} {labels[1]:>{width}} {labels[2]:>{width}}")
    print(f"{labels[3]:>{width}} {labels[4]:>{width}} {labels[5]:>{width}}")
    print(f"{labels[6]:>{width}} {labels[7]:>{width}} {labels[8]:>{width}}")
    print()

    print("Grille numérique :")
    print()
    print(f"{a:>{width}} {b:>{width}} {c:>{width}}")
    print(f"{d:>{width}} {e:>{width}} {f:>{width}}")
    print(f"{g:>{width}} {h:>{width}} {i:>{width}}")
    print()

    print("Détail des cases :")
    names = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
    for name, value in zip(names, vals):
        print(f"  {name} = {fmt_value(value)}")

    print()
    print("Sommes magiques :")
    sums = magic_sums(vals)
    for name, value in sums.items():
        print(f"  {name:<12} = {value}")

    unique_sums = sorted(set(sums.values()))
    if len(unique_sums) == 1:
        print(f"\nConstante magique : {unique_sums[0]}")
    else:
        print(f"\nAttention : sommes différentes : {unique_sums}")

    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    path = Path(args.csv)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("Aucun résultat dans le CSV.")
        return

    print(f"Fichier : {path}")
    print(f"Résultats lus : {len(rows)}")
    print()

    for idx, row in enumerate(rows[:args.limit], start=1):
        print_grid(row, idx)


if __name__ == "__main__":
    main()