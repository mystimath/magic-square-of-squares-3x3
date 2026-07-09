#!/usr/bin/env python3
"""
Branche B2 — recherche optimisée d'un carré magique 3x3 de carrés
avec centre non nécessairement carré et 8 cases extérieures carrées.

Version v2 optimisée :
- génération parallèle des paires opposées (x^2, y^2) autour d'un centre e ;
- sharding sur disque par blocs de centres pour éviter l'explosion mémoire ;
- traitement indépendant des shards ;
- recherche exacte des motifs d'offsets {u, v, u+v, |u-v|} ;
- déduplication par symétries du carré ;
- écriture incrémentale CSV.

FORME UTILISÉE
==============
Tout carré magique 3x3 peut s'écrire avec un centre e et deux offsets u, v :

    a = e-u          b = e+u+v        c = e-v
    d = e+u-v        e                f = e-u+v
    g = e+v          h = e-u-v        i = e+u

Donc les 8 cases extérieures sont carrées ssi les 4 paires opposées suivantes
sont toutes des paires de carrés autour du même centre e :

    e ± u
    e ± v
    e ± (u+v)
    e ± (u-v)

La branche B2 revient donc à chercher des centres e possédant des offsets
u, v > 0 tels que u, v, u+v et |u-v| appartiennent tous à l'ensemble des
offsets carrés autour de e.

CRITÈRES D'ARRÊT — ROADMAP V2
=============================
B2-1 : racines extérieures <= 50 000
    But : dépasser proprement la borne 20 000.
    Stop si mur mémoire persistant après réécriture raisonnable.

B2-2 : racines extérieures <= 100 000
    But : chercher quasi-candidats 8/9 ou motifs riches.
    Stop si rien de nouveau qualitativement.

B2-3 : racines extérieures <= 250 000
    But : établir une nouvelle borne robuste.
    Gel si toujours aucun motif nouveau.

REMARQUES
=========
1. Le script est exact pour le schéma étudié : il ne fait pas de rejet heuristique
   sur les combinaisons (hormis des filtres optionnels contrôlés).
2. La mémoire est maîtrisée par sharding : les paires (centre, offset) sont écrites
   sur disque par plages de centres, puis traitées shard par shard.
3. La première étape est surtout CPU+I/O ; la seconde est CPU légère mais peut
   être parallélisée par shard si nécessaire.
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
from typing import DefaultDict, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


# ============================================================================
# Profils de campagne B2
# ============================================================================


CAMPAIGN_PROFILES = {
    "B2-1": {
        "target_outer_root": 50_000,
        "goal": "Dépasser proprement la borne 20 000.",
        "stop_rule": "Stop si mur mémoire persistant après réécriture raisonnable.",
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
# Modèle de données
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
    "center",
    "u",
    "v",
    "center_is_square",
    "primitive_gcd",
    "roots_distinct",
    "total_squares",
    "symmetry_key",
    "a", "b", "c",
    "d", "e", "f",
    "g", "h", "i",
]


# ============================================================================
# Outils arithmétiques
# ============================================================================


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


def roots_distinct(values: Sequence[int]) -> bool:
    roots = [math.isqrt(v) for v in values]
    return len(set(roots)) == len(roots)


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def chunk_ranges(start: int, stop: int, chunks: int) -> List[Tuple[int, int]]:
    """Partitionne [start, stop] inclus en chunks plages équilibrées."""
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
    """Retourne les 8 symétries du carré 3x3, représentation aplatie ligne-major."""
    # indices ligne-major:
    # 0 1 2
    # 3 4 5
    # 6 7 8
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
    c = min(matrix_symmetries(vals))
    return "|".join(str(x) for x in c)


# ============================================================================
# Génération parallèle des paires (centre, offset) shardées sur disque
# ============================================================================


def _flush_worker_buffers(buffers: Dict[int, List[str]], paths: Dict[int, str]) -> int:
    flushed = 0
    for shard_id, lines in list(buffers.items()):
        if not lines:
            continue
        path = paths[shard_id]
        with open(path, "a", encoding="utf-8", newline="") as f:
            f.writelines(lines)
        flushed += len(lines)
        buffers[shard_id].clear()
    return flushed


def generate_pair_shards_worker(
    worker_id: int,
    x_start: int,
    x_end: int,
    max_root: int,
    shard_size: int,
    tmp_dir: str,
    flush_lines: int,
    non_square_center_only: bool,
) -> Dict[str, int]:
    """
    Génère des lignes 'center,offset\n' pour sa plage de racines basses x.
    Écriture dans des fichiers temporaires séparés par shard et par worker.
    """
    shard_dir = os.path.join(tmp_dir, "pair_shards")
    os.makedirs(shard_dir, exist_ok=True)

    buffers: Dict[int, List[str]] = defaultdict(list)
    paths: Dict[int, str] = {}
    stats = Counter()
    buffered_total = 0

    for x in range(x_start, x_end + 1):
        x2 = x * x
        y0 = x + 1
        if ((y0 - x) & 1) == 1:
            y0 += 1

        for y in range(y0, max_root + 1, 2):
            y2 = y * y
            center2 = x2 + y2
            center = center2 >> 1
            if non_square_center_only and is_square(center):
                stats["reject_center_square_pair"] += 1
                continue
            offset = (y2 - x2) >> 1
            shard_id = center // shard_size
            if shard_id not in paths:
                paths[shard_id] = os.path.join(shard_dir, f"pairs_shard_{shard_id:08d}_worker_{worker_id:03d}.csv")
            buffers[shard_id].append(f"{center},{offset}\n")
            stats["pairs_written"] += 1
            buffered_total += 1

            if buffered_total >= flush_lines:
                _flush_worker_buffers(buffers, paths)
                buffered_total = 0

        stats["x_done"] += 1

    _flush_worker_buffers(buffers, paths)
    stats["shards_touched"] = len(paths)
    return dict(stats)


# ============================================================================
# Traitement d'un shard
# ============================================================================


def iter_shard_records(paths: List[str]) -> Iterator[Tuple[int, int]]:
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                yield int(row[0]), int(row[1])


def load_offsets_by_center(paths: List[str]) -> Dict[int, set[int]]:
    buckets: DefaultDict[int, set[int]] = defaultdict(set)
    for center, offset in iter_shard_records(paths):
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

    total_squares = sum(is_square(x) for x in vals)
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
        roots_distinct=roots_distinct(outer_vals),
        total_squares=total_squares,
        symmetry_key=canonical_key(vals),
    )


def find_candidates_for_center(
    center: int,
    offsets: set[int],
    distinct_roots: bool,
    primitive_only: bool,
    non_square_center_only: bool,
    max_candidates_per_center: int,
) -> Tuple[List[Candidate], Counter]:
    stats = Counter()
    out: List[Candidate] = []

    if len(offsets) < 4:
        stats["centers_too_few_offsets"] += 1
        return out, stats

    if non_square_center_only and is_square(center):
        stats["reject_center_square"] += 1
        return out, stats

    off = sorted(offsets)
    off_set = offsets
    seen = set()

    # On prend u > v > 0, puis on exige u-v et u+v présents.
    # Cela parcourt exactement les quadruples d'offsets requis.
    for idx_u, u in enumerate(off):
        for v in off[:idx_u]:
            diff = u - v
            summ = u + v
            if diff not in off_set or summ not in off_set:
                continue

            cand = candidate_from_uv(center, u, v)

            # Sécurité : les 8 extérieurs doivent être des carrés.
            if cand.total_squares < 8:
                stats["reject_not_8_outer"] += 1
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


def process_shard_worker(
    shard_id: int,
    shard_paths: List[str],
    out_dir: str,
    distinct_roots: bool,
    primitive_only: bool,
    non_square_center_only: bool,
    max_candidates_per_center: int,
) -> Dict[str, int]:
    stats = Counter()
    buckets = load_offsets_by_center(shard_paths)
    stats["centers_seen"] = len(buckets)

    out_path = os.path.join(out_dir, f"results_shard_{shard_id:08d}.csv")
    ensure_parent_dir(out_path)
    wrote_header = False

    for center, offsets in buckets.items():
        rows, local = find_candidates_for_center(
            center=center,
            offsets=offsets,
            distinct_roots=distinct_roots,
            primitive_only=primitive_only,
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


# ============================================================================
# Fusion des résultats des shards
# ============================================================================


def merge_result_csvs(result_paths: List[str], final_out: str) -> Tuple[int, int]:
    ensure_parent_dir(final_out)
    seen = set()
    written = 0
    duplicates = 0

    with open(final_out, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for path in sorted(result_paths):
            with open(path, newline="", encoding="utf-8") as fin:
                reader = csv.DictReader(fin)
                for row in reader:
                    key = row["symmetry_key"]
                    if key in seen:
                        duplicates += 1
                        continue
                    seen.add(key)
                    writer.writerow(row)
                    written += 1
    return written, duplicates


# ============================================================================
# Orchestration
# ============================================================================


def show_profile(profile_name: str) -> None:
    profile = CAMPAIGN_PROFILES.get(profile_name)
    if not profile:
        print(f"Profil inconnu : {profile_name}")
        return
    print(f"Profil {profile_name}")
    print(f"  cible      : racines extérieures <= {profile['target_outer_root']:,}")
    print(f"  objectif   : {profile['goal']}")
    print(f"  arrêt      : {profile['stop_rule']}")


def stage_generate(args: argparse.Namespace) -> Counter:
    t0 = time.time()
    print("[Stage 1/2] Génération parallèle des paires (center, offset) ...")

    workers = args.workers or os.cpu_count() or 4
    x_ranges = chunk_ranges(1, args.max_root, workers)

    total = Counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = []
        for wid, (xa, xb) in enumerate(x_ranges):
            futures.append(ex.submit(
                generate_pair_shards_worker,
                wid,
                xa,
                xb,
                args.max_root,
                args.shard_size,
                args.tmp_dir,
                args.flush_lines,
                args.non_square_center_only,
            ))

        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            print(
                f"  worker done: pairs={stats.get('pairs_written', 0):,}  "
                f"x_done={stats.get('x_done', 0):,}  shards={stats.get('shards_touched', 0):,}"
            )

    elapsed = time.time() - t0
    print(f"[Stage 1 terminé] durée={elapsed:.1f}s  pairs={total.get('pairs_written', 0):,}")
    return total


def discover_shards(tmp_dir: str) -> Dict[int, List[str]]:
    shard_dir = os.path.join(tmp_dir, "pair_shards")
    paths = glob.glob(os.path.join(shard_dir, "pairs_shard_*.csv"))
    grouped: DefaultDict[int, List[str]] = defaultdict(list)
    for path in paths:
        base = os.path.basename(path)
        # pairs_shard_00000012_worker_003.csv
        shard_id = int(base.split("_")[2])
        grouped[shard_id].append(path)
    return dict(grouped)


def stage_search(args: argparse.Namespace) -> Counter:
    t0 = time.time()
    print("[Stage 2/2] Traitement des shards et recherche des candidats ...")

    shard_groups = discover_shards(args.tmp_dir)
    print(f"  shards détectés : {len(shard_groups):,}")

    result_dir = os.path.join(args.tmp_dir, "result_shards")
    os.makedirs(result_dir, exist_ok=True)

    total = Counter()
    workers = args.shard_workers or min(args.workers or os.cpu_count() or 4, max(len(shard_groups), 1))

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = []
        for shard_id, paths in sorted(shard_groups.items()):
            futures.append(ex.submit(
                process_shard_worker,
                shard_id,
                paths,
                result_dir,
                args.distinct_roots,
                args.primitive_only,
                args.non_square_center_only,
                args.max_candidates_per_center,
            ))

        done = 0
        for fut in as_completed(futures):
            stats = Counter(fut.result())
            total.update(stats)
            done += 1
            print(
                f"  shard done {done}/{len(futures)}: centers={stats.get('centers_seen', 0):,}  "
                f"results={stats.get('results_written', 0):,}"
            )

    result_paths = sorted(glob.glob(os.path.join(result_dir, "results_shard_*.csv")))
    merged, dup = merge_result_csvs(result_paths, args.out)
    total["merged_results"] = merged
    total["merged_duplicates"] = dup

    elapsed = time.time() - t0
    print(f"[Stage 2 terminé] durée={elapsed:.1f}s  résultats distincts={merged:,}")
    return total


def run(args: argparse.Namespace) -> None:
    t0 = time.time()
    show_profile(args.profile)
    print("Recherche B2 optimisée — centre non nécessairement carré")
    print(f"  max-root              : {args.max_root:,}")
    print(f"  workers               : {args.workers or os.cpu_count() or 4}")
    print(f"  shard-workers         : {args.shard_workers or '(auto)'}")
    print(f"  shard-size            : {args.shard_size:,}")
    print(f"  tmp-dir               : {args.tmp_dir}")
    print(f"  out                   : {args.out}")
    print(f"  primitive-only        : {args.primitive_only}")
    print(f"  distinct-roots        : {args.distinct_roots}")
    print(f"  non-square-center-only: {args.non_square_center_only}")

    if args.clean_tmp and os.path.isdir(args.tmp_dir):
        shutil.rmtree(args.tmp_dir)
    os.makedirs(args.tmp_dir, exist_ok=True)
    ensure_parent_dir(args.out)

    total = Counter()
    if args.stage in ("all", "generate"):
        total.update(stage_generate(args))
    if args.stage in ("all", "search"):
        total.update(stage_search(args))

    elapsed = time.time() - t0
    print("\nTerminé.")
    print(f"  durée totale          : {elapsed:.1f}s")
    print("  statistiques globales :")
    for k in sorted(total):
        print(f"    {k:24s} : {total[k]:,}")
    print("\nCritère d'arrêt de la campagne :")
    print(f"  {CAMPAIGN_PROFILES[args.profile]['stop_rule']}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--profile", type=str, default="B2-1", choices=sorted(CAMPAIGN_PROFILES))
    p.add_argument("--stage", type=str, default="all", choices=["all", "generate", "search"],
                   help="all : génération + recherche ; generate : seulement shards ; search : traiter des shards existants.")
    p.add_argument("--max-root", type=int, default=50_000,
                   help="Borne sur les racines extérieures.")
    p.add_argument("--workers", type=int, default=None,
                   help="Workers pour la génération parallèle des paires.")
    p.add_argument("--shard-workers", type=int, default=None,
                   help="Workers pour le traitement des shards.")
    p.add_argument("--shard-size", type=int, default=10_000_000,
                   help="Largeur d'un shard en valeur de centre.")
    p.add_argument("--flush-lines", type=int, default=200_000,
                   help="Nombre approximatif de lignes bufferisées avant flush disque par worker.")
    p.add_argument("--tmp-dir", type=str, default="tmp/b2_non_square_center",
                   help="Répertoire temporaire pour les shards.")
    p.add_argument("--clean-tmp", action="store_true",
                   help="Supprime tmp-dir avant l'exécution.")
    p.add_argument("--primitive-only", action="store_true",
                   help="Ne conserve que les candidats primitifs (gcd des racines extérieures = 1).")
    p.add_argument("--distinct-roots", action="store_true",
                   help="Impose des racines extérieures toutes distinctes.")
    p.add_argument("--non-square-center-only", action="store_true",
                   help="Rejette les centres carrés, pour viser strictement la branche B.")
    p.add_argument("--max-candidates-per-center", type=int, default=100,
                   help="Cap de sécurité par centre lors de l'énumération des (u,v).")
    p.add_argument("--out", type=str, default="results/raw/b2_non_square_center_v2.csv",
                   help="CSV final de sortie.")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.max_root < 2:
        parser.error("--max-root doit être >= 2")
    if args.shard_size < 1:
        parser.error("--shard-size doit être >= 1")
    if args.flush_lines < 1:
        parser.error("--flush-lines doit être >= 1")
    if args.max_candidates_per_center < 1:
        parser.error("--max-candidates-per-center doit être >= 1")

    run(args)


if __name__ == "__main__":
    main()