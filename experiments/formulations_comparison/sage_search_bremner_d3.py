#!/usr/bin/env python
"""D3 : tamise localement la condition de fermeture elliptique like-Bremner."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from time import perf_counter
import sys

from sage.all import EllipticCurve, QQ

PACKAGE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.rational_square_sieve import (  # noqa: E402
    DEFAULT_LOCAL_PRIMES,
    rational_local_residues,
    two_upper_minus_lower_square_obstruction,
)
from sage_search_bremner_d0 import (  # noqa: E402
    bremner_grid,
    integral_normalization,
    is_magic,
    point_payload,
    progression_certificate,
    rational_square_root,
    text,
)


DEFAULT_CURVES = (34, 41, 65, 137, 138, 145, 154, 161, 194)


def certified_centers(curve, generators, n, coefficient_bound):
    coefficient_range = range(-coefficient_bound, coefficient_bound + 1)
    tested = 0
    by_center = {}
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
        by_center.setdefault(
            center,
            {
                "half_coefficients": list(coefficients),
                "half": point_payload(half),
                "point": point_payload(point),
                "certificate": certificate,
            },
        )
    return tested, by_center


def search_curve_d3(n, coefficient_bound, *, primes=DEFAULT_LOCAL_PRIMES, proof=True):
    started = perf_counter()
    curve = EllipticCurve(QQ, [0, 0, 0, -(n**2), 0])
    generators = tuple(curve.gens(proof=proof))
    if not generators:
        raise RuntimeError("La courbe n'a pas de générateur non torsion retourné.")

    enumeration_started = perf_counter()
    tested, by_center = certified_centers(curve, generators, n, coefficient_bound)
    enumeration_seconds = perf_counter() - enumeration_started

    ordered = sorted(by_center)
    residues_by_center = {
        center: rational_local_residues(
            center.numerator(), center.denominator(), primes
        )
        for center in ordered
    }
    pair_started = perf_counter()
    pairs_tested = 0
    rejected_nonpositive = 0
    local_rejections = {prime: 0 for prime in primes}
    local_survivors = 0
    exact_square_tests = 0
    exact_square_closures = 0
    candidates = []
    for lower_center, upper_center in itertools.combinations(ordered, 2):
        pairs_tested += 1
        obstruction = two_upper_minus_lower_square_obstruction(
            residues_by_center[lower_center],
            residues_by_center[upper_center],
            n,
            primes,
        )
        if obstruction is not None:
            local_rejections[obstruction] += 1
            continue
        local_survivors += 1
        closing_value = 2 * upper_center - lower_center - n
        if closing_value <= 0:
            rejected_nonpositive += 1
            continue
        exact_square_tests += 1
        if rational_square_root(closing_value) is None:
            continue
        exact_square_closures += 1

        q = upper_center - lower_center
        grid = bremner_grid(upper_center, q, QQ(n))
        square_roots = [rational_square_root(value) for value in grid]
        if not is_magic(grid):
            raise ArithmeticError("La reconstruction D3 n'est pas magique.")
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
                "lower_point": by_center[lower_center],
                "upper_point": by_center[upper_center],
                "grid": [text(value) for value in grid],
                "square_roots": [
                    text(root) if root is not None else None for root in square_roots
                ],
                "integer_normalization": integral_normalization(grid, square_roots),
            }
        )

    pair_seconds = perf_counter() - pair_started
    reduction = 1.0 - exact_square_tests / pairs_tested if pairs_tested else 0.0
    return {
        "engine": "D3-elliptic-local-square-closure-sieve",
        "curve": f"y^2 = x^3 - {n**2}*x",
        "n": n,
        "rank": int(curve.rank(proof=proof)),
        "rank_proof_requested": proof,
        "generators": [point_payload(point) for point in generators],
        "coefficient_bound": coefficient_bound,
        "local_primes": list(primes),
        "half_combinations_tested": tested,
        "certified_progression_centers": len(by_center),
        "center_pairs_tested": pairs_tested,
        "rejected_nonpositive_after_local_sieve": rejected_nonpositive,
        "local_rejection_counts": {
            str(prime): count for prime, count in local_rejections.items()
        },
        "local_sieve_survivors": local_survivors,
        "exact_square_tests": exact_square_tests,
        "exact_square_test_reduction": reduction,
        "horizontal_square_closures": exact_square_closures,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "timing_seconds": {
            "center_enumeration": enumeration_seconds,
            "pair_sieve_and_closure": pair_seconds,
            "total": perf_counter() - started,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=int, nargs="+", default=DEFAULT_CURVES)
    parser.add_argument("--coefficient-bound", type=int, default=3)
    parser.add_argument("--local-primes", type=int, nargs="+", default=DEFAULT_LOCAL_PRIMES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-proof", action="store_true")
    args = parser.parse_args()
    if any(n <= 0 for n in args.n_values):
        parser.error("--n-values exige des entiers positifs")
    if args.coefficient_bound < 1:
        parser.error("--coefficient-bound doit être positif")

    records = [
        search_curve_d3(
            n,
            args.coefficient_bound,
            primes=tuple(args.local_primes),
            proof=not args.no_proof,
        )
        for n in args.n_values
    ]
    payload = {
        "engine": "D3-elliptic-local-square-closure-sieve-campaign",
        "curves": list(args.n_values),
        "coefficient_bound": args.coefficient_bound,
        "local_primes": list(args.local_primes),
        "rank_proof_requested": not args.no_proof,
        "records": records,
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
