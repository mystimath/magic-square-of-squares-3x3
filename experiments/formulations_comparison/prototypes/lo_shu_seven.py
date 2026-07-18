"""Branche B4 : recherche Lo Shu exhaustive pour tous les masques exacts 7/9."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import math

from common.validation import Grid, canonical_d4, validate_grid

from .canonical_progressions import (
    generate_square_progressions_parametric_canonical,
)
from .like_bremner import build_like_bremner_grid
from .model import ArithmeticProgression, validate_bound
from .square_membership import (
    IsqrtSquareMembership,
    SquareMembershipMode,
    build_square_membership,
    square_membership_stats,
)
from .seven_square_masks import mask_orbit, normalize_square_mask


# Coordonnées (x, k) de la grille additive A + x*q + k*r.
PARAMETER_POSITIONS = (
    ("h", "c", "d"),
    ("a", "e", "i"),
    ("f", "g", "b"),
)
POSITION_INDEX = {
    position: index for index, position in enumerate("abcdefghi")
}
REMAINING_GRID_INDICES = tuple(
    tuple(
        tuple(
            POSITION_INDEX[PARAMETER_POSITIONS[x][k]]
            for x in range(3)
            for k in range(3)
            if x != x0 and k != k0
        )
        for k0 in range(3)
    )
    for x0 in range(3)
)


@dataclass(frozen=True)
class ProgressionIncidence:
    progression: ArithmeticProgression
    term_index: int
    root_gcd: int


@dataclass(frozen=True)
class LoShuSevenHit:
    grid: Grid
    canonical: Grid
    A: int
    q: int
    r: int
    square_mask: str
    mask_orbit: str
    square_roots: tuple[int | None, ...]
    primitive_root_gcd: int
    shared_square: int
    r_seed_roots: tuple[int, int, int]
    q_seed_roots: tuple[int, int, int]
    r_intersection_index: int
    q_intersection_index: int


@dataclass(frozen=True)
class LoShuSevenSearchResult:
    formulation: str
    complete_box_root: int
    hits: tuple[LoShuSevenHit, ...]
    stats: dict[str, int]
    orbit_class_counts: dict[str, int]

    @property
    def classes(self) -> tuple[Grid, ...]:
        return tuple(hit.canonical for hit in self.hits)

    def classes_for_orbit(self, orbit_key: str) -> tuple[Grid, ...]:
        return tuple(
            hit.canonical for hit in self.hits if hit.mask_orbit == orbit_key
        )


def seed_crosses_for_mask(mask: str) -> tuple[tuple[int, int], ...]:
    """Donne les croisements ligne-q/ligne-r entièrement carrés d'un masque."""

    selected = set(normalize_square_mask(mask))
    complete_r_rows = tuple(
        x
        for x, row in enumerate(PARAMETER_POSITIONS)
        if all(position in selected for position in row)
    )
    complete_q_columns = tuple(
        k
        for k in range(3)
        if all(PARAMETER_POSITIONS[x][k] in selected for x in range(3))
    )
    return tuple(
        (x, k) for x in complete_r_rows for k in complete_q_columns
    )


def _progression_values(
    progression: ArithmeticProgression,
) -> tuple[int, int, int]:
    return progression.low, progression.center, progression.high


def _progression_roots(
    progression: ArithmeticProgression,
) -> tuple[int, int, int]:
    return (
        progression.low_root,
        progression.center_root,
        progression.high_root,
    )


def _compatible_ordered_incidences(
    incidences: tuple[ProgressionIncidence, ...],
    *,
    primitive_only: bool,
    stats: dict[str, int],
) -> Iterator[tuple[ProgressionIncidence, ProgressionIncidence]]:
    pair_total = len(incidences) * (len(incidences) - 1)
    stats["ordered_seed_pairs"] += pair_total
    if not primitive_only:
        stats["compatible_seed_pairs"] += pair_total
        for r_seed in incidences:
            for q_seed in incidences:
                if r_seed.progression != q_seed.progression:
                    yield r_seed, q_seed
        return

    by_gcd: dict[int, list[ProgressionIncidence]] = {}
    for incidence in incidences:
        by_gcd.setdefault(incidence.root_gcd, []).append(incidence)
    stats["gcd_buckets"] += len(by_gcd)
    buckets = tuple(sorted(by_gcd.items()))
    for r_gcd, r_group in buckets:
        for q_gcd, q_group in buckets:
            pair_count = len(r_group) * len(q_group)
            if r_gcd == q_gcd:
                pair_count -= len(r_group)
            if pair_count == 0:
                continue
            stats["gcd_bucket_pairs_considered"] += 1
            if math.gcd(r_gcd, q_gcd) != 1:
                stats["rejected_nonprimitive_seed"] += pair_count
                continue
            stats["compatible_seed_pairs"] += pair_count
            for r_seed in r_group:
                for q_seed in q_group:
                    if r_seed.progression != q_seed.progression:
                        yield r_seed, q_seed


def _primitive_root_gcd(roots: tuple[int | None, ...]) -> int:
    nonzero = tuple(root for root in roots if root not in (None, 0))
    return math.gcd(*nonzero) if nonzero else 0


def search_lo_shu_seven_box(
    complete_box_root: int,
    *,
    primitive_only: bool = True,
    square_membership_mode: SquareMembershipMode = "isqrt",
    progressions: tuple[ArithmeticProgression, ...] | None = None,
) -> LoShuSevenSearchResult:
    """Cherche toutes les classes Lo Shu exactes 7/9 dans ``0 < case <= R²``.

    Chaque masque à deux cases non carrées conserve une ligne complète dans
    chacune des deux directions de la grille paramétrique ``A+x*q+k*r``. Le
    moteur joint donc deux progressions de carrés sur leur valeur commune et
    reconstruit les quatre cases restantes.
    """

    validate_bound(complete_box_root)
    if progressions is None:
        progressions = generate_square_progressions_parametric_canonical(
            complete_box_root
        )
    if len(set(progressions)) != len(progressions):
        raise ValueError("Le catalogue contient une progression dupliquée.")

    bounded_squares = build_square_membership(complete_box_root, square_membership_mode)
    batch_square_count = (
        bounded_squares.count_bounded_squares
        if isinstance(bounded_squares, IsqrtSquareMembership)
        else None
    )
    by_value: dict[int, list[ProgressionIncidence]] = {}
    for progression in progressions:
        root_gcd = math.gcd(*_progression_roots(progression))
        for term_index, value in enumerate(_progression_values(progression)):
            by_value.setdefault(value, []).append(
                ProgressionIncidence(progression, term_index, root_gcd)
            )

    stats = {
        "progressions": len(progressions),
        "progression_incidences": 3 * len(progressions),
        "indexed_square_values": len(by_value),
        "shared_square_values": 0,
        "gcd_buckets": 0,
        "gcd_bucket_pairs_considered": 0,
        "ordered_seed_pairs": 0,
        "rejected_nonprimitive_seed": 0,
        "compatible_seed_pairs": 0,
        "rejected_equal_steps": 0,
        "reconstructed_grids": 0,
        "rejected_nonpositive": 0,
        "rejected_outside_complete_box": 0,
        "rejected_nondistinct": 0,
        "square_membership_tests": 0,
        "rejected_not_exactly_seven": 0,
        "validated_candidates": 0,
        "rejected_nonprimitive": 0,
        "duplicate_classes": 0,
        "accepted_classes": 0,
    }
    orbit_candidate_counts: dict[str, int] = {}
    hits: dict[Grid, LoShuSevenHit] = {}
    upper = complete_box_root * complete_box_root

    for shared_square, source in sorted(by_value.items()):
        if len(source) < 2:
            continue
        stats["shared_square_values"] += 1
        incidences = tuple(
            sorted(
                source,
                key=lambda item: (
                    item.root_gcd,
                    item.progression.difference,
                    item.term_index,
                ),
            )
        )
        for r_seed, q_seed in _compatible_ordered_incidences(
            incidences,
            primitive_only=primitive_only,
            stats=stats,
        ):
            r = r_seed.progression.difference
            q = q_seed.progression.difference
            if r == q:
                stats["rejected_equal_steps"] += 1
                continue
            x0 = q_seed.term_index
            k0 = r_seed.term_index
            A = shared_square - x0 * q - k0 * r
            grid = build_like_bremner_grid(A, A + q, A + 2 * q, r)
            stats["reconstructed_grids"] += 1
            if min(grid) <= 0:
                stats["rejected_nonpositive"] += 1
                continue
            if max(grid) > upper:
                stats["rejected_outside_complete_box"] += 1
                continue
            if len(set(grid)) != 9:
                stats["rejected_nondistinct"] += 1
                continue

            i0, i1, i2, i3 = REMAINING_GRID_INDICES[x0][k0]
            remaining_values = (grid[i0], grid[i1], grid[i2], grid[i3])
            stats["square_membership_tests"] += 4
            if batch_square_count is not None:
                extra_squares = batch_square_count(remaining_values)
            else:
                extra_squares = sum(
                    value in bounded_squares for value in remaining_values
                )
            if extra_squares != 2:
                stats["rejected_not_exactly_seven"] += 1
                continue

            report = validate_grid(
                grid,
                min_square_count=7,
                require_positive=True,
                require_distinct=True,
                require_primitive=False,
            )
            stats["validated_candidates"] += 1
            if (
                not report.is_magic
                or not report.all_positive
                or not report.all_distinct
                or report.square_count != 7
            ):
                raise ArithmeticError("La reconstruction B4 a produit une grille invalide.")
            orbit_key = mask_orbit(report.square_mask).key
            orbit_candidate_counts[orbit_key] = (
                orbit_candidate_counts.get(orbit_key, 0) + 1
            )
            primitive_root_gcd = _primitive_root_gcd(report.square_roots)
            if primitive_only and primitive_root_gcd != 1:
                stats["rejected_nonprimitive"] += 1
                continue

            canonical = canonical_d4(grid)
            hit = LoShuSevenHit(
                grid=grid,
                canonical=canonical,
                A=A,
                q=q,
                r=r,
                square_mask=report.square_mask,
                mask_orbit=orbit_key,
                square_roots=report.square_roots,
                primitive_root_gcd=primitive_root_gcd,
                shared_square=shared_square,
                r_seed_roots=_progression_roots(r_seed.progression),
                q_seed_roots=_progression_roots(q_seed.progression),
                r_intersection_index=k0,
                q_intersection_index=x0,
            )
            previous = hits.get(canonical)
            if previous is not None:
                stats["duplicate_classes"] += 1
                if grid < previous.grid:
                    hits[canonical] = hit
            else:
                hits[canonical] = hit

    frozen = tuple(hits[key] for key in sorted(hits))
    orbit_class_counts: dict[str, int] = {}
    for hit in frozen:
        orbit_class_counts[hit.mask_orbit] = (
            orbit_class_counts.get(hit.mask_orbit, 0) + 1
        )
    stats["accepted_classes"] = len(frozen)
    stats.update(square_membership_stats(bounded_squares))
    for orbit_key, count in sorted(orbit_candidate_counts.items()):
        stats[f"orbit_candidates_{orbit_key}"] = count
    return LoShuSevenSearchResult(
        "B4-LoShu-exact-7/9-shared-square-index",
        complete_box_root,
        frozen,
        stats,
        orbit_class_counts,
    )
