"""Validation indépendante des grilles magiques 3×3.

Ce module ne génère aucun candidat. Il applique le contrat mathématique figé
par J0 et les distinctions établies par J2.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Iterable, Sequence

Grid = tuple[int, int, int, int, int, int, int, int, int]
POSITIONS = "abcdefghi"


def _as_grid(values: Sequence[int] | Iterable[int]) -> Grid:
    grid = tuple(values)
    if len(grid) != 9:
        raise ValueError(f"Une grille 3×3 doit contenir 9 valeurs, reçu {len(grid)}.")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in grid):
        raise TypeError("Les neuf valeurs doivent être des entiers, hors booléens.")
    return grid  # type: ignore[return-value]


def square_root(value: int) -> int | None:
    """Retourne la racine exacte d'un carré positif, sinon ``None``."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Le test de carré attend un entier, hors booléen.")
    if value <= 0:
        return None
    root = math.isqrt(value)
    return root if root * root == value else None


def is_positive_square(value: int) -> bool:
    return square_root(value) is not None


def line_sums(values: Sequence[int] | Iterable[int]) -> tuple[int, ...]:
    """Retourne lignes, colonnes, diagonale principale et antidiagonale."""

    a, b, c, d, e, f, g, h, i = _as_grid(values)
    return (
        a + b + c,
        d + e + f,
        g + h + i,
        a + d + g,
        b + e + h,
        c + f + i,
        a + e + i,
        c + e + g,
    )


def is_semimagic(values: Sequence[int] | Iterable[int]) -> bool:
    sums = line_sums(values)
    return len(set(sums[:6])) == 1


def is_magic(values: Sequence[int] | Iterable[int]) -> bool:
    return len(set(line_sums(values))) == 1


def _rotate(grid: Grid) -> Grid:
    return (
        grid[6], grid[3], grid[0],
        grid[7], grid[4], grid[1],
        grid[8], grid[5], grid[2],
    )


def _reflect(grid: Grid) -> Grid:
    return (
        grid[2], grid[1], grid[0],
        grid[5], grid[4], grid[3],
        grid[8], grid[7], grid[6],
    )


def d4_orbit(values: Sequence[int] | Iterable[int]) -> tuple[Grid, ...]:
    """Retourne les transformations géométriques distinctes du groupe D4."""

    grid = _as_grid(values)
    transforms: list[Grid] = []
    current = grid
    for _ in range(4):
        transforms.extend((current, _reflect(current)))
        current = _rotate(current)
    return tuple(dict.fromkeys(transforms))


def canonical_d4(values: Sequence[int] | Iterable[int]) -> Grid:
    return min(d4_orbit(values))


def _permute_grid(grid: Grid, rows: tuple[int, ...], cols: tuple[int, ...]) -> Grid:
    return tuple(grid[3 * row + col] for row in rows for col in cols)  # type: ignore[return-value]


def _transpose(grid: Grid) -> Grid:
    return tuple(grid[3 * row + col] for col in range(3) for row in range(3))  # type: ignore[return-value]


def semimagic_orbit_72(values: Sequence[int] | Iterable[int]) -> tuple[Grid, ...]:
    """Retourne l'orbite sous S3×S3 et transposition.

    Ces opérations préservent les six sommes semi-magiques, mais pas toujours
    les diagonales. Cette fonction diagnostique cette différence ; elle ne doit
    pas servir à canonicaliser une grille magique dans le contrat J0.
    """

    grid = _as_grid(values)
    transforms: list[Grid] = []
    permutations = tuple(itertools.permutations(range(3)))
    for rows in permutations:
        for cols in permutations:
            transformed = _permute_grid(grid, rows, cols)
            transforms.extend((transformed, _transpose(transformed)))
    return tuple(dict.fromkeys(transforms))


def common_square_factor(values: Sequence[int] | Iterable[int]) -> int:
    """Plus grand carré parfait divisant les neuf valeurs.

    La valeur retournée est le carré ``k²`` et non sa racine ``k``.
    """

    grid = _as_grid(values)
    gcd_value = math.gcd(*(abs(value) for value in grid))
    if gcd_value == 0:
        return 0
    factor_root = 1
    divisor = 2
    remaining = gcd_value
    while divisor * divisor <= remaining:
        exponent = 0
        while remaining % divisor == 0:
            remaining //= divisor
            exponent += 1
        factor_root *= divisor ** (exponent // 2)
        divisor = 3 if divisor == 2 else divisor + 2
    return factor_root * factor_root


def is_primitive(values: Sequence[int] | Iterable[int]) -> bool:
    return common_square_factor(values) == 1


@dataclass(frozen=True)
class GridReport:
    values: Grid
    sums: tuple[int, ...]
    magic_sum: int | None
    is_semimagic: bool
    is_magic: bool
    all_positive: bool
    all_distinct: bool
    square_count: int
    square_mask: str
    square_roots: tuple[int | None, ...]
    value_gcd: int
    common_square_factor: int
    is_primitive: bool
    canonical_d4: Grid
    accepted: bool
    failures: tuple[str, ...]


def validate_grid(
    values: Sequence[int] | Iterable[int],
    *,
    min_square_count: int = 9,
    require_positive: bool = True,
    require_distinct: bool = True,
    require_primitive: bool = False,
) -> GridReport:
    """Valide une grille sans dépendre d'un générateur.

    ``min_square_count`` exprime un seuil ``>=k/9``. Le rapport conserve
    toujours le score exact afin de ne pas confondre seuil et score.
    """

    if not 0 <= min_square_count <= 9:
        raise ValueError("min_square_count doit être compris entre 0 et 9.")
    grid = _as_grid(values)
    sums = line_sums(grid)
    semimagic = len(set(sums[:6])) == 1
    magic = len(set(sums)) == 1
    roots = tuple(square_root(value) for value in grid)
    mask = "".join(position for position, root in zip(POSITIONS, roots) if root is not None)
    square_count = sum(root is not None for root in roots)
    positive = all(value > 0 for value in grid)
    distinct = len(set(grid)) == 9
    value_gcd = math.gcd(*(abs(value) for value in grid))
    square_factor = common_square_factor(grid)
    primitive = square_factor == 1
    failures: list[str] = []
    if not magic:
        failures.append("not_magic")
    if require_positive and not positive:
        failures.append("not_strictly_positive")
    if require_distinct and not distinct:
        failures.append("not_pairwise_distinct")
    if square_count < min_square_count:
        failures.append("too_few_square_entries")
    if require_primitive and not primitive:
        failures.append("not_primitive")
    return GridReport(
        values=grid,
        sums=sums,
        magic_sum=sums[0] if magic else None,
        is_semimagic=semimagic,
        is_magic=magic,
        all_positive=positive,
        all_distinct=distinct,
        square_count=square_count,
        square_mask=mask,
        square_roots=roots,
        value_gcd=value_gcd,
        common_square_factor=square_factor,
        is_primitive=primitive,
        canonical_d4=canonical_d4(grid),
        accepted=not failures,
        failures=tuple(failures),
    )
