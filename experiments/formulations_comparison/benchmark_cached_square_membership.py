"""Compare B6 avec ``isqrt`` direct et avec son LRU borné."""

from __future__ import annotations

import argparse
import csv
import gc
import json
import pathlib
import statistics
import sys
import time

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes.lo_shu_nine import search_lo_shu_nine_box  # noqa: E402

MODES = ("isqrt", "cached_isqrt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-root", type=int, default=100_000)
    parser.add_argument("--repeats", type=int, default=7)
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

    timings = {mode: [] for mode in MODES}
    stats_by_mode: dict[str, dict[str, int]] = {}
    rows: list[dict[str, object]] = []
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
                    "repetition": repetition,
                    "mode": mode,
                    "seconds": seconds,
                    "class_count": len(result.classes),
                }
            )

    summaries = {
        mode: {
            "seconds": values,
            "median_seconds": statistics.median(values),
            "min_seconds": min(values),
            "max_seconds": max(values),
            "stats": stats_by_mode[mode],
        }
        for mode, values in timings.items()
    }
    payload = {
        "benchmark": "B6 bounded square-membership cache",
        "max_square_root": args.max_root,
        "repeats": args.repeats,
        "catalog": {
            "progressions": len(catalog),
            "generation_seconds": catalog_seconds,
            "shared_between_modes": True,
        },
        "class_count": len(reference_classes or ()),
        "summaries": summaries,
        "direct_over_cached_median_time": (
            summaries["isqrt"]["median_seconds"]
            / summaries["cached_isqrt"]["median_seconds"]
        ),
    }
    stem = f"lo_shu_b6_cached_isqrt_r{args.max_root}"
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
