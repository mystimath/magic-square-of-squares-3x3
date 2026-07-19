"""Compare les tailles de tampon des handles persistants B13."""

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


def _ordered_values(
    values: tuple[int, ...],
    repetition: int,
) -> tuple[int, ...]:
    offset = ((repetition - 1) // 2) % len(values)
    rotated = values[offset:] + values[:offset]
    return rotated if repetition % 2 else tuple(reversed(rotated))


def _worker(
    max_root: int,
    shard_count: int,
    encoded_buffering: int,
    temp_dir: pathlib.Path | None,
) -> int:
    buffering = None if encoded_buffering == -1 else encoded_buffering
    baseline = _memory_info()
    started = time.perf_counter()
    result, stream_stats = _run(
        max_root,
        shard_count,
        temp_dir,
        None,
        None,
        buffering,
    )
    seconds = time.perf_counter() - started
    final = _memory_info()
    print(
        json.dumps(
            {
                "max_square_root": max_root,
                "shard_count": shard_count,
                "write_handle_buffering": encoded_buffering,
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
    encoded_buffering: int,
    temp_dir: pathlib.Path | None,
) -> dict[str, object]:
    command = [
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "--max-root",
        str(max_root),
        "--shard-count",
        str(shard_count),
        "--worker-handle-buffering",
        str(encoded_buffering),
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
    parser.add_argument("--shard-count", type=int, default=512)
    parser.add_argument(
        "--bufferings",
        type=int,
        nargs="+",
        default=(-1, 0, 256, 512, 1024, 2048, 4096, 8192),
        help="-1 désigne le buffering implicite du témoin",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    parser.add_argument(
        "--worker-handle-buffering",
        type=int,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.worker_handle_buffering is not None:
        return _worker(
            args.max_root,
            args.shard_count,
            args.worker_handle_buffering,
            args.temp_dir,
        )

    values = tuple(args.bufferings)
    if args.max_root < 1 or args.shard_count < 1:
        parser.error("la borne et le nombre de shards doivent être positifs")
    if args.repeats < 2:
        parser.error("--repeats doit être au moins 2")
    if any(value < -1 or value == 1 for value in values):
        parser.error("--bufferings exige -1, zéro ou au moins deux")
    if len(set(values)) != len(values):
        parser.error("--bufferings ne doit pas contenir de doublon")

    warm_root = min(args.max_root, 10_000)
    _invoke_worker(warm_root, args.shard_count, -1, args.temp_dir)
    records: list[dict[str, object]] = []
    latest_stream_stats: dict[int, dict[str, int]] = {}
    reference_classes = None
    reference_search_stats = None
    reference_coverage = None
    for repetition in range(1, args.repeats + 1):
        order = _ordered_values(values, repetition)
        for order_index, buffering in enumerate(order, start=1):
            record = _invoke_worker(
                args.max_root,
                args.shard_count,
                buffering,
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
                        f"Classes divergentes avec buffering={buffering}."
                    )
                if record["search_stats"] != reference_search_stats:
                    raise AssertionError(
                        f"Compteurs divergents avec buffering={buffering}."
                    )
                if coverage != reference_coverage:
                    raise AssertionError(
                        f"Couverture divergente avec buffering={buffering}."
                    )
            stream_stats = record["stream_stats"]
            previous = latest_stream_stats.get(buffering)
            if previous is not None and stream_stats != previous:
                raise AssertionError(
                    f"Statistiques E/S instables avec buffering={buffering}."
                )
            latest_stream_stats[buffering] = stream_stats
            records.append(
                {
                    "repetition": repetition,
                    "order_index": order_index,
                    **record,
                }
            )

    summaries: dict[str, object] = {}
    for buffering in values:
        selected = [
            record
            for record in records
            if record["write_handle_buffering"] == buffering
        ]
        seconds = [float(record["seconds"]) for record in selected]
        peaks = [
            int(record["peak_working_set_bytes"])
            for record in selected
        ]
        summaries[str(buffering)] = {
            "label": "default" if buffering == -1 else str(buffering),
            "seconds": seconds,
            "median_seconds": statistics.median(seconds),
            "min_seconds": min(seconds),
            "max_seconds": max(seconds),
            "peak_working_set_bytes": peaks,
            "median_peak_working_set_bytes": statistics.median(peaks),
            "stream_stats": latest_stream_stats[buffering],
        }

    fastest = min(
        values,
        key=lambda value: summaries[str(value)]["median_seconds"],
    )
    lowest_peak = min(
        values,
        key=lambda value: summaries[str(value)][
            "median_peak_working_set_bytes"
        ],
    )
    payload = {
        "benchmark": "B13 persistent handle buffer sizing",
        "max_square_root": args.max_root,
        "complete_box_upper_value": args.max_root**2,
        "shard_count": args.shard_count,
        "bufferings": list(values),
        "minus_one_means": "platform default buffering",
        "repeats": args.repeats,
        "warmup_max_square_root": warm_root,
        "timing_order": [
            list(_ordered_values(values, repetition))
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
        "fastest_buffering": fastest,
        "lowest_peak_buffering": lowest_peak,
    }

    stem = (
        f"lo_shu_b6_handle_buffering_shards{args.shard_count}"
        f"_r{args.max_root}"
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
        "write_handle_buffering",
        "seconds",
        "baseline_working_set_bytes",
        "peak_working_set_bytes",
        "peak_pagefile_bytes",
        "final_private_bytes",
    )
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {key: record[key] for key in fieldnames}
            for record in records
        )

    print(
        json.dumps(
            {
                "max_square_root": args.max_root,
                "shard_count": args.shard_count,
                "class_count": len(reference_classes or ()),
                "fastest_buffering": fastest,
                "lowest_peak_buffering": lowest_peak,
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
