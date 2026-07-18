"""Compare ``isqrt`` vectorisé au set dans les moteurs B3 à B6."""

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
from prototypes.like_bremner_indexed import (  # noqa: E402
    search_like_bremner_indexed_box,
)
from prototypes.lo_shu_eight import search_lo_shu_eight_box  # noqa: E402
from prototypes.lo_shu_nine import search_lo_shu_nine_box  # noqa: E402
from prototypes.lo_shu_seven import search_lo_shu_seven_box  # noqa: E402

MODES = ("isqrt", "materialized_set")
ENGINES = {
    "B3": search_like_bremner_indexed_box,
    "B4": search_lo_shu_seven_box,
    "B5": search_lo_shu_eight_box,
    "B6": search_lo_shu_nine_box,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-root", type=int, default=100_000)
    parser.add_argument("--repeats", type=int, default=5)
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
    for engine in ENGINES.values():
        for mode in MODES:
            engine(
                warm_root,
                progressions=warm_catalog,
                square_membership_mode=mode,
            )

    timings = {
        engine_name: {mode: [] for mode in MODES}
        for engine_name in ENGINES
    }
    stats: dict[str, dict[str, dict[str, int]]] = {
        engine_name: {} for engine_name in ENGINES
    }
    reference_classes: dict[str, tuple[tuple[int, ...], ...]] = {}
    rows: list[dict[str, object]] = []
    for repetition in range(1, args.repeats + 1):
        order = MODES if repetition % 2 else tuple(reversed(MODES))
        for engine_name, engine in ENGINES.items():
            for mode in order:
                gc.collect()
                started = time.perf_counter()
                result = engine(
                    args.max_root,
                    progressions=catalog,
                    square_membership_mode=mode,
                )
                seconds = time.perf_counter() - started
                expected = reference_classes.setdefault(
                    engine_name,
                    result.classes,
                )
                if result.classes != expected:
                    raise AssertionError(
                        f"Classes divergentes pour {engine_name} en mode {mode}."
                    )
                timings[engine_name][mode].append(seconds)
                stats[engine_name][mode] = result.stats
                rows.append(
                    {
                        "repetition": repetition,
                        "engine": engine_name,
                        "mode": mode,
                        "seconds": seconds,
                        "class_count": len(result.classes),
                    }
                )

    summaries: dict[str, object] = {}
    for engine_name, mode_timings in timings.items():
        per_mode = {
            mode: {
                "seconds": values,
                "median_seconds": statistics.median(values),
                "min_seconds": min(values),
                "max_seconds": max(values),
                "stats": stats[engine_name][mode],
            }
            for mode, values in mode_timings.items()
        }
        summaries[engine_name] = {
            "class_count": len(reference_classes[engine_name]),
            "modes": per_mode,
            "materialized_over_isqrt_median_time": (
                per_mode["materialized_set"]["median_seconds"]
                / per_mode["isqrt"]["median_seconds"]
            ),
        }

    payload = {
        "benchmark": "B3-B6 batched isqrt versus materialized set",
        "max_square_root": args.max_root,
        "repeats": args.repeats,
        "catalog": {
            "progressions": len(catalog),
            "generation_seconds": catalog_seconds,
            "shared_between_all_runs": True,
        },
        "summaries": summaries,
    }
    stem = f"lo_shu_b3_b6_batched_isqrt_r{args.max_root}"
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
