#!/usr/bin/env python3
"""
Recherche PARALLELISEE et A GRANDE ECHELLE de carres magiques 3x3
"presque parfaits" (magic squares of squares).

Objectif : depasser le record connu de 7/9 (Andrew Bremner, 2005), voire
trouver une solution complete a 9/9 (probleme ouvert).

============================================================================
CE QUI CHANGE PAR RAPPORT A LA VERSION PRECEDENTE
============================================================================

1. GENERATION DES TRIPLETS (A, E, J) -- MAINTENANT EN O(E log E) AU LIEU DE O(E^2)
   -----------------------------------------------------------------------
   On cherche A, E, J avec 2*E^2 = A^2 + J^2 (progression arithmetique de
   carres). En posant X=J-A, Y=J+A, Z=2E, on obtient :

       X^2 + Y^2 = Z^2

   C'est un TRIPLET PYTHAGORICIEN avec jambes X,Y paires. Tout triplet
   pythagoricien s'obtient a partir d'un triplet primitif (formule d'Euclide)
   multiplie par un entier :

       X0 = m^2 - n^2,  Y0 = 2mn,  Z0 = m^2 + n^2   (m > n > 0, pgcd(m,n)=1,
                                                       parites opposees)

   Comme Z0 est toujours impair pour un triplet primitif, il faut un
   multiplicateur PAIR (2e) pour que Z soit pair (Z=2E). D'ou, pour chaque
   (m,n) et chaque e = 1,2,3... :

       E = e * Z0
       A = e * |Y0 - X0|
       J = e * (Y0 + X0)

   Cette methode genere TOUS les triplets (A,E,J) avec E <= limite, sans
   doublon, en un temps largement sous-quadratique -- c'est ce qui permet
   de monter a E=10 000 000 et au-dela (comme vous l'avez deja fait de
   votre cote).

2. PARALLELISATION (multiprocessing)
   -----------------------------------------------------------------------
   L'etape couteuse reste le balayage de q pour chaque triplet (etape 2).
   Les triplets sont repartis en lots (chunks) distribues sur plusieurs
   processus via ProcessPoolExecutor. Chaque processus fait le balayage
   vectorise (numpy) pour son lot et renvoie les resultats interessants.

3. ECRITURE INCREMENTALE + REPRISE
   -----------------------------------------------------------------------
   Les resultats sont ecrits au fur et a mesure dans le CSV de sortie
   (avec flush), pour ne rien perdre en cas d'interruption (Ctrl+C) sur
   un run de plusieurs heures.

============================================================================
EXEMPLES D'USAGE (du plus rapide au plus ambitieux)
============================================================================

# ETAPE 0 (fortement recommandee avant tout gros run) : estimer le temps
# reel sur VOTRE machine avant de lancer quoi que ce soit de long.
# Fait un comptage exact + un benchmark sur echantillon + une projection :
python3 magic_square_parallel.py --limit 10000000 --qmax 100000 --workers 16 --estimate-only

# Test rapide (quelques secondes), pour verifier que tout fonctionne :
python3 magic_square_parallel.py --limit 5000 --qmax 50000 --workers 4

# Echelle moyenne (quelques minutes), sur une machine de bureau :
python3 magic_square_parallel.py --limit 200000 --qmax 300000 --workers 8 \\
    --min-total 6 --out resultats_200k.csv

# Grande echelle, E jusqu'a 10 millions (~23.5 millions de triplets).
# Chiffres mesures en pratique (1 coeur, machine de reference) :
#     qmax=1000    -> ~1.2h  mono-coeur  (donc ~5 min avec 16 coeurs)
#     qmax=10000   -> ~6.4h  mono-coeur  (donc ~24 min avec 16 coeurs)
#     qmax=100000  -> ~90h   mono-coeur  (donc ~5.6h avec 16 coeurs)
# Le cout croit quasi-lineairement avec qmax : commencez petit, puis montez
# progressivement en fonction du temps dont vous disposez.
python magic_square_parallel.py --limit 10000000 --qmax 10000 --workers 16 \\
    --min-total 7 --out resultats_10M.csv --chunk-size 200

# Si vous avez deja une liste de triplets (A,E,J) generee par votre propre
# script (jusqu'a 10M), vous pouvez la reutiliser directement plutot que
# de la regenerer ici (fichier texte/CSV avec 3 colonnes A,E,J) :
python3 magic_square_parallel.py --triples-file mes_triplets_10M.csv \\
    --qmax 10000 --workers 16 --min-total 7 --out resultats.csv

Notes pratiques :
  - --workers : mettez le nombre de coeurs physiques de votre machine
    (os.cpu_count() par defaut).
  - --qmax : c'est le vrai levier de decouverte, mais le cout total croit
    quasi-lineairement avec lui, ET le nombre de triplets EST DEJA enorme
    a E=10M (~23.5 millions). Utilisez TOUJOURS --estimate-only avant un
    gros run pour eviter de lancer un calcul de plusieurs jours par erreur.
  - --chunk-size : nombre de triplets envoyes a la fois a chaque processus.
    Un chunk trop petit = trop d'overhead IPC ; trop grand = mauvais
    equilibrage de charge et progres moins frequent. 100-500 est un bon
    point de depart.
  - --min-total : plus vous montez en echelle, plus il est important de
    filtrer fort (7 ou 8) pour ne garder qu'un volume de resultats gerable.
"""

import argparse
import csv
import math
import os
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import islice

import numpy as np


# ============================================================================
# ETAPE 1 : generation rapide des triplets (A, E, J) via Euclide
# ============================================================================

def generate_ap_triples_stream(E_limit):
    """
    Generateur (streaming, memoire bornee) de tous les triplets (A, E, J)
    avec 2 <= E <= E_limit et 2*E^2 = A^2 + J^2, via la formule d'Euclide
    des triplets pythagoriciens. Complexite largement sous-quadratique.
    """
    m = 2
    while m * m + 1 <= E_limit:
        for n in range(1, m):
            if (m - n) % 2 == 1 and math.gcd(m, n) == 1:
                X0 = m * m - n * n
                Y0 = 2 * m * n
                Z0 = m * m + n * n
                if Z0 > E_limit:
                    continue
                e = 1
                while e * Z0 <= E_limit:
                    A = e * abs(Y0 - X0)
                    J = e * (Y0 + X0)
                    E = e * Z0
                    if A > 0 and A != E and J != E and A != J:
                        yield (A, E, J) if A < J else (J, E, A)
                    e += 1
        m += 1


def count_triples_estimate(E_limit, sample_limit=20000):
    """Estime grossierement le nombre total de triplets par extrapolation (fallback rapide)."""
    n_sample = sum(1 for _ in generate_ap_triples_stream(min(sample_limit, E_limit)))
    if E_limit <= sample_limit:
        return n_sample
    ratio = E_limit / sample_limit
    return int(n_sample * ratio * math.log(max(ratio, math.e)))


def estimate_runtime(E_limit, q_max, workers, sample_size=2000, seed=42):
    """
    Estimation REELLE (pas theorique) du temps d'execution :
    1) compte le nombre exact de triplets (rapide, la generation est en O(E log E))
    2) prend un echantillon aleatoire representatif de triplets
    3) benchmark scan_q_for_triple sur cet echantillon, SUR CETTE MACHINE
    4) extrapole le temps total mono-coeur, puis divise par --workers

    C'est plus fiable qu'une formule theorique car ca s'adapte a la fois a
    la repartition reelle des triplets (les gros A pres de E_limit coutent
    plus cher) et a la vitesse reelle du CPU de l'utilisateur.
    """
    import random
    rng = random.Random(seed)

    print("Comptage exact des triplets (rapide)...")
    t0 = time.time()
    sample = []
    total_count = 0
    for t in generate_ap_triples_stream(E_limit):
        total_count += 1
        if len(sample) < sample_size:
            sample.append(t)
        else:
            j = rng.randint(0, total_count - 1)
            if j < sample_size:
                sample[j] = t
    print(f"  -> {total_count:,} triplets au total ({time.time()-t0:.1f}s)")

    if not sample:
        print("  Aucun triplet trouve dans cette plage.")
        return

    print(f"\nBenchmark sur un echantillon de {len(sample)} triplets, qmax={q_max:,} "
          f"(sur cette machine)...")
    t0 = time.time()
    for (A, E, J) in sample:
        scan_q_for_triple(A, E, J, q_max)
    elapsed = time.time() - t0
    per_triple_ms = (elapsed / len(sample)) * 1000

    total_1core_s = (elapsed / len(sample)) * total_count
    total_parallel_s = total_1core_s / max(workers, 1)

    def fmt_duration(s):
        if s < 60:
            return f"{s:.0f}s"
        if s < 3600:
            return f"{s/60:.1f}min"
        if s < 86400:
            return f"{s/3600:.1f}h"
        return f"{s/86400:.1f}j"

    print(f"  -> {per_triple_ms:.3f} ms/triplet en moyenne")
    print(f"\nProjection pour la recherche complete ({total_count:,} triplets) :")
    print(f"  Temps mono-coeur estime   : {fmt_duration(total_1core_s)}")
    print(f"  Temps estime avec {workers} coeurs : {fmt_duration(total_parallel_s)}")
    print(f"\n(Ceci est une estimation statistique -- le temps reel peut varier de +/- 30%"
          f" selon la distribution effective des triplets traites.)")


def load_triples_from_file(path):
    """Charge des triplets (A,E,J) depuis un fichier CSV/texte (3 colonnes)."""
    with open(path, newline='') as f:
        sniffer_sample = f.read(2048)
        f.seek(0)
        has_header = any(c.isalpha() for c in sniffer_sample.split('\n')[0])
        reader = csv.reader(f)
        if has_header:
            next(reader, None)
        for row in reader:
            if not row:
                continue
            a, e, j = (int(x) for x in row[:3])
            yield (a, e, j)


# ============================================================================
# ETAPE 2 : balayage de q pour un triplet donne (vectorise numpy)
# ============================================================================

def scan_q_for_triple(A, E, J, q_max):
    """
    Pour un triplet fixe (A, E, J) [avec A^2, E^2, J^2 en PA], balaie q dans
    [1, q_max] et retourne les meilleurs q (max de carres parmi les 6
    valeurs derivees : r+q, r-q, r+p+q, r+p-q, r-p+q, r-p-q).
    """
    E2, A2, J2 = E * E, A * A, J * J

    q_max_eff = min(q_max, A2 - 1)
    if q_max_eff < 1:
        return []

    q = np.arange(1, q_max_eff + 1, dtype=np.int64)

    v1 = E2 + q
    v2 = E2 - q
    v3 = J2 + q
    v4 = J2 - q
    v5 = A2 + q
    v6 = A2 - q

    vs = [v1, v2, v3, v4, v5, v6]
    names = ['b(r+q)', 'i(r-q)', 'top(r+p+q)', 'edge(r+p-q)', 'edge(r-p+q)', 'bottom(r-p-q)']

    pos_mask = np.ones_like(q, dtype=bool)
    for v in vs:
        pos_mask &= (v > 0)
    if not pos_mask.any():
        return []

    square_masks = []
    for v in vs:
        vv = np.where(pos_mask, v, 0)
        root = np.sqrt(vv.astype(np.float64)).astype(np.int64)
        exact = np.zeros_like(vv, dtype=bool)
        for delta in (-1, 0, 1):
            r = root + delta
            exact |= (r >= 0) & (r * r == vv)
        square_masks.append(exact & pos_mask)

    count = np.zeros_like(q, dtype=np.int64)
    for mmask in square_masks:
        count += mmask.astype(np.int64)

    if count.size == 0:
        return []
    best_count = int(count.max())
    if best_count == 0:
        return []

    best_idxs = np.nonzero(count == best_count)[0][:5]

    results = []
    for idx in best_idxs:
        q_val = int(q[idx])
        details = {}
        cellvals = [A2, E2, J2]
        for name, v in zip(names, vs):
            val = int(v[idx])
            details[name] = val
            cellvals.append(val)
        if len(set(cellvals)) != 9:
            continue
        results.append((best_count, q_val, details))

    return results


def process_chunk(chunk, q_max, min_total):
    """
    Fonction executee dans chaque processus worker : traite un lot de
    triplets (A,E,J) et renvoie les resultats qui atteignent le seuil.
    """
    out = []
    for (A, E, J) in chunk:
        for count, q_val, details in scan_q_for_triple(A, E, J, q_max):
            total = 3 + count
            if total >= min_total:
                out.append({
                    'total_carres': total,
                    'bonus_carres': count,
                    'A': A, 'E': E, 'J': J, 'q': q_val,
                    **details,
                })
    return len(chunk), out


# ============================================================================
# Deduplication des multiples triviaux (carre entier x k^2)
# ============================================================================

def divisors(n):
    divs = set()
    i = 1
    while i * i <= n:
        if n % i == 0:
            divs.add(i)
            divs.add(n // i)
        i += 1
    return sorted(divs, reverse=True)


def canonical_form(A, E, J, q):
    g = math.gcd(math.gcd(A, E), J)
    for k in divisors(g):
        if k > 1 and q % (k * k) == 0:
            return (A // k, E // k, J // k, q // (k * k)), k
    return (A, E, J, q), 1


def deduplicate_results(all_results):
    canonical_groups = {}
    for r in all_results:
        key, k = canonical_form(r['A'], r['E'], r['J'], r['q'])
        canonical_groups.setdefault(key, []).append((k, r))

    deduped = []
    nb_removed = 0
    for key, group in canonical_groups.items():
        group.sort(key=lambda x: x[0])
        best_k, best_r = group[0]
        if len(group) > 1:
            scales = sorted(k for k, _ in group)
            best_r = dict(best_r)
            best_r['_aussi_trouve_aux_echelles_k'] = ','.join(str(s) for s in scales[1:])
            nb_removed += len(group) - 1
        deduped.append(best_r)
    return deduped, nb_removed


def chunked(iterable, size):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            return
        yield chunk


# ============================================================================
# Programme principal
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--limit', type=int, default=200000,
                         help="Borne max pour E, le centre (defaut: 200000). Ignore si --triples-file est fourni.")
    parser.add_argument('--qmax', type=int, default=200000,
                         help="Borne max pour q, le parametre balaye librement (defaut: 200000)")
    parser.add_argument('--min-total', type=int, default=6,
                         help="Nombre total minimum de carres (sur 9) pour garder un resultat (defaut: 6)")
    parser.add_argument('--out', type=str, default=None,
                         help="Fichier CSV de sortie (ecriture incrementale)")
    parser.add_argument('--top', type=int, default=10,
                         help="Nombre de meilleurs resultats a afficher en detail (defaut: 10)")
    parser.add_argument('--workers', type=int, default=None,
                         help="Nombre de processus paralleles (defaut: tous les coeurs disponibles)")
    parser.add_argument('--chunk-size', type=int, default=200,
                         help="Nombre de triplets par lot envoye a chaque processus (defaut: 200)")
    parser.add_argument('--triples-file', type=str, default=None,
                         help="Fichier CSV/texte (colonnes A,E,J) de triplets deja generes, "
                              "pour eviter de regenerer (utile si vous avez deja explore jusqu'a 10M)")
    parser.add_argument('--estimate-only', action='store_true',
                         help="N'affiche qu'une estimation du nombre de triplets et quitte "
                              "(utile avant de lancer un tres gros run)")
    args = parser.parse_args()

    workers = args.workers or os.cpu_count() or 4

    t0 = time.time()

    if args.triples_file:
        print(f"Chargement des triplets depuis {args.triples_file}...")
        triples_source = load_triples_from_file(args.triples_file)
    else:
        if args.estimate_only:
            estimate_runtime(args.limit, args.qmax, workers)
            return
        print(f"Generation des triplets (A,E,J) avec E <= {args.limit} (methode d'Euclide)...")
        triples_source = generate_ap_triples_stream(args.limit)

    print(f"Balayage de q (jusqu'a {args.qmax}) avec {workers} processus paralleles "
          f"(chunk-size={args.chunk_size})...\n")

    all_results = []
    n_triples_done = 0
    n_chunks_done = 0
    best_so_far = 0

    csv_writer = None
    csv_file = None
    fieldnames_written = None

    def ensure_csv_writer(fieldnames):
        nonlocal csv_writer, csv_file, fieldnames_written
        if csv_writer is None:
            csv_file = open(args.out, 'w', newline='')
            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames, restval='')
            csv_writer.writeheader()
            fieldnames_written = fieldnames

    try:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {}
            chunk_iter = chunked(triples_source, args.chunk_size)

            # on soumet un nombre limite de chunks a l'avance pour ne pas
            # saturer la memoire si la generation est plus rapide que le traitement
            MAX_INFLIGHT = workers * 4

            def submit_more():
                n_submitted = 0
                for chunk in chunk_iter:
                    fut = executor.submit(process_chunk, chunk, args.qmax, args.min_total)
                    futures[fut] = len(chunk)
                    n_submitted += 1
                    if len(futures) >= MAX_INFLIGHT:
                        break
                return n_submitted

            submit_more()

            while futures:
                for fut in list(as_completed(futures)):
                    n_chunk_triples, chunk_results = fut.result()
                    del futures[fut]
                    n_triples_done += n_chunk_triples
                    n_chunks_done += 1

                    if chunk_results:
                        all_results.extend(chunk_results)
                        if args.out:
                            fieldnames = ['total_carres', 'bonus_carres', 'A', 'E', 'J', 'q',
                                          'b(r+q)', 'i(r-q)', 'top(r+p+q)', 'edge(r+p-q)',
                                          'edge(r-p+q)', 'bottom(r-p-q)']
                            ensure_csv_writer(fieldnames)
                            for r in chunk_results:
                                csv_writer.writerow({k: r.get(k, '') for k in fieldnames_written})
                            csv_file.flush()
                        best_so_far = max(best_so_far, max(r['total_carres'] for r in chunk_results))

                    if n_chunks_done % 20 == 0 or best_so_far >= 7:
                        elapsed = time.time() - t0
                        rate = n_triples_done / elapsed if elapsed > 0 else 0
                        print(f"  [{elapsed:7.1f}s] {n_triples_done:>10,} triplets traites  "
                              f"({rate:,.0f}/s)  meilleur total jusqu'ici : {best_so_far}/9")

                    submit_more()
                    break  # on retraite as_completed depuis le debut apres soumission

    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur -- ecriture des resultats deja trouves...")
    finally:
        if csv_file:
            csv_file.close()

    elapsed = time.time() - t0
    print(f"\nTermine (ou interrompu) en {elapsed:.1f}s -- {n_triples_done:,} triplets traites au total.")

    # Deduplication finale des multiples triviaux
    nb_avant = len(all_results)
    all_results, nb_removed = deduplicate_results(all_results)
    if nb_removed:
        print(f"Deduplication : {nb_removed} multiple(s) trivial(aux) retire(s) "
              f"({nb_avant} -> {len(all_results)} resultats distincts).")

    all_results.sort(key=lambda r: -r['total_carres'])

    print(f"\nNombre de configurations distinctes avec total >= {args.min_total} : {len(all_results)}")
    if all_results:
        counts = Counter(r['total_carres'] for r in all_results)
        print(f"Repartition par total de carres (sur 9) : {dict(sorted(counts.items()))}")

        best_total = all_results[0]['total_carres']
        print(f"\nMeilleur total trouve : {best_total}/9")
        if best_total >= 9:
            print("*** SOLUTION COMPLETE POTENTIELLE (9/9) -- VERIFIEZ MANUELLEMENT, CECI SERAIT HISTORIQUE ***")
        elif best_total >= 8:
            print("*** NOUVEAU RECORD POTENTIEL (le record connu est 7/9) -- A VERIFIER SOIGNEUSEMENT ***")
        elif best_total == 7:
            print("Egale le record connu (7/9).")

        print(f"\nDetail des {min(args.top, len(all_results))} meilleurs resultats :\n")
        for r in all_results[:args.top]:
            print(f"  A={r['A']} E={r['E']} J={r['J']}  q={r['q']}  -> total {r['total_carres']}/9")
            if '_aussi_trouve_aux_echelles_k' in r:
                print(f"      (multiples triviaux aussi presents a l'echelle k="
                      f"{r['_aussi_trouve_aux_echelles_k']} -- non affiches)")
            for k, v in r.items():
                if k in ('A', 'E', 'J', 'q', 'total_carres', 'bonus_carres',
                         '_aussi_trouve_aux_echelles_k'):
                    continue
                root = math.isqrt(v)
                tag = f"{root}^2" if root * root == v else f"{v} (non-carre)"
                print(f"      {k:15s} = {tag}")
            print()

        if args.out:
            print(f"Resultats deja ecrits au fur et a mesure dans : {args.out}")
    else:
        print("\nAucun resultat au-dessus du seuil. Essayez d'augmenter --limit et/ou --qmax, "
              "ou diminuez --min-total.")


if __name__ == "__main__":
    main()
