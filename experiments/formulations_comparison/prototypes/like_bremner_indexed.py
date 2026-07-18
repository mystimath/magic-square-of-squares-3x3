"""Branche B3 : jointure Lo Shu indexée par PGCD compatible."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
import math

from common.validation import Grid, canonical_d4, validate_grid

from .like_bremner import (
    TARGET_MASK,
    LikeBremnerHit,
    LikeBremnerSearchResult,
    build_like_bremner_grid,
)
from .model import ArithmeticProgression, validate_bound
from .square_membership import (
    IsqrtSquareMembership,
    SquareMembershipMode,
    build_square_membership,
    square_membership_stats,
)

ProgressionGroup = tuple[int, Iterable[ArithmeticProgression]]


def group_progressions_by_first(
    progressions: Iterable[ArithmeticProgression],
) -> tuple[tuple[int, tuple[ArithmeticProgression, ...]], ...]:
    """Groupe un catalogue matériel par premier carré ``A``."""

    by_first: dict[int, list[ArithmeticProgression]] = {}
    for progression in progressions:
        by_first.setdefault(progression.low, []).append(progression)
    return tuple(
        (
            first,
            tuple(sorted(group, key=lambda progression: progression.difference)),
        )
        for first, group in sorted(by_first.items())
    )


def _root_gcd(progression: ArithmeticProgression) -> int:
    return math.gcd(
        progression.low_root,
        progression.center_root,
        progression.high_root,
    )


def _compatible_ordered_pairs(
    ordered: tuple[ArithmeticProgression, ...],
    *,
    primitive_only: bool,
    stats: dict[str, int],
) -> Iterator[tuple[ArithmeticProgression, ArithmeticProgression]]:
    """Évite de matérialiser les couples dont les PGCD sont incompatibles."""

    total_pairs = len(ordered) * (len(ordered) - 1)
    stats["ordered_progression_pairs"] += total_pairs
    if not primitive_only:
        stats["compatible_progression_pairs"] += total_pairs
        for vertical in ordered:
            for horizontal in ordered:
                if horizontal != vertical:
                    yield vertical, horizontal
        return

    by_root_gcd: dict[int, list[ArithmeticProgression]] = {}
    for progression in ordered:
        by_root_gcd.setdefault(_root_gcd(progression), []).append(progression)
    stats["gcd_buckets"] += len(by_root_gcd)
    bucket_items = tuple(sorted(by_root_gcd.items()))
    for vertical_gcd, vertical_group in bucket_items:
        for horizontal_gcd, horizontal_group in bucket_items:
            pair_count = len(vertical_group) * len(horizontal_group)
            if vertical_gcd == horizontal_gcd:
                pair_count -= len(vertical_group)
            if pair_count == 0:
                continue
            stats["gcd_bucket_pairs_considered"] += 1
            if math.gcd(vertical_gcd, horizontal_gcd) != 1:
                stats["rejected_nonprimitive_seed"] += pair_count
                continue
            stats["compatible_progression_pairs"] += pair_count
            for vertical in vertical_group:
                for horizontal in horizontal_group:
                    if horizontal != vertical:
                        yield vertical, horizontal


def _primitive_root_gcd(roots: tuple[int | None, ...]) -> int:
    nonzero = tuple(root for root in roots if root not in (None, 0))
    return math.gcd(*nonzero) if nonzero else 0


def search_like_bremner_indexed_groups(
    max_square_root: int,
    groups: Iterable[ProgressionGroup],
    *,
    primitive_only: bool = True,
    square_membership_mode: SquareMembershipMode = "isqrt",
) -> LikeBremnerSearchResult:
    """Consomme des groupes successifs de progressions partageant leur ``A``.

    Cette interface ne requiert pas que tous les groupes résident simultanément
    en mémoire. Un futur générateur par fichiers ou par tranches peut donc
    alimenter directement le cœur B3.
    """

    validate_bound(max_square_root)
    bounded_squares = build_square_membership(max_square_root, square_membership_mode)
    batch_square_test = (
        bounded_squares.all_bounded_squares_short_circuit
        if isinstance(bounded_squares, IsqrtSquareMembership)
        else None
    )
    stats = {
        "progressions": 0,
        "first_term_groups": 0,
        "groups_with_two_progressions": 0,
        "gcd_buckets": 0,
        "gcd_bucket_pairs_considered": 0,
        "ordered_progression_pairs": 0,
        "rejected_nonprimitive_seed": 0,
        "compatible_progression_pairs": 0,
        "square_membership_tests": 0,
        "pair_extension_hits": 0,
        "validated_candidates": 0,
        "rejected_mask": 0,
        "rejected_nonprimitive": 0,
        "duplicate_classes": 0,
        "accepted_classes": 0,
    }
    hits: dict[Grid, LikeBremnerHit] = {}
    for A, source_group in groups:
        ordered = tuple(
            sorted(source_group, key=lambda progression: progression.difference)
        )
        stats["first_term_groups"] += 1
        stats["progressions"] += len(ordered)
        if any(progression.low != A for progression in ordered):
            raise ValueError("Un groupe contient une progression de premier terme différent.")
        if len(set(ordered)) != len(ordered):
            raise ValueError("Un groupe contient une progression dupliquée.")
        if len(ordered) < 2:
            continue
        stats["groups_with_two_progressions"] += 1
        for vertical, horizontal in _compatible_ordered_pairs(
            ordered,
            primitive_only=primitive_only,
            stats=stats,
        ):
            r = vertical.difference
            B, C = horizontal.center, horizontal.high
            stats["square_membership_tests"] += 2
            extension_values = (B + r, C + r)
            if batch_square_test is not None:
                extensions_are_squares = batch_square_test(extension_values)
            else:
                extensions_are_squares = (
                    extension_values[0] in bounded_squares
                    and extension_values[1] in bounded_squares
                )
            if not extensions_are_squares:
                continue
            stats["pair_extension_hits"] += 1
            grid = build_like_bremner_grid(A, B, C, r)
            report = validate_grid(
                grid,
                min_square_count=7,
                require_positive=True,
                require_distinct=True,
                require_primitive=False,
            )
            stats["validated_candidates"] += 1
            if not report.is_magic or not report.all_positive or not report.all_distinct:
                raise ArithmeticError("Le générateur B3 a produit une grille invalide.")
            if report.square_count != 7 or report.square_mask != TARGET_MASK:
                stats["rejected_mask"] += 1
                continue
            primitive_root_gcd = _primitive_root_gcd(report.square_roots)
            if primitive_only and primitive_root_gcd != 1:
                stats["rejected_nonprimitive"] += 1
                continue
            canonical = canonical_d4(grid)
            hit = LikeBremnerHit(
                grid=grid,
                canonical=canonical,
                A=A,
                B=B,
                C=C,
                r=r,
                q=B - A,
                square_roots=report.square_roots,
                primitive_root_gcd=primitive_root_gcd,
            )
            if canonical in hits:
                stats["duplicate_classes"] += 1
                if grid < hits[canonical].grid:
                    hits[canonical] = hit
            else:
                hits[canonical] = hit
    frozen = tuple(hits[key] for key in sorted(hits))
    stats["accepted_classes"] = len(frozen)
    stats.update(square_membership_stats(bounded_squares))
    return LikeBremnerSearchResult(
        "B3-LoShu-Bremner-7/9-gcd-indexed",
        max_square_root,
        frozen,
        stats,
    )


def search_like_bremner_indexed(
    max_square_root: int,
    *,
    primitive_only: bool = True,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
    square_membership_mode: SquareMembershipMode = "isqrt",
) -> LikeBremnerSearchResult:
    """Adapte un catalogue matériel au cœur B3 groupé."""

    validate_bound(max_square_root)
    if progressions is None:
        from .canonical_progressions import (
            generate_square_progressions_parametric_canonical,
        )

        progressions = generate_square_progressions_parametric_canonical(
            max_square_root
        )
    return search_like_bremner_indexed_groups(
        max_square_root,
        group_progressions_by_first(progressions),
        primitive_only=primitive_only,
        square_membership_mode=square_membership_mode,
    )


def search_like_bremner_indexed_box(
    complete_box_root: int,
    *,
    primitive_only: bool = True,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
    square_membership_mode: SquareMembershipMode = "isqrt",
) -> LikeBremnerSearchResult:
    """Ajoute la contrainte ``0 < case <= complete_box_root²`` aux neuf cases."""

    result = search_like_bremner_indexed(
        complete_box_root,
        primitive_only=primitive_only,
        progressions=progressions,
        square_membership_mode=square_membership_mode,
    )
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
