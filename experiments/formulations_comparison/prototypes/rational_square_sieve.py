"""Filtres locaux nécessaires pour les carrés rationnels."""

from __future__ import annotations

import math
from collections.abc import Iterable
from functools import lru_cache


DEFAULT_LOCAL_PRIMES = (13, 29, 19, 17, 23, 31, 7, 11, 37, 41, 43, 47, 53, 59, 61, 67)


@lru_cache(maxsize=None)
def _quadratic_residues(prime: int) -> frozenset[int]:
    return frozenset((value * value) % prime for value in range(prime))


def rational_square_local_obstruction(
    numerator: int,
    denominator: int,
    primes: Iterable[int] = DEFAULT_LOCAL_PRIMES,
) -> int | None:
    """Retourne un premier qui interdit le carré rationnel, sinon ``None``.

    Si le dénominateur est nul modulo ``p``, le test local est indécis et passe
    au premier suivant. L'absence d'obstruction n'est pas une preuve de carré.
    """
    numerator = int(numerator)
    denominator = int(denominator)
    if denominator == 0:
        raise ZeroDivisionError("Le dénominateur rationnel ne peut pas être nul.")
    common = math.gcd(numerator, denominator)
    numerator //= common
    denominator //= common
    for prime in primes:
        if prime < 3:
            raise ValueError("Le tamis exige des nombres premiers impairs.")
        denominator_mod = denominator % prime
        if denominator_mod == 0:
            continue
        residue = numerator % prime * pow(denominator_mod, -1, prime) % prime
        if residue not in _quadratic_residues(prime):
            return prime
    return None


def passes_rational_square_local_sieve(
    numerator: int,
    denominator: int,
    primes: Iterable[int] = DEFAULT_LOCAL_PRIMES,
) -> bool:
    return rational_square_local_obstruction(numerator, denominator, primes) is None


def rational_local_residues(
    numerator: int,
    denominator: int,
    primes: Iterable[int] = DEFAULT_LOCAL_PRIMES,
) -> tuple[int | None, ...]:
    """Pré-calcule un rationnel modulo chaque premier, ou ``None`` si indécis."""
    numerator = int(numerator)
    denominator = int(denominator)
    if denominator == 0:
        raise ZeroDivisionError("Le dénominateur rationnel ne peut pas être nul.")
    common = math.gcd(numerator, denominator)
    numerator //= common
    denominator //= common
    return tuple(
        None
        if denominator % prime == 0
        else numerator % prime * pow(denominator % prime, -1, prime) % prime
        for prime in primes
    )


def two_upper_minus_lower_square_obstruction(
    lower_residues: Iterable[int | None],
    upper_residues: Iterable[int | None],
    constant: int,
    primes: Iterable[int] = DEFAULT_LOCAL_PRIMES,
) -> int | None:
    """Tamise ``2*upper-lower-constant`` depuis des résidus pré-calculés."""
    for prime, lower, upper in zip(primes, lower_residues, upper_residues):
        if lower is None or upper is None:
            continue
        residue = (2 * upper - lower - constant) % prime
        if residue not in _quadratic_residues(prime):
            return prime
    return None