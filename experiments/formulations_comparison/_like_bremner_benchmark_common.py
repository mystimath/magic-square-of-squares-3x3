"""Fonctions communes aux benchmarks ciblés like-Bremner."""

from __future__ import annotations

from collections import Counter
import gc
import math
import time
import tracemalloc
from typing import Callable, Protocol

from common.validation import Grid, canonical_d4, d4_orbit, validate_grid
from prototypes.like_bremner import TARGET_MASK
from prototypes.model import ArithmeticProgression


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
    return tuple(getattr(candidate, cell) for cell in "abcdefghi")  # type: ignore[return-value]


def _mask(grid: Grid) -> str:
    return validate_grid(grid, min_square_count=0).square_mask


def _has_target_mask_in_d4(grid: Grid) -> bool:
    return any(_mask(transformed) == TARGET_MASK for transformed in d4_orbit(grid))


def search_structural_shared_catalog(
    progressions: tuple[ArithmeticProgression, ...],
    recombine_center_offsets: Recombine,
) -> tuple[tuple[Grid, ...], dict[str, int]]:
    """Exécute une recombinaison structurelle en mémoire sur un catalogue donné."""

    offsets_by_center: dict[int, set[int]] = {}
    for progression in progressions:
        offsets_by_center.setdefault(progression.center, set()).add(
            progression.difference
        )
    total = Counter(
        progressions=len(progressions),
        indexed_centers=len(offsets_by_center),
        centers_with_at_least_three_offsets=sum(
            len(offsets) >= 3 for offsets in offsets_by_center.values()
        ),
    )
    classes: set[Grid] = set()
    for center, offsets in offsets_by_center.items():
        candidates, stats = recombine_center_offsets(
            center,
            offsets,
            "relaxed7",
            7,
            True,
            True,
            1_000_000,
        )
        total.update(stats)
        for candidate in candidates:
            grid = _values(candidate)
            report = validate_grid(
                grid,
                min_square_count=7,
                require_positive=True,
                require_distinct=True,
            )
            if not report.accepted or report.square_count != 7:
                continue
            roots = tuple(
                root for root in report.square_roots if root not in (None, 0)
            )
            if math.gcd(*roots) != 1 or not _has_target_mask_in_d4(grid):
                continue
            classes.add(canonical_d4(grid))
    total["target_classes"] = len(classes)
    return tuple(sorted(classes)), dict(total)


def measure(
    name: str,
    function: Callable[[], object],
    run: int,
) -> tuple[dict[str, object], object]:
    gc.collect()
    tracemalloc.start()
    cpu_started = time.process_time()
    wall_started = time.perf_counter()
    result = function()
    wall_seconds = time.perf_counter() - wall_started
    cpu_seconds = time.process_time() - cpu_started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return (
        {
            "engine": name,
            "run": run,
            "wall_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "python_peak_incremental_bytes": peak_bytes,
        },
        result,
    )
