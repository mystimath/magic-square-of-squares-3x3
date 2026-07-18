"""Prototype Lo Shu ciblé sur le motif de Bremner ``acdefgh`` (7/9)."""

from __future__ import annotations

from dataclasses import dataclass
import math

from common.validation import Grid, canonical_d4, validate_grid

from .model import (
    ArithmeticProgression,
    generate_square_progressions_parametric,
    validate_bound,
)

TARGET_MASK = "acdefgh"


@dataclass(frozen=True)
class LikeBremnerHit:
    grid: Grid
    canonical: Grid
    A: int
    B: int
    C: int
    r: int
    q: int
    square_roots: tuple[int | None, ...]
    primitive_root_gcd: int


@dataclass(frozen=True)
class LikeBremnerSearchResult:
    formulation: str
    bound_root: int
    hits: tuple[LikeBremnerHit, ...]
    stats: dict[str, int]

    @property
    def classes(self) -> tuple[Grid, ...]:
        return tuple(hit.canonical for hit in self.hits)


def build_like_bremner_grid(A: int, B: int, C: int, r: int) -> Grid:
    """Construit la forme pleinement magique issue de Lo Shu.

    ``A,B,C`` doivent former une progression de raison ``q``. Le motif ciblé
    exige que ``A,A+r,A+2r``, ``B,B+r`` et ``C,C+r`` soient des carrés ; les
    deux termes forcés ``C+2r`` et ``B+2r`` doivent rester non carrés.
    """

    if any(isinstance(value, bool) or not isinstance(value, int) for value in (A, B, C, r)):
        raise TypeError("A, B, C et r doivent être des entiers, hors booléens.")
    if A + C != 2 * B:
        raise ValueError("A, B et C doivent former une progression arithmétique.")
    return (
        B,
        C + 2 * r,
        A + r,
        A + 2 * r,
        B + r,
        C,
        C + r,
        A,
        B + 2 * r,
    )


def _primitive_root_gcd(roots: tuple[int | None, ...]) -> int:
    square_roots = tuple(root for root in roots if root not in (None, 0))
    return math.gcd(*square_roots) if square_roots else 0


def search_like_bremner(
    max_square_root: int,
    *,
    primitive_only: bool = True,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
    early_primitive_filter: bool = True,
) -> LikeBremnerSearchResult:
    """Recherche sous une borne des racines carrées, et non une boîte complète.

    Produit les classes D4 de motif canonique exact ``acdefgh``.

    L'algorithme joint deux progressions de carrés ayant le même premier terme
    ``A`` : l'une fournit la raison verticale ``r`` et l'autre les premiers
    termes ``A,B,C`` nécessaires à la magie complète. Il ne parcourt ni les
    centres arbitraires, ni les couples généraux d'offsets.
    """

    validate_bound(max_square_root)
    if progressions is None:
        progressions = generate_square_progressions_parametric(max_square_root)
    by_first: dict[int, list[ArithmeticProgression]] = {}
    for progression in progressions:
        by_first.setdefault(progression.low, []).append(progression)
    bounded_squares = {root * root for root in range(1, max_square_root + 1)}
    stats = {
        "progressions": len(progressions),
        "early_primitive_filter_enabled": int(primitive_only and early_primitive_filter),
        "first_term_groups": len(by_first),
        "groups_with_two_progressions": 0,
        "ordered_progression_pairs": 0,
        "rejected_nonprimitive_seed": 0,
        "square_membership_tests": 0,
        "pair_extension_hits": 0,
        "validated_candidates": 0,
        "rejected_mask": 0,
        "rejected_nonprimitive": 0,
        "duplicate_classes": 0,
        "accepted_classes": 0,
    }
    hits: dict[Grid, LikeBremnerHit] = {}
    for A, group in sorted(by_first.items()):
        if len(group) < 2:
            continue
        stats["groups_with_two_progressions"] += 1
        ordered = sorted(group, key=lambda progression: progression.difference)
        for vertical in ordered:
            r = vertical.difference
            for horizontal in ordered:
                if horizontal == vertical:
                    continue
                stats["ordered_progression_pairs"] += 1
                # Si ces cinq racines partagent g > 1, les deux extensions
                # carrées sont aussi multiples de g : la classe ne peut pas
                # être primitive. Ce rejet précède les tests d'appartenance.
                if primitive_only and early_primitive_filter and math.gcd(
                    vertical.low_root,
                    vertical.center_root,
                    vertical.high_root,
                    horizontal.center_root,
                    horizontal.high_root,
                ) != 1:
                    stats["rejected_nonprimitive_seed"] += 1
                    continue
                B, C = horizontal.center, horizontal.high
                stats["square_membership_tests"] += 2
                if B + r not in bounded_squares or C + r not in bounded_squares:
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
                    raise ArithmeticError("Le générateur spécialisé a produit une grille invalide.")
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
    return LikeBremnerSearchResult("LoShu-Bremner-7/9", max_square_root, frozen, stats)
