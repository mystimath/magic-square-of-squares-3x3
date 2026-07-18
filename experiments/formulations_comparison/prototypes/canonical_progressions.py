"""Domaine fondamental sans doublons pour les progressions de trois carrés."""

from __future__ import annotations

from collections.abc import Iterator
import math
import pathlib

from .model import ArithmeticProgression, validate_bound
from .streaming_progressions import ParametricProgressionGroupStream, _RECORD


def iter_canonical_progression_signatures(
    max_square_root: int,
) -> Iterator[tuple[int, int, int]]:
    """Émet chaque triplet de racines une seule fois, dilatations comprises.

    Les quatre représentants positifs usuels sont réduits au domaine

        m < n < (1 + sqrt(2)) m,

    dont la seconde inégalité est testée exactement par
    ``(n-m)² < 2m²``.
    """

    validate_bound(max_square_root)
    parameter_limit = math.isqrt(2 * max_square_root)
    for m in range(1, parameter_limit + 1):
        m2 = m * m
        for n in range(m + 1, parameter_limit + 1):
            if (n - m) * (n - m) >= 2 * m2:
                break
            if math.gcd(m, n) != 1:
                continue
            n2 = n * n
            center = m2 + n2
            if center > 2 * max_square_root:
                continue
            roots = sorted(
                (
                    abs(m2 + 2 * m * n - n2),
                    center,
                    abs(-m2 + 2 * m * n + n2),
                )
            )
            common_factor = math.gcd(*roots)
            low, middle, high = (root // common_factor for root in roots)
            if low <= 0 or high > max_square_root:
                continue
            if not low < middle < high:
                continue
            if low * low + high * high != 2 * middle * middle:
                raise ArithmeticError("Le domaine canonique a produit un triplet invalide.")
            for scale in range(1, max_square_root // high + 1):
                yield scale * low, scale * middle, scale * high


def generate_square_progressions_parametric_canonical(
    max_square_root: int,
) -> tuple[ArithmeticProgression, ...]:
    """Matérialise le catalogue canonique sans ensemble de déduplication."""

    signatures = sorted(iter_canonical_progression_signatures(max_square_root))
    if any(left == right for left, right in zip(signatures, signatures[1:])):
        raise ArithmeticError("Le domaine fondamental a émis une progression dupliquée.")
    return tuple(
        ArithmeticProgression(low, middle, high, middle * middle - low * low)
        for low, middle, high in signatures
    )


class CanonicalParametricProgressionGroupStream(ParametricProgressionGroupStream):
    """Version en flux qui n'écrit qu'un représentant de chaque progression."""

    def _write_raw_records(self, directory: pathlib.Path) -> tuple[pathlib.Path, ...]:
        handles: dict[int, object] = {}
        paths: dict[int, pathlib.Path] = {}
        raw_records = 0
        try:
            for signature in iter_canonical_progression_signatures(
                self.max_square_root
            ):
                shard_id = self._shard_id(signature[0])
                if shard_id not in handles:
                    path = directory / f"shard_{shard_id:04d}.bin"
                    paths[shard_id] = path
                    handles[shard_id] = path.open("wb")
                handles[shard_id].write(_RECORD.pack(*signature))
                raw_records += 1
        finally:
            for handle in handles.values():
                handle.close()
        self.stats["raw_records_written"] = raw_records
        self.stats["shards_used"] = len(paths)
        return tuple(paths[shard_id] for shard_id in sorted(paths))
