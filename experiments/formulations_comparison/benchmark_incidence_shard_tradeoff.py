"""Mesure le compromis temps/mémoire du nombre de shards d'incidences B6."""

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

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.lo_shu_nine import (  # noqa: E402
    search_lo_shu_nine_incidence_groups,
)
from prototypes.streaming_seven_incidences import (  # noqa: E402
    CanonicalProgressionIncidenceStream,
)


def _ordered_counts(
    counts: tuple[int, ...],
    repetition: int,
) -> tuple[int, ...]:
    offset = (repetition - 1) % len(counts)
    rotated = counts[offset:] + counts[:offset]
    return rotated if repetition % 2 else tuple(reversed(rotated))


def _run(
    max_root: int,
    shard_count: int,
    temp_dir: pathlib.Path | None,
    max_open_shard_handles: int | None = None,
    max_buffered_write_bytes: int | None = None,
    write_handle_buffering: int | None = None,
    group_writes_by_shard: bool = False,
):
    stream = CanonicalProgressionIncidenceStream(
        max_root,
        shard_count=shard_count,
        max_open_shard_handles=max_open_shard_handles,
        max_buffered_write_bytes=max_buffered_write_bytes,
        write_handle_buffering=write_handle_buffering,
        group_writes_by_shard=group_writes_by_shard,
        temp_dir=temp_dir,
    )
    result = search_lo_shu_nine_incidence_groups(
        max_root,
        stream,
        validate_incidence_groups=False,
    )
    return result, dict(stream.stats)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-root", type=int, default=100_000)
    parser.add_argument(
        "--shard-counts",
        type=int,
        nargs="+",
        default=(16, 32, 64, 128, 256, 512),
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--skip-memory", action="store_true")
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()

    if args.max_root < 1:
        parser.error("--max-root doit être strictement positif")
    if args.repeats < 2:
        parser.error("--repeats doit être au moins 2")
    counts = tuple(args.shard_counts)
    if any(count < 1 for count in counts):
        parser.error("--shard-counts exige des entiers strictement positifs")
    if len(set(counts)) != len(counts):
        parser.error("--shard-counts ne doit pas contenir de doublon")

    warm_root = min(args.max_root, 601)
    _run(warm_root, min(counts), args.temp_dir)

    timings: dict[int, list[float]] = {count: [] for count in counts}
    latest_stream_stats: dict[int, dict[str, int]] = {}
    rows: list[dict[str, object]] = []
    reference_classes = None
    reference_search_stats = None

    for repetition in range(1, args.repeats + 1):
        order = _ordered_counts(counts, repetition)
        for order_index, shard_count in enumerate(order, start=1):
            gc.collect()
            started = time.perf_counter()
            result, stream_stats = _run(
                args.max_root,
                shard_count,
                args.temp_dir,
            )
            seconds = time.perf_counter() - started
            if reference_classes is None:
                reference_classes = result.classes
                reference_search_stats = result.stats
            else:
                if result.classes != reference_classes:
                    raise AssertionError(
                        f"Classes divergentes avec {shard_count} shards."
                    )
                if result.stats != reference_search_stats:
                    raise AssertionError(
                        f"Compteurs divergents avec {shard_count} shards."
                    )
            timings[shard_count].append(seconds)
            latest_stream_stats[shard_count] = stream_stats
            rows.append(
                {
                    "phase": "timing",
                    "repetition": repetition,
                    "order_index": order_index,
                    "shard_count": shard_count,
                    "seconds": seconds,
                    "peak_bytes": "",
                    "shards_used": stream_stats["shards_used"],
                    "max_incidence_records_in_shard": stream_stats[
                        "max_incidence_records_in_shard"
                    ],
                    "class_count": len(result.classes),
                }
            )

    peaks: dict[int, int] = {}
    if not args.skip_memory:
        for shard_count in counts:
            gc.collect()
            tracemalloc.start()
            result, stream_stats = _run(
                args.max_root,
                shard_count,
                args.temp_dir,
            )
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            if result.classes != reference_classes:
                raise AssertionError(
                    f"Classes divergentes pendant la mesure mémoire à "
                    f"{shard_count} shards."
                )
            if result.stats != reference_search_stats:
                raise AssertionError(
                    f"Compteurs divergents pendant la mesure mémoire à "
                    f"{shard_count} shards."
                )
            peaks[shard_count] = peak_bytes
            if stream_stats != latest_stream_stats[shard_count]:
                raise AssertionError(
                    f"Statistiques de flux divergentes à {shard_count} shards."
                )
            rows.append(
                {
                    "phase": "memory",
                    "repetition": "",
                    "order_index": "",
                    "shard_count": shard_count,
                    "seconds": "",
                    "peak_bytes": peak_bytes,
                    "shards_used": stream_stats["shards_used"],
                    "max_incidence_records_in_shard": stream_stats[
                        "max_incidence_records_in_shard"
                    ],
                    "class_count": len(result.classes),
                }
            )

    summaries = {}
    for shard_count in counts:
        values = timings[shard_count]
        stream_stats = latest_stream_stats[shard_count]
        summaries[str(shard_count)] = {
            "seconds": values,
            "median_seconds": statistics.median(values),
            "min_seconds": min(values),
            "max_seconds": max(values),
            "peak_bytes": peaks.get(shard_count),
            "stream_stats": stream_stats,
            "estimated_file_opens": 2 * stream_stats["shards_used"],
        }

    fastest = min(
        counts,
        key=lambda count: summaries[str(count)]["median_seconds"],
    )
    lowest_peak = (
        min(counts, key=lambda count: peaks[count])
        if peaks
        else None
    )
    payload = {
        "benchmark": "B11 incidence shard time-memory tradeoff",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "max_square_root": args.max_root,
        "complete_box_upper_value": args.max_root**2,
        "repeats": args.repeats,
        "shard_counts": list(counts),
        "timing_order": [
            list(_ordered_counts(counts, repetition))
            for repetition in range(1, args.repeats + 1)
        ],
        "catalog_mode": "streaming",
        "square_membership": "isqrt",
        "trusted_incidence_groups": True,
        "class_count": len(reference_classes or ()),
        "classes": [list(grid) for grid in (reference_classes or ())],
        "search_stats": reference_search_stats,
        "summaries": summaries,
        "fastest_shard_count": fastest,
        "lowest_peak_shard_count": lowest_peak,
    }

    stem = f"lo_shu_b6_shard_tradeoff_r{args.max_root}"
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
                "max_square_root": args.max_root,
                "class_count": len(reference_classes or ()),
                "fastest_shard_count": fastest,
                "lowest_peak_shard_count": lowest_peak,
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
