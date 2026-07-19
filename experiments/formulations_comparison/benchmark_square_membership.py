"""Compare trois oracles exacts d'appartenance aux carrés sur B6."""

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

from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes.lo_shu_nine import search_lo_shu_nine_box  # noqa: E402
from prototypes.lo_shu_nine import search_lo_shu_nine_incidence_groups  # noqa: E402
from prototypes.streaming_seven_incidences import (  # noqa: E402
    CanonicalProgressionIncidenceStream,
)

MODES = ("isqrt", "residue_isqrt", "materialized_set")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-root", type=int, default=100_000)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--shard-count", type=int, default=128)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats doit être strictement positif")

    catalog_started = time.perf_counter()
    catalog = generate_square_progressions_parametric_canonical(args.max_root)
    catalog_seconds = time.perf_counter() - catalog_started

    warm_root = min(args.max_root, 601)
    warm_catalog = generate_square_progressions_parametric_canonical(warm_root)
    for mode in MODES:
        search_lo_shu_nine_box(
            warm_root,
            progressions=warm_catalog,
            square_membership_mode=mode,
        )

    rows: list[dict[str, object]] = []
    timings: dict[str, list[float]] = {mode: [] for mode in MODES}
    stats_by_mode: dict[str, dict[str, int]] = {}
    reference_classes = None
    for repetition in range(1, args.repeats + 1):
        order = MODES if repetition % 2 else tuple(reversed(MODES))
        for mode in order:
            gc.collect()
            started = time.perf_counter()
            result = search_lo_shu_nine_box(
                args.max_root,
                progressions=catalog,
                square_membership_mode=mode,
            )
            seconds = time.perf_counter() - started
            if reference_classes is None:
                reference_classes = result.classes
            elif result.classes != reference_classes:
                raise AssertionError("Les deux oracles produisent des classes différentes.")
            timings[mode].append(seconds)
            stats_by_mode[mode] = result.stats
            rows.append(
                {
                    "phase": "timing",
                    "repetition": repetition,
                    "mode": mode,
                    "seconds": seconds,
                    "peak_bytes": "",
                    "class_count": len(result.classes),
                }
            )

    peaks: dict[str, int] = {}
    stream_stats_by_mode: dict[str, dict[str, int]] = {}
    for mode in MODES:
        gc.collect()
        tracemalloc.start()
        stream = CanonicalProgressionIncidenceStream(
            args.max_root,
            shard_count=args.shard_count,
        )
        result = search_lo_shu_nine_incidence_groups(
            args.max_root,
            stream,
            square_membership_mode=mode,
            validate_incidence_groups=False,
        )
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if result.classes != reference_classes:
            raise AssertionError("La passe mémoire a produit des classes différentes.")
        peaks[mode] = peak_bytes
        stream_stats_by_mode[mode] = dict(stream.stats)
        rows.append(
            {
                "phase": "memory",
                "repetition": "",
                "mode": mode,
                "seconds": "",
                "peak_bytes": peak_bytes,
                "class_count": len(result.classes),
            }
        )

    summaries = {
        mode: {
            "seconds": values,
            "median_seconds": statistics.median(values),
            "min_seconds": min(values),
            "max_seconds": max(values),
            "peak_bytes": peaks[mode],
            "stats": stats_by_mode[mode],
        }
        for mode, values in timings.items()
    }
    direct = summaries["isqrt"]
    residue = summaries["residue_isqrt"]
    materialized = summaries["materialized_set"]
    payload = {
        "benchmark": "B6 square membership oracle",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "max_square_root": args.max_root,
        "complete_box_upper_value": args.max_root**2,
        "repeats": args.repeats,
        "catalog": {
            "parameter_domain": "canonical",
            "progressions": len(catalog),
            "generation_seconds": catalog_seconds,
            "shared_between_modes": True,
        },
        "memory_measurement": {
            "catalog_mode": "streaming",
            "shard_count": args.shard_count,
            "stream_stats_by_mode": stream_stats_by_mode,
        },
        "class_count": len(reference_classes or ()),
        "summaries": summaries,
        "ratios": {
            "materialized_over_residue_median_time": (
                materialized["median_seconds"] / residue["median_seconds"]
            ),
            "materialized_over_residue_peak_memory": (
                materialized["peak_bytes"] / residue["peak_bytes"]
            ),
            "materialized_over_isqrt_median_time": (
                materialized["median_seconds"] / direct["median_seconds"]
            ),
            "materialized_over_isqrt_peak_memory": (
                materialized["peak_bytes"] / direct["peak_bytes"]
            ),
        },
    }

    stem = f"lo_shu_b6_square_membership_r{args.max_root}"
    json_out = (
        args.json_out
        or PROJECT_ROOT / "results" / "formulations_comparison" / "benchmarks" / f"{stem}.json"
    )
    csv_out = (
        args.csv_out
        or PROJECT_ROOT / "results" / "formulations_comparison" / "benchmarks" / f"{stem}.csv"
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
