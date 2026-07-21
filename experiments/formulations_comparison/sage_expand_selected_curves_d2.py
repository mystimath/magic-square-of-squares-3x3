#!/usr/bin/env python
"""D2 : compare de petites boîtes de coefficients sur les courbes D1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sage_search_bremner_d0 import search_curve

DEFAULT_CURVES = (34, 41, 65, 137, 138, 145, 154, 161, 194)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=int, nargs="+", default=DEFAULT_CURVES)
    parser.add_argument("--coefficient-bounds", type=int, nargs="+", default=(2, 3))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-proof", action="store_true")
    args = parser.parse_args()
    if any(n <= 0 for n in args.n_values):
        parser.error("--n-values exige des entiers positifs")
    if any(bound < 1 for bound in args.coefficient_bounds):
        parser.error("--coefficient-bounds exige des entiers positifs")

    records = []
    for n in args.n_values:
        for bound in args.coefficient_bounds:
            result = search_curve(n, bound, proof=not args.no_proof)
            records.append(
                {
                    "n": n,
                    "rank": result["rank"],
                    "coefficient_bound": bound,
                    "half_combinations_tested": result["half_combinations_tested"],
                    "certified_progression_centers": result["certified_progression_centers"],
                    "center_pairs_tested": result["center_pairs_tested"],
                    "horizontal_square_closures": result["horizontal_square_closures"],
                    "candidate_count": result["candidate_count"],
                    "candidates": result["candidates"],
                }
            )

    payload = {
        "engine": "D2-local-height-expansion",
        "curves": list(args.n_values),
        "coefficient_bounds": list(args.coefficient_bounds),
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