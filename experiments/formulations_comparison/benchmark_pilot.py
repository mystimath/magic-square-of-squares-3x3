"""Benchmark pilote J7 des formulations A, B1 et B2 sur un domaine commun."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import tracemalloc

from prototypes.formulation_a import search_formulation_a
from prototypes.formulation_b1 import search_formulation_b1
from prototypes.formulation_b2 import search_formulation_b2


ENGINES = {
    "A": search_formulation_a,
    "B1": search_formulation_b1,
    "B2": search_formulation_b2,
}


def environment_payload() -> dict:
    try:
        git_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
        git_dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
            ).stdout
        )
    except (OSError, subprocess.CalledProcessError):
        git_head = "unavailable"
        git_dirty = None
    return {
        "platform": platform.platform(),
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "logical_cpus": os.cpu_count(),
        "git_head": git_head,
        "git_dirty": git_dirty,
    }


def measure(formulation: str, bound: int) -> tuple[dict, tuple]:
    engine = ENGINES[formulation]
    tracemalloc.start()
    cpu_start = time.process_time()
    wall_start = time.perf_counter()
    result = engine(bound)
    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    row = {
        "formulation": formulation,
        "max_root": bound,
        "domain": "positive distinct 9/9; all roots <= max_root; D4 classes",
        "status": "complete",
        "wall_seconds": wall_seconds,
        "cpu_seconds": cpu_seconds,
        "python_peak_bytes": peak_bytes,
        "class_count": len(result.classes),
        **result.stats,
    }
    return row, result.classes


def write_outputs(rows: list[dict], output_dir: Path, bounds: list[int]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "milestone": "J7-pilot",
        "environment": environment_payload(),
        "bounds": bounds,
        "runs": rows,
        "all_cross_validated": True,
        "completeness_scope": "each listed max_root independently",
    }
    json_path = output_dir / "pilot_benchmarks.json"
    csv_path = output_dir / "pilot_benchmarks.csv"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = sorted({key for row in rows for key in row})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    artifact_sizes = {
        "pilot_benchmarks.csv": csv_path.stat().st_size,
        "pilot_benchmarks.json": json_path.stat().st_size,
    }
    (output_dir / "artifact_sizes.json").write_text(
        json.dumps(artifact_sizes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bounds", type=int, nargs="+", default=[50, 100, 200])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/formulations_comparison/benchmarks"),
    )
    args = parser.parse_args()
    if any(bound < 1 for bound in args.bounds):
        parser.error("les bornes doivent être positives")
    rows: list[dict] = []
    for bound in args.bounds:
        classes_by_engine = {}
        for formulation in ENGINES:
            row, classes = measure(formulation, bound)
            rows.append(row)
            classes_by_engine[formulation] = classes
            print(
                f"{formulation} R={bound}: {row['wall_seconds']:.6f}s, "
                f"peak={row['python_peak_bytes']} bytes, classes={row['class_count']}",
                flush=True,
            )
        if not (classes_by_engine["A"] == classes_by_engine["B1"] == classes_by_engine["B2"]):
            raise RuntimeError(f"divergence des classes à R={bound}")
    write_outputs(rows, args.output_dir, args.bounds)


if __name__ == "__main__":
    main()
