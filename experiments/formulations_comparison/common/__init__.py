"""Noyau commun de validation pour la comparaison des formulations."""

from .validation import (
    GridReport,
    canonical_d4,
    common_square_factor,
    d4_orbit,
    is_magic,
    is_positive_square,
    is_primitive,
    is_semimagic,
    line_sums,
    semimagic_orbit_72,
    square_root,
    validate_grid,
)

__all__ = [
    "GridReport",
    "canonical_d4",
    "common_square_factor",
    "d4_orbit",
    "is_magic",
    "is_positive_square",
    "is_primitive",
    "is_semimagic",
    "line_sums",
    "semimagic_orbit_72",
    "square_root",
    "validate_grid",
]
