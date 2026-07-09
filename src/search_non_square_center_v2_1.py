#!/usr/bin/env python3
"""
Branche B2 — recherche v2.1 d'un carré magique 3x3 de carrés
avec centre non nécessairement carré et 8 cases extérieures carrées.

ARCHITECTURE EN DEUX PASSES + OFFSETS SÉLECTIFS
===============================================
Cette version est conçue pour corriger le défaut majeur de la v2.0 :
la génération brute de toutes les paires (centre, offset), qui écrivait des
quantités massives de données temporaires pour des centres presque tous stériles.

Pass 1 — pré-filtrage des centres
---------------------------------
On génère toujours les paires opposées de carrés (x^2, y^2) autour d'un centre
    e = (x^2 + y^2) / 2
avec offset
    o = (y^2 - x^2) / 2
mais on NE stocke PAS les offsets complets.

À la place, pour chaque centre e, on agrège seulement des statistiques compactes :
  - count(e)    = nombre de paires rencontrées autour de e ;
  - mask1(e)    = bitset des offsets modulo m1 ;
  - mask2(e)    = bitset des offsets modulo m2.

Ces informations suffisent pour appliquer un filtre nécessaire mais bon marché :
si un vrai candidat existe, l'ensemble des offsets de e doit contenir 4 nombres
    {u, v, u+v, |u-v|}
Donc, modulo m, l'ensemble des résidus doit au moins contenir une configuration
analogue. On teste cette condition avec additive_pattern_possible(mask, m).

Un centre e survit à la passe 1 seulement si :
  1) count(e) >= min_offsets
  2) son masque modulo m1 autorise au moins un motif additif
  3) son masque modulo m2 autorise au moins un motif additif
  4) si demandé, e n'est pas lui-même un carré parfait.

Pass 2 — offsets sélectifs
--------------------------
Une fois la shortlist de centres survivants connue, on refait la génération des
paires, mais cette fois on ne conserve les offsets QUE pour les centres retenus
par la passe 1.

On obtient alors, pour chaque centre retenu e, l'ensemble exact S_e des offsets.
On cherche ensuite des u > v > 0 tels que
    u in S_e
    v in S_e
    u+v in S_e
    u-v in S_e

C'est la condition exacte garantissant que les 4 paires opposées
    e ± u, e ± v, e ± (u+v), e ± (u-v)
soient toutes carrées, ce qui reconstruit un carré magique 3x3 à 8 cases
extérieures carrées.

CRITÈRES D'ARRÊT — ROADMAP V2
=============================
B2-1 : racines extérieures <= 50 000
    But : dépasser proprement la borne 20 000.
    Stop si mur mémoire / disque persistant après cette réécriture.

B2-2 : racines extérieures <= 100 000
    But : chercher quasi-candidats 8/9 ou motifs riches.
    Stop si rien de nouveau qualitativement.

B2-3 : racines extérieures <= 250 000
    But : nouvelle borne robuste.
    Gel si toujours aucun motif nouveau.

NOTES D'IMPLÉMENTATION
======================
- Pass 1 est parallélisée par plages de racines x.
- Les agrégats de pass 1 sont flushés par batch de x pour limiter la mémoire.
- Les centres survivants sont écrits par shard.
- Pass 2 peut être relancée seule si la pass 1 a déjà été faite.
- La recherche exacte finale se fait shard par shard et déduplique les symétries.
"""

from __future__ import annotations

import argparse
import csv
import glob
import math
import os
import shutil
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, Iterator, List, Sequence, Set, Tuple


# ============================================================================
# Profils de campagne
# ============================================================================


CAMPAIGN_PROFILES = {
    "B2-1": {
        "target_outer_root": 50_000,
        "goal": "Dépasser proprement la borne 20 000.",
        "stop_rule": "Stop si mur mémoire / disque persistant après cette réécriture.",
    },
    "B2-2": {
        "target_outer_root": 100_000,
        "goal": "Chercher quasi-candidats 8/9 ou motifs riches.",
        "stop_rule": "Stop si rien de nouveau qualitativement.",
    },
    "B2-3": {
        "target_outer_root": 250_000,
        "goal": "Établir une nouvelle borne robuste.",
        "stop_rule": "Gel si toujours aucun motif nouveau.",
    },
}


# ============================================================================
# Modèle candidat
# ============================================================================


@dataclass(frozen=True)
class Candidate:
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
    primitive_gcd: int
    roots_distinct: bool
    total_squares: int
    symmetry_key: str


CSV_FIELDS = [
    "center", "u", "v", "center_is_square", "primitive_gcd", "roots_distinct", "total_squares", "symmetry_key",
    "a", "b", "c", "d", "e", "f", "g", "h", "i",
]


# ============================================================================
# Utilitaires
# ============================================================================


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


def gcd_list(values: Sequence[int]) -> int:
    g = 0
    for v in values:
        g = math.gcd(g, v)
    return g


def primitive_gcd_of_square_values(values: Sequence[int]) -> int:
    roots = []
    for v in values:
        if not is_square(v):
            return gcd_list(values)
        roots.append(math.isqrt(v))
    return gcd_list(roots)


def roots_all_distinct(values: Sequence[int]) -> bool:
    roots = [math.isqrt(v) for v in values]
    return len(set(roots)) == len(roots)


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
    def rot90(m):
        return (m[6], m[3], m[0], m[7], m[4], m[1], m[8], m[5], m[2])
    def refl(m):
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


def bit(mask: int, i: int) -> bool:
    return ((mask >> i) & 1) == 1


def additive_pattern_possible(mask: int, modulus: int) -> bool:
    """
    Test nécessaire modulo m.
    Si l'ensemble exact contient {u,v,u+v,u-v} avec u>v>0, alors modulo m
    le masque des résidus contient aussi r, s, r+s, r-s.
    """
    residues = [r for r in range(modulus) if bit(mask, r)]
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


# ============================================================================
# Pass 1 — génération parallèle des agrégats compacts par centre
# ============================================================================


def flush_pass1_batch(
    local: Dict[int, Dict[int, List[int]]],
    paths: Dict[int, str],
) -> int:
    """
    Écrit pour chaque shard des lignes : center,count,mask1,mask2
    local[shard][center] = [count, mask1, mask2]
    """
    lines_written = 0
    for shard_id, center_map in local.items():
        if not center_map:
            continue
        path = paths[shard_id]
        with open(path, "a", encoding="utf-8", newline="") as f:
            for center, triple in center_map.items():
                cnt, m1, m2 = triple
                f.write(f"{center},{cnt},{m1},{m2}\n")
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
    modulus1: int,
    modulus2: int,
    non_square_center_only: bool,
    tmp_dir: str,
) -> Dict[str, int]:
    """
    Pour une plage de racines x, agrège par batch des comptes de centres et des
    signatures de résidus d'offsets. N'écrit jamais les offsets complets.
    """
    part_dir = os.path.join(tmp_dir, "pass1_partials")
    ensure_dir(part_dir)
    stats = Counter()
    shard_paths: Dict[int, str] = {}

    batch_start = x_start
    while batch_start <= x_end:
        batch_end = min(batch_start + x_batch_size - 1, x_end)
        # local[shard_id][center] = [count, mask1, mask2]
        local: Dict[int, Dict[int, List[int]]] = defaultdict(dict)

        for x in range(batch_start, batch_end + 1):
            x2 = x * x
            y0 = x + 1
            if ((y0 - x) & 1) == 1:
                y0 += 1
            for y in range(y0, max_root + 1, 2):
                y2 = y * y
                center = (x2 + y2) >> 1
                if non_square_center_only and is_square(center):
                    stats["reject_center_square_pair"] += 1
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
                    center_map[center] = [1, 1 << (offset % modulus1), 1 << (offset % modulus2)]
                else:
                    item[0] += 1
                    item[1] |= 1 << (offset % modulus1)
                    item[2] |= 1 << (offset % modulus2)
                stats["pairs_seen"] += 1
            stats["x_done"] += 1

        stats["partial_rows_written"] += flush_pass1_batch(local, shard_paths)
        stats["x_batches"] += 1
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
    min_offsets: int,
    modulus1: int,
    modulus2: int,
    non_square_center_only: bool,
) -> Dict[str, int]:
    """
    Réduit tous les partiels d'un shard en agrégat exact center -> (count, mask1, mask2),
    puis sélectionne les centres survivants.
    """
    agg: Dict[int, List[int]] = {}
    stats = Counter()
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                center = int(row[0])
                cnt = int(row[1])
                m1 = int(row[2])
                m2 = int(row[3])
                item = agg.get(center)
                if item is None:
                    agg[center] = [cnt, m1, m2]
                else:
                    item[0] += cnt
                    item[1] |= m1
                    item[2] |= m2
    stats["centers_seen"] = len(agg)

    ensure_dir(selected_dir)
    out_path = os.path.join(selected_dir, f"selected_shard_{shard_id:08d}.csv")
    survivors = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["center", "count", "mask1", "mask2"])
        for center, (cnt, m1, m2) in agg.items():
            if non_square_center_only and is_square(center):
                stats["reject_center_square"] += 1
                continue
            if cnt < min_offsets:
                stats["reject_count"] += 1
                continue
            if not additive_pattern_possible(m1, modulus1):
                stats["reject_mod1"] += 1
                continue
            if not additive_pattern_possible(m2, modulus2):
                stats["reject_mod2"] += 1
                continue
            writer.writerow([center, cnt, m1, m2])
            survivors += 1
    stats["selected_centers"] = survivors
    stats["shard_id"] = shard_id
    return dict(stats)


# ============================================================================
# Pass 2 — régénération sélective des offsets des centres retenus
# ============================================================================


def load_selected_centers_by_shard(tmp_dir: str) -> Dict[int, Set[int]]:
    selected_dir = os.path.join(tmp_dir, "selected_centers")
    paths = glob.glob(os.path.join(selected_dir, "selected_shard_*.csv"))
    grouped: Dict[int, Set[int]] = {}
    for path in paths:
        base = os.path.basename(path)
        shard_id = int(base.split("_")[2].split(".")[0])
        s = set()
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                s.add(int(row["center"]))
        if s:
            grouped[shard_id] = s
    return grouped


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
    non_square_center_only: bool,
    tmp_dir: str,
) -> Dict[str, int]:
    """
    Refait la génération des paires, mais n'écrit les offsets que pour les centres
    sélectionnés par la passe 1.
    """
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
            if non_square_center_only and is_square(center):
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

    pass2_flush_offsets(local, shard_paths)
    stats["shards_touched"] = len(shard_paths)
    return dict(stats)


# ============================================================================
# Recombinaison exacte des offsets sélectionnés
# ============================================================================


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
                center = int(row[0])
                offset = int(row[1])
                buckets[center].add(offset)
    return dict(buckets)


def candidate_from_uv(center: int, u: int, v: int) -> Candidate:
    a = center - u
    i = center + u
    c = center - v
    g = center + v
    b = center + u + v
    h = center - u - v
    d = center + u - v
    f = center - u + v
    vals = (a, b, c, d, center, f, g, h, i)
    outer_vals = (a, b, c, d, f, g, h, i)
    return Candidate(
        center=center,
        u=u,
        v=v,
        a=a,
        b=b,
        c=c,
        d=d,
        e=center,
        f=f,
        g=g,
        h=h,
        i=i,
        center_is_square=is_square(center),
        primitive_gcd=primitive_gcd_of_square_values(outer_vals),
        roots_distinct=roots_all_distinct(outer_vals),
        total_squares=sum(is_square(x) for x in vals),
        symmetry_key=canonical_key(vals),
    )


def recombine_center_offsets(
    center: int,
    offsets: Set[int],
    primitive_only: bool,
    distinct_roots: bool,
    non_square_center_only: bool,
    max_candidates_per_center: int,
) -> Tuple[List[Candidate], Counter]:
    stats = Counter()
    out: List[Candidate] = []

    if non_square_center_only and is_square(center):
        stats["reject_center_square"] += 1
        return out, stats

    off = sorted(offsets)
    if len(off) < 4:
        stats["reject_too_few_offsets_exact"] += 1
        return out, stats

    off_set = offsets
    seen = set()
    for idx_u, u in enumerate(off):
        for v in off[:idx_u]:
            diff = u - v
            summ = u + v
            if diff not in off_set or summ not in off_set:
                continue
            cand = candidate_from_uv(center, u, v)
            if cand.total_squares < 8:
                stats["reject_not_8_outer_exact"] += 1
                continue
            if distinct_roots and not cand.roots_distinct:
                stats["reject_duplicate_roots"] += 1
                continue
            if primitive_only and cand.primitive_gcd != 1:
                stats["reject_non_primitive"] += 1
                continue
            if cand.symmetry_key in seen:
                stats["reject_duplicate_symmetry"] += 1
                continue
            seen.add(cand.symmetry_key)
            out.append(cand)
            stats["candidates_kept"] += 1
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
    primitive_only: bool,
    distinct_roots: bool,
    non_square_center_only: bool,
    max_candidates_per_center: int,
) -> Dict[str, int]:
    buckets = load_offsets_by_center(paths)
    stats = Counter()
    stats["centers_seen"] = len(buckets)

    out_path = os.path.join(out_dir, f"results_shard_{shard_id:08d}.csv")
    wrote_header = False

    for center, offsets in buckets.items():
        rows, local = recombine_center_offsets(
            center=center,
            offsets=offsets,
            primitive_only=primitive_only,
            distinct_roots=distinct_roots,
            non_square_center_only=non_square_center_only,
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
                    writer.writerow(cand.__dict__)
            stats["results_written"] += len(rows)
    stats["shard_id"] = shard_id
    return dict(stats)


def merge_result_csvs(result_paths: List[str], final_out: str) -> Tuple[int, int]:
    ensure_parent(final_out)
    seen = set()
    written = 0
    dup = 0
    with open(final_out, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for path in sorted(result_paths):
            with open(path, newline="", encoding="utf-8") as fin:
                reader = csv.DictReader(fin)
                for row in reader:
                    key = row["symmetry_key"]
                    if key in seen:
                        dup += 1
                        continue
                    seen.add(key)
                    writer.writerow(row)
                    written += 1
    return written, dup


# ============================================================================
# Orchestration des stages
# ============================================================================


def show_profile(name: str) -> None:
    p = CAMPAIGN_PROFILES[name]
    print(f"Profil {name}")
    print(f"  cible      : racines extérieures <= {p['target_outer_root']:,}")
    print(f"  objectif   : {p['goal']}")
    print(f"  arrêt      : {p['stop_rule']}")


def stage_pass1(args: argparse.Namespace) -> Counter:
    t0 = time.time()
    print("[Pass 1A] Génération parallèle des agrégats compacts par centre...")
    workers = args.workers or os.cpu_count() or 4
    xranges = chunk_ranges(1, args.max_root, workers)
    total = Counter()

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = []
        for wid, (xa, xb) in enumerate(xranges):
            futures.append(ex.submit(
                pass1_generate_worker,
                wid,
                xa,
                xb,
                args.max_root,
                args.x_batch_size,
                args.shard_size,
                args.modulus1,
                args.modulus2,
                args.non_square_center_only,
                args.tmp_dir,
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
    ensure_dir(selected_dir)

    with ProcessPoolExecutor(max_workers=args.reduce_workers or min(workers, max(len(partials), 1))) as ex:
        futures = []
        for shard_id, paths in sorted(partials.items()):
            futures.append(ex.submit(
                pass1_reduce_shard_worker,
                shard_id,
                paths,
                selected_dir,
                args.min_offsets,
                args.modulus1,
                args.modulus2,
                args.non_square_center_only,
            ))
        done = 0
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            done += 1
            print(
                f"  shard reduce {done}/{len(futures)}: centers={stats.get('centers_seen', 0):,}  "
                f"selected={stats.get('selected_centers', 0):,}"
            )

    print(f"[Pass 1 terminé] durée totale pass1={time.time() - t0:.1f}s")
    return total


def stage_pass2(args: argparse.Namespace) -> Counter:
    t0 = time.time()
    print("[Pass 2A] Régénération sélective des offsets des centres retenus...")
    total = Counter()
    workers = args.pass2_workers or min(args.workers or os.cpu_count() or 4, 2)
    xranges = chunk_ranges(1, args.max_root, workers)

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = []
        for wid, (xa, xb) in enumerate(xranges):
            futures.append(ex.submit(
                pass2_generate_offsets_worker,
                wid,
                xa,
                xb,
                args.max_root,
                args.shard_size,
                args.non_square_center_only,
                args.tmp_dir,
            ))
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            print(
                f"  worker done: offsets={stats.get('offset_rows_written', 0):,}  "
                f"x_done={stats.get('x_done', 0):,}"
            )

    print(f"[Pass 2A terminé] durée={time.time() - t0:.1f}s")

    print("[Pass 2B] Recombinaison exacte des offsets par shard...")
    offset_groups = discover_pass2_offset_files(args.tmp_dir)
    result_dir = os.path.join(args.tmp_dir, "result_shards")
    ensure_dir(result_dir)
    recomb_workers = args.recombine_workers or min(args.workers or os.cpu_count() or 4, max(len(offset_groups), 1))

    with ProcessPoolExecutor(max_workers=recomb_workers) as ex:
        futures = []
        for shard_id, paths in sorted(offset_groups.items()):
            futures.append(ex.submit(
                recombine_shard_worker,
                shard_id,
                paths,
                result_dir,
                args.primitive_only,
                args.distinct_roots,
                args.non_square_center_only,
                args.max_candidates_per_center,
            ))
        done = 0
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            done += 1
            print(
                f"  shard recombine {done}/{len(futures)}: centers={stats.get('centers_seen', 0):,}  "
                f"results={stats.get('results_written', 0):,}"
            )

    result_paths = sorted(glob.glob(os.path.join(result_dir, "results_shard_*.csv")))
    merged, dup = merge_result_csvs(result_paths, args.out)
    total["merged_results"] = merged
    total["merged_duplicates"] = dup
    print(f"[Pass 2 terminé] durée totale pass2={time.time() - t0:.1f}s  résultats distincts={merged:,}")
    return total


# ============================================================================
# CLI
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--profile", type=str, default="B2-1", choices=sorted(CAMPAIGN_PROFILES))
    p.add_argument("--stage", type=str, default="all", choices=["all", "pass1", "pass2"],
                   help="all = pass1 + pass2 ; pass1 = pré-filtrage seul ; pass2 = offsets sélectifs + recombinaison à partir d'une pass1 existante.")
    p.add_argument("--max-root", type=int, default=50_000)
    p.add_argument("--workers", type=int, default=None,
                   help="Workers pour la pass 1.")
    p.add_argument("--reduce-workers", type=int, default=None,
                   help="Workers pour la réduction des shards de pass 1.")
    p.add_argument("--pass2-workers", type=int, default=None,
                   help="Workers pour la régénération sélective des offsets (par défaut petit pour ménager la RAM).")
    p.add_argument("--recombine-workers", type=int, default=None,
                   help="Workers pour la recombinaison exacte finale.")
    p.add_argument("--x-batch-size", type=int, default=256,
                   help="Taille de batch en x pour la pass 1 (mémoire contrôlée).")
    p.add_argument("--shard-size", type=int, default=10_000_000,
                   help="Largeur d'un shard en valeur de centre.")
    p.add_argument("--modulus1", type=int, default=64,
                   help="Premier module de signature d'offsets pour la pass 1.")
    p.add_argument("--modulus2", type=int, default=63,
                   help="Second module de signature d'offsets pour la pass 1.")
    p.add_argument("--min-offsets", type=int, default=4,
                   help="Nombre minimal d'offsets/paires autour d'un centre pour survivre à la pass 1.")
    p.add_argument("--primitive-only", action="store_true")
    p.add_argument("--distinct-roots", action="store_true")
    p.add_argument("--non-square-center-only", action="store_true")
    p.add_argument("--max-candidates-per-center", type=int, default=100)
    p.add_argument("--tmp-dir", type=str, default="tmp/b2_non_square_center_v2_1")
    p.add_argument("--clean-tmp", action="store_true")
    p.add_argument("--out", type=str, default="results/raw/b2_non_square_center_v2_1.csv")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.max_root < 2:
        parser.error("--max-root doit être >= 2")
    if args.x_batch_size < 1:
        parser.error("--x-batch-size doit être >= 1")
    if args.shard_size < 1:
        parser.error("--shard-size doit être >= 1")
    if args.min_offsets < 1:
        parser.error("--min-offsets doit être >= 1")
    if args.max_candidates_per_center < 1:
        parser.error("--max-candidates-per-center doit être >= 1")
    if args.modulus1 < 2 or args.modulus2 < 2:
        parser.error("--modulus1 et --modulus2 doivent être >= 2")

    show_profile(args.profile)
    print("Recherche B2 v2.1 — deux passes + offsets sélectifs")
    print(f"  max-root               : {args.max_root:,}")
    print(f"  workers pass1          : {args.workers or os.cpu_count() or 4}")
    print(f"  workers pass2          : {args.pass2_workers or min(args.workers or os.cpu_count() or 4, 2)}")
    print(f"  workers recombine      : {args.recombine_workers or '(auto)'}")
    print(f"  x-batch-size           : {args.x_batch_size}")
    print(f"  shard-size             : {args.shard_size:,}")
    print(f"  moduli signatures      : {args.modulus1}, {args.modulus2}")
    print(f"  min-offsets            : {args.min_offsets}")
    print(f"  primitive-only         : {args.primitive_only}")
    print(f"  distinct-roots         : {args.distinct_roots}")
    print(f"  non-square-center-only : {args.non_square_center_only}")
    print(f"  tmp-dir                : {args.tmp_dir}")
    print(f"  out                    : {args.out}")

    if args.clean_tmp and os.path.isdir(args.tmp_dir):
        shutil.rmtree(args.tmp_dir)
    ensure_dir(args.tmp_dir)
    ensure_parent(args.out)

    total = Counter()
    t0 = time.time()

    if args.stage in ("all", "pass1"):
        total.update(stage_pass1(args))
    if args.stage in ("all", "pass2"):
        total.update(stage_pass2(args))

    elapsed = time.time() - t0
    print("\nTerminé.")
    print(f"  durée totale           : {elapsed:.1f}s")
    print("  statistiques globales  :")
    for k in sorted(total):
        print(f"    {k:28s} : {total[k]:,}")
    print("\nCritère d'arrêt de la campagne :")
    print(f"  {CAMPAIGN_PROFILES[args.profile]['stop_rule']}")


if __name__ == "__main__":
    main()
