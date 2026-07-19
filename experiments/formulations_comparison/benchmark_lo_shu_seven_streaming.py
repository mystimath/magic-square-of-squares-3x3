"""Benchmark bout-en-bout du catalogue B4 matériel contre le flux par incidences."""

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
from dataclasses import dataclass

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes.lo_shu_seven import (  # noqa: E402
    LoShuSevenSearchResult,
    search_lo_shu_seven_box,
)
from prototypes.lo_shu_seven_grouped import (  # noqa: E402
    search_lo_shu_seven_incidence_groups,
)
from prototypes.streaming_seven_incidences import (  # noqa: E402
    CanonicalProgressionIncidenceStream,
)


@dataclass(frozen=True)
class Outcome:
    result: LoShuSevenSearchResult
    catalog_stats: dict[str, int]


def _material(max_root: int) -> Outcome:
    catalog = generate_square_progressions_parametric_canonical(max_root)
    result = search_lo_shu_seven_box(max_root, progressions=catalog)
    return Outcome(result, {"progressions": len(catalog)})


def _streaming(max_root: int, shard_count: int) -> Outcome:
    stream = CanonicalProgressionIncidenceStream(
        max_root,
        shard_count=shard_count,
    )
    result = search_lo_shu_seven_incidence_groups(
        max_root,
        stream,
        validate_incidence_groups=False,
    )
    return Outcome(result, dict(stream.stats))


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


def _measure(function: Callable[[], Outcome]) -> tuple[float, float, Outcome]:
    gc.collect()
    cpu_started = time.process_time()
    wall_started = time.perf_counter()
    result = function()
    return (
        time.perf_counter() - wall_started,
        time.process_time() - cpu_started,
        result,
    )


def _peak(function: Callable[[], Outcome]) -> tuple[int, Outcome]:
    gc.collect()
    tracemalloc.start()
    outcome = function()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak, outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-square-root", type=int, default=100_000)
    parser.add_argument("--shard-count", type=int, default=128)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()
    if args.repeats < 2:
        parser.error("--repeats doit être au moins 2")

    functions = {
        "material": lambda: _material(args.max_square_root),
        "streaming": lambda: _streaming(
            args.max_square_root,
            args.shard_count,
        ),
    }
    names = tuple(functions)
    rows: list[dict[str, object]] = []
    latest: dict[str, Outcome] = {}
    for run in range(1, args.repeats + 1):
        order = names if run % 2 else tuple(reversed(names))
        for order_index, name in enumerate(order, start=1):
            wall, cpu, outcome = _measure(functions[name])
            latest[name] = outcome
            rows.append(
                {
                    "run": run,
                    "order_index": order_index,
                    "variant": name,
                    "wall_seconds": wall,
                    "cpu_seconds": cpu,
                    "class_count": len(outcome.result.classes),
                }
            )

    peaks: dict[str, int] = {}
    for name in names:
        peak, outcome = _peak(functions[name])
        peaks[name] = peak
        latest[name] = outcome

    material = latest["material"]
    streaming = latest["streaming"]
    if material.result.classes != streaming.result.classes:
        raise RuntimeError("Les classes B4 matérielles et streaming diffèrent.")
    if material.result.stats != streaming.result.stats:
        raise RuntimeError("Les compteurs B4 matériels et streaming diffèrent.")

    wall_seconds = {
        name: _summary(
            [
                float(row["wall_seconds"])
                for row in rows
                if row["variant"] == name
            ]
        )
        for name in names
    }
    cpu_seconds = {
        name: _summary(
            [
                float(row["cpu_seconds"])
                for row in rows
                if row["variant"] == name
            ]
        )
        for name in names
    }
    memory_reduction = 100.0 * (1.0 - peaks["streaming"] / peaks["material"])
    wall_overhead = 100.0 * (
        wall_seconds["streaming"]["median"]
        / wall_seconds["material"]["median"]
        - 1.0
    )
    payload = {
        "benchmark": "lo_shu_b4_material_vs_streaming_incidences",
        "domain": {
            "max_square_root": args.max_square_root,
            "shard_count": args.shard_count,
            "complete_box": True,
            "exact_square_count": 7,
            "primitive_only": True,
            "equivalence": "D4",
        },
        "repeats": args.repeats,
        "class_sets_equal": True,
        "classes": [list(grid) for grid in material.result.classes],
        "orbit_class_counts": material.result.orbit_class_counts,
        "runs": rows,
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "python_peak_bytes": peaks,
        "streaming_memory_reduction_percent": memory_reduction,
        "streaming_wall_overhead_percent": wall_overhead,
        "catalog_stats": {
            "material": material.catalog_stats,
            "streaming": streaming.catalog_stats,
        },
        "search_stats": material.result.stats,
    }
    stem = f"lo_shu_b4_streaming_r{args.max_square_root}"
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
                "class_count": len(material.result.classes),
                "orbit_class_counts": material.result.orbit_class_counts,
                "streaming_memory_reduction_percent": memory_reduction,
                "streaming_wall_overhead_percent": wall_overhead,
                "python_peak_bytes": peaks,
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
