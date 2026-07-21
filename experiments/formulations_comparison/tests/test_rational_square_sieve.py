from __future__ import annotations

from fractions import Fraction
import pathlib
import sys

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from prototypes.rational_square_sieve import (  # noqa: E402
    DEFAULT_LOCAL_PRIMES,
    passes_rational_square_local_sieve,
    rational_local_residues,
    rational_square_local_obstruction,
    two_upper_minus_lower_square_obstruction,
)


def test_rational_squares_always_pass_local_sieve() -> None:
    for numerator in range(-20, 21):
        for denominator in range(1, 21):
            square = Fraction(numerator, denominator) ** 2
            assert passes_rational_square_local_sieve(
                square.numerator, square.denominator
            )


def test_known_nonsquare_has_local_obstruction() -> None:
    obstruction = rational_square_local_obstruction(3, 1)
    assert obstruction in DEFAULT_LOCAL_PRIMES


def test_prime_dividing_denominator_is_inconclusive() -> None:
    assert rational_square_local_obstruction(3, 7, primes=(7,)) is None


def test_precomputed_affine_residues_match_direct_sieve() -> None:
    lower = Fraction(5, 9)
    upper = Fraction(11, 4)
    closing = 2 * upper - lower - 1
    lower_residues = rational_local_residues(lower.numerator, lower.denominator)
    upper_residues = rational_local_residues(upper.numerator, upper.denominator)
    assert (
        two_upper_minus_lower_square_obstruction(
            lower_residues, upper_residues, 1
        )
        == rational_square_local_obstruction(closing.numerator, closing.denominator)
    )