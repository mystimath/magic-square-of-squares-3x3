"""Pont entre une sortie elliptique normalisée et le scanner B4 exact 7/9."""

from __future__ import annotations

import json
from math import isqrt
from pathlib import Path
from typing import Sequence

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


def progressions_from_d0_artifact(path: Path) -> tuple[ArithmeticProgression, ...]:
    """Charge les grilles entières d'un artefact D0 et en extrait les graines B4."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    progressions: set[ArithmeticProgression] = set()
    for candidate in payload.get("candidates", []):
        normalized = candidate.get("integer_normalization")
        raw_grid = normalized["grid"] if normalized is not None else candidate["grid"]
        progressions.update(progressions_from_integer_grid(tuple(map(int, raw_grid))))
    return tuple(sorted(progressions, key=lambda item: (item.low, item.difference)))


def search_b4_from_d0_artifact(path: Path, complete_box_root: int):
    """Injecte un petit catalogue elliptique dans B4, sans catalogue paramétrique global."""
    progressions = progressions_from_d0_artifact(path)
    return search_lo_shu_seven_box(
        complete_box_root,
        primitive_only=True,
        progressions=progressions,
    )