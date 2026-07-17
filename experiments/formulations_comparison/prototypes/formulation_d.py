"""Sonde rationnelle J6 pour E_n : y² = x³ - n²x.

Ce module vérifie des points et des certificats ; il ne calcule ni rang, ni
générateurs du groupe de Mordell–Weil, ni hauteur canonique.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from .formulation_c import RationalSquareProgression
from .model import (
    ArithmeticProgression,
    SearchResult,
    accept_grid,
    build_centered_grid,
    freeze_classes,
    generate_square_progressions,
    validate_bound,
)


@dataclass(frozen=True)
class EllipticPoint:
    x: Fraction
    y: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", Fraction(self.x))
        object.__setattr__(self, "y", Fraction(self.y))


Point = EllipticPoint | None  # None représente le point à l'infini.


def _validate_n(n: int | Fraction) -> Fraction:
    value = Fraction(n)
    if value <= 0:
        raise ValueError("n doit être strictement positif.")
    return value


def rational_square_root(value: Fraction | int) -> Fraction | None:
    value = Fraction(value)
    if value < 0:
        return None
    numerator_root = math.isqrt(value.numerator)
    denominator_root = math.isqrt(value.denominator)
    if numerator_root * numerator_root != value.numerator:
        return None
    if denominator_root * denominator_root != value.denominator:
        return None
    return Fraction(numerator_root, denominator_root)


def is_on_curve(n: int | Fraction, point: Point) -> bool:
    n = _validate_n(n)
    if point is None:
        return True
    return point.y * point.y == point.x**3 - n * n * point.x


def negate(point: Point) -> Point:
    return None if point is None else EllipticPoint(point.x, -point.y)


def add_points(n: int | Fraction, left: Point, right: Point) -> Point:
    n = _validate_n(n)
    if not is_on_curve(n, left) or not is_on_curve(n, right):
        raise ValueError("Les points doivent appartenir à E_n.")
    if left is None:
        return right
    if right is None:
        return left
    if left.x == right.x and left.y == -right.y:
        return None
    if left == right:
        if left.y == 0:
            return None
        slope = (3 * left.x * left.x - n * n) / (2 * left.y)
    else:
        slope = (right.y - left.y) / (right.x - left.x)
    x3 = slope * slope - left.x - right.x
    y3 = slope * (left.x - x3) - left.y
    result = EllipticPoint(x3, y3)
    if not is_on_curve(n, result):
        raise ArithmeticError("La loi de groupe a produit un point invalide.")
    return result


def double_point(n: int | Fraction, point: Point) -> Point:
    return add_points(n, point, point)


def point_from_progression(
    progression: RationalSquareProgression,
) -> tuple[Fraction, EllipticPoint]:
    u = Fraction(progression.low_root)
    v = Fraction(progression.center_root)
    w = Fraction(progression.high_root)
    n = progression.difference
    if n <= 0 or v * v + n != w * w:
        raise ValueError("La progression doit être positive et non constante.")
    point = EllipticPoint(v * v, u * v * w)
    if not is_on_curve(n, point):
        raise ArithmeticError("La progression n'a pas produit un point de E_n.")
    return n, point


def two_descent_square_certificate(
    n: int | Fraction,
    point: EllipticPoint,
) -> tuple[Fraction, Fraction, Fraction] | None:
    """Certifie les trois carrés x-n, x, x+n du critère de 2-descente.

    Le résultat constitue le certificat algébrique utilisé dans J2. Les points
    de 2-torsion et les progressions non strictement positives sont rejetés.
    """

    n = _validate_n(n)
    if not is_on_curve(n, point) or point.y == 0 or point.x <= n:
        return None
    roots = tuple(rational_square_root(value) for value in (point.x - n, point.x, point.x + n))
    if any(root is None for root in roots):
        return None
    low, center, high = roots
    assert low is not None and center is not None and high is not None
    if low * center * high != abs(point.y):
        return None
    return (low, center, high)


def progression_from_point(
    n: int | Fraction,
    point: EllipticPoint,
) -> RationalSquareProgression | None:
    roots = two_descent_square_certificate(n, point)
    if roots is None:
        return None
    return RationalSquareProgression(*roots)


def naive_x_height(point: EllipticPoint) -> int:
    """Hauteur naïve multiplicative de l'abscisse rationnelle."""

    return max(abs(point.x.numerator), point.x.denominator)


def probe_formulation_d(
    max_root: int,
    *,
    primitive_only: bool = False,
    progressions: tuple[ArithmeticProgression, ...] | None = None,
) -> SearchResult:
    """Sonde finie obtenue depuis le catalogue entier de progressions.

    Elle valide la traduction B2–D sur un domaine déjà borné par les racines.
    Elle n'énumère pas les points de E_n par hauteur et n'est donc pas un moteur
    elliptique indépendant.
    """

    validate_bound(max_root)
    integer_progressions = (
        generate_square_progressions(max_root) if progressions is None else progressions
    )
    points_by_n: dict[Fraction, dict[int, EllipticPoint]] = {}
    stats = {
        "progressions": len(integer_progressions),
        "points_constructed": 0,
        "points_on_curve": 0,
        "two_descent_certificates": 0,
        "n_groups": 0,
        "x_pairs": 0,
        "x_ap_tests": 0,
        "x_ap_hits": 0,
        "complete_candidates": 0,
        "accepted_candidates": 0,
        "duplicate_classes": 0,
    }
    for row in integer_progressions:
        progression = RationalSquareProgression(
            Fraction(row.low_root), Fraction(row.center_root), Fraction(row.high_root)
        )
        n, point = point_from_progression(progression)
        stats["points_constructed"] += 1
        if is_on_curve(n, point):
            stats["points_on_curve"] += 1
        if two_descent_square_certificate(n, point) is not None:
            stats["two_descent_certificates"] += 1
        points_by_n.setdefault(n, {})[point.x.numerator] = point
    stats["n_groups"] = len(points_by_n)
    classes = set()
    for n, points in points_by_n.items():
        if n.denominator != 1 or any(point.x.denominator != 1 for point in points.values()):
            raise ArithmeticError("La sonde entière attend n et x entiers.")
        ordered = sorted(points)
        for low_index, low in enumerate(ordered):
            for center in ordered[low_index + 1 :]:
                stats["x_pairs"] += 1
                high = 2 * center - low
                stats["x_ap_tests"] += 1
                if high not in points:
                    continue
                stats["x_ap_hits"] += 1
                grid = build_centered_grid(center, n.numerator, center - low)
                stats["complete_candidates"] += 1
                canonical = accept_grid(grid, max_root=max_root, primitive_only=primitive_only)
                if canonical is None:
                    continue
                if canonical in classes:
                    stats["duplicate_classes"] += 1
                else:
                    classes.add(canonical)
                    stats["accepted_candidates"] += 1
    return SearchResult("D-probe", max_root, freeze_classes(classes), stats)
