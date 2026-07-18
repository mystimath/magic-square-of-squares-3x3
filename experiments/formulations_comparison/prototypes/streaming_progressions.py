"""Catalogue paramétrique de progressions de carrés, groupé en flux par ``A``."""

from __future__ import annotations

from collections.abc import Iterator
import math
import pathlib
import struct
import tempfile

from .like_bremner_indexed import ProgressionGroup
from .model import ArithmeticProgression, validate_bound

_RECORD = struct.Struct("<QQQ")


class ParametricProgressionGroupStream:
    """Écrit des signatures compactes par tranche, puis émet les groupes triés.

    La paramétrisation peut représenter plusieurs fois une même progression.
    Chaque doublon possède le même premier terme et tombe donc dans la même
    tranche. La déduplication reste ainsi exacte avec une mémoire bornée par la
    plus grande tranche, et non par le catalogue complet.
    """

    def __init__(
        self,
        max_square_root: int,
        *,
        shard_count: int = 64,
        temp_dir: pathlib.Path | None = None,
    ) -> None:
        validate_bound(max_square_root)
        if isinstance(shard_count, bool) or not isinstance(shard_count, int):
            raise ValueError("shard_count doit être un entier positif.")
        if shard_count < 1:
            raise ValueError("shard_count doit être un entier positif.")
        self.max_square_root = max_square_root
        self.shard_count = shard_count
        self.temp_dir = temp_dir
        self.stats: dict[str, int] = {}
        self._active = False

    def _shard_id(self, low_root: int) -> int:
        return min(
            self.shard_count - 1,
            (low_root - 1) * self.shard_count // self.max_square_root,
        )

    def _write_raw_records(self, directory: pathlib.Path) -> tuple[pathlib.Path, ...]:
        handles: dict[int, object] = {}
        paths: dict[int, pathlib.Path] = {}
        raw_records = 0
        parameter_limit = math.isqrt(2 * self.max_square_root)
        try:
            for m in range(1, parameter_limit + 1):
                m2 = m * m
                for n in range(1, parameter_limit + 1):
                    if math.gcd(m, n) != 1:
                        continue
                    n2 = n * n
                    center = m2 + n2
                    if center > 2 * self.max_square_root:
                        continue
                    roots = sorted(
                        (
                            abs(m2 + 2 * m * n - n2),
                            center,
                            abs(-m2 + 2 * m * n + n2),
                        )
                    )
                    common_factor = math.gcd(*roots)
                    low, middle, high = (
                        root // common_factor for root in roots
                    )
                    if low <= 0 or high > self.max_square_root:
                        continue
                    if not low < middle < high:
                        continue
                    if low * low + high * high != 2 * middle * middle:
                        raise ArithmeticError(
                            "La paramétrisation en flux a produit une progression invalide."
                        )
                    for scale in range(1, self.max_square_root // high + 1):
                        signature = (
                            scale * low,
                            scale * middle,
                            scale * high,
                        )
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

    @staticmethod
    def _read_unique(path: pathlib.Path) -> set[tuple[int, int, int]]:
        signatures: set[tuple[int, int, int]] = set()
        with path.open("rb") as handle:
            while record := handle.read(_RECORD.size):
                if len(record) != _RECORD.size:
                    raise IOError(f"Enregistrement tronqué dans {path}.")
                signatures.add(_RECORD.unpack(record))
        return signatures

    def __iter__(self) -> Iterator[ProgressionGroup]:
        if self._active:
            raise RuntimeError("Le flux de catalogue est déjà en cours d'utilisation.")
        self._active = True
        self.stats = {
            "raw_records_written": 0,
            "shards_used": 0,
            "unique_progressions": 0,
            "duplicate_records": 0,
            "max_unique_progressions_in_shard": 0,
            "groups_yielded": 0,
        }
        try:
            base_dir = None if self.temp_dir is None else str(self.temp_dir)
            with tempfile.TemporaryDirectory(
                prefix="like_bremner_catalog_",
                dir=base_dir,
            ) as temporary:
                paths = self._write_raw_records(pathlib.Path(temporary))
                unique_total = 0
                for path in paths:
                    signatures = self._read_unique(path)
                    unique_total += len(signatures)
                    self.stats["max_unique_progressions_in_shard"] = max(
                        self.stats["max_unique_progressions_in_shard"],
                        len(signatures),
                    )
                    current_low: int | None = None
                    current_group: list[ArithmeticProgression] = []
                    for low, middle, high in sorted(signatures):
                        if current_low is not None and low != current_low:
                            self.stats["groups_yielded"] += 1
                            yield current_low * current_low, tuple(current_group)
                            current_group = []
                        current_low = low
                        current_group.append(
                            ArithmeticProgression(
                                low,
                                middle,
                                high,
                                middle * middle - low * low,
                            )
                        )
                    if current_low is not None:
                        self.stats["groups_yielded"] += 1
                        yield current_low * current_low, tuple(current_group)
                self.stats["unique_progressions"] = unique_total
                self.stats["duplicate_records"] = (
                    self.stats["raw_records_written"] - unique_total
                )
        finally:
            self._active = False
