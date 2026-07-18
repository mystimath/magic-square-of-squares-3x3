"""Recherche B3 like-Bremner, avec catalogue matériel ou groupé en flux."""

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

from prototypes.like_bremner import LikeBremnerSearchResult  # noqa: E402
from prototypes.canonical_progressions import (  # noqa: E402
    CanonicalParametricProgressionGroupStream,
    generate_square_progressions_parametric_canonical,
)
from prototypes.like_bremner_indexed import (  # noqa: E402
    search_like_bremner_indexed_box,
    search_like_bremner_indexed_groups,
)
from prototypes.model import generate_square_progressions_parametric  # noqa: E402
from prototypes.streaming_progressions import (  # noqa: E402
    ParametricProgressionGroupStream,
)


def _complete_box(
    result: LikeBremnerSearchResult,
    complete_box_root: int,
) -> LikeBremnerSearchResult:
    upper = complete_box_root * complete_box_root
    kept = tuple(hit for hit in result.hits if max(hit.grid) <= upper)
    stats = dict(result.stats)
    stats["pre_box_classes"] = len(result.hits)
    stats["rejected_outside_complete_box"] = len(result.hits) - len(kept)
    stats["accepted_classes"] = len(kept)
    return LikeBremnerSearchResult(
        result.formulation + "-box",
        complete_box_root,
        kept,
        stats,
    )


def _hit_record(hit: object) -> dict[str, object]:
    record: dict[str, object] = {
        "parameter_A": hit.A,
        "parameter_B": hit.B,
        "parameter_C": hit.C,
        "r": hit.r,
        "q": hit.q,
        "primitive_root_gcd": hit.primitive_root_gcd,
    }
    record.update({cell: value for cell, value in zip("abcdefghi", hit.grid)})
    record.update(
        {
            f"root_{cell}": "" if root is None else root
            for cell, root in zip("abcdefghi", hit.square_roots)
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
    )
    parser.add_argument(
        "--catalog-mode",
        choices=("material", "streaming"),
        default="material",
    )
    parser.add_argument(
        "--parameter-domain",
        choices=("canonical", "historical"),
        default="canonical",
        help="canonical évite les quatre représentants paramétriques historiques",
    )
    parser.add_argument(
        "--square-membership",
        choices=("isqrt", "residue_isqrt", "materialized_set"),
        default="isqrt",
        help="isqrt direct par défaut; les deux témoins restent disponibles",
    )
    parser.add_argument("--shard-count", type=int, default=64)
    parser.add_argument("--temp-dir", type=pathlib.Path)
    parser.add_argument("--all-scalings", action="store_true")
    parser.add_argument("--csv-out", type=pathlib.Path)
    parser.add_argument("--json-out", type=pathlib.Path)
    args = parser.parse_args()

    primitive_only = not args.all_scalings
    catalog_started = time.perf_counter()
    catalog_stats: dict[str, int]
    if args.catalog_mode == "material":
        generator = (
            generate_square_progressions_parametric_canonical
            if args.parameter_domain == "canonical"
            else generate_square_progressions_parametric
        )
        catalog = generator(args.complete_box_root)
        catalog_seconds = time.perf_counter() - catalog_started
        search_started = time.perf_counter()
        result = search_like_bremner_indexed_box(
            args.complete_box_root,
            primitive_only=primitive_only,
            square_membership_mode=args.square_membership,
            progressions=catalog,
        )
        search_seconds = time.perf_counter() - search_started
        catalog_stats = {"unique_progressions": len(catalog)}
    else:
        stream_type = (
            CanonicalParametricProgressionGroupStream
            if args.parameter_domain == "canonical"
            else ParametricProgressionGroupStream
        )
        stream = stream_type(
            args.complete_box_root,
            shard_count=args.shard_count,
            temp_dir=args.temp_dir,
        )
        # En mode flux, génération et recherche sont entrelacées pendant la
        # phase de lecture des tranches : seul le total bout-en-bout est séparé.
        search_started = time.perf_counter()
        unboxed = search_like_bremner_indexed_groups(
            args.complete_box_root,
            stream,
            primitive_only=primitive_only,
            square_membership_mode=args.square_membership,
        )
        result = _complete_box(unboxed, args.complete_box_root)
        search_seconds = time.perf_counter() - search_started
        catalog_seconds = 0.0
        catalog_stats = dict(stream.stats)

    records = [_hit_record(hit) for hit in result.hits]
    stem = (
        f"like_bremner_b3_{args.catalog_mode}_{args.parameter_domain}"
        f"_box_R{args.complete_box_root}"
    )
    csv_out = args.csv_out or PROJECT_ROOT / "results" / "raw" / f"{stem}.csv"
    json_out = args.json_out or PROJECT_ROOT / "results" / "raw" / f"{stem}_summary.json"
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "parameter_A", "parameter_B", "parameter_C",
        "r", "q", "primitive_root_gcd",
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
            "complete_box_upper_value": args.complete_box_root ** 2,
            "target_mask": "acdefgh",
            "primitive_only": primitive_only,
            "equivalence": "D4",
        },
        "catalog_mode": args.catalog_mode,
        "parameter_domain": args.parameter_domain,
        "catalog_stats": catalog_stats,
        "catalog_seconds_material_only": catalog_seconds,
        "search_seconds": search_seconds,
        "total_seconds": catalog_seconds + search_seconds,
        "square_membership": args.square_membership,
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
