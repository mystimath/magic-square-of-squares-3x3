"""Benchmark B4 multi-masque contre B3 ciblé sur un catalogue partagé."""

from __future__ import annotations

import argparse
import csv
import gc
import json
import pathlib
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes.like_bremner_indexed import (  # noqa: E402
    search_like_bremner_indexed_box,
)
from prototypes.lo_shu_seven import search_lo_shu_seven_box  # noqa: E402


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "maximum": max(values),
        "sample_standard_deviation": statistics.stdev(values)
        if len(values) > 1
        else 0.0,
    }


def _measure(function: Callable[[], object]) -> tuple[float, float, object]:
    gc.collect()
    cpu_started = time.process_time()
    wall_started = time.perf_counter()
    result = function()
    return (
        time.perf_counter() - wall_started,
        time.process_time() - cpu_started,
        result,
    )


def _peak(function: Callable[[], object]) -> tuple[int, object]:
    gc.collect()
    tracemalloc.start()
    result = function()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-square-root", type=int, default=100_000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error("--repeats doit être au moins 2")

    catalog_wall, catalog_cpu, catalog_object = _measure(
        lambda: generate_square_progressions_parametric_canonical(
            args.max_square_root
        )
    )
    catalog = catalog_object
    assert isinstance(catalog, tuple)
    functions = {
        "b3_bremner_mask": lambda: search_like_bremner_indexed_box(
            args.max_square_root,
            progressions=catalog,
        ),
        "b4_all_exact7_masks": lambda: search_lo_shu_seven_box(
            args.max_square_root,
            progressions=catalog,
        ),
    }
    rows: list[dict[str, object]] = []
    latest: dict[str, object] = {}
    names = tuple(functions)
    for run in range(1, args.repeats + 1):
        order = names if run % 2 else tuple(reversed(names))
        for order_index, name in enumerate(order, start=1):
            wall, cpu, result = _measure(functions[name])
            latest[name] = result
            rows.append(
                {
                    "run": run,
                    "order_index": order_index,
                    "engine": name,
                    "wall_seconds": wall,
                    "cpu_seconds": cpu,
                    "class_count": len(result.classes),
                }
            )

    peaks: dict[str, int] = {}
    for name in names:
        peak, result = _peak(functions[name])
        peaks[name] = peak
        latest[name] = result

    b3 = latest["b3_bremner_mask"]
    b4 = latest["b4_all_exact7_masks"]
    if not set(b3.classes) <= set(b4.classes):
        raise RuntimeError("B4 ne contient pas toutes les classes de B3.")

    wall_seconds = {
        name: _summary(
            [
                float(row["wall_seconds"])
                for row in rows
                if row["engine"] == name
            ]
        )
        for name in names
    }
    cpu_seconds = {
        name: _summary(
            [
                float(row["cpu_seconds"])
                for row in rows
                if row["engine"] == name
            ]
        )
        for name in names
    }
    coverage_cost_ratio = (
        wall_seconds["b4_all_exact7_masks"]["median"]
        / wall_seconds["b3_bremner_mask"]["median"]
    )
    payload = {
        "benchmark": "lo_shu_b4_all_exact7_masks_vs_b3_bremner",
        "domain": {
            "max_square_root": args.max_square_root,
            "complete_box": True,
            "exact_square_count": 7,
            "primitive_only": True,
            "equivalence": "D4",
        },
        "repeats": args.repeats,
        "catalog": {
            "progressions": len(catalog),
            "wall_seconds": catalog_wall,
            "cpu_seconds": catalog_cpu,
        },
        "runs": rows,
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "python_peak_incremental_bytes": peaks,
        "b4_over_b3_median_wall_ratio": coverage_cost_ratio,
        "b3_classes_subset_of_b4": True,
        "b3_classes": [list(grid) for grid in b3.classes],
        "b4_classes": [list(grid) for grid in b4.classes],
        "b4_orbit_class_counts": b4.orbit_class_counts,
        "b3_stats": b3.stats,
        "b4_stats": b4.stats,
    }
    stem = f"lo_shu_b4_vs_b3_r{args.max_square_root}"
    json_out = (
        args.json_out
        or PROJECT_ROOT
        / "results"
        / "formulations_comparison"
        / "benchmarks"
        / f"{stem}.json"
    )
    csv_out = (
        args.csv_out
        or PROJECT_ROOT
        / "results"
        / "formulations_comparison"
        / "benchmarks"
        / f"{stem}.csv"
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
                "b3_class_count": len(b3.classes),
                "b4_class_count": len(b4.classes),
                "b4_orbit_class_counts": b4.orbit_class_counts,
                "b4_over_b3_median_wall_ratio": coverage_cost_ratio,
                "python_peak_incremental_bytes": peaks,
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
