"""Adaptateur exhaustif à petite borne pour contrôler B6 contre v2.2 SAFE."""

from __future__ import annotations

from collections import Counter
import math

from _seven_square_v2_2_oracle import (
    CandidateLike,
    Recombine,
    generate_all_center_offsets,
)
from common.validation import Grid, canonical_d4, validate_grid
from prototypes.model import validate_bound


def _values(candidate: CandidateLike) -> Grid:
    return tuple(
        getattr(candidate, position) for position in "abcdefghi"
    )  # type: ignore[return-value]


def search_v2_2_nine_box(
    complete_box_root: int,
    recombine_center_offsets: Recombine,
    *,
    primitive_only: bool = True,
) -> tuple[tuple[Grid, ...], dict[str, int]]:
    """Exécute les chemins exact8 et relaxed7, puis exige neuf carrés."""

    validate_bound(complete_box_root)
    upper = complete_box_root * complete_box_root
    offsets_by_center = generate_all_center_offsets(complete_box_root)
    stats = Counter(
        center_offset_pairs=sum(len(offsets) for offsets in offsets_by_center.values()),
        indexed_centers=len(offsets_by_center),
        centers_with_two_offsets=sum(
            len(offsets) >= 2 for offsets in offsets_by_center.values()
        ),
        centers_with_four_offsets=sum(
            len(offsets) >= 4 for offsets in offsets_by_center.values()
        ),
    )
    classes: set[Grid] = set()
    for center, offsets in sorted(offsets_by_center.items()):
        if len(offsets) < 2:
            continue
        candidates, recombine_stats = recombine_center_offsets(
            center,
            offsets,
            "both",
            9,
            False,
            False,
            1_000_000,
        )
        stats.update(recombine_stats)
        for candidate in candidates:
            grid = _values(candidate)
            if min(grid) <= 0 or max(grid) > upper or len(set(grid)) != 9:
                stats["rejected_complete_box_or_distinctness"] += 1
                continue
            report = validate_grid(
                grid,
                min_square_count=9,
                require_positive=True,
                require_distinct=True,
                require_primitive=False,
            )
            if not report.accepted or report.square_count != 9:
                stats["rejected_not_all_nine_square"] += 1
                continue
            roots = tuple(
                root for root in report.square_roots if root not in (None, 0)
            )
            if primitive_only and math.gcd(*roots) != 1:
                stats["rejected_nonprimitive"] += 1
                continue
            canonical = canonical_d4(grid)
            if canonical in classes:
                stats["duplicate_classes"] += 1
                continue
            classes.add(canonical)
    stats["accepted_classes"] = len(classes)
    return tuple(sorted(classes)), dict(stats)
