"""Cœur B4 consommant des groupes successifs par valeur carrée partagée."""

from __future__ import annotations

from collections.abc import Iterable
import math

from common.validation import Grid, canonical_d4, validate_grid

from .like_bremner import build_like_bremner_grid
from .lo_shu_seven import (
    REMAINING_PARAMETER_COORDINATES,
    LoShuSevenHit,
    LoShuSevenSearchResult,
    ProgressionIncidence,
    _compatible_ordered_incidences,
    _primitive_root_gcd,
    _progression_roots,
    _progression_values,
)
from .model import ArithmeticProgression, validate_bound
from .square_membership import (
    IsqrtSquareMembership,
    SquareMembershipMode,
    build_square_membership,
    square_membership_stats,
)
from .seven_square_masks import mask_orbit


IncidenceGroup = tuple[int, Iterable[ProgressionIncidence]]


def group_progression_incidences(
    progressions: Iterable[ArithmeticProgression],
) -> tuple[tuple[int, tuple[ProgressionIncidence, ...]], ...]:
    """Adapte un catalogue matériel au cœur B4 groupé."""

    by_value: dict[int, list[ProgressionIncidence]] = {}
    for progression in progressions:
        root_gcd = math.gcd(*_progression_roots(progression))
        for term_index, value in enumerate(_progression_values(progression)):
            by_value.setdefault(value, []).append(
                ProgressionIncidence(progression, term_index, root_gcd)
            )
    return tuple(
        (
            value,
            tuple(
                sorted(
                    incidences,
                    key=lambda item: (
                        item.root_gcd,
                        item.progression.difference,
                        item.term_index,
                    ),
                )
            ),
        )
        for value, incidences in sorted(by_value.items())
    )


def search_lo_shu_seven_incidence_groups(
    complete_box_root: int,
    groups: Iterable[IncidenceGroup],
    *,
    primitive_only: bool = True,
    square_membership_mode: SquareMembershipMode = "isqrt",
    validate_incidence_groups: bool = True,
) -> LoShuSevenSearchResult:
    """Cherche les classes 7/9 sans conserver l'index global.

    La validation défensive reste active par défaut. Elle ne peut être omise
    que pour un flux interne qui garantit déjà l'ordre et les incidences.
    """

    validate_bound(complete_box_root)
    bounded_squares = build_square_membership(complete_box_root, square_membership_mode)
    batch_square_count = (
        bounded_squares.count_bounded_squares
        if isinstance(bounded_squares, IsqrtSquareMembership)
        else None
    )
    stats = {
        "progressions": 0,
        "progression_incidences": 0,
        "indexed_square_values": 0,
        "shared_square_values": 0,
        "gcd_buckets": 0,
        "gcd_bucket_pairs_considered": 0,
        "ordered_seed_pairs": 0,
        "rejected_nonprimitive_seed": 0,
        "compatible_seed_pairs": 0,
        "rejected_equal_steps": 0,
        "incidence_group_validation": int(validate_incidence_groups),
        "candidate_parameter_triples": 0,
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
    previous_shared_square = 0

    for shared_square, source in groups:
        if validate_incidence_groups:
            if shared_square <= previous_shared_square:
                raise ValueError(
                    "Les groupes d'incidences doivent être strictement croissants."
                )
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
            if not incidences:
                raise ValueError("Un groupe d'incidences ne peut pas être vide.")
            if len(set(incidences)) != len(incidences):
                raise ValueError("Un groupe contient une incidence dupliquée.")
            for incidence in incidences:
                values = _progression_values(incidence.progression)
                if values[incidence.term_index] != shared_square:
                    raise ValueError(
                        "Une incidence ne correspond pas à sa valeur partagée."
                    )
        else:
            incidences = tuple(source)
        previous_shared_square = shared_square

        stats["indexed_square_values"] += 1
        stats["progression_incidences"] += len(incidences)
        if len(incidences) < 2:
            continue
        stats["shared_square_values"] += 1
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
            stats["candidate_parameter_triples"] += 1
            x0 = q_seed.term_index
            k0 = r_seed.term_index
            A = shared_square - x0 * q - k0 * r
            if A <= 0:
                stats["rejected_nonpositive"] += 1
                continue
            if A + 2 * q + 2 * r > upper:
                stats["rejected_outside_complete_box"] += 1
                continue
            if q == 2 * r or r == 2 * q:
                stats["rejected_nondistinct"] += 1
                continue

            (x1, k1), (x2, k2), (x3, k3), (x4, k4) = (
                REMAINING_PARAMETER_COORDINATES[x0][k0]
            )
            remaining_values = (
                A + x1 * q + k1 * r,
                A + x2 * q + k2 * r,
                A + x3 * q + k3 * r,
                A + x4 * q + k4 * r,
            )
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

            grid = build_like_bremner_grid(A, A + q, A + 2 * q, r)
            stats["reconstructed_grids"] += 1
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

    if stats["progression_incidences"] % 3:
        raise ValueError("Le flux ne contient pas trois incidences par progression.")
    stats["progressions"] = stats["progression_incidences"] // 3
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
        "B4-LoShu-exact-7/9-shared-square-stream",
        complete_box_root,
        frozen,
        stats,
        orbit_class_counts,
    )
