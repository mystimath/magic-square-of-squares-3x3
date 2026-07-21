#!/usr/bin/env python
"""Énumère des candidats 7/9 de type Bremner depuis une courbe congruente.

À courbe ``E_n`` fixée, ce prototype Sage énumère des combinaisons bornées des
générateurs de Mordell--Weil, les double, certifie les triplets de carrés
rationnels associés, puis ferme deux colonnes en une grille 7/9. Il ne lit
aucun catalogue de progressions B.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ, ZZ


def text(value):
    return str(QQ(value))


def point_payload(point):
    return {"x": text(point[0]), "y": text(point[1])}


def rational_square_root(value):
    """Retourne la racine rationnelle positive exacte, sinon ``None``."""
    value = QQ(value)
    if value <= 0:
        return None
    numerator = ZZ(value.numerator())
    denominator = ZZ(value.denominator())
    if not numerator.is_square() or not denominator.is_square():
        return None
    return QQ(numerator.sqrt()) / QQ(denominator.sqrt())


def progression_certificate(n, point):
    """Certifie ``x-n, x, x+n`` comme trois carrés rationnels."""
    x = QQ(point[0])
    roots = tuple(rational_square_root(value) for value in (x - n, x, x + n))
    if any(root is None for root in roots):
        return None
    u, v, w = roots
    if abs(QQ(point[1])) != u * v * w:
        return None
    return {
        "center": text(x),
        "roots": [text(u), text(v), text(w)],
        "values": [text(x - n), text(x), text(x + n)],
    }


def integral_normalization(grid, square_roots):
    """Multiplie une grille rationnelle par le plus petit carré rendant tout entier."""
    prime_exponents = {}
    for value in grid:
        denominator = ZZ(QQ(value).denominator())
        for prime, exponent in denominator.factor():
            required = (int(exponent) + 1) // 2
            prime_exponents[prime] = max(prime_exponents.get(prime, 0), required)
    root_scale = ZZ(1)
    for prime, exponent in prime_exponents.items():
        root_scale *= prime**exponent
    value_scale = root_scale**2
    integer_grid = tuple(QQ(value) * value_scale for value in grid)
    if any(value.denominator() != 1 for value in integer_grid):
        raise ArithmeticError("La normalisation entière a échoué.")
    return {
        "root_scale": str(root_scale),
        "value_scale": str(value_scale),
        "grid": [str(ZZ(value)) for value in integer_grid],
        "square_roots": [
            str(ZZ(root * root_scale)) if root is not None else None
            for root in square_roots
        ],
    }
def bremner_grid(center, horizontal_step, vertical_step):
    """Grille Lo Shu centrée, reconstruite depuis deux progressions verticales."""
    e = QQ(center)
    q = QQ(horizontal_step)
    r = QQ(vertical_step)
    return (
        e - q, e + q + r, e - r,
        e + q - r, e, e - q + r,
        e + r, e - q - r, e + q,
    )


def is_magic(grid):
    target = grid[0] + grid[1] + grid[2]
    lines = (
        grid[0:3], grid[3:6], grid[6:9],
        grid[0:9:3], grid[1:9:3], grid[2:9:3],
        (grid[0], grid[4], grid[8]), (grid[2], grid[4], grid[6]),
    )
    return all(sum(line) == target for line in lines)


def search_curve(n, coefficient_bound, *, proof=True):
    if n <= 0:
        raise ValueError("n doit être strictement positif")
    if coefficient_bound < 1:
        raise ValueError("coefficient_bound doit être positif")

    curve = EllipticCurve(QQ, [0, 0, 0, -(n**2), 0])
    generators = tuple(curve.gens(proof=proof))
    if not generators:
        raise RuntimeError("La courbe n'a pas de générateur non torsion retourné.")

    coefficient_range = range(-coefficient_bound, coefficient_bound + 1)
    tested = 0
    certified_by_center = {}
    for coefficients in itertools.product(coefficient_range, repeat=len(generators)):
        if not any(coefficients):
            continue
        half = curve(0)
        for coefficient, generator in zip(coefficients, generators):
            half += coefficient * generator
        point = 2 * half
        if point.is_zero():
            continue
        tested += 1
        certificate = progression_certificate(n, point)
        if certificate is None:
            continue
        center = QQ(point[0])
        certified_by_center.setdefault(
            center,
            {
                "half_coefficients": list(coefficients),
                "half": point_payload(half),
                "point": point_payload(point),
                "certificate": certificate,
            },
        )

    candidates = []
    pairs_tested = 0
    horizontal_square_closures = 0
    ordered = sorted(certified_by_center)
    for lower_center, upper_center in itertools.combinations(ordered, 2):
        pairs_tested += 1
        q = upper_center - lower_center
        lower_left = lower_center - n
        closing_root = rational_square_root(lower_left + 2 * q)
        if closing_root is None:
            continue
        horizontal_square_closures += 1
        grid = bremner_grid(upper_center, q, QQ(n))
        square_roots = [rational_square_root(value) for value in grid]
        if not is_magic(grid):
            raise ArithmeticError("La reconstruction elliptique n'est pas magique.")
        if sum(root is not None for root in square_roots) != 7:
            continue
        if len(set(grid)) != 9 or any(value <= 0 for value in grid):
            continue
        candidates.append(
            {
                "lower_center": text(lower_center),
                "upper_center": text(upper_center),
                "horizontal_difference": text(q),
                "vertical_difference": str(n),
                "lower_point": certified_by_center[lower_center],
                "upper_point": certified_by_center[upper_center],
                "grid": [text(value) for value in grid],
                "square_roots": [text(root) if root is not None else None for root in square_roots],
                "integer_normalization": integral_normalization(grid, square_roots),
            }
        )

    return {
        "engine": "D0-elliptic-fixed-curve-bremner-7of9",
        "curve": f"y^2 = x^3 - {n**2}*x",
        "n": n,
        "rank": int(curve.rank(proof=proof)),
        "rank_proof_requested": proof,
        "generators": [point_payload(point) for point in generators],
        "generator_heights": [str(point.height()) for point in generators],
        "coefficient_bound": coefficient_bound,
        "half_combinations_tested": tested,
        "certified_progression_centers": len(certified_by_center),
        "center_pairs_tested": pairs_tested,
        "horizontal_square_closures": horizontal_square_closures,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--coefficient-bound", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-proof", action="store_true")
    args = parser.parse_args()
    payload = search_curve(
        args.n,
        args.coefficient_bound,
        proof=not args.no_proof,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()