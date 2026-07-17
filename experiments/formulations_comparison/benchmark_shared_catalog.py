"""Mesure séparément le catalogue commun et les adaptateurs B1/B2/C/D."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import time

from prototypes.formulation_b1 import search_formulation_b1
from prototypes.formulation_b2 import search_formulation_b2
from prototypes.formulation_c import search_formulation_c
from prototypes.formulation_d import probe_formulation_d
from prototypes.model import (
    generate_square_progressions,
    generate_square_progressions_parametric,
)


CATALOG_ENGINES = {
    "quadratic": generate_square_progressions,
    "parametric": generate_square_progressions_parametric,
}


ENGINES = {
    "B1": search_formulation_b1,
    "B2": search_formulation_b2,
    "C": search_formulation_c,
    "D-probe": probe_formulation_d,
}


def alternating_order(repetition: int) -> list[str]:
    names = list(ENGINES)
    shift = repetition % len(names)
    rotated = names[shift:] + names[:shift]
    return rotated if repetition % 2 == 0 else list(reversed(rotated))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bound", type=int, default=10_000)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--catalog-engine", choices=CATALOG_ENGINES, default="quadratic")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/formulations_comparison/benchmarks/shared_catalog_r10000.json"),
    )
    args = parser.parse_args()
    if args.bound < 1 or args.repetitions < 1:
        parser.error("la borne et le nombre de répétitions doivent être positifs")

    start = time.perf_counter()
    catalog = CATALOG_ENGINES[args.catalog_engine](args.bound)
    catalog_seconds = time.perf_counter() - start
    raw_runs = []
    reference_classes = None
    for repetition in range(args.repetitions):
        order = alternating_order(repetition)
        for position, name in enumerate(order):
            start = time.perf_counter()
            result = ENGINES[name](args.bound, progressions=catalog)
            seconds = time.perf_counter() - start
            if reference_classes is None:
                reference_classes = result.classes
            elif result.classes != reference_classes:
                raise RuntimeError(f"divergence des classes pour {name}")
            raw_runs.append(
                {
                    "repetition": repetition + 1,
                    "position": position + 1,
                    "formulation": name,
                    "wall_seconds": seconds,
                    "class_count": len(result.classes),
                    "stats": result.stats,
                }
            )
            print(f"rep={repetition + 1} pos={position + 1} {name}: {seconds:.6f}s")

    summary = {}
    for name in ENGINES:
        samples = [row["wall_seconds"] for row in raw_runs if row["formulation"] == name]
        summary[name] = {
            "samples": len(samples),
            "min_seconds": min(samples),
            "median_seconds": statistics.median(samples),
            "max_seconds": max(samples),
        }
    payload = {
        "schema_version": 1,
        "status": "complete",
        "max_root": args.bound,
        "repetitions": args.repetitions,
        "catalog_seconds": catalog_seconds,
        "catalog_engine": args.catalog_engine,
        "catalog_size": len(catalog),
        "all_classes_equal": True,
        "class_count": len(reference_classes or ()),
        "timing_scope": "adapter only; shared catalog excluded",
        "summary": summary,
        "runs": raw_runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"catalog_seconds": catalog_seconds, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
