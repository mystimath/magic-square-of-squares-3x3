#!/usr/bin/env python3
"""
Branche B2 — v2.2 SAFE / HYBRIDE
=================================
Recherche de carrés magiques 3x3 presque composés de carrés parfaits.

Cette version remplace v2.1 pour deux usages :

1) exact8
   Centre quelconque / carré / non carré, et 8 cases extérieures carrées.
   On cherche des offsets u, v tels que :
       u, v, u+v, |u-v| ∈ S_e
   où S_e est l'ensemble des offsets o pour lesquels e-o et e+o sont tous deux carrés.

2) relaxed7
   Recherche plus large visant >= 7 carrés sur 9, incluant les formes de type Bremner.
   On choisit deux offsets p, q ∈ S_e, ce qui garantit quatre cases carrées :
       e-p, e+p, e-q, e+q
   puis on teste les quatre autres cases déduites par la magie :
       e-p+q, e+2p-q, e-2p+q, e+p-q
   ainsi que le centre e.

Cette version ajoute :
- mode exact8 / relaxed7 / both ;
- centre any / square / non-square ;
- profils de tuning pour machine 16 Go ;
- nettoyage automatique des pass1_partials après réduction ;
- garde-fous disque et sélection ;
- résumé JSON de run ;
- export des centres sélectionnés les plus riches.

Important : ce script reste expérimental. Il documente des recherches bornées ;
il ne constitue pas une preuve d'impossibilité.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import os
import shutil
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import DefaultDict, Dict, Iterable, Iterator, List, Sequence, Set, Tuple


# =============================================================================
# Profils de ressources
# =============================================================================

RESOURCE_PROFILES = {
    "home16_safe": {
        "workers": 6,
        "reduce_workers": 3,
        "pass2_workers": 2,
        "recombine_workers": 4,
        "x_batch_size": 512,
        "shard_size": 10_000_000,
        "moduli": "127,131",
        "max_selected_centers": 2_500_000,
        "max_tmp_gb": 120.0,
        "min_free_gb": 80.0,
    },
    "home16_balanced": {
        "workers": 7,
        "reduce_workers": 4,
        "pass2_workers": 2,
        "recombine_workers": 5,
        "x_batch_size": 768,
        "shard_size": 10_000_000,
        "moduli": "127,131,137",
        "max_selected_centers": 3_000_000,
        "max_tmp_gb": 160.0,
        "min_free_gb": 70.0,
    },
    "home16_aggressive": {
        "workers": 8,
        "reduce_workers": 4,
        "pass2_workers": 2,
        "recombine_workers": 6,
        "x_batch_size": 1024,
        "shard_size": 12_000_000,
        "moduli": "127,131,137",
        "max_selected_centers": 4_000_000,
        "max_tmp_gb": 220.0,
        "min_free_gb": 60.0,
    },
}


# =============================================================================
# Modèle candidat
# =============================================================================

CSV_FIELDS = [
    "mode", "center", "u", "v", "center_is_square", "primitive_root_gcd",
    "roots_distinct", "total_squares", "square_positions", "symmetry_key",
    "a", "b", "c", "d", "e", "f", "g", "h", "i",
]


@dataclass(frozen=True)
class Candidate:
    mode: str
    center: int
    u: int
    v: int
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    g: int
    h: int
    i: int
    center_is_square: bool
    primitive_root_gcd: int
    roots_distinct: bool
    total_squares: int
    square_positions: str
    symmetry_key: str


# =============================================================================
# Utilitaires
# =============================================================================

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def is_square(n: int) -> bool:
    if n < 0:
        return False
    r = math.isqrt(n)
    return r * r == n


def center_allowed(center: int, center_mode: str) -> bool:
    sq = is_square(center)
    if center_mode == "any":
        return True
    if center_mode == "square":
        return sq
    if center_mode == "non-square":
        return not sq
    raise ValueError(f"center_mode inconnu: {center_mode}")


def square_roots(values: Sequence[int]) -> List[int]:
    roots: List[int] = []
    for v in values:
        if is_square(v):
            roots.append(math.isqrt(v))
    return roots


def gcd_list(values: Sequence[int]) -> int:
    g = 0
    for v in values:
        g = math.gcd(g, v)
    return g


def primitive_root_gcd(values: Sequence[int]) -> int:
    roots = [r for r in square_roots(values) if r != 0]
    return gcd_list(roots) if roots else 0


def roots_are_distinct(values: Sequence[int]) -> bool:
    roots = [r for r in square_roots(values) if r != 0]
    return len(roots) == len(set(roots))


def square_positions(vals: Tuple[int, ...]) -> str:
    names = ["a", "b", "c", "d", "e", "f", "g", "h", "i"]
    return ";".join(name for name, value in zip(names, vals) if is_square(value))


def chunk_ranges(start: int, stop: int, chunks: int) -> List[Tuple[int, int]]:
    n = stop - start + 1
    base = n // chunks
    rem = n % chunks
    out = []
    cur = start
    for i in range(chunks):
        size = base + (1 if i < rem else 0)
        if size <= 0:
            continue
        out.append((cur, cur + size - 1))
        cur += size
    return out


def matrix_symmetries(vals: Tuple[int, ...]) -> List[Tuple[int, ...]]:
    def rot90(m: Tuple[int, ...]) -> Tuple[int, ...]:
        return (m[6], m[3], m[0], m[7], m[4], m[1], m[8], m[5], m[2])

    def refl(m: Tuple[int, ...]) -> Tuple[int, ...]:
        return (m[2], m[1], m[0], m[5], m[4], m[3], m[8], m[7], m[6])

    m0 = vals
    m1 = rot90(m0)
    m2 = rot90(m1)
    m3 = rot90(m2)
    r0 = refl(m0)
    r1 = refl(m1)
    r2 = refl(m2)
    r3 = refl(m3)
    return [m0, m1, m2, m3, r0, r1, r2, r3]


def canonical_key(vals: Tuple[int, ...]) -> str:
    return "|".join(str(x) for x in min(matrix_symmetries(vals)))


def dir_size_bytes(path: str) -> int:
    if not os.path.exists(path):
        return 0
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def gb(nbytes: int) -> float:
    return nbytes / (1024 ** 3)


def free_gb_for(path: str) -> float:
    ensure_dir(path)
    usage = shutil.disk_usage(path)
    return usage.free / (1024 ** 3)


def parse_moduli(text: str) -> List[int]:
    out = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        m = int(part)
        if m < 2:
            raise ValueError("Tous les modules doivent être >= 2")
        out.append(m)
    if not out:
        raise ValueError("Au moins un module est nécessaire")
    return out


# =============================================================================
# Filtrage modulaire
# =============================================================================

@lru_cache(maxsize=500_000)
def additive_pattern_possible_cached(mask: int, modulus: int) -> bool:
    residues = [r for r in range(modulus) if (mask >> r) & 1]
    if len(residues) < 3:
        return False
    sset = set(residues)
    for r in residues:
        for s in residues:
            if r == s:
                continue
            if ((r + s) % modulus) in sset and ((r - s) % modulus) in sset:
                return True
    return False


def residue_count(mask: int) -> int:
    return int(mask.bit_count())


def should_select_center(
    count: int,
    masks: Sequence[int],
    moduli: Sequence[int],
    search_mode: str,
    min_offsets_exact: int,
    min_offsets_relaxed: int,
) -> Tuple[bool, str]:
    """Retourne (selected, reason)."""
    if search_mode in ("relaxed7", "both") and count >= min_offsets_relaxed:
        if search_mode == "relaxed7":
            return True, "relaxed_count"
        # En mode both, on garde aussi ces centres pour la recherche relaxed.
        return True, "relaxed_count"

    if search_mode in ("exact8", "both"):
        if count < min_offsets_exact:
            return False, "reject_count"
        for mask, modulus in zip(masks, moduli):
            if residue_count(mask) < 3:
                return False, f"reject_residue_count_{modulus}"
            if not additive_pattern_possible_cached(mask, modulus):
                return False, f"reject_mod_{modulus}"
        return True, "exact_modular"

    return False, "reject_mode"


# =============================================================================
# Pass 1 : agrégation compacte
# =============================================================================

def flush_pass1_batch(local: Dict[int, Dict[int, List[int]]], paths: Dict[int, str], moduli_len: int) -> int:
    lines_written = 0
    for shard_id, center_map in local.items():
        if not center_map:
            continue
        path = paths[shard_id]
        with open(path, "a", encoding="utf-8", newline="") as f:
            for center, data in center_map.items():
                # data = [count, mask0, mask1, ...]
                f.write(",".join([str(center), str(data[0]), *[str(x) for x in data[1:1 + moduli_len]]]) + "\n")
                lines_written += 1
        center_map.clear()
    return lines_written


def pass1_generate_worker(
    worker_id: int,
    x_start: int,
    x_end: int,
    max_root: int,
    x_batch_size: int,
    shard_size: int,
    moduli: Sequence[int],
    center_mode: str,
    tmp_dir: str,
    min_free_gb: float,
) -> Dict[str, int]:
    part_dir = os.path.join(tmp_dir, "pass1_partials")
    ensure_dir(part_dir)
    stats = Counter()
    shard_paths: Dict[int, str] = {}
    batch_start = x_start

    while batch_start <= x_end:
        batch_end = min(batch_start + x_batch_size - 1, x_end)
        local: Dict[int, Dict[int, List[int]]] = defaultdict(dict)

        for x in range(batch_start, batch_end + 1):
            x2 = x * x
            y0 = x + 1
            # x et y doivent avoir même parité pour que (x²+y²)/2 soit entier.
            if ((y0 - x) & 1) == 1:
                y0 += 1
            for y in range(y0, max_root + 1, 2):
                y2 = y * y
                center = (x2 + y2) >> 1
                if not center_allowed(center, center_mode):
                    stats[f"reject_center_{center_mode}"] += 1
                    continue
                offset = (y2 - x2) >> 1
                shard_id = center // shard_size
                if shard_id not in shard_paths:
                    shard_paths[shard_id] = os.path.join(
                        part_dir,
                        f"pass1_shard_{shard_id:08d}_worker_{worker_id:03d}.csv",
                    )
                center_map = local[shard_id]
                item = center_map.get(center)
                if item is None:
                    masks = [1 << (offset % m) for m in moduli]
                    center_map[center] = [1, *masks]
                else:
                    item[0] += 1
                    for k, m in enumerate(moduli, start=1):
                        item[k] |= 1 << (offset % m)
                stats["pairs_seen"] += 1
            stats["x_done"] += 1

        stats["partial_rows_written"] += flush_pass1_batch(local, shard_paths, len(moduli))
        stats["x_batches"] += 1

        if min_free_gb > 0 and free_gb_for(tmp_dir) < min_free_gb:
            raise RuntimeError(
                f"Arrêt sécurité disque worker {worker_id}: espace libre < {min_free_gb:.1f} Go"
            )
        batch_start = batch_end + 1

    stats["shards_touched"] = len(shard_paths)
    return dict(stats)


def discover_pass1_partial_files(tmp_dir: str) -> Dict[int, List[str]]:
    part_dir = os.path.join(tmp_dir, "pass1_partials")
    paths = glob.glob(os.path.join(part_dir, "pass1_shard_*.csv"))
    grouped: DefaultDict[int, List[str]] = defaultdict(list)
    for path in paths:
        base = os.path.basename(path)
        shard_id = int(base.split("_")[2])
        grouped[shard_id].append(path)
    return dict(grouped)


def pass1_reduce_shard_worker(
    shard_id: int,
    paths: List[str],
    selected_dir: str,
    moduli: Sequence[int],
    center_mode: str,
    search_mode: str,
    min_offsets_exact: int,
    min_offsets_relaxed: int,
    cleanup_partials: bool,
    top_centers_dir: str,
    top_n_per_shard: int,
) -> Dict[str, int]:
    stats = Counter()
    agg: Dict[int, List[int]] = {}

    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                center = int(row[0])
                cnt = int(row[1])
                masks = [int(x) for x in row[2:2 + len(moduli)]]
                item = agg.get(center)
                if item is None:
                    agg[center] = [cnt, *masks]
                else:
                    item[0] += cnt
                    for k, mask in enumerate(masks, start=1):
                        item[k] |= mask

    stats["centers_seen"] = len(agg)
    ensure_dir(selected_dir)
    out_path = os.path.join(selected_dir, f"selected_shard_{shard_id:08d}.csv")
    header = ["center", "count", "reason", *[f"mask_mod_{m}" for m in moduli]]

    top_rows: List[Tuple[int, int, str]] = []
    survivors = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for center, data in agg.items():
            if not center_allowed(center, center_mode):
                stats[f"reject_center_{center_mode}"] += 1
                continue
            cnt = data[0]
            masks = data[1:]
            selected, reason = should_select_center(
                cnt, masks, moduli, search_mode, min_offsets_exact, min_offsets_relaxed
            )
            if not selected:
                stats[reason] += 1
                continue
            writer.writerow([center, cnt, reason, *masks])
            survivors += 1
            if top_n_per_shard > 0:
                top_rows.append((cnt, center, reason))

    stats["selected_centers"] = survivors
    stats["shard_id"] = shard_id

    if top_n_per_shard > 0 and top_rows:
        ensure_dir(top_centers_dir)
        top_rows.sort(reverse=True)
        top_path = os.path.join(top_centers_dir, f"top_centers_shard_{shard_id:08d}.csv")
        with open(top_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["center", "count", "reason"])
            for cnt, center, reason in top_rows[:top_n_per_shard]:
                writer.writerow([center, cnt, reason])
        stats["top_centers_written"] = min(len(top_rows), top_n_per_shard)

    if cleanup_partials:
        deleted = 0
        bytes_deleted = 0
        for path in paths:
            try:
                bytes_deleted += os.path.getsize(path)
                os.remove(path)
                deleted += 1
            except OSError:
                pass
        stats["partial_files_deleted"] = deleted
        stats["partial_bytes_deleted"] = bytes_deleted

    return dict(stats)


# =============================================================================
# Pass 2 : offsets sélectifs
# =============================================================================

def load_selected_centers_by_shard(tmp_dir: str) -> Dict[int, Set[int]]:
    selected_dir = os.path.join(tmp_dir, "selected_centers")
    paths = glob.glob(os.path.join(selected_dir, "selected_shard_*.csv"))
    grouped: Dict[int, Set[int]] = {}
    for path in paths:
        base = os.path.basename(path)
        shard_id = int(base.split("_")[2].split(".")[0])
        s: Set[int] = set()
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                s.add(int(row["center"]))
        if s:
            grouped[shard_id] = s
    return grouped


def count_selected_centers(tmp_dir: str) -> int:
    total = 0
    selected_dir = os.path.join(tmp_dir, "selected_centers")
    for path in glob.glob(os.path.join(selected_dir, "selected_shard_*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            total += sum(1 for _ in csv.DictReader(f))
    return total


def pass2_flush_offsets(local: Dict[int, List[str]], paths: Dict[int, str]) -> int:
    rows = 0
    for shard_id, lines in local.items():
        if not lines:
            continue
        with open(paths[shard_id], "a", encoding="utf-8", newline="") as f:
            f.writelines(lines)
        rows += len(lines)
        lines.clear()
    return rows


def pass2_generate_offsets_worker(
    worker_id: int,
    x_start: int,
    x_end: int,
    max_root: int,
    shard_size: int,
    center_mode: str,
    tmp_dir: str,
    min_free_gb: float,
) -> Dict[str, int]:
    selected = load_selected_centers_by_shard(tmp_dir)
    offsets_dir = os.path.join(tmp_dir, "pass2_offsets")
    ensure_dir(offsets_dir)
    shard_paths: Dict[int, str] = {}
    local: Dict[int, List[str]] = defaultdict(list)
    stats = Counter()

    for x in range(x_start, x_end + 1):
        x2 = x * x
        y0 = x + 1
        if ((y0 - x) & 1) == 1:
            y0 += 1
        for y in range(y0, max_root + 1, 2):
            y2 = y * y
            center = (x2 + y2) >> 1
            if not center_allowed(center, center_mode):
                continue
            shard_id = center // shard_size
            selected_centers = selected.get(shard_id)
            if not selected_centers or center not in selected_centers:
                continue
            offset = (y2 - x2) >> 1
            if shard_id not in shard_paths:
                shard_paths[shard_id] = os.path.join(
                    offsets_dir,
                    f"offsets_shard_{shard_id:08d}_worker_{worker_id:03d}.csv",
                )
            local[shard_id].append(f"{center},{offset}\n")
            stats["offset_rows_written"] += 1
            if len(local[shard_id]) >= 200_000:
                pass2_flush_offsets(local, shard_paths)
        stats["x_done"] += 1
        if min_free_gb > 0 and x % 1000 == 0 and free_gb_for(tmp_dir) < min_free_gb:
            raise RuntimeError(
                f"Arrêt sécurité disque worker {worker_id}: espace libre < {min_free_gb:.1f} Go"
            )

    pass2_flush_offsets(local, shard_paths)
    stats["shards_touched"] = len(shard_paths)
    return dict(stats)


def discover_pass2_offset_files(tmp_dir: str) -> Dict[int, List[str]]:
    offsets_dir = os.path.join(tmp_dir, "pass2_offsets")
    paths = glob.glob(os.path.join(offsets_dir, "offsets_shard_*.csv"))
    grouped: DefaultDict[int, List[str]] = defaultdict(list)
    for path in paths:
        base = os.path.basename(path)
        shard_id = int(base.split("_")[2])
        grouped[shard_id].append(path)
    return dict(grouped)


def load_offsets_by_center(paths: List[str]) -> Dict[int, Set[int]]:
    buckets: DefaultDict[int, Set[int]] = defaultdict(set)
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                buckets[int(row[0])].add(int(row[1]))
    return dict(buckets)


# =============================================================================
# Recombinaisons
# =============================================================================

def make_candidate(mode: str, center: int, u: int, v: int, vals: Tuple[int, ...]) -> Candidate:
    return Candidate(
        mode=mode,
        center=center,
        u=u,
        v=v,
        a=vals[0], b=vals[1], c=vals[2], d=vals[3], e=vals[4],
        f=vals[5], g=vals[6], h=vals[7], i=vals[8],
        center_is_square=is_square(center),
        primitive_root_gcd=primitive_root_gcd(vals),
        roots_distinct=roots_are_distinct(vals),
        total_squares=sum(is_square(x) for x in vals),
        square_positions=square_positions(vals),
        symmetry_key=canonical_key(vals),
    )


def candidate_exact8(center: int, u: int, v: int) -> Candidate:
    vals = (
        center - u,
        center + u + v,
        center - v,
        center + u - v,
        center,
        center - u + v,
        center + v,
        center - u - v,
        center + u,
    )
    return make_candidate("exact8", center, u, v, vals)


def candidate_relaxed7(center: int, p: int, q: int) -> Candidate:
    # Forme :
    # a=e-p+q, b=e+2p-q, c=e-p
    # d=e-q,   e=e,      f=e+q
    # g=e+p,   h=e-2p+q, i=e+p-q
    vals = (
        center - p + q,
        center + 2 * p - q,
        center - p,
        center - q,
        center,
        center + q,
        center + p,
        center - 2 * p + q,
        center + p - q,
    )
    return make_candidate("relaxed7", center, p, q, vals)


def candidate_ok(cand: Candidate, min_total: int, primitive_only: bool, distinct_roots: bool) -> bool:
    if cand.total_squares < min_total:
        return False
    if distinct_roots and not cand.roots_distinct:
        return False
    if primitive_only and cand.primitive_root_gcd != 1:
        return False
    return True


def recombine_center_offsets(
    center: int,
    offsets: Set[int],
    search_mode: str,
    min_total: int,
    primitive_only: bool,
    distinct_roots: bool,
    max_candidates_per_center: int,
) -> Tuple[List[Candidate], Counter]:
    stats = Counter()
    out: List[Candidate] = []
    seen: Set[str] = set()
    off = sorted(offsets)
    off_set = offsets

    if search_mode in ("exact8", "both"):
        if len(off) < 4:
            stats["centers_too_few_offsets_exact"] += 1
        else:
            for idx_u, u in enumerate(off):
                for v in off[:idx_u]:
                    diff = u - v
                    summ = u + v
                    if diff not in off_set or summ not in off_set:
                        continue
                    cand = candidate_exact8(center, u, v)
                    if not candidate_ok(cand, max(min_total, 8), primitive_only, distinct_roots):
                        stats["reject_candidate_exact8"] += 1
                        continue
                    key = cand.mode + "|" + cand.symmetry_key
                    if key in seen:
                        stats["reject_duplicate_symmetry"] += 1
                        continue
                    seen.add(key)
                    out.append(cand)
                    stats["candidates_kept_exact8"] += 1
                    if len(out) >= max_candidates_per_center:
                        stats["cap_hit_center"] += 1
                        return out, stats

    if search_mode in ("relaxed7", "both"):
        if len(off) < 2:
            stats["centers_too_few_offsets_relaxed"] += 1
        else:
            for idx_p, p in enumerate(off):
                for q in off[:idx_p]:
                    cand = candidate_relaxed7(center, p, q)
                    if not candidate_ok(cand, min_total, primitive_only, distinct_roots):
                        stats["reject_candidate_relaxed7"] += 1
                        continue
                    key = cand.mode + "|" + cand.symmetry_key
                    if key in seen:
                        stats["reject_duplicate_symmetry"] += 1
                        continue
                    seen.add(key)
                    out.append(cand)
                    stats["candidates_kept_relaxed7"] += 1
                    if len(out) >= max_candidates_per_center:
                        stats["cap_hit_center"] += 1
                        return out, stats

    if not out:
        stats["centers_no_candidate"] += 1
    return out, stats


def recombine_shard_worker(
    shard_id: int,
    paths: List[str],
    out_dir: str,
    search_mode: str,
    min_total: int,
    primitive_only: bool,
    distinct_roots: bool,
    max_candidates_per_center: int,
) -> Dict[str, int]:
    buckets = load_offsets_by_center(paths)
    stats = Counter()
    stats["centers_seen"] = len(buckets)
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, f"results_shard_{shard_id:08d}.csv")
    wrote_header = False

    for center, offsets in buckets.items():
        rows, local = recombine_center_offsets(
            center=center,
            offsets=offsets,
            search_mode=search_mode,
            min_total=min_total,
            primitive_only=primitive_only,
            distinct_roots=distinct_roots,
            max_candidates_per_center=max_candidates_per_center,
        )
        stats.update(local)
        if rows:
            mode = "a" if wrote_header else "w"
            with open(out_path, mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                if not wrote_header:
                    writer.writeheader()
                    wrote_header = True
                for cand in rows:
                    writer.writerow(asdict(cand))
            stats["results_written"] += len(rows)

    stats["shard_id"] = shard_id
    return dict(stats)


def merge_result_csvs(result_paths: List[str], final_out: str) -> Tuple[int, int]:
    ensure_parent(final_out)
    seen: Set[str] = set()
    written = 0
    duplicates = 0
    with open(final_out, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for path in sorted(result_paths):
            with open(path, newline="", encoding="utf-8") as fin:
                reader = csv.DictReader(fin)
                for row in reader:
                    key = row["mode"] + "|" + row["symmetry_key"]
                    if key in seen:
                        duplicates += 1
                        continue
                    seen.add(key)
                    writer.writerow(row)
                    written += 1
    return written, duplicates


# =============================================================================
# Orchestration
# =============================================================================

def apply_resource_profile(args: argparse.Namespace) -> None:
    if not args.resource_profile:
        return
    prof = RESOURCE_PROFILES[args.resource_profile]
    for key, value in prof.items():
        if getattr(args, key) in (None, ""):
            setattr(args, key, value)


def print_config(args: argparse.Namespace, moduli: Sequence[int]) -> None:
    print("Recherche B2 v2.2 SAFE / HYBRIDE")
    print(f"  max-root              : {args.max_root:,}")
    print(f"  search-mode           : {args.search_mode}")
    print(f"  center-mode           : {args.center_mode}")
    print(f"  min-total             : {args.min_total}")
    print(f"  workers pass1         : {args.workers}")
    print(f"  workers reduce        : {args.reduce_workers}")
    print(f"  workers pass2         : {args.pass2_workers}")
    print(f"  workers recombine     : {args.recombine_workers}")
    print(f"  x-batch-size          : {args.x_batch_size}")
    print(f"  shard-size            : {args.shard_size:,}")
    print(f"  moduli                : {', '.join(map(str, moduli))}")
    print(f"  min-offsets exact     : {args.min_offsets_exact}")
    print(f"  min-offsets relaxed   : {args.min_offsets_relaxed}")
    print(f"  max-selected-centers  : {args.max_selected_centers:,}")
    print(f"  max-tmp-gb            : {args.max_tmp_gb}")
    print(f"  min-free-gb           : {args.min_free_gb}")
    print(f"  cleanup-partials      : {args.cleanup_partials}")
    print(f"  primitive-only        : {args.primitive_only}")
    print(f"  distinct-roots        : {args.distinct_roots}")
    print(f"  tmp-dir               : {args.tmp_dir}")
    print(f"  out                   : {args.out}")


def preflight(args: argparse.Namespace) -> None:
    ensure_dir(args.tmp_dir)
    free = free_gb_for(args.tmp_dir)
    print(f"[Préflight] Espace disque libre : {free:.1f} Go")
    if args.min_free_gb and free < args.min_free_gb:
        raise SystemExit(f"Espace libre insuffisant (< {args.min_free_gb:.1f} Go).")
    if args.search_mode == "relaxed7" and args.center_mode == "any" and args.max_root >= 50_000:
        print("[Attention] relaxed7 + center-mode any peut sélectionner énormément de centres.")
        print("            Pour chercher du Bremner-like, préférer --center-mode square.")


def stage_pass1(args: argparse.Namespace, moduli: Sequence[int]) -> Counter:
    t0 = time.time()
    total = Counter()
    print("[Pass 1A] Génération parallèle des agrégats compacts par centre...")
    xranges = chunk_ranges(1, args.max_root, args.workers)

    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = []
        for wid, (xa, xb) in enumerate(xranges):
            futures.append(ex.submit(
                pass1_generate_worker,
                wid, xa, xb, args.max_root, args.x_batch_size, args.shard_size,
                list(moduli), args.center_mode, args.tmp_dir, args.min_free_gb,
            ))
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            print(
                f"  worker done: pairs={stats.get('pairs_seen', 0):,}  "
                f"partial_rows={stats.get('partial_rows_written', 0):,}  "
                f"x_done={stats.get('x_done', 0):,}"
            )

    print(f"[Pass 1A terminé] durée={time.time() - t0:.1f}s")
    print("[Pass 1B] Réduction par shard et sélection des centres survivants...")
    partials = discover_pass1_partial_files(args.tmp_dir)
    selected_dir = os.path.join(args.tmp_dir, "selected_centers")
    top_centers_dir = os.path.join(args.tmp_dir, "top_centers")
    ensure_dir(selected_dir)

    with ProcessPoolExecutor(max_workers=args.reduce_workers) as ex:
        futures = []
        for shard_id, paths in sorted(partials.items()):
            futures.append(ex.submit(
                pass1_reduce_shard_worker,
                shard_id, paths, selected_dir, list(moduli), args.center_mode,
                args.search_mode, args.min_offsets_exact, args.min_offsets_relaxed,
                args.cleanup_partials, top_centers_dir, args.top_n_per_shard,
            ))
        done = 0
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            done += 1
            print(
                f"  shard reduce {done}/{len(futures)}: "
                f"centers={stats.get('centers_seen', 0):,}  "
                f"selected={stats.get('selected_centers', 0):,}"
            )

    selected_total = count_selected_centers(args.tmp_dir)
    total["selected_centers_counted"] = selected_total
    tmp_gb = gb(dir_size_bytes(args.tmp_dir))
    print(f"[Pass 1 terminé] durée totale={time.time() - t0:.1f}s")
    print(f"  centres sélectionnés comptés : {selected_total:,}")
    print(f"  taille tmp actuelle          : {tmp_gb:.2f} Go")
    return total


def stage_pass2(args: argparse.Namespace) -> Counter:
    t0 = time.time()
    total = Counter()
    selected_total = count_selected_centers(args.tmp_dir)
    tmp_gb = gb(dir_size_bytes(args.tmp_dir))

    if not args.force_pass2:
        if args.max_selected_centers and selected_total > args.max_selected_centers:
            raise SystemExit(
                f"Pass2 annulée par sécurité : {selected_total:,} centres sélectionnés "
                f"> limite {args.max_selected_centers:,}. Utiliser --force-pass2 pour forcer."
            )
        if args.max_tmp_gb and tmp_gb > args.max_tmp_gb:
            raise SystemExit(
                f"Pass2 annulée par sécurité : tmp={tmp_gb:.2f} Go > limite {args.max_tmp_gb:.2f} Go."
            )

    print("[Pass 2A] Régénération sélective des offsets des centres retenus...")
    xranges = chunk_ranges(1, args.max_root, args.pass2_workers)
    with ProcessPoolExecutor(max_workers=args.pass2_workers) as ex:
        futures = []
        for wid, (xa, xb) in enumerate(xranges):
            futures.append(ex.submit(
                pass2_generate_offsets_worker,
                wid, xa, xb, args.max_root, args.shard_size,
                args.center_mode, args.tmp_dir, args.min_free_gb,
            ))
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            print(
                f"  worker done: offsets={stats.get('offset_rows_written', 0):,}  "
                f"x_done={stats.get('x_done', 0):,}"
            )

    print(f"[Pass 2A terminé] durée={time.time() - t0:.1f}s")
    print("[Pass 2B] Recombinaison exacte / relâchée par shard...")
    offset_groups = discover_pass2_offset_files(args.tmp_dir)
    result_dir = os.path.join(args.tmp_dir, "result_shards")
    ensure_dir(result_dir)

    with ProcessPoolExecutor(max_workers=args.recombine_workers) as ex:
        futures = []
        for shard_id, paths in sorted(offset_groups.items()):
            futures.append(ex.submit(
                recombine_shard_worker,
                shard_id, paths, result_dir, args.search_mode, args.min_total,
                args.primitive_only, args.distinct_roots, args.max_candidates_per_center,
            ))
        done = 0
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            done += 1
            print(
                f"  shard recombine {done}/{len(futures)}: "
                f"centers={stats.get('centers_seen', 0):,}  "
                f"results={stats.get('results_written', 0):,}"
            )

    result_paths = sorted(glob.glob(os.path.join(result_dir, "results_shard_*.csv")))
    merged, dup = merge_result_csvs(result_paths, args.out)
    total["merged_results"] = merged
    total["merged_duplicates"] = dup
    print(f"[Pass 2 terminé] durée totale={time.time() - t0:.1f}s  résultats distincts={merged:,}")
    return total


def write_summary(args: argparse.Namespace, moduli: Sequence[int], total: Counter, elapsed: float) -> None:
    if not args.summary_json:
        return
    ensure_parent(args.summary_json)
    data = {
        "script": "search_non_square_center_v2_2_safe.py",
        "elapsed_seconds": elapsed,
        "config": {
            "max_root": args.max_root,
            "search_mode": args.search_mode,
            "center_mode": args.center_mode,
            "min_total": args.min_total,
            "workers": args.workers,
            "reduce_workers": args.reduce_workers,
            "pass2_workers": args.pass2_workers,
            "recombine_workers": args.recombine_workers,
            "x_batch_size": args.x_batch_size,
            "shard_size": args.shard_size,
            "moduli": list(moduli),
            "min_offsets_exact": args.min_offsets_exact,
            "min_offsets_relaxed": args.min_offsets_relaxed,
            "primitive_only": args.primitive_only,
            "distinct_roots": args.distinct_roots,
        },
        "stats": dict(total),
        "tmp_size_gb": gb(dir_size_bytes(args.tmp_dir)),
        "free_gb": free_gb_for(args.tmp_dir),
        "out": args.out,
    }
    with open(args.summary_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Résumé JSON écrit : {args.summary_json}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--resource-profile", choices=sorted(RESOURCE_PROFILES), default=None)
    p.add_argument("--stage", choices=["all", "pass1", "pass2"], default="all")
    p.add_argument("--search-mode", choices=["exact8", "relaxed7", "both"], default="exact8")
    p.add_argument("--center-mode", choices=["any", "square", "non-square"], default="non-square")
    p.add_argument("--max-root", type=int, default=50_000)
    p.add_argument("--min-total", type=int, default=8)

    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--reduce-workers", type=int, default=None)
    p.add_argument("--pass2-workers", type=int, default=None)
    p.add_argument("--recombine-workers", type=int, default=None)
    p.add_argument("--x-batch-size", type=int, default=None)
    p.add_argument("--shard-size", type=int, default=None)
    p.add_argument("--moduli", type=str, default="")
    p.add_argument("--min-offsets-exact", type=int, default=4)
    p.add_argument("--min-offsets-relaxed", type=int, default=2)

    p.add_argument("--primitive-only", action="store_true")
    p.add_argument("--distinct-roots", action="store_true")
    p.add_argument("--max-candidates-per-center", type=int, default=100)
    p.add_argument("--top-n-per-shard", type=int, default=20)

    p.add_argument("--tmp-dir", type=str, default="tmp/b2_v2_2_safe")
    p.add_argument("--clean-tmp", action="store_true")
    p.add_argument("--cleanup-partials", action="store_true", default=True)
    p.add_argument("--keep-partials", dest="cleanup_partials", action="store_false")
    p.add_argument("--out", type=str, default="results/raw/b2_v2_2_safe.csv")
    p.add_argument("--summary-json", type=str, default="")

    p.add_argument("--max-selected-centers", type=int, default=None)
    p.add_argument("--max-tmp-gb", type=float, default=None)
    p.add_argument("--min-free-gb", type=float, default=None)
    p.add_argument("--force-pass2", action="store_true")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    apply_resource_profile(args)

    # Valeurs par défaut si aucun profil n'est donné.
    cpu = os.cpu_count() or 4
    if args.workers is None:
        args.workers = min(cpu, 6)
    if args.reduce_workers is None:
        args.reduce_workers = min(args.workers, 3)
    if args.pass2_workers is None:
        args.pass2_workers = min(args.workers, 2)
    if args.recombine_workers is None:
        args.recombine_workers = min(args.workers, 4)
    if args.x_batch_size is None:
        args.x_batch_size = 512
    if args.shard_size is None:
        args.shard_size = 10_000_000
    if not args.moduli:
        args.moduli = "127,131"
    if args.max_selected_centers is None:
        args.max_selected_centers = 2_500_000
    if args.max_tmp_gb is None:
        args.max_tmp_gb = 120.0
    if args.min_free_gb is None:
        args.min_free_gb = 80.0

    if args.search_mode == "relaxed7" and args.min_total > 7:
        print("[Info] relaxed7 avec min-total > 7 : recherche très restrictive.")
    if args.search_mode == "relaxed7" and args.min_total < 7:
        parser.error("Pour relaxed7, --min-total doit être >= 7.")
    if args.search_mode == "exact8" and args.min_total < 8:
        args.min_total = 8

    moduli = parse_moduli(args.moduli)
    if args.max_root < 2:
        parser.error("--max-root doit être >= 2")
    if args.x_batch_size < 1:
        parser.error("--x-batch-size doit être >= 1")
    if args.shard_size < 1:
        parser.error("--shard-size doit être >= 1")

    print_config(args, moduli)
    preflight(args)

    if args.clean_tmp and os.path.isdir(args.tmp_dir):
        shutil.rmtree(args.tmp_dir)
    ensure_dir(args.tmp_dir)
    ensure_parent(args.out)
    if args.summary_json:
        ensure_parent(args.summary_json)

    total = Counter()
    t0 = time.time()
    if args.stage in ("all", "pass1"):
        total.update(stage_pass1(args, moduli))
    if args.stage in ("all", "pass2"):
        total.update(stage_pass2(args))

    elapsed = time.time() - t0
    print("\nTerminé.")
    print(f"  durée totale          : {elapsed:.1f}s")
    print(f"  taille tmp            : {gb(dir_size_bytes(args.tmp_dir)):.2f} Go")
    print(f"  espace libre          : {free_gb_for(args.tmp_dir):.1f} Go")
    print("  statistiques globales :")
    for k in sorted(total):
        v = total[k]
        if isinstance(v, int):
            print(f"    {k:30s} : {v:,}")
        else:
            print(f"    {k:30s} : {v}")
    write_summary(args, moduli, total, elapsed)


if __name__ == "__main__":
    main()
