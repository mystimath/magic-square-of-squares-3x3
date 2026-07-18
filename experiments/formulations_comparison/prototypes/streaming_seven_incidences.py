"""Flux canonique d'incidences B4, découpé par racine carrée partagée."""

from __future__ import annotations

from collections.abc import Iterator
import math
import pathlib
import struct
import tempfile

from .canonical_progressions import iter_canonical_progression_signatures
from .lo_shu_seven import ProgressionIncidence
from .lo_shu_seven_grouped import IncidenceGroup
from .model import ArithmeticProgression, validate_bound


_INCIDENCE_RECORD = struct.Struct("<QQQB")


class CanonicalProgressionIncidenceStream:
    """Émet l'index B4 par valeur sans matérialiser ses trois incidences globales."""

    def __init__(
        self,
        max_square_root: int,
        *,
        shard_count: int = 128,
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

    def _shard_id(self, shared_root: int) -> int:
        return min(
            self.shard_count - 1,
            (shared_root - 1) * self.shard_count // self.max_square_root,
        )

    def _write_records(self, directory: pathlib.Path) -> tuple[pathlib.Path, ...]:
        handles: dict[int, object] = {}
        paths: dict[int, pathlib.Path] = {}
        progression_count = 0
        incidence_count = 0
        try:
            for signature in iter_canonical_progression_signatures(
                self.max_square_root
            ):
                progression_count += 1
                for term_index, shared_root in enumerate(signature):
                    shard_id = self._shard_id(shared_root)
                    if shard_id not in handles:
                        path = directory / f"shard_{shard_id:04d}.bin"
                        paths[shard_id] = path
                        handles[shard_id] = path.open("wb")
                    handles[shard_id].write(
                        _INCIDENCE_RECORD.pack(*signature, term_index)
                    )
                    incidence_count += 1
        finally:
            for handle in handles.values():
                handle.close()
        self.stats["progressions"] = progression_count
        self.stats["raw_incidence_records"] = incidence_count
        self.stats["shards_used"] = len(paths)
        return tuple(paths[shard_id] for shard_id in sorted(paths))

    @staticmethod
    def _read_records(
        path: pathlib.Path,
    ) -> list[tuple[int, int, int, int]]:
        records: list[tuple[int, int, int, int]] = []
        with path.open("rb") as handle:
            while record := handle.read(_INCIDENCE_RECORD.size):
                if len(record) != _INCIDENCE_RECORD.size:
                    raise IOError(f"Enregistrement tronqué dans {path}.")
                low, middle, high, term_index = _INCIDENCE_RECORD.unpack(record)
                if term_index > 2:
                    raise IOError(f"Indice de terme invalide dans {path}.")
                records.append((low, middle, high, term_index))
        return records

    def __iter__(self) -> Iterator[IncidenceGroup]:
        if self._active:
            raise RuntimeError("Le flux d'incidences est déjà en cours d'utilisation.")
        self._active = True
        self.stats = {
            "progressions": 0,
            "raw_incidence_records": 0,
            "shards_used": 0,
            "duplicate_incidence_records": 0,
            "max_incidence_records_in_shard": 0,
            "indexed_square_values": 0,
        }
        try:
            base_dir = None if self.temp_dir is None else str(self.temp_dir)
            with tempfile.TemporaryDirectory(
                prefix="lo_shu_seven_incidences_",
                dir=base_dir,
            ) as temporary:
                paths = self._write_records(pathlib.Path(temporary))
                for path in paths:
                    records = self._read_records(path)
                    records.sort(
                        key=lambda item: (
                            item[item[3]],
                            item[0],
                            item[1],
                            item[2],
                            item[3],
                        )
                    )
                    duplicates = sum(
                        left == right
                        for left, right in zip(records, records[1:])
                    )
                    if duplicates:
                        raise ArithmeticError(
                            "Le domaine canonique a produit une incidence dupliquée."
                        )
                    self.stats["duplicate_incidence_records"] += duplicates
                    self.stats["max_incidence_records_in_shard"] = max(
                        self.stats["max_incidence_records_in_shard"],
                        len(records),
                    )
                    current_root: int | None = None
                    current_group: list[ProgressionIncidence] = []
                    for low, middle, high, term_index in records:
                        roots = (low, middle, high)
                        shared_root = roots[term_index]
                        if current_root is not None and shared_root != current_root:
                            self.stats["indexed_square_values"] += 1
                            yield current_root * current_root, tuple(current_group)
                            current_group = []
                        current_root = shared_root
                        current_group.append(
                            ProgressionIncidence(
                                ArithmeticProgression(
                                    low,
                                    middle,
                                    high,
                                    middle * middle - low * low,
                                ),
                                term_index,
                                math.gcd(low, middle, high),
                            )
                        )
                    if current_root is not None:
                        self.stats["indexed_square_values"] += 1
                        yield current_root * current_root, tuple(current_group)
        finally:
            self._active = False
