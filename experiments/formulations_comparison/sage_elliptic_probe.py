#!/usr/bin/env python
"""Sonde à exécuter avec le Python de l'environnement SageMath."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ


def rational_text(value) -> str:
    return str(QQ(value))


def point_payload(point) -> dict[str, str]:
    return {"x": rational_text(point[0]), "y": rational_text(point[1])}


def inspect_curve(n: int, x: str, y: str, *, proof: bool = True) -> dict:
    if n <= 0:
        raise ValueError("n doit être strictement positif")
    curve = EllipticCurve(QQ, [0, 0, 0, -(n**2), 0])
    point = curve(QQ(x), QQ(y))
    halves = point.division_points(2)
    generators = curve.gens(proof=proof)
    return {
        "n": n,
        "curve": f"y^2 = x^3 - {n**2}*x",
        "point": point_payload(point),
        "rank": int(curve.rank(proof=proof)),
        "rank_proof_requested": proof,
        "torsion_invariants": [int(v) for v in curve.torsion_subgroup().invariants()],
        "generators": [point_payload(generator) for generator in generators],
        "halves": [point_payload(half) for half in halves],
        "point_is_divisible_by_2": bool(halves),
        "halves_verified": all(2 * half == point for half in halves),
        "generator_heights": [str(generator.height()) for generator in generators],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=24)
    parser.add_argument("--x", default="25")
    parser.add_argument("--y", default="35")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-proof", action="store_true")
    args = parser.parse_args()
    payload = inspect_curve(args.n, args.x, args.y, proof=not args.no_proof)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
