"""Oracle direct A, volontairement simple et exhaustif à petite borne."""

from __future__ import annotations

import math

from .model import SearchResult, accept_grid, build_centered_grid, freeze_classes, validate_bound


def search_formulation_a(max_root: int, *, primitive_only: bool = False) -> SearchResult:
    validate_bound(max_root)
    squares = {root * root for root in range(1, max_root + 1)}
    classes = set()
    stats = {
        "base_triples": 0,
        "rejected_base_collision": 0,
        "forced_values_computed": 0,
        "rejected_nonpositive": 0,
        "square_membership_tests": 0,
        "rejected_forced_nonsquare": 0,
        "complete_candidates": 0,
        "accepted_candidates": 0,
        "duplicate_classes": 0,
    }
    for x in range(1, max_root + 1):
        center = x * x
        for y in range(1, max_root + 1):
            y2 = y * y
            for z in range(1, max_root + 1):
                stats["base_triples"] += 1
                z2 = z * z
                if len({center, y2, z2}) < 3:
                    stats["rejected_base_collision"] += 1
                    continue
                p = center - y2
                q = center - z2
                grid = build_centered_grid(center, p, q)
                forced_indices = (1, 3, 5, 6, 7, 8)
                forced = tuple(grid[index] for index in forced_indices)
                stats["forced_values_computed"] += len(forced)
                if min(forced) <= 0:
                    stats["rejected_nonpositive"] += 1
                    continue
                stats["square_membership_tests"] += len(forced)
                if any(value not in squares for value in forced):
                    stats["rejected_forced_nonsquare"] += 1
                    continue
                stats["complete_candidates"] += 1
                canonical = accept_grid(grid, max_root=max_root, primitive_only=primitive_only)
                if canonical is None:
                    continue
                if canonical in classes:
                    stats["duplicate_classes"] += 1
                else:
                    classes.add(canonical)
                    stats["accepted_candidates"] += 1
    return SearchResult("A", max_root, freeze_classes(classes), stats)
