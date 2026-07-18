"""Benchmark équilibré : index PGCD, filtre pairwise et oracle sans filtre."""

from __future__ import annotations

import argparse
import csv
import gc
import json
import pathlib
import platform
import statistics
import sys
import time
from collections.abc import Callable

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.like_bremner import search_like_bremner  # noqa: E402
from prototypes.like_bremner_indexed import search_like_bremner_indexed  # noqa: E402
from prototypes.model import generate_square_progressions_parametric  # noqa: E402


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "maximum": max(values),
        "sample_standard_deviation": statistics.stdev(values),
    }


def _timed(function: Callable[[], object]) -> tuple[float, float, object]:
    gc.collect()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    result = function()
    return (
        time.perf_counter() - wall_start,
        time.process_time() - cpu_start,
        result,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-square-root",
        "--max-root",
        dest="max_square_root",
        type=int,
        default=100_000,
    )
    parser.add_argument("--repeats", type=int, default=9)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()
    if args.repeats < 3 or args.repeats % 3:
        parser.error("--repeats doit être un multiple de 3, au moins égal à 3")

    catalog_start = time.perf_counter()
    catalog = generate_square_progressions_parametric(args.max_square_root)
    catalog_seconds = time.perf_counter() - catalog_start

    warm_bound = min(args.max_square_root, 2000)
    warm_catalog = generate_square_progressions_parametric(warm_bound)
    search_like_bremner_indexed(warm_bound, progressions=warm_catalog)
    search_like_bremner(
        warm_bound,
        progressions=warm_catalog,
        early_primitive_filter=True,
    )
    search_like_bremner(
        warm_bound,
        progressions=warm_catalog,
        early_primitive_filter=False,
    )

    variants: tuple[tuple[str, Callable[[], object]], ...] = (
        (
            "gcd_indexed",
            lambda: search_like_bremner_indexed(
                args.max_square_root,
                progressions=catalog,
            ),
        ),
        (
            "pairwise_gcd",
            lambda: search_like_bremner(
                args.max_square_root,
                progressions=catalog,
                early_primitive_filter=True,
            ),
        ),
        (
            "filter_disabled",
            lambda: search_like_bremner(
                args.max_square_root,
                progressions=catalog,
                early_primitive_filter=False,
            ),
        ),
    )
    rows: list[dict[str, object]] = []
    class_reference = None
    stats_by_variant: dict[str, dict[str, int]] = {}
    for run in range(1, args.repeats + 1):
        shift = (run - 1) % len(variants)
        order = variants[shift:] + variants[:shift]
        for order_index, (variant, function) in enumerate(order, start=1):
            wall_seconds, cpu_seconds, result = _timed(function)
            if class_reference is None:
                class_reference = result.classes
            elif result.classes != class_reference:
                raise RuntimeError("Les trois stratégies ne donnent pas les mêmes classes.")
            current_stats = dict(result.stats)
            previous = stats_by_variant.setdefault(variant, current_stats)
            if previous != current_stats:
                raise RuntimeError("Les compteurs d'une stratégie ne sont pas stables.")
            rows.append(
                {
                    "run": run,
                    "order_index": order_index,
                    "variant": variant,
                    "wall_seconds": wall_seconds,
                    "cpu_seconds": cpu_seconds,
                    "class_count": len(result.classes),
                }
            )

    names = tuple(name for name, _ in variants)
    wall_values = {
        name: [
            float(row["wall_seconds"])
            for row in rows
            if row["variant"] == name
        ]
        for name in names
    }
    cpu_values = {
        name: [
            float(row["cpu_seconds"])
            for row in rows
            if row["variant"] == name
        ]
        for name in names
    }
    wall_summary = {name: _summary(values) for name, values in wall_values.items()}
    cpu_summary = {name: _summary(values) for name, values in cpu_values.items()}

    paired_pairwise_speedups: list[float] = []
    paired_disabled_speedups: list[float] = []
    for run in range(1, args.repeats + 1):
        paired = {
            str(row["variant"]): float(row["wall_seconds"])
            for row in rows
            if row["run"] == run
        }
        paired_pairwise_speedups.append(
            paired["pairwise_gcd"] / paired["gcd_indexed"]
        )
        paired_disabled_speedups.append(
            paired["filter_disabled"] / paired["gcd_indexed"]
        )

    pairwise_ratio = (
        wall_summary["pairwise_gcd"]["median"]
        / wall_summary["gcd_indexed"]["median"]
    )
    disabled_ratio = (
        wall_summary["filter_disabled"]["median"]
        / wall_summary["gcd_indexed"]["median"]
    )
    payload = {
        "benchmark": "like_bremner_gcd_index_balanced",
        "domain": {
            "max_square_root": args.max_square_root,
            "bound_semantics": "racines des cases carrées, pas boîte complète",
            "primitive_only": True,
            "target_mask": "acdefgh",
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "repeats": args.repeats,
        "catalog_size": len(catalog),
        "catalog_seconds": catalog_seconds,
        "class_sets_equal": True,
        "classes": [list(grid) for grid in (class_reference or ())],
        "runs": rows,
        "wall_seconds": wall_summary,
        "cpu_seconds": cpu_summary,
        "pairwise_over_indexed_median_ratio": pairwise_ratio,
        "pairwise_to_indexed_reduction_percent": 100.0 * (1.0 - 1.0 / pairwise_ratio),
        "disabled_over_indexed_median_ratio": disabled_ratio,
        "disabled_to_indexed_reduction_percent": 100.0 * (1.0 - 1.0 / disabled_ratio),
        "paired_pairwise_over_indexed": _summary(paired_pairwise_speedups),
        "paired_disabled_over_indexed": _summary(paired_disabled_speedups),
        "stats": stats_by_variant,
    }

    stem = f"like_bremner_gcd_index_r{args.max_square_root}"
    json_out = args.json_out or (
        PROJECT_ROOT / "results" / "formulations_comparison" / "benchmarks" / f"{stem}.json"
    )
    csv_out = args.csv_out or (
        PROJECT_ROOT / "results" / "formulations_comparison" / "benchmarks" / f"{stem}.csv"
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(
        json.dumps(
            {
                "catalog_size": len(catalog),
                "class_count": len(class_reference or ()),
                "repeats": args.repeats,
                "pairwise_over_indexed_median_ratio": pairwise_ratio,
                "pairwise_to_indexed_reduction_percent": payload[
                    "pairwise_to_indexed_reduction_percent"
                ],
                "disabled_over_indexed_median_ratio": disabled_ratio,
                "disabled_to_indexed_reduction_percent": payload[
                    "disabled_to_indexed_reduction_percent"
                ],
                "json": str(json_out),
                "csv": str(csv_out),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
