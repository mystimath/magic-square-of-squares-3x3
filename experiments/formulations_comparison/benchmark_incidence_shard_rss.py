"""Mesure le pic RSS de chaque configuration de shards dans un processus isolé."""

from __future__ import annotations

import argparse
import ctypes
import csv
import json
import pathlib
import subprocess
import sys
import time


PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from benchmark_incidence_shard_tradeoff import _run  # noqa: E402


class _ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = (
        ("cb", ctypes.c_ulong),
        ("page_fault_count", ctypes.c_ulong),
        ("peak_working_set_size", ctypes.c_size_t),
        ("working_set_size", ctypes.c_size_t),
        ("quota_peak_paged_pool_usage", ctypes.c_size_t),
        ("quota_paged_pool_usage", ctypes.c_size_t),
        ("quota_peak_nonpaged_pool_usage", ctypes.c_size_t),
        ("quota_nonpaged_pool_usage", ctypes.c_size_t),
        ("pagefile_usage", ctypes.c_size_t),
        ("peak_pagefile_usage", ctypes.c_size_t),
        ("private_usage", ctypes.c_size_t),
    )


def _memory_info() -> _ProcessMemoryCountersEx:
    if sys.platform != "win32":
        raise RuntimeError("La sonde RSS B11 requiert Windows.")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    get_current_process = kernel32.GetCurrentProcess
    get_current_process.argtypes = ()
    get_current_process.restype = ctypes.c_void_p
    get_process_memory_info = psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = (
        ctypes.c_void_p,
        ctypes.POINTER(_ProcessMemoryCountersEx),
        ctypes.c_ulong,
    )
    get_process_memory_info.restype = ctypes.c_int

    counters = _ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    success = get_process_memory_info(
        get_current_process(),
        ctypes.byref(counters),
        counters.cb,
    )
    if not success:
        raise ctypes.WinError(ctypes.get_last_error())
    return counters


def _worker(
    max_root: int,
    shard_count: int,
    temp_dir: pathlib.Path | None,
) -> int:
    baseline = _memory_info()
    started = time.perf_counter()
    result, stream_stats = _run(max_root, shard_count, temp_dir)
    seconds = time.perf_counter() - started
    final = _memory_info()
    payload = {
        "max_square_root": max_root,
        "shard_count": shard_count,
        "seconds": seconds,
        "class_count": len(result.classes),
        "classes": [list(grid) for grid in result.classes],
        "search_stats": result.stats,
        "stream_stats": stream_stats,
        "baseline_working_set_bytes": baseline.working_set_size,
        "peak_working_set_bytes": final.peak_working_set_size,
        "peak_pagefile_bytes": final.peak_pagefile_usage,
        "final_private_bytes": final.private_usage,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-root", type=int, default=1_000_000)
    parser.add_argument(
        "--shard-counts",
        type=int,
        nargs="+",
        default=(64, 128, 256, 512),
    )
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    parser.add_argument(
        "--worker-shard-count",
        type=int,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.worker_shard_count is not None:
        return _worker(
            args.max_root,
            args.worker_shard_count,
            args.temp_dir,
        )

    counts = tuple(args.shard_counts)
    if args.max_root < 1:
        parser.error("--max-root doit être strictement positif")
    if any(count < 1 for count in counts):
        parser.error("--shard-counts exige des entiers strictement positifs")
    if len(set(counts)) != len(counts):
        parser.error("--shard-counts ne doit pas contenir de doublon")

    records = []
    reference_classes = None
    reference_search_stats = None
    for shard_count in counts:
        command = [
            sys.executable,
            str(pathlib.Path(__file__).resolve()),
            "--max-root",
            str(args.max_root),
            "--worker-shard-count",
            str(shard_count),
        ]
        if args.temp_dir is not None:
            command.extend(("--temp-dir", str(args.temp_dir)))
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        record = json.loads(completed.stdout)
        if reference_classes is None:
            reference_classes = record["classes"]
            reference_search_stats = record["search_stats"]
        else:
            if record["classes"] != reference_classes:
                raise AssertionError(
                    f"Classes divergentes avec {shard_count} shards."
                )
            if record["search_stats"] != reference_search_stats:
                raise AssertionError(
                    f"Compteurs divergents avec {shard_count} shards."
                )
        records.append(record)

    lowest_peak = min(
        records,
        key=lambda record: record["peak_working_set_bytes"],
    )["shard_count"]
    fastest = min(records, key=lambda record: record["seconds"])[
        "shard_count"
    ]
    payload = {
        "benchmark": "B11 isolated incidence shard RSS",
        "max_square_root": args.max_root,
        "complete_box_upper_value": args.max_root**2,
        "shard_counts": list(counts),
        "class_count": len(reference_classes or ()),
        "classes": reference_classes or [],
        "search_stats": reference_search_stats,
        "fastest_shard_count": fastest,
        "lowest_peak_shard_count": lowest_peak,
        "records": records,
    }

    stem = f"lo_shu_b6_shard_rss_r{args.max_root}"
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
    fieldnames = (
        "max_square_root",
        "shard_count",
        "seconds",
        "class_count",
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
                "class_count": len(reference_classes or ()),
                "fastest_shard_count": fastest,
                "lowest_peak_shard_count": lowest_peak,
                "records": [
                    {
                        key: record[key]
                        for key in fieldnames
                    }
                    for record in records
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
