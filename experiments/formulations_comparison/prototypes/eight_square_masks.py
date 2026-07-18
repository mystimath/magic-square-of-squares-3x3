"""Orbites D4 des masques possédant exactement huit cases carrées."""

from __future__ import annotations

from dataclasses import dataclass

from common.validation import POSITIONS, d4_orbit


@dataclass(frozen=True)
class EightSquareMaskOrbit:
    key: str
    representative_missing: str
    missing_positions: tuple[str, ...]

    @property
    def representative_mask(self) -> str:
        return "".join(
            position
            for position in POSITIONS
            if position != self.representative_missing
        )

    @property
    def masks(self) -> tuple[str, ...]:
        return tuple(
            "".join(
                position for position in POSITIONS if position != missing
            )
            for missing in self.missing_positions
        )


def _missing_orbit(representative: str) -> tuple[str, ...]:
    if representative not in POSITIONS:
        raise ValueError("Le représentant doit être une position de la grille.")
    indicator = tuple(int(position == representative) for position in POSITIONS)
    transformed = {
        next(
            position
            for position, flag in zip(POSITIONS, grid)
            if flag
        )
        for grid in d4_orbit(indicator)
    }
    return tuple(sorted(transformed))


_ORBIT_SPECS = (
    ("center", "e"),
    ("corner", "a"),
    ("edge", "b"),
)

EIGHT_SQUARE_MASK_ORBITS = tuple(
    EightSquareMaskOrbit(key, representative, _missing_orbit(representative))
    for key, representative in _ORBIT_SPECS
)

ORBIT_BY_KEY = {orbit.key: orbit for orbit in EIGHT_SQUARE_MASK_ORBITS}
ORBIT_BY_MASK = {
    mask: orbit
    for orbit in EIGHT_SQUARE_MASK_ORBITS
    for mask in orbit.masks
}

if len(ORBIT_BY_KEY) != 3 or len(ORBIT_BY_MASK) != 9:
    raise ArithmeticError("La partition D4 attendue des neuf masques est incomplète.")


def normalize_square_mask(mask: str) -> str:
    if not isinstance(mask, str):
        raise TypeError("Le masque doit être une chaîne.")
    selected = set(mask)
    if len(mask) != 8 or len(selected) != 8 or not selected <= set(POSITIONS):
        raise ValueError("Le masque doit contenir huit positions distinctes.")
    return "".join(position for position in POSITIONS if position in selected)


def mask_orbit(mask: str) -> EightSquareMaskOrbit:
    return ORBIT_BY_MASK[normalize_square_mask(mask)]
