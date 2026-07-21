#!/usr/bin/env python
"""D1 : sélectionne des courbes congruentes sans facteur carré pour D0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sage.all import EllipticCurve, QQ, ZZ

from sage_search_bremner_d0 import search_curve


def is_squarefree(n: int) -> bool:
    return all(exponent == 1 for _, exponent in ZZ(n).factor())


def curve_rank_record(n: int, *, proof: bool) -> dict:
    curve = EllipticCurve(QQ, [0, 0, 0, -(n**2), 0])
    try:
        rank = int(curve.rank(proof=proof))
        generators = curve.gens(proof=proof)
    except Exception as error:  # Le pilote doit conserver les courbes non certifiées.
        return {"n": n, "status": "rank_error", "error": repr(error)}
    return {
        "n": n,
        "status": "certified",
        "rank": rank,
        "generators": [
            {"x": str(QQ(point[0])), "y": str(QQ(point[1]))}
            for point in generators
        ],
    }


def select_curves(max_n: int, min_rank: int, coefficient_bound: int, *, proof: bool):
    if max_n < 1:
        raise ValueError("max_n doit être positif")
    if min_rank < 1:
        raise ValueError("min_rank doit être positif")
    records = []
    selected = []
    for n in range(1, max_n + 1):
        if not is_squarefree(n):
            continue
        record = curve_rank_record(n, proof=proof)
        records.append(record)
        if record.get("rank", -1) < min_rank:
            continue
        d0 = search_curve(n, coefficient_bound, proof=proof)
        selected.append(
            {
                "n": n,
                "rank": record["rank"],
                "generators": record["generators"],
                "d0": d0,
            }
        )
    return {
        "engine": "D1-squarefree-rank-selector",
        "max_n": max_n,
        "min_rank": min_rank,
        "coefficient_bound": coefficient_bound,
        "rank_proof_requested": proof,
        "squarefree_curves_considered": len(records),
        "rank_errors": sum(record["status"] == "rank_error" for record in records),
        "rank_records": records,
        "selected_curve_count": len(selected),
        "selected_curves": selected,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-n", type=int, default=200)
    parser.add_argument("--min-rank", type=int, default=2)
    parser.add_argument("--coefficient-bound", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-proof", action="store_true")
    args = parser.parse_args()
    payload = select_curves(
        args.max_n,
        args.min_rank,
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