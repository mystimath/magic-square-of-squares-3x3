"""Orbites D4 des masques possédant exactement sept cases carrées."""

from __future__ import annotations

from dataclasses import dataclass

from common.validation import POSITIONS, d4_orbit


@dataclass(frozen=True)
class SevenSquareMaskOrbit:
    key: str
    representative_missing: str
    missing_pairs: tuple[str, ...]

    @property
    def representative_mask(self) -> str:
        return "".join(
            position
            for position in POSITIONS
            if position not in self.representative_missing
        )

    @property
    def masks(self) -> tuple[str, ...]:
        return tuple(
            "".join(
                position
                for position in POSITIONS
                if position not in missing
            )
            for missing in self.missing_pairs
        )


def _missing_orbit(representative: str) -> tuple[str, ...]:
    if len(representative) != 2 or len(set(representative)) != 2:
        raise ValueError("Un représentant doit contenir deux positions distinctes.")
    missing = set(representative)
    indicator = tuple(int(position in missing) for position in POSITIONS)
    transformed = {
        "".join(
            position
            for position, flag in zip(POSITIONS, grid)
            if flag
        )
        for grid in d4_orbit(indicator)
    }
    return tuple(sorted(transformed))


_ORBIT_SPECS = (
    ("center_corner", "ae"),
    ("center_edge", "be"),
    ("corner_corner_adjacent", "ac"),
    ("corner_corner_opposite", "ai"),
    ("edge_edge_adjacent", "bd"),
    ("edge_edge_opposite", "bh"),
    ("corner_edge_incident", "ab"),
    ("corner_edge_nonincident", "af"),
)

SEVEN_SQUARE_MASK_ORBITS = tuple(
    SevenSquareMaskOrbit(key, representative, _missing_orbit(representative))
    for key, representative in _ORBIT_SPECS
)

ORBIT_BY_KEY = {orbit.key: orbit for orbit in SEVEN_SQUARE_MASK_ORBITS}
ORBIT_BY_MASK = {
    mask: orbit
    for orbit in SEVEN_SQUARE_MASK_ORBITS
    for mask in orbit.masks
}

if len(ORBIT_BY_KEY) != 8 or len(ORBIT_BY_MASK) != 36:
    raise ArithmeticError("La partition D4 attendue des 36 masques est incomplète.")


def normalize_square_mask(mask: str) -> str:
    """Valide et remet un masque de positions dans l'ordre ``abcdefghi``."""

    if not isinstance(mask, str):
        raise TypeError("Le masque doit être une chaîne.")
    selected = set(mask)
    if len(mask) != 7 or len(selected) != 7 or not selected <= set(POSITIONS):
        raise ValueError("Le masque doit contenir sept positions distinctes.")
    return "".join(position for position in POSITIONS if position in selected)


def mask_orbit(mask: str) -> SevenSquareMaskOrbit:
    """Retourne l'orbite D4 d'un masque exactement 7/9."""

    return ORBIT_BY_MASK[normalize_square_mask(mask)]
