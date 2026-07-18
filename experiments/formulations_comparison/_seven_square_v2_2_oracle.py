"""Adaptateur exhaustif à petite borne pour contrôler B4 contre v2.2 SAFE."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import math
from typing import Protocol

from common.validation import Grid, canonical_d4, validate_grid
from prototypes.model import validate_bound
from prototypes.seven_square_masks import mask_orbit


class CandidateLike(Protocol):
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    g: int
    h: int
    i: int


Recombine = Callable[
    [int, set[int], str, int, bool, bool, int],
    tuple[list[CandidateLike], Counter[str]],
]


def _values(candidate: CandidateLike) -> Grid:
    return tuple(
        getattr(candidate, position) for position in "abcdefghi"
    )  # type: ignore[return-value]


def generate_all_center_offsets(max_root: int) -> dict[int, set[int]]:
    """Indexe toutes les paires opposées de carrés dans la boîte de racines."""

    validate_bound(max_root)
    offsets_by_center: dict[int, set[int]] = {}
    for low_root in range(1, max_root + 1):
        low = low_root * low_root
        for high_root in range(low_root + 2, max_root + 1, 2):
            high = high_root * high_root
            center = (low + high) // 2
            offset = (high - low) // 2
            offsets_by_center.setdefault(center, set()).add(offset)
    return offsets_by_center


def search_v2_2_seven_box(
    complete_box_root: int,
    recombine_center_offsets: Recombine,
    *,
    primitive_only: bool = True,
) -> tuple[tuple[Grid, ...], dict[str, int], dict[str, int]]:
    """Exécute la recombinaison v2.2 sans sélection heuristique de centres."""

    validate_bound(complete_box_root)
    upper = complete_box_root * complete_box_root
    offsets_by_center = generate_all_center_offsets(complete_box_root)
    stats = Counter(
        center_offset_pairs=sum(len(offsets) for offsets in offsets_by_center.values()),
        indexed_centers=len(offsets_by_center),
        centers_with_two_offsets=sum(
            len(offsets) >= 2 for offsets in offsets_by_center.values()
        ),
    )
    classes: set[Grid] = set()
    orbit_counts: dict[str, int] = {}
    for center, offsets in sorted(offsets_by_center.items()):
        if len(offsets) < 2:
            continue
        candidates, recombine_stats = recombine_center_offsets(
            center,
            offsets,
            "relaxed7",
            7,
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
                min_square_count=7,
                require_positive=True,
                require_distinct=True,
                require_primitive=False,
            )
            if not report.accepted or report.square_count != 7:
                stats["rejected_not_exactly_seven"] += 1
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
            orbit_key = mask_orbit(report.square_mask).key
            orbit_counts[orbit_key] = orbit_counts.get(orbit_key, 0) + 1
    stats["accepted_classes"] = len(classes)
    return tuple(sorted(classes)), dict(stats), orbit_counts
