#!/usr/bin/env python3
"""
Recherche PARALLELISEE et CRIBLEE de carres magiques 3x3
"presque parfaits" (magic squares of squares).

Version amelioree :
  1) generation streaming des triplets (A,E,J) via triplets pythagoriciens ;
  2) borne de rejet immediate selon qmax (gap bound) ;
  3) crible modulaire par triplet (petits modules) ;
  4) generation SPARSE des seuls q compatibles avec au moins une case carree ;
  5) filtrage modulaire des q ;
  6) verification exacte sans balayage dense sur [1..qmax].

Le script explore la famille standard :
    A^2, E^2, J^2 en progression arithmetique, donc A^2 + J^2 = 2 E^2,
avec les six autres cases donnees par :
    E^2+q, E^2-q, J^2+q, J^2-q, A^2+q, A^2-q.

Par defaut, tous les cribles actives sont NECESSAIRES (pas de faux negatifs)
pour le modele de recherche retenu. Le mode --strict-24 est experimental et
plus agressif : il peut accelerer une recherche de type 8/9-9/9 primitive,
mais n'est pas garanti sans faux negatifs pour des quasi-solutions exotiques.
"""

import argparse
import csv
import math
import os
import random
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import islice

# ---------------------------------------------------------------------------
# Globals workers
# ---------------------------------------------------------------------------

WORKER_CONFIG = None
CELL_NAMES = [
    'b(r+q)',
    'i(r-q)',
    'top(r+p+q)',
    'edge(r+p-q)',
    'edge(r-p+q)',
    'bottom(r-p-q)',
]

BIT_E_PLUS   = 1 << 0
BIT_E_MINUS  = 1 << 1
BIT_J_PLUS   = 1 << 2
BIT_J_MINUS  = 1 << 3
BIT_A_PLUS   = 1 << 4
BIT_A_MINUS  = 1 << 5
ALL_6_MASK   = (1 << 6) - 1


# ---------------------------------------------------------------------------
# Generation des triplets (A,E,J)
# ---------------------------------------------------------------------------


def generate_ap_triples_stream(E_limit):
    """
    Genere tous les triplets (A,E,J) avec 2*E^2 = A^2 + J^2, A<E<J possibles,
    par la parametrisation pythagoricienne.
    """
    m = 2
    while m * m + 1 <= E_limit:
        for n in range(1, m):
            if ((m - n) & 1) == 1 and math.gcd(m, n) == 1:
                x0 = m * m - n * n
                y0 = 2 * m * n
                z0 = m * m + n * n
                if z0 > E_limit:
                    continue
                e = 1
                while e * z0 <= E_limit:
                    a = e * abs(y0 - x0)
                    j = e * (y0 + x0)
                    E = e * z0
                    if a > 0 and a != E and j != E and a != j:
                        yield (a, E, j) if a < j else (j, E, a)
                    e += 1
        m += 1


def load_triples_from_file(path):
    with open(path, newline='') as f:
        sample = f.read(2048)
        f.seek(0)
        has_header = any(c.isalpha() for c in sample.split('\n')[0])
        reader = csv.reader(f)
        if has_header:
            next(reader, None)
        for row in reader:
            if not row:
                continue
            a, e, j = (int(x) for x in row[:3])
            if a <= 0 or e <= 0 or j <= 0:
                continue
            yield (a, e, j)


# ---------------------------------------------------------------------------
# Outils divers
# ---------------------------------------------------------------------------


def popcount(x):
    return x.bit_count()


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
        kk = k * k
        if k > 1 and q % kk == 0:
            return (A // k, E // k, J // k, q // kk), k
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


def fmt_duration(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}min"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}j"


# ---------------------------------------------------------------------------
# Crible modulaire
# ---------------------------------------------------------------------------


def quadratic_residues_mod(m, strict_24=False):
    if strict_24 and m == 24:
        return {1}
    return { (x * x) % m for x in range(m) }


def build_module_table(m, min_bonus, strict_24=False):
    """
    Pour chaque paire (a2 mod m, e2 mod m), precompute :
      - best_score_mod : max possible du nombre de cases carrees modulo m
      - mask_k : residues q mod m pour lesquels score_mod >= k
    On deduit j2 mod m = 2 e2 - a2.
    """
    qr = quadratic_residues_mod(m, strict_24=strict_24)

    plus_mask = [0] * m
    minus_mask = [0] * m
    for s in range(m):
        pm = 0
        mm = 0
        for r in range(m):
            if (s + r) % m in qr:
                pm |= (1 << r)
            if (s - r) % m in qr:
                mm |= (1 << r)
        plus_mask[s] = pm
        minus_mask[s] = mm

    table = [[None] * m for _ in range(m)]
    for a2 in range(m):
        for e2 in range(m):
            j2 = (2 * e2 - a2) % m
            counts = [0] * m
            pe, me = plus_mask[e2], minus_mask[e2]
            pj, mj = plus_mask[j2], minus_mask[j2]
            pa, ma = plus_mask[a2], minus_mask[a2]
            for r in range(m):
                counts[r] = (
                    ((pe >> r) & 1) + ((me >> r) & 1) +
                    ((pj >> r) & 1) + ((mj >> r) & 1) +
                    ((pa >> r) & 1) + ((ma >> r) & 1)
                )
            best = max(counts)
            masks = [0] * 7
            for k in range(7):
                mask = 0
                for r, c in enumerate(counts):
                    if c >= k:
                        mask |= (1 << r)
                masks[k] = mask
            table[a2][e2] = (best, tuple(masks))

    return {
        'm': m,
        'min_bonus': min_bonus,
        'table': table,
    }


def parse_moduli(spec):
    if not spec.strip():
        return []
    out = []
    for part in spec.split(','):
        part = part.strip()
        if part:
            out.append(int(part))
    return out


def build_config(args):
    min_bonus = args.min_total - 3
    moduli = parse_moduli(args.moduli)
    if args.strict_24 and 24 not in moduli:
        moduli.append(24)
    moduli = list(dict.fromkeys(moduli))

    modules = [build_module_table(m, min_bonus, strict_24=args.strict_24) for m in moduli]
    return {
        'qmax': args.qmax,
        'min_total': args.min_total,
        'min_bonus': min_bonus,
        'strict_24': args.strict_24,
        'modules': modules,
    }


def modular_triplet_filter(A, E, J, config):
    """
    Retourne (ok, residue_filters).
    residue_filters = liste de tuples (m, allowed_mask) a appliquer ensuite sur q.
    """
    min_bonus = config['min_bonus']
    residue_filters = []
    for mod in config['modules']:
        m = mod['m']
        a2 = (A * A) % m
        e2 = (E * E) % m
        best, masks = mod['table'][a2][e2]
        if best < min_bonus:
            return False, None
        residue_filters.append((m, masks[min_bonus]))
    return True, residue_filters


# ---------------------------------------------------------------------------
# Borne de rejet qmax (gap bound)
# ---------------------------------------------------------------------------


def root_square_contribution_upper_bound(n, qmax_eff):
    """
    Nombre maximal de cases parmi n^2 +/- q qui PEUVENT etre carrees pour un q<=qmax_eff.
    Borne necessaire ultra-rapide.
    """
    if qmax_eff < 2 * n - 1:
        return 0
    return 2


def triplet_upper_bound_total(A, E, J, qmax):
    qmax_eff = min(qmax, A * A - 1)
    if qmax_eff < 1:
        return 3, qmax_eff
    bonus = (
        root_square_contribution_upper_bound(A, qmax_eff) +
        root_square_contribution_upper_bound(E, qmax_eff) +
        root_square_contribution_upper_bound(J, qmax_eff)
    )
    return 3 + bonus, qmax_eff


# ---------------------------------------------------------------------------
# Generation SPARSE des q candidats
# ---------------------------------------------------------------------------


def q_passes_residue_filters(q, residue_filters):
    for m, allowed_mask in residue_filters:
        if ((allowed_mask >> (q % m)) & 1) == 0:
            return False
    return True


def add_q_family(candidate_bits, n, qmax_eff, bit_plus, bit_minus, residue_filters):
    # n^2 + q = (n+t)^2  <=> q = t(2n+t)
    t = 1
    while True:
        q = t * (2 * n + t)
        if q > qmax_eff:
            break
        if q_passes_residue_filters(q, residue_filters):
            candidate_bits[q] = candidate_bits.get(q, 0) | bit_plus
        t += 1

    # n^2 - q = (n-t)^2  <=> q = t(2n-t), 1 <= t < n
    t = 1
    while t < n:
        q = t * (2 * n - t)
        if q > qmax_eff:
            break
        if q_passes_residue_filters(q, residue_filters):
            candidate_bits[q] = candidate_bits.get(q, 0) | bit_minus
        t += 1


def exact_results_for_triple(A, E, J, config):
    """
    Retourne les meilleurs q (jusqu'a 5) pour un triplet donne, apres :
      - borne qmax
      - crible modulaire par triplet
      - generation sparse des q
      - verification exacte du nombre de cases carrees et de la distinctivite.
    """
    min_total = config['min_total']
    min_bonus = config['min_bonus']
    qmax = config['qmax']

    total_upper, qmax_eff = triplet_upper_bound_total(A, E, J, qmax)
    if total_upper < min_total or qmax_eff < 1:
        return [], 'gap'

    ok, residue_filters = modular_triplet_filter(A, E, J, config)
    if not ok:
        return [], 'mod'

    candidate_bits = {}
    add_q_family(candidate_bits, E, qmax_eff, BIT_E_PLUS, BIT_E_MINUS, residue_filters)
    add_q_family(candidate_bits, J, qmax_eff, BIT_J_PLUS, BIT_J_MINUS, residue_filters)
    add_q_family(candidate_bits, A, qmax_eff, BIT_A_PLUS, BIT_A_MINUS, residue_filters)

    if not candidate_bits:
        return [], 'sparse_empty'

    A2, E2, J2 = A * A, E * E, J * J

    results = []
    best_bonus = -1
    for q, mask in candidate_bits.items():
        bonus = popcount(mask)
        if bonus < min_bonus:
            continue

        v = [E2 + q, E2 - q, J2 + q, J2 - q, A2 + q, A2 - q]
        if any(x <= 0 for x in v):
            continue
        cellvals = [A2, E2, J2] + v
        if len(set(cellvals)) != 9:
            continue

        total = 3 + bonus
        if total < min_total:
            continue

        if bonus > best_bonus:
            results.clear()
            best_bonus = bonus
        if bonus == best_bonus and len(results) < 5:
            details = {name: val for name, val in zip(CELL_NAMES, v)}
            results.append((bonus, q, details, mask))

    return results, 'ok'


# ---------------------------------------------------------------------------
# Worker multiprocessing
# ---------------------------------------------------------------------------


def init_worker(config):
    global WORKER_CONFIG
    WORKER_CONFIG = config


def process_chunk(chunk):
    config = WORKER_CONFIG
    out = []
    stats = Counter()
    stats['triplets_seen'] = len(chunk)

    for (A, E, J) in chunk:
        results, reason = exact_results_for_triple(A, E, J, config)
        stats[f'reject_{reason}'] += 1 if not results else 0
        if not results:
            continue
        stats['triplets_with_results'] += 1
        for bonus, q_val, details, mask in results:
            total = 3 + bonus
            out.append({
                'total_carres': total,
                'bonus_carres': bonus,
                'A': A,
                'E': E,
                'J': J,
                'q': q_val,
                'square_mask': format(mask, '06b'),
                **details,
            })
    return len(chunk), out, dict(stats)


# ---------------------------------------------------------------------------
# Benchmark / estimation
# ---------------------------------------------------------------------------


def estimate_runtime(E_limit, workers, config, sample_size=3000, seed=42):
    rng = random.Random(seed)
    print('Comptage exact des triplets (rapide)...')
    t0 = time.time()
    total_count = 0
    sample = []
    for t in generate_ap_triples_stream(E_limit):
        total_count += 1
        if len(sample) < sample_size:
            sample.append(t)
        else:
            j = rng.randint(0, total_count - 1)
            if j < sample_size:
                sample[j] = t
    print(f'  -> {total_count:,} triplets au total ({time.time() - t0:.1f}s)')

    if not sample:
        print('  Aucun triplet dans cette plage.')
        return

    global WORKER_CONFIG
    WORKER_CONFIG = config

    print(f'Benchmark exact sur {len(sample)} triplets echantillons...')
    t0 = time.time()
    total_hits = 0
    reject_stats = Counter()
    for A, E, J in sample:
        results, reason = exact_results_for_triple(A, E, J, config)
        if results:
            total_hits += 1
        else:
            reject_stats[reason] += 1
    elapsed = time.time() - t0
    per_triplet_ms = elapsed / len(sample) * 1000
    total_1core_s = elapsed / len(sample) * total_count
    total_parallel_s = total_1core_s / max(workers, 1)

    print(f'  -> {per_triplet_ms:.4f} ms/triplet sur l\'echantillon')
    print(f'  -> Survivants echantillon : {total_hits}/{len(sample)}')
    if reject_stats:
        print(f'  -> Rejets echantillon     : {dict(reject_stats)}')
    print(f'Projection mono-coeur       : {fmt_duration(total_1core_s)}')
    print(f'Projection avec {workers} coeurs : {fmt_duration(total_parallel_s)}')
    print('(Estimation statistique ; le temps reel dependra de la distribution des triplets.)')


# ---------------------------------------------------------------------------
# Programme principal
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--limit', type=int, default=200000,
                        help='Borne max pour E (ignoree si --triples-file est fourni).')
    parser.add_argument('--triples-file', type=str, default=None,
                        help='Fichier CSV/texte contenant des triplets A,E,J deja generes.')
    parser.add_argument('--qmax', type=int, default=200000,
                        help='Borne max pour q.')
    parser.add_argument('--min-total', type=int, default=6,
                        help='Nombre total minimum de carres sur 9 pour conserver un resultat.')
    parser.add_argument('--workers', type=int, default=None,
                        help='Nombre de processus paralleles (defaut: tous les coeurs).')
    parser.add_argument('--chunk-size', type=int, default=1000,
                        help='Nombre de triplets par lot. Avec le crible, 500-5000 est souvent bon.')
    parser.add_argument('--top', type=int, default=10,
                        help='Nombre de meilleurs resultats affiches en fin de run.')
    parser.add_argument('--out', type=str, default=None,
                        help='CSV de sortie (ecriture incrementale).')
    parser.add_argument('--estimate-only', action='store_true',
                        help='Fait un comptage exact + benchmark sur echantillon, puis quitte.')
    parser.add_argument('--moduli', type=str, default='16,5,7,11',
                        help='Modules du crible modulaire, separes par des virgules.')
    parser.add_argument('--strict-24', action='store_true',
                        help='Ajoute un filtre experimental mod 24 plus agressif (mode 1 mod 24).')
    args = parser.parse_args()

    if not (4 <= args.min_total <= 9):
        parser.error('--min-total doit etre entre 4 et 9.')
    if args.qmax < 1:
        parser.error('--qmax doit etre >= 1.')
    if args.chunk_size < 1:
        parser.error('--chunk-size doit etre >= 1.')

    workers = args.workers or os.cpu_count() or 4
    config = build_config(args)

    print('Crible modulaire actif sur les modules :', ', '.join(str(m['m']) for m in config['modules']) or '(aucun)')
    print(f'Seuil de conservation : {args.min_total}/9 (donc {config["min_bonus"]} carres parmi les 6 cases derivees)')
    if args.strict_24:
        print('Mode strict-24 ACTIF : filtre plus agressif, experimental.')

    if args.estimate_only:
        if args.triples_file:
            print('--estimate-only n\'est actuellement supporte que pour --limit, pas pour --triples-file.')
            return
        estimate_runtime(args.limit, workers, config)
        return

    if args.triples_file:
        print(f'Chargement des triplets depuis {args.triples_file}...')
        triples_source = load_triples_from_file(args.triples_file)
    else:
        print(f'Generation des triplets (A,E,J) avec E <= {args.limit}...')
        triples_source = generate_ap_triples_stream(args.limit)

    t0 = time.time()
    all_results = []
    n_triples_done = 0
    n_chunks_done = 0
    best_so_far = 0
    global_stats = Counter()

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
        with ProcessPoolExecutor(max_workers=workers, initializer=init_worker, initargs=(config,)) as executor:
            futures = {}
            chunk_iter = chunked(triples_source, args.chunk_size)
            max_inflight = workers * 4

            def submit_more():
                submitted = 0
                for chunk in chunk_iter:
                    fut = executor.submit(process_chunk, chunk)
                    futures[fut] = len(chunk)
                    submitted += 1
                    if len(futures) >= max_inflight:
                        break
                return submitted

            submit_more()

            while futures:
                for fut in list(as_completed(futures)):
                    n_chunk_triples, chunk_results, chunk_stats = fut.result()
                    del futures[fut]
                    n_triples_done += n_chunk_triples
                    n_chunks_done += 1
                    global_stats.update(chunk_stats)

                    if chunk_results:
                        all_results.extend(chunk_results)
                        if args.out:
                            fieldnames = ['total_carres', 'bonus_carres', 'A', 'E', 'J', 'q', 'square_mask'] + CELL_NAMES
                            ensure_csv_writer(fieldnames)
                            for r in chunk_results:
                                csv_writer.writerow({k: r.get(k, '') for k in fieldnames_written})
                            csv_file.flush()
                        best_so_far = max(best_so_far, max(r['total_carres'] for r in chunk_results))

                    if n_chunks_done % 20 == 0 or best_so_far >= 7:
                        elapsed = time.time() - t0
                        rate = n_triples_done / elapsed if elapsed > 0 else 0
                        print(f'  [{elapsed:7.1f}s] {n_triples_done:>12,} triplets traites  ({rate:,.0f}/s)  meilleur total : {best_so_far}/9')

                    submit_more()
                    break

    except KeyboardInterrupt:
        print('\n\nInterrompu par l\'utilisateur -- ecriture des resultats deja trouves...')
    finally:
        if csv_file:
            csv_file.close()

    elapsed = time.time() - t0
    print(f'\nTermine en {elapsed:.1f}s -- {n_triples_done:,} triplets traites.')

    nb_avant = len(all_results)
    all_results, nb_removed = deduplicate_results(all_results)
    if nb_removed:
        print(f'Deduplication : {nb_removed} multiple(s) trivial(aux) retire(s) ({nb_avant} -> {len(all_results)}).')

    all_results.sort(key=lambda r: (-r['total_carres'], -r['bonus_carres'], r['A'], r['E'], r['J'], r['q']))

    print('\nStatistiques de rejet / survie :')
    if global_stats:
        keys = sorted(global_stats)
        for k in keys:
            print(f'  {k:22s} : {global_stats[k]:,}')

    print(f'\nNombre de configurations distinctes avec total >= {args.min_total} : {len(all_results)}')
    if all_results:
        counts = Counter(r['total_carres'] for r in all_results)
        print(f'Repartition par total de carres (sur 9) : {dict(sorted(counts.items()))}')
        best_total = all_results[0]['total_carres']
        print(f'\nMeilleur total trouve : {best_total}/9')
        if best_total >= 9:
            print('*** SOLUTION COMPLETE POTENTIELLE (9/9) -- VERIFICATION MANUELLE IMPERATIVE ***')
        elif best_total >= 8:
            print('*** NOUVEAU RECORD POTENTIEL (>=8/9) -- VERIFICATION MANUELLE IMPERATIVE ***')
        elif best_total == 7:
            print('Egale le record connu (7/9).')

        print(f'\nDetail des {min(args.top, len(all_results))} meilleurs resultats :\n')
        for r in all_results[:args.top]:
            print(f"  A={r['A']} E={r['E']} J={r['J']}  q={r['q']}  -> total {r['total_carres']}/9  mask={r['square_mask']}")
            if '_aussi_trouve_aux_echelles_k' in r:
                print(f"      (multiples triviaux aussi presents a l'echelle k={r['_aussi_trouve_aux_echelles_k']} -- non affiches)")
            for name in CELL_NAMES:
                v = r[name]
                root = math.isqrt(v)
                tag = f'{root}^2' if root * root == v else f'{v} (non-carre)'
                print(f'      {name:15s} = {tag}')
            print()

        if args.out:
            print(f'Resultats deja ecrits au fur et a mesure dans : {args.out}')
    else:
        print('\nAucun resultat au-dessus du seuil. Essayez d\'augmenter --limit et/ou --qmax, ou de diminuer --min-total.')


if __name__ == '__main__':
    main()
