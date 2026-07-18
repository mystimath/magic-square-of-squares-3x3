"""Benchmark apparié du filtre précoce de primitivité like-Bremner."""

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

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.like_bremner import search_like_bremner  # noqa: E402
from prototypes.model import generate_square_progressions_parametric  # noqa: E402


def _measure(
    max_square_root: int,
    catalog: tuple[object, ...],
    *,
    early_filter: bool,
) -> tuple[dict[str, object], object]:
    gc.collect()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    result = search_like_bremner(
        max_square_root,
        primitive_only=True,
        progressions=catalog,
        early_primitive_filter=early_filter,
    )
    return (
        {
            "wall_seconds": time.perf_counter() - wall_start,
            "cpu_seconds": time.process_time() - cpu_start,
        },
        result,
    )


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "maximum": max(values),
        "sample_standard_deviation": statistics.stdev(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-square-root",
        "--max-root",
        dest="max_square_root",
        type=int,
        default=100_000,
        help="borne des racines des cases carrées (défaut: 100000)",
    )
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()
    if args.repeats < 3:
        parser.error("--repeats doit valoir au moins 3")

    catalog_start = time.perf_counter()
    catalog = generate_square_progressions_parametric(args.max_square_root)
    catalog_seconds = time.perf_counter() - catalog_start

    # Petit échauffement indépendant du domaine mesuré.
    warm_catalog = generate_square_progressions_parametric(min(args.max_square_root, 2000))
    search_like_bremner(
        min(args.max_square_root, 2000),
        progressions=warm_catalog,
        early_primitive_filter=True,
    )
    search_like_bremner(
        min(args.max_square_root, 2000),
        progressions=warm_catalog,
        early_primitive_filter=False,
    )

    rows: list[dict[str, object]] = []
    class_reference = None
    stats_by_variant: dict[str, dict[str, int]] = {}
    for run in range(1, args.repeats + 1):
        order = (("filtered", True), ("legacy", False))
        if run % 2 == 0:
            order = tuple(reversed(order))
        for order_index, (variant, enabled) in enumerate(order, start=1):
            timing, result = _measure(
                args.max_square_root,
                catalog,
                early_filter=enabled,
            )
            if class_reference is None:
                class_reference = result.classes
            elif result.classes != class_reference:
                raise RuntimeError("Le filtre a changé l'ensemble des classes primitives.")
            current_stats = dict(result.stats)
            previous_stats = stats_by_variant.setdefault(variant, current_stats)
            if current_stats != previous_stats:
                raise RuntimeError("Les compteurs varient entre répétitions identiques.")
            rows.append(
                {
                    "run": run,
                    "order_index": order_index,
                    "variant": variant,
                    "early_primitive_filter": enabled,
                    "wall_seconds": timing["wall_seconds"],
                    "cpu_seconds": timing["cpu_seconds"],
                    "class_count": len(result.classes),
                }
            )

    wall_by_variant = {
        variant: [
            float(row["wall_seconds"])
            for row in rows
            if row["variant"] == variant
        ]
        for variant in ("filtered", "legacy")
    }
    cpu_by_variant = {
        variant: [
            float(row["cpu_seconds"])
            for row in rows
            if row["variant"] == variant
        ]
        for variant in ("filtered", "legacy")
    }
    paired_speedups = []
    for run in range(1, args.repeats + 1):
        paired = {
            str(row["variant"]): float(row["wall_seconds"])
            for row in rows
            if row["run"] == run
        }
        paired_speedups.append(paired["legacy"] / paired["filtered"])

    wall_summary = {
        variant: _summary(values) for variant, values in wall_by_variant.items()
    }
    cpu_summary = {
        variant: _summary(values) for variant, values in cpu_by_variant.items()
    }
    median_ratio = (
        wall_summary["legacy"]["median"] / wall_summary["filtered"]["median"]
    )
    payload = {
        "benchmark": "like_bremner_early_primitive_filter_paired",
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
        "paired_speedups": paired_speedups,
        "paired_speedup_summary": _summary(paired_speedups),
        "median_wall_speedup": median_ratio,
        "median_wall_reduction_percent": 100.0 * (1.0 - 1.0 / median_ratio),
        "stats": stats_by_variant,
    }

    stem = f"like_bremner_primitive_filter_paired_r{args.max_square_root}"
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
                "median_wall_speedup": median_ratio,
                "median_wall_reduction_percent": payload[
                    "median_wall_reduction_percent"
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
