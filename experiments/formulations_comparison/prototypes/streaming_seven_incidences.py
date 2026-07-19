"""Flux canonique d'incidences B4, découpé par racine carrée partagée."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
import math
import pathlib
import struct
import tempfile
from typing import BinaryIO

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
        max_open_shard_handles: int | None = None,
        max_buffered_write_bytes: int | None = None,
        write_handle_buffering: int | None = None,
        group_writes_by_shard: bool = False,
        temp_dir: pathlib.Path | None = None,
    ) -> None:
        validate_bound(max_square_root)
        if isinstance(shard_count, bool) or not isinstance(shard_count, int):
            raise ValueError("shard_count doit être un entier positif.")
        if shard_count < 1:
            raise ValueError("shard_count doit être un entier positif.")
        if (
            isinstance(max_open_shard_handles, bool)
            or max_open_shard_handles is not None
            and not isinstance(max_open_shard_handles, int)
        ):
            raise ValueError(
                "max_open_shard_handles doit être None ou un entier positif."
            )
        if (
            max_open_shard_handles is not None
            and max_open_shard_handles < 1
        ):
            raise ValueError(
                "max_open_shard_handles doit être None ou un entier positif."
            )
        if (
            isinstance(max_buffered_write_bytes, bool)
            or max_buffered_write_bytes is not None
            and not isinstance(max_buffered_write_bytes, int)
        ):
            raise ValueError(
                "max_buffered_write_bytes doit être None ou un entier."
            )
        if (
            max_buffered_write_bytes is not None
            and max_buffered_write_bytes < _INCIDENCE_RECORD.size
        ):
            raise ValueError(
                "max_buffered_write_bytes doit contenir au moins "
                "un enregistrement."
            )
        if (
            max_open_shard_handles is not None
            and max_buffered_write_bytes is not None
        ):
            raise ValueError(
                "Les caches de handles et de tampons sont mutuellement exclusifs."
            )
        if (
            isinstance(write_handle_buffering, bool)
            or write_handle_buffering is not None
            and not isinstance(write_handle_buffering, int)
        ):
            raise ValueError(
                "write_handle_buffering doit être None, zéro ou au moins deux."
            )
        if (
            write_handle_buffering is not None
            and (
                write_handle_buffering < 0
                or write_handle_buffering == 1
            )
        ):
            raise ValueError(
                "write_handle_buffering doit être None, zéro ou au moins deux."
            )
        if (
            max_buffered_write_bytes is not None
            and write_handle_buffering is not None
        ):
            raise ValueError(
                "Les tampons applicatifs et de handles sont mutuellement exclusifs."
            )
        if not isinstance(group_writes_by_shard, bool):
            raise ValueError("group_writes_by_shard doit être booléen.")
        if group_writes_by_shard and (
            max_open_shard_handles is not None
            or max_buffered_write_bytes is not None
            or write_handle_buffering is not None
        ):
            raise ValueError(
                "Le regroupement par shard est exclusif des autres modes d'écriture."
            )
        self.max_square_root = max_square_root
        self.shard_count = shard_count
        self.max_open_shard_handles = max_open_shard_handles
        self.max_buffered_write_bytes = max_buffered_write_bytes
        self.write_handle_buffering = write_handle_buffering
        self.group_writes_by_shard = group_writes_by_shard
        self.temp_dir = temp_dir
        self.stats: dict[str, int] = {}
        self._active = False

    def _shard_id(self, shared_root: int) -> int:
        return min(
            self.shard_count - 1,
            (shared_root - 1) * self.shard_count // self.max_square_root,
        )

    def _write_records(self, directory: pathlib.Path) -> tuple[pathlib.Path, ...]:
        if self.group_writes_by_shard:
            return self._write_grouped_records(directory)
        if self.max_buffered_write_bytes is not None:
            return self._write_buffered_records(directory)
        handles: OrderedDict[int, BinaryIO] = OrderedDict()
        paths: dict[int, pathlib.Path] = {}
        progression_count = 0
        incidence_count = 0
        write_handle_opens = 0
        write_handle_evictions = 0
        max_open_write_handles = 0
        try:
            for signature in iter_canonical_progression_signatures(
                self.max_square_root
            ):
                progression_count += 1
                for term_index, shared_root in enumerate(signature):
                    shard_id = self._shard_id(shared_root)
                    handle = handles.get(shard_id)
                    if handle is None:
                        if (
                            self.max_open_shard_handles is not None
                            and len(handles) >= self.max_open_shard_handles
                        ):
                            _, evicted_handle = handles.popitem(last=False)
                            evicted_handle.close()
                            write_handle_evictions += 1
                        path = directory / f"shard_{shard_id:04d}.bin"
                        mode = "ab" if shard_id in paths else "wb"
                        paths[shard_id] = path
                        if self.write_handle_buffering is None:
                            handle = path.open(mode)
                        else:
                            handle = path.open(
                                mode,
                                buffering=self.write_handle_buffering,
                            )
                        handles[shard_id] = handle
                        write_handle_opens += 1
                        max_open_write_handles = max(
                            max_open_write_handles,
                            len(handles),
                        )
                    elif self.max_open_shard_handles is not None:
                        handles.move_to_end(shard_id)
                    handle.write(
                        _INCIDENCE_RECORD.pack(*signature, term_index)
                    )
                    incidence_count += 1
        finally:
            for handle in handles.values():
                handle.close()
        self.stats["progressions"] = progression_count
        self.stats["raw_incidence_records"] = incidence_count
        self.stats["shards_used"] = len(paths)
        self.stats["write_handle_cache_capacity"] = (
            self.max_open_shard_handles or 0
        )
        self.stats["write_handle_opens"] = write_handle_opens
        self.stats["write_handle_evictions"] = write_handle_evictions
        self.stats["max_open_write_handles"] = max_open_write_handles
        self.stats["write_handle_buffering"] = (
            -1
            if self.write_handle_buffering is None
            else self.write_handle_buffering
        )
        self.stats["write_buffer_capacity_bytes"] = 0
        self.stats["write_buffer_flushes"] = 0
        self.stats["write_buffer_evictions"] = 0
        self.stats["max_buffered_write_bytes"] = 0
        return tuple(paths[shard_id] for shard_id in sorted(paths))

    def _write_grouped_records(
        self,
        directory: pathlib.Path,
    ) -> tuple[pathlib.Path, ...]:
        buffers: dict[int, bytearray] = {}
        paths: dict[int, pathlib.Path] = {}
        progression_count = 0
        incidence_count = 0
        buffered_bytes = 0
        for signature in iter_canonical_progression_signatures(
            self.max_square_root
        ):
            progression_count += 1
            for term_index, shared_root in enumerate(signature):
                shard_id = self._shard_id(shared_root)
                if shard_id not in paths:
                    paths[shard_id] = (
                        directory / f"shard_{shard_id:04d}.bin"
                    )
                record = _INCIDENCE_RECORD.pack(*signature, term_index)
                buffers.setdefault(shard_id, bytearray()).extend(record)
                buffered_bytes += len(record)
                incidence_count += 1

        for shard_id in sorted(buffers):
            with paths[shard_id].open("wb") as handle:
                handle.write(buffers[shard_id])

        self.stats["progressions"] = progression_count
        self.stats["raw_incidence_records"] = incidence_count
        self.stats["shards_used"] = len(paths)
        self.stats["write_handle_cache_capacity"] = 0
        self.stats["write_handle_opens"] = len(paths)
        self.stats["write_handle_evictions"] = 0
        self.stats["max_open_write_handles"] = 1 if paths else 0
        self.stats["write_handle_buffering"] = -1
        self.stats["write_buffer_capacity_bytes"] = buffered_bytes
        self.stats["write_buffer_flushes"] = len(paths)
        self.stats["write_buffer_evictions"] = 0
        self.stats["max_buffered_write_bytes"] = buffered_bytes
        self.stats["group_writes_by_shard"] = 1
        return tuple(paths[shard_id] for shard_id in sorted(paths))

    def _write_buffered_records(
        self,
        directory: pathlib.Path,
    ) -> tuple[pathlib.Path, ...]:
        capacity = self.max_buffered_write_bytes
        if capacity is None:
            raise AssertionError("Le budget de tampons B13 est absent.")
        buffers: OrderedDict[int, bytearray] = OrderedDict()
        paths: dict[int, pathlib.Path] = {}
        written_shards: set[int] = set()
        progression_count = 0
        incidence_count = 0
        buffered_bytes = 0
        max_buffered_bytes = 0
        flushes = 0
        buffer_evictions = 0

        def flush(shard_id: int, buffer: bytearray) -> None:
            nonlocal flushes
            path = paths[shard_id]
            mode = "ab" if shard_id in written_shards else "wb"
            with path.open(mode) as handle:
                handle.write(buffer)
            written_shards.add(shard_id)
            flushes += 1

        for signature in iter_canonical_progression_signatures(
            self.max_square_root
        ):
            progression_count += 1
            for term_index, shared_root in enumerate(signature):
                shard_id = self._shard_id(shared_root)
                if shard_id not in paths:
                    paths[shard_id] = (
                        directory / f"shard_{shard_id:04d}.bin"
                    )
                record = _INCIDENCE_RECORD.pack(*signature, term_index)
                buffer = buffers.pop(shard_id, bytearray())
                buffered_bytes -= len(buffer)
                required_bytes = len(buffer) + len(record)
                while buffered_bytes + required_bytes > capacity:
                    if buffers:
                        evicted_id, evicted_buffer = buffers.popitem(
                            last=False
                        )
                        buffered_bytes -= len(evicted_buffer)
                        flush(evicted_id, evicted_buffer)
                        buffer_evictions += 1
                    elif buffer:
                        flush(shard_id, buffer)
                        buffer_evictions += 1
                        buffer = bytearray()
                        required_bytes = len(record)
                    else:
                        raise AssertionError(
                            "Le budget validé ne contient pas un enregistrement."
                        )
                buffer.extend(record)
                buffers[shard_id] = buffer
                buffered_bytes += len(buffer)
                max_buffered_bytes = max(
                    max_buffered_bytes,
                    buffered_bytes,
                )
                incidence_count += 1

        for shard_id, buffer in buffers.items():
            flush(shard_id, buffer)

        self.stats["progressions"] = progression_count
        self.stats["raw_incidence_records"] = incidence_count
        self.stats["shards_used"] = len(paths)
        self.stats["write_handle_cache_capacity"] = 0
        self.stats["write_handle_opens"] = flushes
        self.stats["write_handle_evictions"] = 0
        self.stats["max_open_write_handles"] = 1 if flushes else 0
        self.stats["write_handle_buffering"] = -1
        self.stats["write_buffer_capacity_bytes"] = capacity
        self.stats["write_buffer_flushes"] = flushes
        self.stats["write_buffer_evictions"] = buffer_evictions
        self.stats["max_buffered_write_bytes"] = max_buffered_bytes
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
            "write_handle_cache_capacity": (
                self.max_open_shard_handles or 0
            ),
            "write_handle_opens": 0,
            "write_handle_evictions": 0,
            "max_open_write_handles": 0,
            "write_handle_buffering": (
                -1
                if self.write_handle_buffering is None
                else self.write_handle_buffering
            ),
            "write_buffer_capacity_bytes": (
                self.max_buffered_write_bytes or 0
            ),
            "write_buffer_flushes": 0,
            "write_buffer_evictions": 0,
            "max_buffered_write_bytes": 0,
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
