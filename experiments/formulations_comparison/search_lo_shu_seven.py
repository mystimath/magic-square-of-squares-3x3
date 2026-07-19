"""Recherche B4 de toutes les orbites D4 exactement 7/9 en boîte complète."""

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

from prototypes.canonical_progressions import (  # noqa: E402
    generate_square_progressions_parametric_canonical,
)
from prototypes.lo_shu_seven import search_lo_shu_seven_box  # noqa: E402
from prototypes.lo_shu_seven_grouped import (  # noqa: E402
    search_lo_shu_seven_incidence_groups,
)
from prototypes.streaming_seven_incidences import (  # noqa: E402
    CanonicalProgressionIncidenceStream,
)
from prototypes.seven_square_masks import (  # noqa: E402
    SEVEN_SQUARE_MASK_ORBITS,
)


def _hit_record(hit: object) -> dict[str, object]:
    record: dict[str, object] = {
        "parameter_A": hit.A,
        "q": hit.q,
        "r": hit.r,
        "square_mask": hit.square_mask,
        "mask_orbit": hit.mask_orbit,
        "primitive_root_gcd": hit.primitive_root_gcd,
        "shared_square": hit.shared_square,
        "r_seed_roots": ",".join(str(root) for root in hit.r_seed_roots),
        "q_seed_roots": ",".join(str(root) for root in hit.q_seed_roots),
        "r_intersection_index": hit.r_intersection_index,
        "q_intersection_index": hit.q_intersection_index,
    }
    record.update(
        {position: value for position, value in zip("abcdefghi", hit.grid)}
    )
    record.update(
        {
            f"root_{position}": "" if root is None else root
            for position, root in zip("abcdefghi", hit.square_roots)
        }
    )
    record["canonical_d4"] = ",".join(
        str(value) for value in hit.canonical
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--complete-box-root",
        "--max-root",
        dest="complete_box_root",
        type=int,
        default=601,
    )
    parser.add_argument(
        "--catalog-mode",
        choices=("material", "streaming"),
        default="material",
    )
    parser.add_argument(
        "--square-membership",
        choices=("isqrt", "residue_isqrt", "materialized_set"),
        default="isqrt",
        help="isqrt direct par défaut; les deux témoins restent disponibles",
    )
    parser.add_argument(
        "--shard-count",
        type=int,
        default=128,
        help="128 par défaut ; 256 recommandé vers R=1000000",
    )
    parser.add_argument(
        "--max-open-shard-handles",
        type=int,
        help="active un cache LRU borné des handles d'écriture",
    )
    parser.add_argument(
        "--max-buffered-write-bytes",
        type=int,
        help="active les tampons LRU B13 sous ce budget global",
    )
    parser.add_argument(
        "--write-handle-buffering",
        type=int,
        help="taille du tampon binaire de chaque handle (-1 implicite par défaut)",
    )
    parser.add_argument(
        "--group-writes-by-shard",
        action="store_true",
        help="regroupe toutes les incidences en mémoire avant écriture",
    )
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--all-scalings", action="store_true")
    parser.add_argument("--csv-out", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    args = parser.parse_args()

    catalog_started = time.perf_counter()
    if args.catalog_mode == "material":
        catalog = generate_square_progressions_parametric_canonical(
            args.complete_box_root
        )
        catalog_seconds = time.perf_counter() - catalog_started
        search_started = time.perf_counter()
        result = search_lo_shu_seven_box(
            args.complete_box_root,
            primitive_only=not args.all_scalings,
            square_membership_mode=args.square_membership,
            progressions=catalog,
        )
        search_seconds = time.perf_counter() - search_started
        catalog_payload: dict[str, object] = {
            "mode": "material",
            "parameter_domain": "canonical",
            "progressions": len(catalog),
            "seconds": catalog_seconds,
        }
    else:
        stream = CanonicalProgressionIncidenceStream(
            args.complete_box_root,
            shard_count=args.shard_count,
            max_open_shard_handles=args.max_open_shard_handles,
            max_buffered_write_bytes=args.max_buffered_write_bytes,
            write_handle_buffering=args.write_handle_buffering,
            group_writes_by_shard=args.group_writes_by_shard,
            temp_dir=args.temp_dir,
        )
        search_started = time.perf_counter()
        result = search_lo_shu_seven_incidence_groups(
            args.complete_box_root,
            stream,
            primitive_only=not args.all_scalings,
            square_membership_mode=args.square_membership,
            validate_incidence_groups=False,
        )
        search_seconds = time.perf_counter() - search_started
        catalog_seconds = 0.0
        catalog_payload = {
            "mode": "streaming",
            "parameter_domain": "canonical",
            "seconds_included_in_search": True,
            **stream.stats,
        }

    records = [_hit_record(hit) for hit in result.hits]
    stem = f"lo_shu_b4_exact7_{args.catalog_mode}_box_R{args.complete_box_root}"
    csv_out = args.csv_out or PROJECT_ROOT / "results" / "raw" / f"{stem}.csv"
    json_out = (
        args.json_out
        or PROJECT_ROOT / "results" / "raw" / f"{stem}_summary.json"
    )
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "parameter_A", "q", "r", "square_mask", "mask_orbit",
        "primitive_root_gcd", "shared_square",
        "r_seed_roots", "q_seed_roots",
        "r_intersection_index", "q_intersection_index",
        *"abcdefghi",
        *(f"root_{position}" for position in "abcdefghi"),
        "canonical_d4",
    ]
    with csv_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    orbit_inventory = [
        {
            "key": orbit.key,
            "representative_missing": orbit.representative_missing,
            "representative_mask": orbit.representative_mask,
            "orbit_size": len(orbit.masks),
            "class_count": result.orbit_class_counts.get(orbit.key, 0),
        }
        for orbit in SEVEN_SQUARE_MASK_ORBITS
    ]
    payload = {
        "engine": result.formulation,
        "domain": {
            "complete_box_root": args.complete_box_root,
            "complete_box_upper_value": args.complete_box_root ** 2,
            "exact_square_count": 7,
            "primitive_only": not args.all_scalings,
            "positive_distinct_entries": True,
            "equivalence": "D4",
            "mask_orbit_count": 8,
        },
        "catalog": catalog_payload,
        "search_seconds": search_seconds,
        "total_seconds": catalog_seconds + search_seconds,
        "square_membership": args.square_membership,
        "stats": result.stats,
        "orbit_inventory": orbit_inventory,
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
