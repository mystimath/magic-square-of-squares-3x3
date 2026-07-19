"""Compare le cache LRU borné des handles de shards au témoin non borné."""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import statistics
import subprocess
import sys
import time


PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from benchmark_incidence_shard_rss import _memory_info  # noqa: E402
from benchmark_incidence_shard_tradeoff import _run  # noqa: E402


_COVERAGE_KEYS = (
    "progressions",
    "raw_incidence_records",
    "shards_used",
    "duplicate_incidence_records",
    "max_incidence_records_in_shard",
    "indexed_square_values",
)


def _ordered_limits(
    limits: tuple[int, ...],
    repetition: int,
) -> tuple[int, ...]:
    offset = ((repetition - 1) // 2) % len(limits)
    rotated = limits[offset:] + limits[:offset]
    return rotated if repetition % 2 else tuple(reversed(rotated))


def _worker(
    max_root: int,
    shard_count: int,
    encoded_limit: int,
    temp_dir: pathlib.Path | None,
) -> int:
    limit = None if encoded_limit == 0 else encoded_limit
    baseline = _memory_info()
    started = time.perf_counter()
    result, stream_stats = _run(
        max_root,
        shard_count,
        temp_dir,
        limit,
    )
    seconds = time.perf_counter() - started
    final = _memory_info()
    print(
        json.dumps(
            {
                "max_square_root": max_root,
                "shard_count": shard_count,
                "max_open_shard_handles": limit,
                "seconds": seconds,
                "class_count": len(result.classes),
                "classes": [list(grid) for grid in result.classes],
                "search_stats": result.stats,
                "stream_stats": stream_stats,
                "baseline_working_set_bytes": baseline.working_set_size,
                "peak_working_set_bytes": final.peak_working_set_size,
                "peak_pagefile_bytes": final.peak_pagefile_usage,
                "final_private_bytes": final.private_usage,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _invoke_worker(
    max_root: int,
    shard_count: int,
    encoded_limit: int,
    temp_dir: pathlib.Path | None,
) -> dict[str, object]:
    command = [
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "--max-root",
        str(max_root),
        "--shard-count",
        str(shard_count),
        "--worker-handle-limit",
        str(encoded_limit),
    ]
    if temp_dir is not None:
        command.extend(("--temp-dir", str(temp_dir)))
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-root", type=int, default=100_000)
    parser.add_argument("--shard-count", type=int, default=256)
    parser.add_argument(
        "--handle-limits",
        type=int,
        nargs="+",
        default=(0, 16, 32, 64, 128),
        help="0 désigne le témoin non borné",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    parser.add_argument(
        "--worker-handle-limit",
        type=int,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.worker_handle_limit is not None:
        return _worker(
            args.max_root,
            args.shard_count,
            args.worker_handle_limit,
            args.temp_dir,
        )

    limits = tuple(args.handle_limits)
    if args.max_root < 1:
        parser.error("--max-root doit être strictement positif")
    if args.shard_count < 1:
        parser.error("--shard-count doit être strictement positif")
    if args.repeats < 2:
        parser.error("--repeats doit être au moins 2")
    if any(limit < 0 for limit in limits):
        parser.error("--handle-limits exige 0 ou des entiers positifs")
    if len(set(limits)) != len(limits):
        parser.error("--handle-limits ne doit pas contenir de doublon")

    records: list[dict[str, object]] = []
    latest_stream_stats: dict[int, dict[str, int]] = {}
    reference_classes = None
    reference_search_stats = None
    reference_coverage = None
    warm_root = min(args.max_root, 10_000)
    _invoke_worker(
        warm_root,
        args.shard_count,
        0,
        args.temp_dir,
    )
    for repetition in range(1, args.repeats + 1):
        order = _ordered_limits(limits, repetition)
        for order_index, encoded_limit in enumerate(order, start=1):
            record = _invoke_worker(
                args.max_root,
                args.shard_count,
                encoded_limit,
                args.temp_dir,
            )
            coverage = {
                key: record["stream_stats"][key]
                for key in _COVERAGE_KEYS
            }
            if reference_classes is None:
                reference_classes = record["classes"]
                reference_search_stats = record["search_stats"]
                reference_coverage = coverage
            else:
                if record["classes"] != reference_classes:
                    raise AssertionError(
                        f"Classes divergentes avec la limite {encoded_limit}."
                    )
                if record["search_stats"] != reference_search_stats:
                    raise AssertionError(
                        f"Compteurs divergents avec la limite {encoded_limit}."
                    )
                if coverage != reference_coverage:
                    raise AssertionError(
                        "Couverture du flux divergente avec la limite "
                        f"{encoded_limit}."
                    )
            stream_stats = record["stream_stats"]
            previous = latest_stream_stats.get(encoded_limit)
            if previous is not None and stream_stats != previous:
                raise AssertionError(
                    f"Statistiques E/S instables avec la limite {encoded_limit}."
                )
            latest_stream_stats[encoded_limit] = stream_stats
            records.append(
                {
                    "repetition": repetition,
                    "order_index": order_index,
                    **record,
                }
            )

    summaries: dict[str, object] = {}
    for encoded_limit in limits:
        selected = [
            record
            for record in records
            if (record["max_open_shard_handles"] or 0) == encoded_limit
        ]
        seconds = [float(record["seconds"]) for record in selected]
        peaks = [
            int(record["peak_working_set_bytes"])
            for record in selected
        ]
        increments = [
            int(record["peak_working_set_bytes"])
            - int(record["baseline_working_set_bytes"])
            for record in selected
        ]
        summaries[str(encoded_limit)] = {
            "label": "unbounded" if encoded_limit == 0 else str(encoded_limit),
            "seconds": seconds,
            "median_seconds": statistics.median(seconds),
            "min_seconds": min(seconds),
            "max_seconds": max(seconds),
            "peak_working_set_bytes": peaks,
            "median_peak_working_set_bytes": statistics.median(peaks),
            "median_incremental_peak_bytes": statistics.median(increments),
            "stream_stats": latest_stream_stats[encoded_limit],
        }

    fastest = min(
        limits,
        key=lambda limit: summaries[str(limit)]["median_seconds"],
    )
    lowest_peak = min(
        limits,
        key=lambda limit: summaries[str(limit)][
            "median_peak_working_set_bytes"
        ],
    )
    payload = {
        "benchmark": "B12 bounded LRU shard handle cache",
        "max_square_root": args.max_root,
        "complete_box_upper_value": args.max_root**2,
        "shard_count": args.shard_count,
        "handle_limits": list(limits),
        "zero_limit_means": "unbounded",
        "repeats": args.repeats,
        "warmup_max_square_root": warm_root,
        "timing_order": [
            list(_ordered_limits(limits, repetition))
            for repetition in range(1, args.repeats + 1)
        ],
        "rss_measurement": "isolated Windows peak working set",
        "all_classes_equal": True,
        "all_search_stats_equal": True,
        "all_coverage_stats_equal": True,
        "class_count": len(reference_classes or ()),
        "classes": reference_classes or [],
        "search_stats": reference_search_stats,
        "coverage_stats": reference_coverage,
        "records": records,
        "summaries": summaries,
        "fastest_handle_limit": fastest,
        "lowest_peak_handle_limit": lowest_peak,
    }

    stem = (
        f"lo_shu_b6_handle_lru_shards{args.shard_count}_r{args.max_root}"
    )
    output_dir = (
        PROJECT_ROOT
        / "results"
        / "formulations_comparison"
        / "benchmarks"
    )
    json_out = args.json_out or output_dir / f"{stem}.json"
    csv_out = args.csv_out or output_dir / f"{stem}.csv"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    fieldnames = (
        "repetition",
        "order_index",
        "max_open_shard_handles",
        "seconds",
        "baseline_working_set_bytes",
        "peak_working_set_bytes",
        "peak_pagefile_bytes",
        "final_private_bytes",
        "write_handle_opens",
        "write_handle_evictions",
        "max_open_write_handles",
    )
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    **{key: record[key] for key in fieldnames[:8]},
                    **{
                        key: record["stream_stats"][key]
                        for key in fieldnames[8:]
                    },
                }
            )

    print(
        json.dumps(
            {
                "max_square_root": args.max_root,
                "shard_count": args.shard_count,
                "class_count": len(reference_classes or ()),
                "fastest_handle_limit": fastest,
                "lowest_peak_handle_limit": lowest_peak,
                "summaries": summaries,
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
