"""Compare les domaines paramétriques historique et canonique, en RAM et en flux."""

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
    CanonicalParametricProgressionGroupStream,
    generate_square_progressions_parametric_canonical,
)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-square-root", "--max-root", dest="max_square_root", type=int, default=100_000)
    parser.add_argument("--repeats", type=int, default=4)
    parser.add_argument("--shard-count", type=int, default=64)
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()
    if args.repeats < 4 or args.repeats % 4:
        parser.error("--repeats doit être un multiple de 4, au moins égal à 4")

    def material_historical() -> tuple[object, dict[str, int]]:
        catalog = generate_square_progressions_parametric(args.max_square_root)
        return search_like_bremner_indexed(args.max_square_root, progressions=catalog), {"raw_records": 4 * len(catalog), "unique_progressions": len(catalog)}

    def material_canonical() -> tuple[object, dict[str, int]]:
        catalog = generate_square_progressions_parametric_canonical(args.max_square_root)
        return search_like_bremner_indexed(args.max_square_root, progressions=catalog), {"raw_records": len(catalog), "unique_progressions": len(catalog)}

    def streaming_historical() -> tuple[object, dict[str, int]]:
        stream = ParametricProgressionGroupStream(args.max_square_root, shard_count=args.shard_count, temp_dir=args.temp_dir)
        result = search_like_bremner_indexed_groups(args.max_square_root, stream)
        return result, dict(stream.stats)

    def streaming_canonical() -> tuple[object, dict[str, int]]:
        stream = CanonicalParametricProgressionGroupStream(args.max_square_root, shard_count=args.shard_count, temp_dir=args.temp_dir)
        result = search_like_bremner_indexed_groups(args.max_square_root, stream)
        return result, dict(stream.stats)

    variants: tuple[tuple[str, Callable[[], tuple[object, dict[str, int]]]], ...] = (
        ("material_historical", material_historical),
        ("material_canonical", material_canonical),
        ("streaming_historical", streaming_historical),
        ("streaming_canonical", streaming_canonical),
    )
    rows: list[dict[str, object]] = []
    class_reference = None
    search_stats: dict[str, dict[str, int]] = {}
    catalog_stats: dict[str, dict[str, int]] = {}
    for run in range(1, args.repeats + 1):
        shift = (run - 1) % 4
        order = variants[shift:] + variants[:shift]
        for order_index, (variant, function) in enumerate(order, start=1):
            gc.collect()
            cpu_start = time.process_time()
            wall_start = time.perf_counter()
            result, current_catalog_stats = function()
            wall = time.perf_counter() - wall_start
            cpu = time.process_time() - cpu_start
            if class_reference is None:
                class_reference = result.classes
            elif result.classes != class_reference:
                raise RuntimeError("Un catalogue a changé l'ensemble des classes.")
            current_search_stats = dict(result.stats)
            if search_stats.setdefault(variant, current_search_stats) != current_search_stats:
                raise RuntimeError("Les compteurs de recherche varient.")
            if catalog_stats.setdefault(variant, current_catalog_stats) != current_catalog_stats:
                raise RuntimeError("Les compteurs de catalogue varient.")
            rows.append({"run": run, "order_index": order_index, "variant": variant, "wall_seconds": wall, "cpu_seconds": cpu, "class_count": len(result.classes)})

    peaks: dict[str, int] = {}
    for variant, function in variants:
        gc.collect()
        tracemalloc.start()
        result, current_catalog_stats = function()
        _, peaks[variant] = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if result.classes != class_reference or current_catalog_stats != catalog_stats[variant]:
            raise RuntimeError("La mesure mémoire a modifié le résultat.")

    names = tuple(name for name, _ in variants)
    wall = {name: _summary([float(row["wall_seconds"]) for row in rows if row["variant"] == name]) for name in names}
    cpu = {name: _summary([float(row["cpu_seconds"]) for row in rows if row["variant"] == name]) for name in names}
    material_ratio = wall["material_historical"]["median"] / wall["material_canonical"]["median"]
    streaming_ratio = wall["streaming_historical"]["median"] / wall["streaming_canonical"]["median"]
    payload = {
        "benchmark": "like_bremner_canonical_parameter_domain",
        "domain": {"max_square_root": args.max_square_root, "shard_count": args.shard_count, "target_mask": "acdefgh"},
        "repeats": args.repeats,
        "class_sets_equal": True,
        "classes": [list(grid) for grid in (class_reference or ())],
        "runs": rows,
        "wall_seconds": wall,
        "cpu_seconds": cpu,
        "python_peak_bytes": peaks,
        "material_historical_over_canonical_ratio": material_ratio,
        "material_canonical_reduction_percent": 100.0 * (1.0 - 1.0 / material_ratio),
        "streaming_historical_over_canonical_ratio": streaming_ratio,
        "streaming_canonical_reduction_percent": 100.0 * (1.0 - 1.0 / streaming_ratio),
        "catalog_stats": catalog_stats,
        "search_stats": search_stats,
    }
    stem = f"like_bremner_canonical_catalog_r{args.max_square_root}"
    json_out = args.json_out or PROJECT_ROOT / "results" / "formulations_comparison" / "benchmarks" / f"{stem}.json"
    csv_out = args.csv_out or PROJECT_ROOT / "results" / "formulations_comparison" / "benchmarks" / f"{stem}.csv"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "class_count": len(class_reference or ()),
        "material_canonical_reduction_percent": payload["material_canonical_reduction_percent"],
        "streaming_canonical_reduction_percent": payload["streaming_canonical_reduction_percent"],
        "python_peak_bytes": peaks,
        "json": str(json_out),
        "csv": str(csv_out),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
