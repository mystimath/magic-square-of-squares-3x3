"""Benchmark correct du prototype Lo Shu contre v2.2 SAFE, qui trouve Bremner."""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import statistics
import sys

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import _like_bremner_benchmark_common as common_benchmark  # noqa: E402
from common.validation import Grid, canonical_d4  # noqa: E402
from prototypes.like_bremner import search_like_bremner  # noqa: E402
from prototypes.model import generate_square_progressions_parametric  # noqa: E402
from search_non_square_center_v2_2_safe import (  # noqa: E402
    recombine_center_offsets as recombine_v2_2,
)
from search_non_square_center_v2_3_structural import (  # noqa: E402
    recombine_center_offsets as recombine_v2_3,
)


def median(rows: list[dict[str, object]], engine: str, field: str) -> float:
    return statistics.median(float(row[field]) for row in rows if row["engine"] == engine)


def recorded_classes(path: pathlib.Path) -> tuple[Grid, ...]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(
            sorted(
                canonical_d4(tuple(int(row[cell]) for cell in "abcdefghi"))
                for row in csv.DictReader(handle)
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-square-root", "--max-root",
        dest="max_square_root", type=int, default=100_000,
    )
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--recorded-summary", type=pathlib.Path)
    parser.add_argument("--recorded-csv", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    parser.add_argument("--csv-out", type=pathlib.Path)
    args = parser.parse_args()

    catalog_row, catalog_object = common_benchmark.measure(
        "parametric_catalog",
        lambda: generate_square_progressions_parametric(args.max_square_root),
        1,
    )
    catalog = catalog_object
    assert isinstance(catalog, tuple)
    catalog_row["class_count"] = ""
    rows = [catalog_row]
    specialized = None
    baseline_classes = None
    baseline_stats = None
    for run in range(1, args.repeats + 1):
        row, specialized_object = common_benchmark.measure(
            "lo_shu_like_bremner",
            lambda: search_like_bremner(
                args.max_square_root,
                progressions=catalog,
            ),
            run,
        )
        specialized = specialized_object
        row["class_count"] = len(specialized.classes)
        rows.append(row)

        row, baseline_object = common_benchmark.measure(
            "structural_v2_2_shared_catalog",
            lambda: common_benchmark.search_structural_shared_catalog(
                catalog,
                recombine_v2_2,
            ),
            run,
        )
        baseline_classes, baseline_stats = baseline_object
        row["class_count"] = len(baseline_classes)
        rows.append(row)

    assert specialized is not None and baseline_classes is not None
    assert baseline_stats is not None
    if specialized.classes != baseline_classes:
        raise RuntimeError("Lo Shu et v2.2 SAFE ne produisent pas les mêmes classes.")

    offsets_by_center: dict[int, set[int]] = {}
    for progression in catalog:
        offsets_by_center.setdefault(progression.center, set()).add(progression.difference)
    bremner_center = 180625
    v2_3_rows, v2_3_stats = recombine_v2_3(
        bremner_center,
        offsets_by_center.get(bremner_center, set()),
        "relaxed7",
        7,
        True,
        True,
        1_000_000,
    )

    history = None
    if args.recorded_summary:
        history = json.loads(args.recorded_summary.read_text(encoding="utf-8"))
    history_classes = None
    if args.recorded_csv:
        history_classes = recorded_classes(args.recorded_csv)
        if history_classes != specialized.classes:
            raise RuntimeError("La sortie historique diffère de Lo Shu.")

    engines = ("lo_shu_like_bremner", "structural_v2_2_shared_catalog")
    medians = {
        engine: {
            "wall_seconds": median(rows, engine, "wall_seconds"),
            "cpu_seconds": median(rows, engine, "cpu_seconds"),
            "python_peak_incremental_bytes": median(
                rows, engine, "python_peak_incremental_bytes"
            ),
        }
        for engine in engines
    }
    speedup = (
        medians["structural_v2_2_shared_catalog"]["wall_seconds"]
        / medians["lo_shu_like_bremner"]["wall_seconds"]
    )
    payload = {
        "domain": {
            "max_square_root": args.max_square_root,
            "target_mask": "acdefgh",
            "exact_square_count": 7,
            "fully_magic": True,
            "positive_distinct_entries": True,
            "primitive_square_roots": True,
            "equivalence": "D4",
        },
        "catalog_size": len(catalog),
        "runs": rows,
        "medians": medians,
        "shared_catalog_adapter_speedup": speedup,
        "class_sets_equal": True,
        "classes": [list(grid) for grid in specialized.classes],
        "specialized_stats": specialized.stats,
        "v2_2_stats": baseline_stats,
        "v2_3_bremner_center_diagnostic": {
            "offset_count": len(offsets_by_center.get(bremner_center, set())),
            "candidate_count": len(v2_3_rows),
            "stats": dict(v2_3_stats),
            "complete_for_target": bool(v2_3_rows),
        },
        "recorded_full_pipeline": history,
        "recorded_classes_equal": history_classes is None
        or history_classes == specialized.classes,
    }
    json_out = args.json_out or PROJECT_ROOT / "results" / "formulations_comparison" / (
        f"benchmarks/like_bremner_v2_2_r{args.max_square_root}.json"
    )
    csv_out = args.csv_out or PROJECT_ROOT / "results" / "formulations_comparison" / (
        f"benchmarks/like_bremner_v2_2_r{args.max_square_root}.csv"
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "catalog_size": len(catalog),
        "class_count": len(specialized.classes),
        "class_sets_equal": True,
        "shared_catalog_adapter_speedup": speedup,
        "v2_3_complete_for_target": bool(v2_3_rows),
        "json": str(json_out),
        "csv": str(csv_out),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
