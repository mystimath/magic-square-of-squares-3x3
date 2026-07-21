"""Pont entre des sorties elliptiques normalisées et le scanner B4 exact 7/9."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping, Sequence
from math import isqrt
from pathlib import Path

from common.validation import POSITIONS

from .lo_shu_seven import PARAMETER_POSITIONS, search_lo_shu_seven_box
from .model import ArithmeticProgression


def _square_root(value: int) -> int | None:
    if value <= 0:
        return None
    root = isqrt(value)
    return root if root * root == value else None


def progressions_from_integer_grid(grid: Sequence[int]) -> tuple[ArithmeticProgression, ...]:
    """Extrait les lignes/colonnes paramétriques entièrement carrées d'une grille.

    La grille est donnée dans l'ordre ``abcdefghi``. Les lignes et colonnes de
    ``PARAMETER_POSITIONS`` sont les progressions arithmétiques de la forme
    Lo Shu additive ``A + x*q + k*r``. Seules celles dont les trois termes sont
    des carrés positifs distincts sont retenues.
    """
    if len(grid) != 9:
        raise ValueError("La grille doit contenir neuf entiers.")
    values = tuple(int(value) for value in grid)
    by_position = dict(zip(POSITIONS, values))
    directions = list(PARAMETER_POSITIONS) + [
        tuple(PARAMETER_POSITIONS[row][column] for row in range(3))
        for column in range(3)
    ]
    progressions: set[ArithmeticProgression] = set()
    for positions in directions:
        triple = tuple(by_position[position] for position in positions)
        roots = tuple(_square_root(value) for value in triple)
        if any(root is None for root in roots):
            continue
        low, center, high = triple
        if not (low < center < high and low + high == 2 * center):
            continue
        low_root, center_root, high_root = roots
        assert low_root is not None and center_root is not None and high_root is not None
        progressions.add(
            ArithmeticProgression(
                low_root, center_root, high_root, center - low
            )
        )
    return tuple(sorted(progressions, key=lambda item: (item.low, item.difference)))


def _integer_candidate_grids(node: object) -> Iterator[tuple[int, ...]]:
    """Parcourt les artefacts D0--D2 et rend leurs grilles entières normalisées."""
    if isinstance(node, Mapping):
        normalized = node.get("integer_normalization")
        if isinstance(normalized, Mapping) and isinstance(normalized.get("grid"), list):
            grid = tuple(map(int, normalized["grid"]))
            if len(grid) == 9:
                yield grid
        elif isinstance(node.get("grid"), list):
            try:
                grid = tuple(map(int, node["grid"]))
            except ValueError:
                grid = ()
            if len(grid) == 9:
                yield grid
        for key, value in node.items():
            if key != "integer_normalization":
                yield from _integer_candidate_grids(value)
    elif isinstance(node, list):
        for value in node:
            yield from _integer_candidate_grids(value)


def integer_grids_from_elliptic_artifact(path: Path) -> tuple[tuple[int, ...], ...]:
    """Charge et déduplique les grilles entières de tout artefact D0, D1 ou D2."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(sorted(set(_integer_candidate_grids(payload))))


def progressions_from_elliptic_artifact(path: Path) -> tuple[ArithmeticProgression, ...]:
    """Extrait les graines B4 d'un artefact elliptique D0, D1 ou D2."""
    progressions: set[ArithmeticProgression] = set()
    for grid in integer_grids_from_elliptic_artifact(path):
        progressions.update(progressions_from_integer_grid(grid))
    return tuple(sorted(progressions, key=lambda item: (item.low, item.difference)))


def progressions_from_d0_artifact(path: Path) -> tuple[ArithmeticProgression, ...]:
    """Alias de compatibilité pour l'ancien nom D0."""
    return progressions_from_elliptic_artifact(path)


def inferred_complete_box_root(grids: Sequence[Sequence[int]]) -> int:
    """Plus petite borne B4 couvrant les valeurs des grilles fournies."""
    maximum = max((value for grid in grids for value in grid), default=1)
    return isqrt(maximum - 1) + 1


def search_b4_from_elliptic_artifact(path: Path, complete_box_root: int | None = None):
    """Injecte un catalogue elliptique dans B4, sans catalogue paramétrique global."""
    grids = integer_grids_from_elliptic_artifact(path)
    progressions = progressions_from_elliptic_artifact(path)
    bound = inferred_complete_box_root(grids) if complete_box_root is None else complete_box_root
    return search_lo_shu_seven_box(bound, primitive_only=True, progressions=progressions)


def search_b4_from_d0_artifact(path: Path, complete_box_root: int):
    """Alias de compatibilité pour l'ancien point d'entrée D0."""
    return search_b4_from_elliptic_artifact(path, complete_box_root)