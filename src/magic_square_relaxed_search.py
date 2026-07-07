#!/usr/bin/env python3
"""
Recherche RELACHEE de carres magiques 3x3 "presque parfaits" (magic squares
of squares) -- version optimisee visant a depasser le record connu (7/9,
Andrew Bremner 2005), voire a trouver une solution complete a 9/9 (probleme
ouvert).

RAPPEL DU PARAMETRAGE GENERAL (equivalent a Lucas)
----------------------------------------------------
Tout carre magique 3x3 d'entiers distincts s'ecrit, pour un centre r et deux
parametres p, q :

    r+p       r-p-q      r+q
    r-p+q      r         r+p-q
    r-q       r+p+q      r-p

(La constante magique vaut 3r. Vous pouvez retrouver ce schema a partir de
votre propre parametrage a,b,c,d,e,f,h,i,j -- c'est le meme objet, ecrit
autrement.)

STRATEGIE DE CETTE VERSION (contrainte relachee)
--------------------------------------------------
Etape 1 (comme avant, mais on ne fixe plus qu'UNE SEULE diagonale) :
    r = E^2
    On cherche p tel que r-p = A^2 et r+p = J^2 soient tous deux des carres,
    i.e. (A, E, J) est une progression arithmetique de carres : 2E^2 = A^2+J^2.
    => 3 carres garantis : A^2, E^2, J^2.

Etape 2 (la partie relachee / optimisee) :
    Pour chaque triplet (A, E, J) valide, on NE FIXE PLUS q a l'avance.
    On balaie une large plage de q (vectorise avec numpy) et on verifie,
    pour chaque q, combien des 6 valeurs suivantes sont des carres parfaits :

        r+q,  r-q,  r+p+q (= J^2+q),  r+p-q (= J^2-q),
        r-p+q (= A^2+q),  r-p-q (= A^2-q)

    On ne force plus rien sur ces 6 valeurs : elles peuvent tomber sur des
    carres "par chance algebrique". Comme on n'a fixe que 3 carres au lieu
    de 5 (version precedente), il reste beaucoup plus de marge de manoeuvre
    pour que 4, 5 ou (ideal) 6 des valeurs restantes soient aussi carrees.

    Total de carres dans le carre magique = 3 (fixes) + (nb trouve parmi les 6).
    Objectif : >= 8 (nouveau record) ou 9 (solution complete, Graal).

IMPORTANT- HONNETETE SCIENTIFIQUE
-------------------------- ----------
Ce script est un OUTIL DE RECHERCHE HEURISTIQUE, pas une preuve. Le record
de Bremner (7/9) a probablement ete trouve via des techniques de courbes
elliptiques bien plus sophistiquees qu'un simple balayage. Ce script peut
neanmoins :
  - retrouver ou approcher des configurations connues,
  - potentiellement decouvrir de nouvelles configurations a 7 ou 8 carres
    si on balaie suffisamment large,
  - servir de base pour restreindre ensuite la recherche autour des
    meilleurs candidats trouves.

USAGE
-----
    python magic_square_relaxed_search.py --limit 5000 --qmax 200000
    python magic_square_relaxed_search.py --limit 20000 --qmax 500000 --min-total 7 --out best.csv

    --limit    : borne max pour E (centre), meme role que dans le script precedent
    --qmax      : borne max pour q (le parametre balaye librement)
    --min-total : nombre total minimum de carres (sur 9) pour qu'un resultat soit garde/affiche
    --out      : fichier CSV optionnel pour exporter TOUS les resultats >= min-total
"""

import argparse
import csv
import math
import time
from collections import Counter

try:
    import numpy as np
except ImportError:
    raise SystemExit("Ce script necessite numpy. Installez-le avec : pip install numpy")


def find_ap_triples(E_limit, progress_every=2000):
    """
    Retourne la liste de tous les triplets (A, E, J) avec 2 <= E <= E_limit,
    1 <= A < E, tels que 2*E^2 - A^2 = J^2 (progression arithmetique de carres).
    """
    triples = []
    t0 = time.time()
    for E in range(2, E_limit + 1):
        E2 = E * E
        A = np.arange(1, E, dtype=np.int64)
        diff = 2 * E2 - A * A
        mask = diff > 0
        A = A[mask]
        diff = diff[mask]
        if len(A) == 0:
            continue
        J_approx = np.sqrt(diff.astype(np.float64)).astype(np.int64)
        for delta in (-1, 0, 1, 2):
            Jc = J_approx + delta
            good = (Jc > 0) & (Jc * Jc == diff) & (Jc != A)
            for idx in np.nonzero(good)[0]:
                a_val, j_val = int(A[idx]), int(Jc[idx])
                triples.append((a_val, E, j_val))
        if progress_every and E % progress_every == 0:
            print(f"  [etape 1] E={E}/{E_limit}  ({time.time()-t0:.1f}s)")
    # dedupe
    return sorted(set(triples))


def scan_q_for_triple(A, E, J, q_max):
    """
    Pour un triplet fixe (A, E, J), balaie q dans [1, q_max] (vectorise numpy)
    et retourne le(s) meilleur(s) q avec le plus grand nombre de carres parmi
    les 6 valeurs derivees.

    Retourne une liste de tuples (count, q, details_dict) pour les meilleurs q
    (uniquement ceux qui atteignent le maximum trouve pour ce triplet).
    """
    E2, A2, J2 = E * E, A * A, J * J

    q_max_eff = min(q_max, A2 - 1)  # r-p-q = A^2-q doit rester > 0
    if q_max_eff < 1:
        return []

    q = np.arange(1, q_max_eff + 1, dtype=np.int64)

    v1 = E2 + q          # r+q
    v2 = E2 - q          # r-q
    v3 = J2 + q          # r+p+q
    v4 = J2 - q          # r+p-q
    v5 = A2 + q          # r-p+q
    v6 = A2 - q          # r-p-q

    vs = [v1, v2, v3, v4, v5, v6]
    names = ['b(r+q)', 'i(r-q)', 'top(r+p+q)', 'edge(r+p-q)', 'edge(r-p+q)', 'bottom(r-p-q)']

    # positivite : toutes les valeurs doivent rester > 0
    pos_mask = np.ones_like(q, dtype=bool)
    for v in vs:
        pos_mask &= (v > 0)

    if not pos_mask.any():
        return []

    # verification carre parfait, vectorisee, avec verification exacte
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
    for m in square_masks:
        count += m.astype(np.int64)

    if count.size == 0:
        return []

    best_count = int(count.max())
    if best_count == 0:
        return []

    best_idxs = np.nonzero(count == best_count)[0]
    # on limite le nombre de q retournes par triplet pour ne pas exploser la memoire
    best_idxs = best_idxs[:5]

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


def is_square(n):
    if n < 0:
        return False
    r = math.isqrt(n)
    return r * r == n


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--limit', type=int, default=5000,
                         help="Borne max pour E, le centre (defaut: 5000)")
    parser.add_argument('--qmax', type=int, default=200000,
                         help="Borne max pour q, le parametre balaye librement (defaut: 200000)")
    parser.add_argument('--min-total', type=int, default=6,
                         help="Nombre total minimum de carres (sur 9) pour garder un resultat (defaut: 6)")
    parser.add_argument('--out', type=str, default=None,
                         help="Fichier CSV optionnel pour export complet")
    parser.add_argument('--top', type=int, default=10,
                         help="Nombre de meilleurs resultats a afficher en detail (defaut: 10)")
    parser.add_argument('--progress-every', type=int, default=2000,
                         help="Frequence d'affichage de la progression pour l'etape 1 (defaut: 2000)")
    args = parser.parse_args()

    t0 = time.time()
    print(f"Etape 1 : recherche des triplets (A,E,J) avec E <= {args.limit}...")
    triples = find_ap_triples(args.limit, progress_every=args.progress_every)
    print(f"  -> {len(triples)} triplets trouves en {time.time()-t0:.1f}s\n")

    print(f"Etape 2 : balayage de q (jusqu'a {args.qmax}) pour chaque triplet...")
    t1 = time.time()
    all_results = []
    for i, (A, E, J) in enumerate(triples):
        res = scan_q_for_triple(A, E, J, args.qmax)
        for count, q_val, details in res:
            total = 3 + count
            if total >= args.min_total:
                all_results.append({
                    'total_carres': total,
                    'bonus_carres': count,
                    'A': A, 'E': E, 'J': J, 'q': q_val,
                    **details,
                })
        if args.progress_every and (i + 1) % args.progress_every == 0:
            print(f"  [etape 2] {i+1}/{len(triples)} triplets traites  ({time.time()-t1:.1f}s)")

    print(f"  -> balayage termine en {time.time()-t1:.1f}s\n")

    all_results.sort(key=lambda r: -r['total_carres'])

    print(f"Nombre de configurations avec total >= {args.min_total} : {len(all_results)}")
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
            print(f"  A={r['A']} E={r['E']} J={r['J']}  q={r['q']}  "
                  f"-> total {r['total_carres']}/9")
            for k, v in r.items():
                if k in ('A', 'E', 'J', 'q', 'total_carres', 'bonus_carres'):
                    continue
                root = math.isqrt(v)
                tag = f"{root}^2" if root * root == v else f"{v} (non-carre)"
                print(f"      {k:15s} = {tag}")
            print()
    else:
        print("\nAucun resultat au-dessus du seuil. Essayez d'augmenter --limit et/ou --qmax, "
              "ou diminuez --min-total.")

    if args.out and all_results:
        fieldnames = list(all_results[0].keys())
        with open(args.out, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in all_results:
                writer.writerow(r)
        print(f"\nResultats complets exportes vers : {args.out}")

    print(f"\nTemps total d'execution : {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
