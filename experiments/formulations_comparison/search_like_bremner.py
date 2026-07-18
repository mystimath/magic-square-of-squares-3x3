"""Recherche exécutable du motif magique 7/9 de Bremner dans une boîte complète."""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
import time

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.like_bremner_box import search_like_bremner_box  # noqa: E402
from prototypes.model import generate_square_progressions_parametric  # noqa: E402


def _hit_record(hit: object) -> dict[str, object]:
    grid = hit.grid
    roots = hit.square_roots
    record: dict[str, object] = {
        "parameter_A": hit.A,
        "parameter_B": hit.B,
        "parameter_C": hit.C,
        "r": hit.r,
        "q": hit.q,
        "primitive_root_gcd": hit.primitive_root_gcd,
    }
    record.update({cell: value for cell, value in zip("abcdefghi", grid)})
    record.update(
        {
            f"root_{cell}": "" if root is None else root
            for cell, root in zip("abcdefghi", roots)
        }
    )
    record["canonical_d4"] = ",".join(str(value) for value in hit.canonical)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--complete-box-root",
        "--max-root",
        dest="complete_box_root",
        type=int,
        default=601,
        help="borne R imposant 0 < case <= R^2 sur les neuf cases (défaut: 601)",
    )
    parser.add_argument(
        "--all-scalings",
        action="store_true",
        help="conserver aussi les dilatations non primitives",
    )
    parser.add_argument(
        "--csv-out",
        type=pathlib.Path,
        help="sortie CSV (défaut: results/raw/like_bremner_box_R<borne>.csv)",
    )
    parser.add_argument(
        "--json-out",
        type=pathlib.Path,
        help="résumé JSON (défaut: results/raw/like_bremner_box_R<borne>_summary.json)",
    )
    args = parser.parse_args()

    csv_out = args.csv_out or (
        PROJECT_ROOT / "results" / "raw" / f"like_bremner_box_R{args.complete_box_root}.csv"
    )
    json_out = args.json_out or (
        PROJECT_ROOT
        / "results"
        / "raw"
        / f"like_bremner_box_R{args.complete_box_root}_summary.json"
    )

    catalog_start = time.perf_counter()
    catalog = generate_square_progressions_parametric(args.complete_box_root)
    catalog_seconds = time.perf_counter() - catalog_start
    search_start = time.perf_counter()
    result = search_like_bremner_box(
        args.complete_box_root,
        primitive_only=not args.all_scalings,
        progressions=catalog,
    )
    search_seconds = time.perf_counter() - search_start

    records = [_hit_record(hit) for hit in result.hits]
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "parameter_A", "parameter_B", "parameter_C", "r", "q", "primitive_root_gcd",
        *"abcdefghi",
        *(f"root_{cell}" for cell in "abcdefghi"),
        "canonical_d4",
    ]
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    payload = {
        "engine": result.formulation,
        "domain": {
            "complete_box_root": args.complete_box_root,
            "complete_box_upper_value": args.complete_box_root * args.complete_box_root,
            "target_mask": "acdefgh",
            "exact_square_count": 7,
            "fully_magic": True,
            "positive_distinct_entries": True,
            "primitive_only": not args.all_scalings,
            "equivalence": "D4",
        },
        "catalog_size": len(catalog),
        "catalog_seconds": catalog_seconds,
        "search_seconds": search_seconds,
        "total_seconds": catalog_seconds + search_seconds,
        "stats": result.stats,
        "class_count": len(result.classes),
        "hits": records,
        "csv": str(csv_out),
    }
    json_out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
