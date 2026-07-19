"""Compare les tampons LRU B13 au writer non borné des incidences."""

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


def _ordered_budgets(
    budgets: tuple[int, ...],
    repetition: int,
) -> tuple[int, ...]:
    offset = ((repetition - 1) // 2) % len(budgets)
    rotated = budgets[offset:] + budgets[:offset]
    return rotated if repetition % 2 else tuple(reversed(rotated))


def _worker(
    max_root: int,
    shard_count: int,
    encoded_budget: int,
    temp_dir: pathlib.Path | None,
) -> int:
    budget = None if encoded_budget == 0 else encoded_budget
    baseline = _memory_info()
    started = time.perf_counter()
    result, stream_stats = _run(
        max_root,
        shard_count,
        temp_dir,
        None,
        budget,
    )
    seconds = time.perf_counter() - started
    final = _memory_info()
    print(
        json.dumps(
            {
                "max_square_root": max_root,
                "shard_count": shard_count,
                "max_buffered_write_bytes": budget,
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
    encoded_budget: int,
    temp_dir: pathlib.Path | None,
) -> dict[str, object]:
    command = [
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "--max-root",
        str(max_root),
        "--shard-count",
        str(shard_count),
        "--worker-buffer-budget",
        str(encoded_budget),
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
        "--buffer-budgets",
        type=int,
        nargs="+",
        default=(0, 262_144, 524_288, 1_048_576, 2_097_152),
        help="0 désigne le writer non borné témoin",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    parser.add_argument(
        "--worker-buffer-budget",
        type=int,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.worker_buffer_budget is not None:
        return _worker(
            args.max_root,
            args.shard_count,
            args.worker_buffer_budget,
            args.temp_dir,
        )

    budgets = tuple(args.buffer_budgets)
    if args.max_root < 1:
        parser.error("--max-root doit être strictement positif")
    if args.shard_count < 1:
        parser.error("--shard-count doit être strictement positif")
    if args.repeats < 2:
        parser.error("--repeats doit être au moins 2")
    if any(budget != 0 and budget < 25 for budget in budgets):
        parser.error("--buffer-budgets exige 0 ou au moins 25 octets")
    if len(set(budgets)) != len(budgets):
        parser.error("--buffer-budgets ne doit pas contenir de doublon")

    warm_root = min(args.max_root, 10_000)
    _invoke_worker(warm_root, args.shard_count, 0, args.temp_dir)
    records: list[dict[str, object]] = []
    latest_stream_stats: dict[int, dict[str, int]] = {}
    reference_classes = None
    reference_search_stats = None
    reference_coverage = None
    for repetition in range(1, args.repeats + 1):
        order = _ordered_budgets(budgets, repetition)
        for order_index, encoded_budget in enumerate(order, start=1):
            record = _invoke_worker(
                args.max_root,
                args.shard_count,
                encoded_budget,
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
                        f"Classes divergentes avec le budget {encoded_budget}."
                    )
                if record["search_stats"] != reference_search_stats:
                    raise AssertionError(
                        f"Compteurs divergents avec le budget {encoded_budget}."
                    )
                if coverage != reference_coverage:
                    raise AssertionError(
                        f"Couverture divergente avec le budget {encoded_budget}."
                    )
            stream_stats = record["stream_stats"]
            previous = latest_stream_stats.get(encoded_budget)
            if previous is not None and stream_stats != previous:
                raise AssertionError(
                    f"Statistiques E/S instables au budget {encoded_budget}."
                )
            latest_stream_stats[encoded_budget] = stream_stats
            records.append(
                {
                    "repetition": repetition,
                    "order_index": order_index,
                    **record,
                }
            )

    summaries: dict[str, object] = {}
    for encoded_budget in budgets:
        selected = [
            record
            for record in records
            if (record["max_buffered_write_bytes"] or 0) == encoded_budget
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
        summaries[str(encoded_budget)] = {
            "label": (
                "unbounded"
                if encoded_budget == 0
                else str(encoded_budget)
            ),
            "seconds": seconds,
            "median_seconds": statistics.median(seconds),
            "min_seconds": min(seconds),
            "max_seconds": max(seconds),
            "peak_working_set_bytes": peaks,
            "median_peak_working_set_bytes": statistics.median(peaks),
            "median_incremental_peak_bytes": statistics.median(increments),
            "stream_stats": latest_stream_stats[encoded_budget],
        }

    fastest = min(
        budgets,
        key=lambda budget: summaries[str(budget)]["median_seconds"],
    )
    lowest_peak = min(
        budgets,
        key=lambda budget: summaries[str(budget)][
            "median_peak_working_set_bytes"
        ],
    )
    payload = {
        "benchmark": "B13 bounded buffered shard writes",
        "max_square_root": args.max_root,
        "complete_box_upper_value": args.max_root**2,
        "shard_count": args.shard_count,
        "buffer_budgets": list(budgets),
        "zero_budget_means": "unbounded handle writer",
        "repeats": args.repeats,
        "warmup_max_square_root": warm_root,
        "timing_order": [
            list(_ordered_budgets(budgets, repetition))
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
        "fastest_buffer_budget": fastest,
        "lowest_peak_buffer_budget": lowest_peak,
    }

    stem = (
        f"lo_shu_b6_buffered_writes_shards{args.shard_count}"
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
        "max_buffered_write_bytes",
        "seconds",
        "baseline_working_set_bytes",
        "peak_working_set_bytes",
        "write_handle_opens",
        "write_buffer_flushes",
        "write_buffer_evictions",
        "max_buffered_write_bytes_observed",
    )
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    **{key: record[key] for key in fieldnames[:6]},
                    "write_handle_opens": record["stream_stats"][
                        "write_handle_opens"
                    ],
                    "write_buffer_flushes": record["stream_stats"][
                        "write_buffer_flushes"
                    ],
                    "write_buffer_evictions": record["stream_stats"][
                        "write_buffer_evictions"
                    ],
                    "max_buffered_write_bytes_observed": record[
                        "stream_stats"
                    ]["max_buffered_write_bytes"],
                }
            )

    print(
        json.dumps(
            {
                "max_square_root": args.max_root,
                "shard_count": args.shard_count,
                "class_count": len(reference_classes or ()),
                "fastest_buffer_budget": fastest,
                "lowest_peak_buffer_budget": lowest_peak,
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
