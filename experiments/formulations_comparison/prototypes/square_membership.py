"""Tests exacts de carré borné, avec ou sans table matérialisée."""

from __future__ import annotations

from collections.abc import Container
from functools import lru_cache
import math
from typing import Literal

from .model import validate_bound


SquareMembershipMode = Literal["isqrt", "cached_isqrt", "residue_isqrt", "materialized_set"]
SquareMembership = Container[int]


def _quadratic_residue_mask(modulus: int) -> int:
    mask = 0
    for residue in range(modulus):
        mask |= 1 << ((residue * residue) % modulus)
    return mask


_SQUARE_CACHE_CAPACITY = 4096
_FILTER_MODULI = (1001, 41, 37, 29, 31)
_QUADRATIC_RESIDUE_FILTERS = tuple(
    (modulus, _quadratic_residue_mask(modulus))
    for modulus in _FILTER_MODULI
)


class IsqrtSquareMembership:
    """Oracle exact direct pour les carrés ``1²`` à ``R²``."""

    __slots__ = (
        "max_root",
        "upper",
        "queries",
        "range_rejections",
        "isqrt_tests",
        "hits",
    )

    def __init__(self, max_root: int) -> None:
        validate_bound(max_root)
        self.max_root = max_root
        self.upper = max_root * max_root
        self.queries = 0
        self.range_rejections = 0
        self.isqrt_tests = 0
        self.hits = 0

    def __contains__(self, value: object) -> bool:
        self.queries += 1
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            or value > self.upper
        ):
            self.range_rejections += 1
            return False
        self.isqrt_tests += 1
        root = math.isqrt(value)
        if root * root != value:
            return False
        self.hits += 1
        return True

    @property
    def stats(self) -> dict[str, int]:
        return {
            "square_oracle_cached_isqrt": 0,
            "square_oracle_isqrt": 1,
            "square_oracle_residue_isqrt": 0,
            "square_oracle_materialized_set": 0,
            "square_oracle_queries": self.queries,
            "square_oracle_range_rejections": self.range_rejections,
            "square_oracle_residue_rejections": 0,
            "square_oracle_isqrt_tests": self.isqrt_tests,
            "square_oracle_hits": self.hits,
        }


    def all_bounded_squares_short_circuit(
        self,
        values: tuple[int, ...],
    ) -> bool:
        """Teste un lot borné en s'arrêtant au premier non-carré."""

        isqrt = math.isqrt
        upper = self.upper
        for value in values:
            self.queries += 1
            if value <= 0 or value > upper:
                self.range_rejections += 1
                return False
            self.isqrt_tests += 1
            root = isqrt(value)
            if root * root != value:
                return False
            self.hits += 1
        return True

    def count_bounded_squares(self, values: tuple[int, ...]) -> int:
        """Compte un lot d'entiers déjà vérifiés dans ``[1, R²]``."""

        self.queries += len(values)
        self.isqrt_tests += len(values)
        hits = 0
        isqrt = math.isqrt
        for value in values:
            root = isqrt(value)
            hits += root * root == value
        self.hits += hits
        return hits

    def all_bounded_squares(self, values: tuple[int, ...]) -> bool:
        return self.count_bounded_squares(values) == len(values)


class CachedIsqrtSquareMembership:
    """Oracle exact avec un LRU de taille fixe autour de ``isqrt``."""

    __slots__ = (
        "max_root",
        "upper",
        "queries",
        "range_rejections",
        "isqrt_tests",
        "hits",
        "_cached_test",
    )

    def __init__(self, max_root: int) -> None:
        validate_bound(max_root)
        self.max_root = max_root
        self.upper = max_root * max_root
        self.queries = 0
        self.range_rejections = 0
        self.isqrt_tests = 0
        self.hits = 0
        self._cached_test = lru_cache(maxsize=_SQUARE_CACHE_CAPACITY)(
            self._test_uncached
        )

    def _test_uncached(self, value: int) -> bool:
        self.isqrt_tests += 1
        root = math.isqrt(value)
        return root * root == value

    def __contains__(self, value: object) -> bool:
        self.queries += 1
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            or value > self.upper
        ):
            self.range_rejections += 1
            return False
        result = self._cached_test(value)
        if result:
            self.hits += 1
        return result

    @property
    def stats(self) -> dict[str, int]:
        cache = self._cached_test.cache_info()
        return {
            "square_oracle_cached_isqrt": 1,
            "square_oracle_isqrt": 0,
            "square_oracle_residue_isqrt": 0,
            "square_oracle_materialized_set": 0,
            "square_oracle_queries": self.queries,
            "square_oracle_range_rejections": self.range_rejections,
            "square_oracle_residue_rejections": 0,
            "square_oracle_isqrt_tests": self.isqrt_tests,
            "square_oracle_hits": self.hits,
            "square_oracle_cache_capacity": _SQUARE_CACHE_CAPACITY,
            "square_oracle_cache_hits": cache.hits,
            "square_oracle_cache_misses": cache.misses,
            "square_oracle_cache_current_size": cache.currsize,
        }


class ResidueIsqrtSquareMembership:
    """Oracle exact à mémoire constante pour les carrés ``1²`` à ``R²``."""

    __slots__ = (
        "max_root",
        "upper",
        "queries",
        "range_rejections",
        "residue_rejections",
        "isqrt_tests",
        "hits",
    )

    def __init__(self, max_root: int) -> None:
        validate_bound(max_root)
        self.max_root = max_root
        self.upper = max_root * max_root
        self.queries = 0
        self.range_rejections = 0
        self.residue_rejections = [0] * len(_QUADRATIC_RESIDUE_FILTERS)
        self.isqrt_tests = 0
        self.hits = 0

    def __contains__(self, value: object) -> bool:
        self.queries += 1
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value <= 0
            or value > self.upper
        ):
            self.range_rejections += 1
            return False
        for index, (modulus, residue_mask) in enumerate(
            _QUADRATIC_RESIDUE_FILTERS
        ):
            if not (residue_mask >> (value % modulus)) & 1:
                self.residue_rejections[index] += 1
                return False
        self.isqrt_tests += 1
        root = math.isqrt(value)
        if root * root != value:
            return False
        self.hits += 1
        return True

    @property
    def stats(self) -> dict[str, int]:
        payload = {
            "square_oracle_cached_isqrt": 0,
            "square_oracle_isqrt": 0,
            "square_oracle_residue_isqrt": 1,
            "square_oracle_materialized_set": 0,
            "square_oracle_queries": self.queries,
            "square_oracle_range_rejections": self.range_rejections,
            "square_oracle_residue_rejections": sum(self.residue_rejections),
            "square_oracle_isqrt_tests": self.isqrt_tests,
            "square_oracle_hits": self.hits,
        }
        payload.update(
            {
                f"square_oracle_mod{modulus}_rejections": rejected
                for modulus, rejected in zip(
                    _FILTER_MODULI,
                    self.residue_rejections,
                )
            }
        )
        return payload


def build_square_membership(
    max_root: int,
    mode: SquareMembershipMode = "isqrt",
) -> SquareMembership:
    validate_bound(max_root)
    if mode == "isqrt":
        return IsqrtSquareMembership(max_root)
    if mode == "cached_isqrt":
        return CachedIsqrtSquareMembership(max_root)
    if mode == "residue_isqrt":
        return ResidueIsqrtSquareMembership(max_root)
    if mode == "materialized_set":
        return {root * root for root in range(1, max_root + 1)}
    raise ValueError(f"Mode de test de carré inconnu : {mode}")


def square_membership_stats(membership: SquareMembership) -> dict[str, int]:
    if isinstance(membership, IsqrtSquareMembership):
        return membership.stats
    if isinstance(membership, CachedIsqrtSquareMembership):
        return membership.stats
    if isinstance(membership, ResidueIsqrtSquareMembership):
        return membership.stats
    return {
        "square_oracle_cached_isqrt": 0,
        "square_oracle_isqrt": 0,
        "square_oracle_residue_isqrt": 0,
        "square_oracle_materialized_set": 1,
    }
