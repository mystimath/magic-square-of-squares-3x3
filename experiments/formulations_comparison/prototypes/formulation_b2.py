"""Prototype B2 : progressions groupées par différence commune."""

from __future__ import annotations

from .model import (
    ArithmeticProgression,
    SearchResult,
    accept_grid,
    build_centered_grid,
    freeze_classes,
    generate_square_progressions,
    validate_bound,
)


def search_formulation_b2(
    max_root: int,
    *,
    primitive_only: bool = False,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
) -> SearchResult:
    validate_bound(max_root)
    if progressions is None:
        progressions = generate_square_progressions(max_root)
    centers_by_difference: dict[int, set[int]] = {}
    for progression in progressions:
        centers_by_difference.setdefault(progression.difference, set()).add(progression.center)
    classes = set()
    stats = {
        "progressions": len(progressions),
        "difference_groups": len(centers_by_difference),
        "center_pairs": 0,
        "third_center_tests": 0,
        "center_progression_hits": 0,
        "complete_candidates": 0,
        "accepted_candidates": 0,
        "duplicate_classes": 0,
    }
    for difference, centers in centers_by_difference.items():
        ordered = sorted(centers)
        for low_index, low in enumerate(ordered):
            for center in ordered[low_index + 1 :]:
                stats["center_pairs"] += 1
                high = 2 * center - low
                stats["third_center_tests"] += 1
                if high not in centers:
                    continue
                stats["center_progression_hits"] += 1
                center_difference = center - low
                grid = build_centered_grid(center, difference, center_difference)
                stats["complete_candidates"] += 1
                canonical = accept_grid(grid, max_root=max_root, primitive_only=primitive_only)
                if canonical is None:
                    continue
                if canonical in classes:
                    stats["duplicate_classes"] += 1
                else:
                    classes.add(canonical)
                    stats["accepted_candidates"] += 1
    return SearchResult("B2", max_root, freeze_classes(classes), stats)
