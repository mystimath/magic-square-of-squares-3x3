"""Structures communes des prototypes J4."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from common.validation import Grid, canonical_d4, validate_grid


@dataclass(frozen=True)
class ArithmeticProgression:
    low_root: int
    center_root: int
    high_root: int
    difference: int

    @property
    def low(self) -> int:
        return self.low_root * self.low_root

    @property
    def center(self) -> int:
        return self.center_root * self.center_root

    @property
    def high(self) -> int:
        return self.high_root * self.high_root


@dataclass(frozen=True)
class SearchResult:
    formulation: str
    max_root: int
    classes: tuple[Grid, ...]
    stats: dict[str, int]


def validate_bound(max_root: int) -> None:
    if isinstance(max_root, bool) or not isinstance(max_root, int) or max_root < 1:
        raise ValueError("max_root doit être un entier positif.")


def build_centered_grid(center: int, p: int, q: int) -> Grid:
    return (
        center - p,
        center + p + q,
        center - q,
        center + p - q,
        center,
        center - p + q,
        center + q,
        center - p - q,
        center + p,
    )


def generate_square_progressions(max_root: int) -> tuple[ArithmeticProgression, ...]:
    """Énumère chaque progression positive de trois carrés une seule fois."""

    validate_bound(max_root)
    squares = {root * root: root for root in range(1, max_root + 1)}
    progressions: list[ArithmeticProgression] = []
    for low_root in range(1, max_root + 1):
        low = low_root * low_root
        for center_root in range(low_root + 1, max_root + 1):
            center = center_root * center_root
            high = 2 * center - low
            high_root = squares.get(high)
            if high_root is None or high_root <= center_root:
                continue
            progressions.append(
                ArithmeticProgression(
                    low_root=low_root,
                    center_root=center_root,
                    high_root=high_root,
                    difference=center - low,
                )
            )
    return tuple(progressions)


def generate_square_progressions_parametric(
    max_root: int,
) -> tuple[ArithmeticProgression, ...]:
    """Génère les progressions via la paramétrisation rationnelle classique.

    Pour des entiers positifs m,n, les trois racines non ordonnées

        m² + 2mn - n²,  m² + n²,  -m² + 2mn + n²

    ont leurs carrés en progression arithmétique. Les dilatations entières sont
    ajoutées explicitement et un ensemble élimine les représentations multiples.
    """

    validate_bound(max_root)
    signatures: set[tuple[int, int, int]] = set()
    parameter_limit = math.isqrt(2 * max_root)
    for m in range(1, parameter_limit + 1):
        m2 = m * m
        for n in range(1, parameter_limit + 1):
            if math.gcd(m, n) != 1:
                continue
            n2 = n * n
            center = m2 + n2
            if center > 2 * max_root:
                continue
            roots = sorted(
                (
                    abs(m2 + 2 * m * n - n2),
                    center,
                    abs(-m2 + 2 * m * n + n2),
                )
            )
            common_factor = math.gcd(*roots)
            roots = [root // common_factor for root in roots]
            low, middle, high = roots
            if low <= 0 or high > max_root or not low < middle < high:
                continue
            if low * low + high * high != 2 * middle * middle:
                raise ArithmeticError("La paramétrisation a produit une progression invalide.")
            for scale in range(1, max_root // high + 1):
                signatures.add((scale * low, scale * middle, scale * high))
    return tuple(
        ArithmeticProgression(low, center, high, center * center - low * low)
        for low, center, high in sorted(signatures)
    )


def accept_grid(
    grid: Iterable[int],
    *,
    max_root: int,
    primitive_only: bool,
) -> Grid | None:
    report = validate_grid(
        grid,
        min_square_count=9,
        require_positive=True,
        require_distinct=True,
        require_primitive=primitive_only,
    )
    if not report.accepted:
        return None
    roots = [math.isqrt(value) for value in report.values]
    if max(roots) > max_root:
        return None
    return canonical_d4(report.values)


def freeze_classes(classes: set[Grid]) -> tuple[Grid, ...]:
    return tuple(sorted(classes))
