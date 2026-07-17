"""Prototype C : progressions de carrés vues comme triangles de même aire."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .model import (
    ArithmeticProgression,
    SearchResult,
    accept_grid,
    build_centered_grid,
    freeze_classes,
    generate_square_progressions,
    validate_bound,
)


def _fraction(value: int | Fraction) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


@dataclass(frozen=True)
class RationalTriangle:
    leg_a: Fraction
    leg_b: Fraction
    hypotenuse: Fraction

    def __post_init__(self) -> None:
        a = _fraction(self.leg_a)
        b = _fraction(self.leg_b)
        c = _fraction(self.hypotenuse)
        if min(a, b, c) <= 0:
            raise ValueError("Les côtés du triangle doivent être strictement positifs.")
        if a > b:
            a, b = b, a
        if a * a + b * b != c * c:
            raise ValueError("Les côtés ne forment pas un triangle rectangle exact.")
        object.__setattr__(self, "leg_a", a)
        object.__setattr__(self, "leg_b", b)
        object.__setattr__(self, "hypotenuse", c)

    @property
    def area(self) -> Fraction:
        return self.leg_a * self.leg_b / 2

    @property
    def similarity_key(self) -> tuple[Fraction, Fraction, Fraction]:
        scale = self.leg_a
        return (Fraction(1), self.leg_b / scale, self.hypotenuse / scale)


@dataclass(frozen=True)
class RationalSquareProgression:
    low_root: Fraction
    center_root: Fraction
    high_root: Fraction

    @property
    def difference(self) -> Fraction:
        return self.center_root * self.center_root - self.low_root * self.low_root


def progression_to_triangle(
    progression: ArithmeticProgression | RationalSquareProgression,
) -> RationalTriangle:
    u = _fraction(progression.low_root)
    v = _fraction(progression.center_root)
    w = _fraction(progression.high_root)
    if not 0 <= u < v < w:
        raise ValueError("Les racines doivent vérifier 0 <= u < v < w.")
    if v * v - u * u != w * w - v * v:
        raise ValueError("Les trois carrés ne sont pas en progression arithmétique.")
    return RationalTriangle(w - u, w + u, 2 * v)


def triangle_to_progression(triangle: RationalTriangle) -> RationalSquareProgression:
    a, b, c = triangle.leg_a, triangle.leg_b, triangle.hypotenuse
    progression = RationalSquareProgression((b - a) / 2, c / 2, (a + b) / 2)
    if progression.difference != triangle.area:
        raise ArithmeticError("La conversion triangle–progression a perdu l'aire exacte.")
    return progression


def search_formulation_c(
    max_root: int,
    *,
    primitive_only: bool = False,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
) -> SearchResult:
    validate_bound(max_root)
    if progressions is None:
        progressions = generate_square_progressions(max_root)
    triangles = tuple(progression_to_triangle(row) for row in progressions)
    centers_by_area: dict[Fraction, set[int]] = {}
    for progression, triangle in zip(progressions, triangles):
        if triangle.area != progression.difference:
            raise ArithmeticError("L'aire et la différence doivent coïncider.")
        centers_by_area.setdefault(triangle.area, set()).add(progression.center)
    classes = set()
    stats = {
        "progressions": len(progressions),
        "triangles": len(triangles),
        "area_groups": len(centers_by_area),
        "similarity_classes": len({triangle.similarity_key for triangle in triangles}),
        "center_pairs": 0,
        "hypotenuse_square_ap_tests": 0,
        "hypotenuse_square_ap_hits": 0,
        "complete_candidates": 0,
        "accepted_candidates": 0,
        "duplicate_classes": 0,
    }
    for area, centers in centers_by_area.items():
        if area.denominator != 1:
            raise ArithmeticError("Le catalogue entier doit avoir des aires entières.")
        difference = area.numerator
        ordered = sorted(centers)
        for low_index, low in enumerate(ordered):
            for center in ordered[low_index + 1 :]:
                stats["center_pairs"] += 1
                high = 2 * center - low
                stats["hypotenuse_square_ap_tests"] += 1
                if high not in centers:
                    continue
                stats["hypotenuse_square_ap_hits"] += 1
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
    return SearchResult("C", max_root, freeze_classes(classes), stats)
