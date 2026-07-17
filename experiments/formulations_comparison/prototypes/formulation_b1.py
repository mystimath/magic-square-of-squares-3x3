"""Prototype B1 : catalogue des offsets par centre carré."""

from __future__ import annotations

import itertools

from .model import (
    ArithmeticProgression,
    SearchResult,
    accept_grid,
    build_centered_grid,
    freeze_classes,
    generate_square_progressions,
    validate_bound,
)


def search_formulation_b1(
    max_root: int,
    *,
    primitive_only: bool = False,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
) -> SearchResult:
    validate_bound(max_root)
    if progressions is None:
        progressions = generate_square_progressions(max_root)
    offsets_by_center: dict[int, set[int]] = {}
    for progression in progressions:
        offsets_by_center.setdefault(progression.center, set()).add(progression.difference)
    classes = set()
    stats = {
        "progressions": len(progressions),
        "indexed_centers": len(offsets_by_center),
        "offset_pairs": 0,
        "additive_membership_tests": 0,
        "additive_hits": 0,
        "complete_candidates": 0,
        "accepted_candidates": 0,
        "duplicate_classes": 0,
    }
    for center, offsets in offsets_by_center.items():
        ordered = sorted(offsets)
        for q, p in itertools.combinations(ordered, 2):
            stats["offset_pairs"] += 1
            stats["additive_membership_tests"] += 2
            if p - q not in offsets or p + q not in offsets:
                continue
            stats["additive_hits"] += 1
            grid = build_centered_grid(center, p, q)
            stats["complete_candidates"] += 1
            canonical = accept_grid(grid, max_root=max_root, primitive_only=primitive_only)
            if canonical is None:
                continue
            if canonical in classes:
                stats["duplicate_classes"] += 1
            else:
                classes.add(canonical)
                stats["accepted_candidates"] += 1
    return SearchResult("B1", max_root, freeze_classes(classes), stats)
