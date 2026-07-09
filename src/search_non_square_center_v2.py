#!/usr/bin/env python3
"""
Branche B2 — recherche d'un carré magique 3x3 avec centre non nécessairement carré
et huit cases extérieures carrées, en version streaming / block-processing.

OBJECTIF
========
Dépasser les anciennes bornes de la branche B sans exploser en mémoire.
La version historique plafonnait à cause d'une génération trop large de centres
et d'offsets. Cette v2 pose une architecture orientée flux :

    1) génération des paires opposées de carrés ;
    2) regroupement par centre e=(x^2+y^2)/2 ;
    3) traitement par blocs de centres ;
    4) crible modulaire précoce ;
    5) combinaison incrémentale des quatre paires opposées ;
    6) écriture incrémentale des résultats.

REMARQUE IMPORTANTE
===================
Ceci est un SQUELETTE DE RECHERCHE :
- l'architecture, l'API CLI, les checkpoints et les points d'extension sont en place ;
- les cribles modulaires simples sont implémentés ;
- la combinaison finale exhaustive de toutes les familles est volontairement laissée
  partiellement TODO, pour pouvoir être adaptée proprement à la stratégie B2 réelle.

Le fichier est pensé pour être intégré dans le repo et complété itérativement.

FORMALISME UTILISÉ
==================
On note le carré magique 3x3 sous la forme standard :

    a  b  c
    d  e  f
    g  h  i

avec les contraintes magiques usuelles. Pour un carré 3x3, on a toujours :

    a + i = 2e
    b + h = 2e
    c + g = 2e
    d + f = 2e

Dans la branche B, on cherche des cas où les 8 cases extérieures
(a,b,c,d,f,g,h,i) sont des carrés parfaits, mais e n'est pas forcément un carré.

CRITÈRES D'ARRÊT — TABLEAU B2
==============================
B2-1 : racines extérieures <= 50 000
    But : dépasser proprement l'ancienne borne 20 000.
    Stop si mur mémoire persistant après réécriture raisonnable.

B2-2 : racines extérieures <= 100 000
    But : chercher quasi-candidats 8/9 ou motifs riches.
    Stop si rien de nouveau qualitativement.

B2-3 : racines extérieures <= 250 000
    But : nouvelle borne robuste.
    Gel si toujours aucun motif nouveau.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from typing import DefaultDict, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


# ============================================================================
# Structures de données
# ============================================================================


@dataclass(frozen=True)
class OppositeSquarePair:
    """
    Une paire opposée autour d'un même centre e.

    left_value + right_value = 2e
    left_value = x^2
    right_value = y^2

    offset = y^2 - e = e - x^2 > 0
    """
    root_lo: int
    root_hi: int
    val_lo: int
    val_hi: int
    center: int
    offset: int


@dataclass
class CandidateSquare:
    """Candidat complet ou quasi-complet reconstruit à partir de 4 paires opposées."""
    center: int
    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    g: int
    h: int
    i: int
    outer_square_count: int
    center_is_square: bool
    primitive_gcd: int
    notes: str = ""


@dataclass
class SearchStats:
    started_at: float
    pairs_total: int = 0
    centers_seen: int = 0
    centers_after_mod_filter: int = 0
    center_blocks: int = 0
    candidate_centers_combined: int = 0
    results_kept: int = 0

    def to_counter(self) -> Counter:
        return Counter({
            "pairs_total": self.pairs_total,
            "centers_seen": self.centers_seen,
            "centers_after_mod_filter": self.centers_after_mod_filter,
            "center_blocks": self.center_blocks,
            "candidate_centers_combined": self.candidate_centers_combined,
            "results_kept": self.results_kept,
        })


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


def primitive_gcd_of_square(values: Sequence[int]) -> int:
    """GCD au niveau des racines si toutes les valeurs sont des carrés, sinon GCD des valeurs."""
    roots = []
    for v in values:
        if is_square(v):
            roots.append(math.isqrt(v))
        else:
            return gcd_list(values)
    return gcd_list(roots)


def parse_moduli(spec: str) -> List[int]:
    if not spec.strip():
        return []
    return [int(x.strip()) for x in spec.split(",") if x.strip()]


def quadratic_residues_mod(m: int) -> set[int]:
    return {(x * x) % m for x in range(m)}


# ============================================================================
# Génération streaming des paires opposées
# ============================================================================


def generate_opposite_square_pairs(max_root: int) -> Iterator[OppositeSquarePair]:
    """
    Génère toutes les paires de carrés (x^2, y^2) de même parité de somme,
    afin que e=(x^2+y^2)/2 soit entier.

    x<y pour éviter les doublons. Les deux racines doivent avoir la même parité
    car x^2 ≡ x (mod 2), donc x^2+y^2 doit être pair.
    """
    for x in range(1, max_root + 1):
        x2 = x * x
        start = x + 1
        # y de même parité que x
        if (start - x) & 1:
            start += 1
        for y in range(start, max_root + 1, 2):
            y2 = y * y
            s = x2 + y2
            # ici s est pair par construction
            center = s // 2
            offset = y2 - center
            yield OppositeSquarePair(
                root_lo=x,
                root_hi=y,
                val_lo=x2,
                val_hi=y2,
                center=center,
                offset=offset,
            )


def bucket_pairs_by_center(
    max_root: int,
    center_min: int,
    center_max: int,
    modular_filter: Optional["ModularCenterFilter"] = None,
) -> Dict[int, List[OppositeSquarePair]]:
    """
    Construit un seau center -> liste de paires opposées, uniquement pour le bloc
    de centres demandé.

    C'est la primitive clé pour éviter d'accumuler tout l'espace en mémoire.
    """
    buckets: DefaultDict[int, List[OppositeSquarePair]] = defaultdict(list)
    for pair in generate_opposite_square_pairs(max_root):
        if pair.center < center_min or pair.center > center_max:
            continue
        if modular_filter and not modular_filter.center_passes(pair.center):
            continue
        buckets[pair.center].append(pair)
    return dict(buckets)


# ============================================================================
# Cribles modulaires simples
# ============================================================================


class ModularCenterFilter:
    """
    Filtre modulaire simple sur le centre et sur les paires opposées.

    Ce filtre est volontairement conservateur : il ne doit pas jeter des cas
    potentiellement valides sans justification claire.
    """

    def __init__(self, moduli: Sequence[int], require_outer_nonzero_mod: bool = False):
        self.moduli = list(moduli)
        self.qr = {m: quadratic_residues_mod(m) for m in self.moduli}
        self.require_outer_nonzero_mod = require_outer_nonzero_mod

    def center_passes(self, center: int) -> bool:
        # TODO : raffiner selon les observations expérimentales de la branche B2.
        # Filtre volontairement très léger pour le squelette.
        for m in self.moduli:
            c = center % m
            # Exemple conservateur : rien n'interdit a priori un centre non carré,
            # donc on ne filtre pas fort ici.
            if self.require_outer_nonzero_mod and c == 0:
                return False
        return True

    def pair_passes(self, pair: OppositeSquarePair) -> bool:
        for m in self.moduli:
            lo = pair.val_lo % m
            hi = pair.val_hi % m
            qr = self.qr[m]
            if lo not in qr or hi not in qr:
                return False
        return True


# ============================================================================
# Combinaison des paires autour d'un centre
# ============================================================================


def center_has_enough_pairs(pairs: List[OppositeSquarePair], min_pairs: int = 4) -> bool:
    return len(pairs) >= min_pairs


def choose_structural_pairs(pairs: List[OppositeSquarePair]) -> Iterator[Tuple[OppositeSquarePair, OppositeSquarePair, OppositeSquarePair, OppositeSquarePair]]:
    """
    Itérateur volontairement minimal : choisit 4 paires distinctes parmi celles
    d'un même centre. À compléter avec des heuristiques plus fines.

    TODO majeur B2 :
    - imposer des racines distinctes si désiré ;
    - imposer la cohérence avec la structure magique ;
    - éviter les symétries inutiles ;
    - prioriser certaines classes d'offsets.
    """
    n = len(pairs)
    if n < 4:
        return
    # squelette simple, sans recherche exhaustive déraisonnable dans ce fichier
    limit = min(n, 12)  # garde-fou pour le squelette
    for i in range(limit):
        for j in range(i + 1, limit):
            for k in range(j + 1, limit):
                for l in range(k + 1, limit):
                    yield pairs[i], pairs[j], pairs[k], pairs[l]


def build_candidate_from_four_pairs(
    p_ai: OppositeSquarePair,
    p_bh: OppositeSquarePair,
    p_cg: OppositeSquarePair,
    p_df: OppositeSquarePair,
) -> CandidateSquare:
    """
    Reconstruit un candidat brut en affectant les 4 paires opposées.

    Convention de placement :
      (a,i), (b,h), (c,g), (d,f)

    TODO majeur B2 :
      ajouter les tests complets des lignes/colonnes/diagonales si besoin,
      et autoriser plusieurs affectations / symétries contrôlées.
    """
    e = p_ai.center
    assert e == p_bh.center == p_cg.center == p_df.center

    a, i = p_ai.val_lo, p_ai.val_hi
    b, h = p_bh.val_lo, p_bh.val_hi
    c, g = p_cg.val_lo, p_cg.val_hi
    d, f = p_df.val_lo, p_df.val_hi

    outer_values = [a, b, c, d, f, g, h, i]
    outer_square_count = sum(is_square(v) for v in outer_values)
    center_is_square = is_square(e)
    primitive_g = primitive_gcd_of_square(outer_values)

    return CandidateSquare(
        center=e,
        a=a,
        b=b,
        c=c,
        d=d,
        e=e,
        f=f,
        g=g,
        h=h,
        i=i,
        outer_square_count=outer_square_count,
        center_is_square=center_is_square,
        primitive_gcd=primitive_g,
        notes="raw-combination",
    )


def candidate_is_magic(candidate: CandidateSquare) -> bool:
    """
    Teste les 8 contraintes magiques classiques.

    Même si la structure par paires opposées garantit déjà certaines identités,
    on garde ici la vérification explicite.
    """
    rows = [candidate.a + candidate.b + candidate.c,
            candidate.d + candidate.e + candidate.f,
            candidate.g + candidate.h + candidate.i]
    cols = [candidate.a + candidate.d + candidate.g,
            candidate.b + candidate.e + candidate.h,
            candidate.c + candidate.f + candidate.i]
    diags = [candidate.a + candidate.e + candidate.i,
             candidate.c + candidate.e + candidate.g]
    return len(set(rows + cols + diags)) == 1


def candidate_outer_roots_distinct(candidate: CandidateSquare) -> bool:
    vals = [candidate.a, candidate.b, candidate.c, candidate.d,
            candidate.f, candidate.g, candidate.h, candidate.i]
    roots = [math.isqrt(v) for v in vals]
    return len(set(roots)) == len(roots)


def process_center_block(
    center_buckets: Dict[int, List[OppositeSquarePair]],
    require_distinct_roots: bool,
    primitive_only: bool,
    max_combinations_per_center: int,
) -> Tuple[List[CandidateSquare], Counter]:
    """
    Traite un bloc de centres en mémoire.

    Le traitement est volontairement conservateur / limité pour ce squelette.
    Il constitue une base d'extension, pas la version finale de B2.
    """
    out: List[CandidateSquare] = []
    stats = Counter()

    for center, pairs in center_buckets.items():
        stats["centers_seen_in_block"] += 1
        if not center_has_enough_pairs(pairs, 4):
            stats["centers_too_sparse"] += 1
            continue

        stats["candidate_centers_combined"] += 1
        n_done = 0
        for p_ai, p_bh, p_cg, p_df in choose_structural_pairs(pairs):
            cand = build_candidate_from_four_pairs(p_ai, p_bh, p_cg, p_df)

            if require_distinct_roots and not candidate_outer_roots_distinct(cand):
                stats["reject_duplicate_roots"] += 1
                continue

            if primitive_only and cand.primitive_gcd != 1:
                stats["reject_non_primitive"] += 1
                continue

            if not candidate_is_magic(cand):
                stats["reject_non_magic"] += 1
                continue

            out.append(cand)
            stats["results_kept"] += 1

            n_done += 1
            if n_done >= max_combinations_per_center:
                stats["center_combination_cap_hit"] += 1
                break

    return out, stats


# ============================================================================
# Ecriture / reporting
# ============================================================================


CSV_FIELDS = [
    "center",
    "a", "b", "c",
    "d", "e", "f",
    "g", "h", "i",
    "outer_square_count",
    "center_is_square",
    "primitive_gcd",
    "notes",
]


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def append_results_csv(path: str, rows: List[CandidateSquare], header_written: bool) -> bool:
    ensure_parent_dir(path)
    mode = "a" if header_written else "w"
    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not header_written:
            writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    return True


def print_checkpoint(stats: Counter, t0: float) -> None:
    elapsed = time.time() - t0
    centers = stats.get("centers_seen", 0)
    rate = centers / elapsed if elapsed > 0 else 0.0
    print(
        f"  [{elapsed:7.1f}s] centers={centers:,}  "
        f"results={stats.get('results_kept', 0):,}  "
        f"rate={rate:,.0f} centers/s"
    )


# ============================================================================
# Profils B2 / critères d'arrêt de campagne
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


def show_campaign_profile(profile_name: str) -> None:
    profile = CAMPAIGN_PROFILES.get(profile_name)
    if not profile:
        print(f"Profil inconnu : {profile_name}")
        return
    print(f"Profil {profile_name}")
    print(f"  cible      : racines extérieures <= {profile['target_outer_root']:,}")
    print(f"  objectif   : {profile['goal']}")
    print(f"  arrêt      : {profile['stop_rule']}")


# ============================================================================
# Boucle principale
# ============================================================================


def run_search(args: argparse.Namespace) -> None:
    t0 = time.time()
    stats = SearchStats(started_at=t0)
    counter = Counter()

    moduli = parse_moduli(args.moduli)
    modular_filter = ModularCenterFilter(moduli, require_outer_nonzero_mod=args.require_outer_nonzero_mod)

    if args.profile:
        show_campaign_profile(args.profile)

    print("Recherche B2 — centre non nécessairement carré")
    print(f"  max-root           : {args.max_root:,}")
    print(f"  center-block-size  : {args.center_block_size:,}")
    print(f"  moduli             : {moduli or '(aucun)'}")
    print(f"  primitive-only     : {args.primitive_only}")
    print(f"  distinct-roots     : {args.distinct_roots}")
    print(f"  out                : {args.out or '(aucune sortie CSV)'}")

    csv_header_written = False
    center_min = args.center_min
    center_max = args.center_max if args.center_max is not None else args.max_root * args.max_root

    # Découpage par blocs de centres
    current = center_min
    while current <= center_max:
        block_lo = current
        block_hi = min(current + args.center_block_size - 1, center_max)
        stats.center_blocks += 1

        buckets = bucket_pairs_by_center(
            max_root=args.max_root,
            center_min=block_lo,
            center_max=block_hi,
            modular_filter=modular_filter,
        )

        local_centers = len(buckets)
        stats.centers_seen += local_centers
        stats.centers_after_mod_filter += local_centers

        # Comptage approximatif des paires générées pour le reporting de ce bloc
        local_pairs = sum(len(v) for v in buckets.values())
        stats.pairs_total += local_pairs
        counter["pairs_total"] += local_pairs
        counter["centers_seen"] += local_centers
        counter["center_blocks"] += 1

        rows, local_stats = process_center_block(
            center_buckets=buckets,
            require_distinct_roots=args.distinct_roots,
            primitive_only=args.primitive_only,
            max_combinations_per_center=args.max_combinations_per_center,
        )
        counter.update(local_stats)

        if rows and args.out:
            csv_header_written = append_results_csv(args.out, rows, csv_header_written)
        stats.results_kept += len(rows)

        # Checkpoint périodique
        if stats.center_blocks % args.checkpoint_every_blocks == 0:
            print_checkpoint(counter, t0)

        current = block_hi + 1

    elapsed = time.time() - t0
    print("\nTerminé.")
    print(f"  durée totale       : {elapsed:.1f}s")
    print(f"  paires générées    : {stats.pairs_total:,}")
    print(f"  centres vus        : {stats.centers_seen:,}")
    print(f"  blocs de centres   : {stats.center_blocks:,}")
    print(f"  résultats gardés   : {stats.results_kept:,}")

    print("\nStatistiques détaillées :")
    for k in sorted(counter):
        print(f"  {k:28s} : {counter[k]:,}")

    if args.out:
        print(f"\nRésultats CSV écrits dans : {args.out}")

    print("\nRappel critère d'arrêt campagne :")
    if args.profile and args.profile in CAMPAIGN_PROFILES:
        print(f"  {CAMPAIGN_PROFILES[args.profile]['stop_rule']}")
    else:
        print("  Définir explicitement la règle de stop pour cette campagne.")


# ============================================================================
# CLI
# ============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--profile", type=str, default="B2-1",
                        help="Profil de campagne : B2-1, B2-2, B2-3.")
    parser.add_argument("--max-root", type=int, default=50_000,
                        help="Borne max sur les racines extérieures.")
    parser.add_argument("--center-min", type=int, default=1,
                        help="Centre minimal à traiter.")
    parser.add_argument("--center-max", type=int, default=None,
                        help="Centre maximal à traiter (défaut : max-root^2).")
    parser.add_argument("--center-block-size", type=int, default=200_000,
                        help="Taille d'un bloc de centres traité en mémoire.")
    parser.add_argument("--moduli", type=str, default="8,3,5,7,11",
                        help="Modules du crible léger, séparés par des virgules.")
    parser.add_argument("--require-outer-nonzero-mod", action="store_true",
                        help="Filtre expérimental très léger sur le centre modulo m.")
    parser.add_argument("--primitive-only", action="store_true",
                        help="Ne garder que les candidats primitifs.")
    parser.add_argument("--distinct-roots", action="store_true",
                        help="Impose des racines extérieures distinctes.")
    parser.add_argument("--max-combinations-per-center", type=int, default=5_000,
                        help="Garde-fou sur le nombre de combinaisons testées par centre.")
    parser.add_argument("--checkpoint-every-blocks", type=int, default=1,
                        help="Fréquence des checkpoints de progression.")
    parser.add_argument("--out", type=str, default=None,
                        help="CSV de sortie incrémental.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.max_root < 2:
        parser.error("--max-root doit être >= 2")
    if args.center_block_size < 1:
        parser.error("--center-block-size doit être >= 1")
    if args.max_combinations_per_center < 1:
        parser.error("--max-combinations-per-center doit être >= 1")
    if args.center_max is not None and args.center_max < args.center_min:
        parser.error("--center-max doit être >= --center-min")

    run_search(args)


if __name__ == "__main__":
    main()
