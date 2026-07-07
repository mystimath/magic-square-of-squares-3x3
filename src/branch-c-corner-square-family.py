#!/usr/bin/env python3
"""
Recherche de carres magiques 3x3 "presque parfaits" (magic squares of squares).

RAPPEL DU PROBLEME
------------------
On cherche un carre magique 3x3 dont les 9 cases sont des carres d'entiers
distincts. C'est un probleme ouvert : le meilleur resultat connu (Andrew
Bremner, 2005) contient 7 carres sur 9.

PARAMETRAGE UTILISE
--------------------
Carre :
    a b c
    d e f
    h i j

La constante magique d'un carre 3x3 vaut toujours 3*e (e = centre).
Les deux diagonales donnent :
    j = 2e - a        (diagonale a, e, j)
    h = 2e - c        (anti-diagonale c, e, h)

Les 4 cases restantes se deduisent de a, c, e :
    b = 3e - a - c   = (h + j) - e
    d = e + c - a    = (c + j) - e
    f = e + a - c    = (a + h) - e
    i = a + c - e

==> a, c, e sont les 3 seuls degres de liberte reels.

CONTRAINTE ACTUELLE (etape 1, stricte)
---------------------------------------
On impose que a, c, e, h, j soient TOUS des carres parfaits, c'est a dire :
    a = A^2, c = C^2, e = E^2
    j = 2E^2 - A^2 doit etre un carre parfait J^2   -> (A, E, J) en PA de carres
    h = 2E^2 - C^2 doit etre un carre parfait H^2   -> (C, E, H) en PA de carres

Cela fixe deja 5 des 9 cases comme carres. On compte ensuite combien, parmi
b, d, f, i, sont EUX AUSSI des carres parfaits (objectif : 3 ou 4, pour battre
ou egaler le record de 7/9).

USAGE
-----
    python magic_square_of_squares.py --limit 20000
    python magic_square_of_squares.py --limit 200000 --min-count 1 --out resultats.csv

Le parametre --limit borne la racine du centre E (E va de 2 a limit).
Attention : le cout de la recherche des progressions arithmetiques croit
en O(limit^2). Comptez large mais raisonnable (qq dizaines de milliers pour
commencer, selon la puissance de votre machine).
"""

import argparse
import csv
import math
import time
from collections import Counter


def find_ap_pairs(E_limit, progress_every=2000):
    """
    Pour chaque E de 2 a E_limit, cherche tous les A < E tels que
    2*E^2 - A^2 soit un carre parfait J^2 (avec J != A).

    Retourne un dict : E -> liste de tuples (A, J) tries, dedupliques.

    Utilise numpy si disponible (beaucoup plus rapide), avec une
    verification finale en entiers exacts (math.isqrt) pour eviter
    tout probleme d'arrondi flottant.
    """
    try:
        import numpy as np
        use_numpy = True
    except ImportError:
        use_numpy = False

    result = {}
    t0 = time.time()

    for E in range(2, E_limit + 1):
        E2 = E * E

        if use_numpy:
            A = np.arange(1, E, dtype=np.int64)
            diff = 2 * E2 - A * A
            mask = diff > 0
            A = A[mask]
            diff = diff[mask]
            if len(A) == 0:
                continue
            J_approx = np.sqrt(diff.astype(np.float64)).astype(np.int64)
            candidates = set()
            for delta in (-1, 0, 1, 2):
                Jc = J_approx + delta
                good = (Jc > 0)
                for idx in np.nonzero(good)[0]:
                    candidates.add((int(A[idx]), int(Jc[idx])))
        else:
            candidates = set()
            for a_val in range(1, E):
                diff = 2 * E2 - a_val * a_val
                if diff <= 0:
                    continue
                j_val = math.isqrt(diff)
                candidates.add((a_val, j_val))
                candidates.add((a_val, j_val + 1))

        # verification exacte (entiers, pas de flottants) + A != J
        verified = []
        for A_val, J_val in candidates:
            if J_val <= 0 or A_val == J_val:
                continue
            if 2 * E2 - A_val * A_val == J_val * J_val:
                verified.append((A_val, J_val))

        if verified:
            result[E] = sorted(set(verified))

        if progress_every and E % progress_every == 0:
            elapsed = time.time() - t0
            print(f"  ... E={E}/{E_limit}  ({elapsed:.1f}s ecoulees)")

    return result


def is_square(n):
    if n < 0:
        return False
    r = math.isqrt(n)
    return r * r == n


def search(E_limit, min_count=1, progress_every=2000):
    print(f"Etape 1 : recherche des progressions arithmetiques de carres (E <= {E_limit})...")
    ap = find_ap_pairs(E_limit, progress_every=progress_every)
    total_pairs = sum(len(v) for v in ap.values())
    print(f"  -> {total_pairs} paires (A, J) trouvees, reparties sur {len(ap)} valeurs de E.\n")

    print("Etape 2 : combinaison des paires partageant le meme centre E, "
          "verification des 4 cases derivees (b, d, f, i)...")

    results = []
    for E, lst in ap.items():
        E2 = E * E
        n = len(lst)
        if n < 2:
            continue
        for idx1 in range(n):
            A, J = lst[idx1]
            for idx2 in range(idx1 + 1, n):
                C, H = lst[idx2]
                if A == C:
                    continue

                a2, c2 = A * A, C * C

                b_val = 3 * E2 - a2 - c2
                d_val = E2 + c2 - a2
                f_val = E2 + a2 - c2
                i_val = a2 + c2 - E2

                # toutes les cases doivent etre des entiers strictement positifs
                if min(b_val, d_val, f_val, i_val) <= 0:
                    continue

                # les 9 valeurs du carre doivent etre distinctes
                cellvals = [a2, c2, E2, H * H, J * J, b_val, d_val, f_val, i_val]
                if len(set(cellvals)) != 9:
                    continue

                derived = {'b': b_val, 'd': d_val, 'f': f_val, 'i': i_val}
                count = sum(1 for v in derived.values() if is_square(v))

                if count >= min_count:
                    results.append({
                        'count_bonus_carres': count,
                        'E': E, 'A': A, 'C': C, 'J': J, 'H': H,
                        'a': a2, 'c': c2, 'e': E2, 'h': H * H, 'j': J * J,
                        'b': b_val, 'd': d_val, 'f': f_val, 'i': i_val,
                    })

    results.sort(key=lambda r: -r['count_bonus_carres'])
    return results


def print_square(r):
    """Affiche le carre 3x3 complet pour un resultat donne."""
    a, b, c = r['a'], r['b'], r['c']
    d, e, f = r['d'], r['e'], r['f']
    h, i, j = r['h'], r['i'], r['j']

    def fmt(v):
        root = math.isqrt(v)
        if root * root == v:
            return f"{root}^2"
        return str(v)

    print(f"    {fmt(a):>12} {fmt(b):>12} {fmt(c):>12}")
    print(f"    {fmt(d):>12} {fmt(e):>12} {fmt(f):>12}")
    print(f"    {fmt(h):>12} {fmt(i):>12} {fmt(j):>12}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--limit', type=int, default=20000,
                         help="Borne max pour la racine du centre E (defaut: 20000)")
    parser.add_argument('--min-count', type=int, default=1,
                         help="Nombre minimum de carres bonus parmi b,d,f,i pour garder un resultat (defaut: 1)")
    parser.add_argument('--out', type=str, default=None,
                         help="Fichier CSV de sortie (optionnel)")
    parser.add_argument('--top', type=int, default=15,
                         help="Nombre de meilleurs resultats a afficher en detail (defaut: 15)")
    parser.add_argument('--progress-every', type=int, default=2000,
                         help="Frequence d'affichage de la progression (defaut: 2000)")
    args = parser.parse_args()

    t0 = time.time()
    results = search(args.limit, min_count=args.min_count, progress_every=args.progress_every)
    elapsed = time.time() - t0

    print(f"\nTemps total : {elapsed:.1f}s")
    print(f"Nombre de configurations valides trouvees : {len(results)}")

    counts = Counter(r['count_bonus_carres'] for r in results)
    print(f"Repartition par nombre de carres bonus (b,d,f,i) : {dict(sorted(counts.items()))}")

    if results:
        best = results[0]['count_bonus_carres']
        total_squares = 5 + best
        print(f"\nMeilleur resultat : {best} carre(s) bonus => {total_squares} carres sur 9 au total.")
        if total_squares >= 8:
            print("*** NOUVEAU RECORD POTENTIEL (le record connu est 7/9) - A VERIFIER SOIGNEUSEMENT ***")
        elif total_squares == 7:
            print("Egale le record connu (7/9) - a comparer avec la solution de Bremner.")

        print(f"\nDetail des {min(args.top, len(results))} meilleures configurations :\n")
        for r in results[:args.top]:
            print(f"  E={r['E']} A={r['A']} C={r['C']} J={r['J']} H={r['H']}  "
                  f"-> {r['count_bonus_carres']} carre(s) bonus parmi b,d,f,i")
            print_square(r)
            print()
    else:
        print("\nAucune configuration trouvee dans cette plage. Essayez d'augmenter --limit.")

    if args.out and results:
        fieldnames = ['count_bonus_carres', 'E', 'A', 'C', 'J', 'H',
                      'a', 'b', 'c', 'd', 'e', 'f', 'h', 'i', 'j']
        with open(args.out, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        print(f"\nResultats complets exportes vers : {args.out}")


if __name__ == "__main__":
    main()