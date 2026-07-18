"""Benchmark bout-en-bout du catalogue matériel contre le catalogue en flux."""

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
import tracemalloc
from collections.abc import Callable

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.like_bremner_indexed import (  # noqa: E402
    search_like_bremner_indexed,
    search_like_bremner_indexed_groups,
)
from prototypes.model import generate_square_progressions_parametric  # noqa: E402
from prototypes.streaming_progressions import (  # noqa: E402
    ParametricProgressionGroupStream,
)


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "maximum": max(values),
        "sample_standard_deviation": statistics.stdev(values),
    }


def _timed(function: Callable[[], tuple[object, dict[str, int]]]) -> tuple[float, float, object, dict[str, int]]:
    gc.collect()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    result, catalog_stats = function()
    return (
        time.perf_counter() - wall_start,
        time.process_time() - cpu_start,
        result,
        catalog_stats,
    )


def _memory(function: Callable[[], tuple[object, dict[str, int]]]) -> tuple[int, object, dict[str, int]]:
    gc.collect()
    tracemalloc.start()
    result, catalog_stats = function()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, result, catalog_stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-square-root",
        "--max-root",
        dest="max_square_root",
        type=int,
        default=100_000,
    )
    parser.add_argument("--timing-repeats", type=int, default=6)
    parser.add_argument("--shard-count", type=int, default=64)
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()
    if args.timing_repeats < 2 or args.timing_repeats % 2:
        parser.error("--timing-repeats doit être un entier pair au moins égal à 2")

    def material() -> tuple[object, dict[str, int]]:
        catalog = generate_square_progressions_parametric(args.max_square_root)
        result = search_like_bremner_indexed(
            args.max_square_root,
            progressions=catalog,
        )
        return result, {"unique_progressions": len(catalog)}

    def streaming() -> tuple[object, dict[str, int]]:
        stream = ParametricProgressionGroupStream(
            args.max_square_root,
            shard_count=args.shard_count,
            temp_dir=args.temp_dir,
        )
        result = search_like_bremner_indexed_groups(
            args.max_square_root,
            stream,
        )
        return result, dict(stream.stats)

    variants: tuple[tuple[str, Callable[[], tuple[object, dict[str, int]]]], ...] = (
        ("material", material),
        ("streaming", streaming),
    )
    warm_bound = min(args.max_square_root, 2000)
    warm_catalog = generate_square_progressions_parametric(warm_bound)
    search_like_bremner_indexed(warm_bound, progressions=warm_catalog)

    rows: list[dict[str, object]] = []
    class_reference = None
    search_stats: dict[str, dict[str, int]] = {}
    catalog_stats: dict[str, dict[str, int]] = {}
    for run in range(1, args.timing_repeats + 1):
        order = variants if run % 2 else tuple(reversed(variants))
        for order_index, (variant, function) in enumerate(order, start=1):
            wall, cpu, result, current_catalog_stats = _timed(function)
            if class_reference is None:
                class_reference = result.classes
            elif result.classes != class_reference:
                raise RuntimeError("Le flux et le catalogue matériel divergent.")
            current_search_stats = dict(result.stats)
            previous_search = search_stats.setdefault(variant, current_search_stats)
            previous_catalog = catalog_stats.setdefault(variant, current_catalog_stats)
            if previous_search != current_search_stats:
                raise RuntimeError("Les compteurs de recherche ne sont pas stables.")
            if previous_catalog != current_catalog_stats:
                raise RuntimeError("Les compteurs de catalogue ne sont pas stables.")
            rows.append(
                {
                    "run": run,
                    "order_index": order_index,
                    "variant": variant,
                    "wall_seconds": wall,
                    "cpu_seconds": cpu,
                    "class_count": len(result.classes),
                }
            )

    memory: dict[str, int] = {}
    for variant, function in variants:
        peak, result, current_catalog_stats = _memory(function)
        if result.classes != class_reference:
            raise RuntimeError("La mesure mémoire a changé l'ensemble des classes.")
        if current_catalog_stats != catalog_stats[variant]:
            raise RuntimeError("La mesure mémoire a changé le catalogue.")
        memory[variant] = peak

    names = tuple(name for name, _ in variants)
    wall_summary = {
        name: _summary(
            [float(row["wall_seconds"]) for row in rows if row["variant"] == name]
        )
        for name in names
    }
    cpu_summary = {
        name: _summary(
            [float(row["cpu_seconds"]) for row in rows if row["variant"] == name]
        )
        for name in names
    }
    wall_ratio = wall_summary["streaming"]["median"] / wall_summary["material"]["median"]
    memory_ratio = memory["streaming"] / memory["material"]
    payload = {
        "benchmark": "like_bremner_material_vs_streaming_end_to_end",
        "domain": {
            "max_square_root": args.max_square_root,
            "primitive_only": True,
            "target_mask": "acdefgh",
            "shard_count": args.shard_count,
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "timing_repeats": args.timing_repeats,
        "class_sets_equal": True,
        "classes": [list(grid) for grid in (class_reference or ())],
        "runs": rows,
        "wall_seconds": wall_summary,
        "cpu_seconds": cpu_summary,
        "streaming_over_material_wall_ratio": wall_ratio,
        "streaming_wall_change_percent": 100.0 * (wall_ratio - 1.0),
        "python_peak_bytes": memory,
        "streaming_over_material_memory_ratio": memory_ratio,
        "streaming_memory_reduction_percent": 100.0 * (1.0 - memory_ratio),
        "catalog_stats": catalog_stats,
        "search_stats": search_stats,
    }

    stem = f"like_bremner_streaming_r{args.max_square_root}"
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
                "class_count": len(class_reference or ()),
                "timing_repeats": args.timing_repeats,
                "streaming_wall_change_percent": payload["streaming_wall_change_percent"],
                "streaming_memory_reduction_percent": payload[
                    "streaming_memory_reduction_percent"
                ],
                "python_peak_bytes": memory,
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
