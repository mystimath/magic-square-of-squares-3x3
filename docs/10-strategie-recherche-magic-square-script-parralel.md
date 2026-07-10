# Stratégie de recherche — carré magique 3x3 de carrés presque parfaits

_Date : 2026-07-08_

## 1. Objectif

Dans le cadre de notre recherche, notre ambition nous a amené vers un autre palier.

Le but pratique n'est pas seulement de retrouver le carré de Bremner à 7/9, mais de maximiser la probabilité de trouver un **Bremner-like inédit** :

- soit un nouveau 7/9 primitif ;
- soit, idéalement, un **8/9** ;
- et en parallèle documenter proprement les zones déjà explorées, les bornes utiles et les familles qui ne donnent rien.

Le moteur de recherche retenu part de triplets \((A,E,J)\) tels que
\[
A^2 + J^2 = 2E^2,
\]
c'est-à-dire de trois carrés en progression arithmétique, puis cherche un paramètre \(q\) pour rendre carrées le plus grand nombre possible parmi les six autres cases du carré magique 3x3 standard. Cette famille est exactement celle explorée par le script optimisé. Voir : script original, script optimisé et paramétrisation rationnelle de Bremner.  
Sources : [script original], [Bremner 1999](http://www.multimagie.com/Bremner1.pdf)

---

## 2. Principes directeurs

### 2.1. Toujours faire croître `qmax` et `limit` ensemble

Le point clé est la borne d'écart entre deux carrés. Si \(q < 2n-1\), alors \(n^2 \pm q\) ne peut pas être carré. Donc :

- pour viser **7/9**, il faut nécessairement que **au moins deux** des trois racines \(A,E,J\) soient \(\le (qmax+1)/2\) ; comme \(A<E<J\), cela impose **nécessairement**
  \[
  E \le (qmax+1)/2 ;
  \]
- pour viser **8/9** ou **9/9**, il faut nécessairement que **les trois** racines puissent contribuer, donc
  \[
  J \le (qmax+1)/2.
  \]

Conséquence stratégique : il est peu utile de lancer une campagne avec `limit` énorme si `qmax` reste petit. Mieux vaut augmenter `qmax`, puis fixer `limit` à peu près à `qmax/2`.  
Source : [script optimisé]

### 2.2. Deux voies de recherche en parallèle

Il faut séparer les campagnes en deux familles :

- **voie SÛRE** : crible modulaire standard, sans `--strict-24`, pour ne pas risquer de jeter des quasi-solutions atypiques ;
- **voie AGRESSIVE** : avec `--strict-24` et éventuellement un module supplémentaire 13, ciblée sur le 8/9.

La voie sûre sert à la couverture large. La voie agressive sert à la chasse au jackpot.  
Sources : [script optimisé], [Wikipedia](https://en.wikipedia.org/wiki/Magic_square_of_squares)

### 2.3. Chercher d'abord des motifs “Bremner-like” primitifs

Les résultats qui comptent vraiment sont :

- un 7/9 **non trivial** et **non homothétique** ;
- un 8/9 primitif ;
- ou une famille récurrente nouvelle menant souvent à 6/9 ou 7/9.

La déduplication par facteur carré commun doit donc être gardée en permanence, et tout résultat prometteur doit être réexécuté localement avec une borne `qmax` plus grande pour vérifier qu'il ne s'agit pas d'un artefact de bord.  
Sources : [script optimisé], [MystiMath](https://mystimath.org/fr/articles/carre-magique-3x3-carres-parfaits-probleme-ouvert/)

---

## 3. Convention de nommage des runs

Nom de fichier CSV recommandé :

```text
results/YYYY-MM-DD_P{phase}_E{limit}_q{qmax}_T{min_total}_W{workers}_M{mods}.csv
```

Exemples :

```text
results/2026-07-08_P1_E25000_q50000_T7_W8_M16-5-7-11.csv
results/2026-07-08_P3_E50000_q100000_T8_W8_M16-5-7-11-13_s24.csv
```

Nom de log recommandé :

```text
logs/YYYY-MM-DD_P{phase}_E{limit}_q{qmax}_T{min_total}_W{workers}.log
```

Astuce pratique : garder le même nom de base pour le CSV et le log.

---

## 4. Petite amélioration de notre arborescence du repo

```text
repo/
├── src/
|   |── (...)
│   ├── magic_square_parallel.py
│   └── magic_square_parallel_optimized.py
├── results/
│   ├── raw/
│   ├── promising/
│   └── summaries/
├── logs/
├── notes/
│   ├── bremner_like_candidates.md
│   └── negative_results.md
└── README.md
```

---

## 5. Campagnes de calcul — feuille de route concrète

Les commandes ci-dessous supposent une machine à **8 cœurs physiques**. Si la machine a 16 cœurs physiques, remplacer `--workers 8` par `--workers 16` et monter `--chunk-size` de 2000 à 4000 si le débit reste bon.

### Phase 0 — Validation et calibration

Objectif : vérifier l'installation, la cohérence des sorties et le débit réel.

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 5000 \
  --qmax 50000 \
  --workers 4 \
  --chunk-size 1000 \
  --min-total 6 \
  --top 20 \
  --out results/raw/2026-07-08_P0_E5000_q50000_T6_W4_M16-5-7-11.csv \
  | tee logs/2026-07-08_P0_E5000_q50000_T6_W4.log
```

Puis estimation sur borne plus sérieuse :

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 50000 \
  --qmax 100000 \
  --workers 8 \
  --chunk-size 2000 \
  --min-total 7 \
  --estimate-only
```

**Critère de sortie de phase** : débit stable, aucun problème mémoire, résultats de petite borne cohérents avec le script de référence.

---

### Phase 1 — Couverture sûre 7/9 avec `qmax = 50k`

Ici, la borne naturelle est `limit = 25000`, car pour viser 7/9 il faut nécessairement `E <= qmax/2`.

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 25000 \
  --qmax 50000 \
  --workers 8 \
  --chunk-size 2000 \
  --min-total 7 \
  --moduli 16,5,7,11 \
  --top 50 \
  --out results/raw/2026-07-08_P1_E25000_q50000_T7_W8_M16-5-7-11.csv \
  | tee logs/2026-07-08_P1_E25000_q50000_T7_W8.log
```

En parallèle, faire aussi une cartographie 6/9 pour repérer les familles récurrentes :

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 25000 \
  --qmax 50000 \
  --workers 8 \
  --chunk-size 2000 \
  --min-total 6 \
  --moduli 16,5,7,11 \
  --top 100 \
  --out results/raw/2026-07-08_P1b_E25000_q50000_T6_W8_M16-5-7-11.csv \
  | tee logs/2026-07-08_P1b_E25000_q50000_T6_W8.log
```

**But** : récupérer des triplets qui “chauffent” souvent, même s'ils s'arrêtent à 6/9.

---

### Phase 2 — Couverture sûre 7/9 avec `qmax = 100k`

C'est le premier vrai palier Bremner-like.

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 50000 \
  --qmax 100000 \
  --workers 8 \
  --chunk-size 2000 \
  --min-total 7 \
  --moduli 16,5,7,11 \
  --top 50 \
  --out results/raw/2026-07-08_P2_E50000_q100000_T7_W8_M16-5-7-11.csv \
  | tee logs/2026-07-08_P2_E50000_q100000_T7_W8.log
```

Variante plus large si la machine tient bien :

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 50000 \
  --qmax 100000 \
  --workers 16 \
  --chunk-size 4000 \
  --min-total 7 \
  --moduli 16,5,7,11 \
  --top 50 \
  --out results/raw/2026-07-08_P2_E50000_q100000_T7_W16_M16-5-7-11.csv \
  | tee logs/2026-07-08_P2_E50000_q100000_T7_W16.log
```

**Action post-run** : isoler tous les 6/9 et 7/9 primitifs, les trier par fréquence de motif et par taille des racines.

---

### Phase 3 — Première offensive 8/9, voie sûre

Pour 8/9, il faut que les trois racines puissent contribuer. Avec `qmax = 100k`, il faut donc essentiellement rester dans la zone `J <= 50000`, donc `E < 50000`. On garde `limit = 50000` comme borne naturelle.

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 50000 \
  --qmax 100000 \
  --workers 8 \
  --chunk-size 2000 \
  --min-total 8 \
  --moduli 16,5,7,11,13 \
  --top 50 \
  --out results/raw/2026-07-08_P3_E50000_q100000_T8_W8_M16-5-7-11-13.csv \
  | tee logs/2026-07-08_P3_E50000_q100000_T8_W8.log
```

Cette phase est coûteuse en termes de rareté des survivants, mais c'est là que peut tomber un premier vrai choc statistique.

---

### Phase 4 — Offensive 8/9, voie agressive

Même domaine, mais avec filtre supplémentaire expérimental `--strict-24`.

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 50000 \
  --qmax 100000 \
  --workers 8 \
  --chunk-size 2000 \
  --min-total 8 \
  --moduli 16,5,7,11,13 \
  --strict-24 \
  --top 50 \
  --out results/raw/2026-07-08_P4_E50000_q100000_T8_W8_M16-5-7-11-13_s24.csv \
  | tee logs/2026-07-08_P4_E50000_q100000_T8_W8_s24.log
```

**Important** : cette phase ne remplace pas la phase 3 ; elle la complète.

---

### Phase 5 — Montée coordonnée `qmax` / `limit`

Si les phases 2 à 4 ne donnent rien de neuf, la bonne montée n'est pas `limit -> énorme` avec `qmax` fixe, mais une montée coordonnée.

#### Palier 5A

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 75000 \
  --qmax 150000 \
  --workers 8 \
  --chunk-size 2500 \
  --min-total 7 \
  --moduli 16,5,7,11 \
  --top 50 \
  --out results/raw/2026-07-08_P5A_E75000_q150000_T7_W8_M16-5-7-11.csv \
  | tee logs/2026-07-08_P5A_E75000_q150000_T7_W8.log
```

#### Palier 5B

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 75000 \
  --qmax 150000 \
  --workers 8 \
  --chunk-size 2500 \
  --min-total 8 \
  --moduli 16,5,7,11,13 \
  --top 50 \
  --out results/raw/2026-07-08_P5B_E75000_q150000_T8_W8_M16-5-7-11-13.csv \
  | tee logs/2026-07-08_P5B_E75000_q150000_T8_W8.log
```

#### Palier 5C

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 100000 \
  --qmax 200000 \
  --workers 8 \
  --chunk-size 3000 \
  --min-total 7 \
  --moduli 16,5,7,11 \
  --top 50 \
  --out results/raw/2026-07-08_P5C_E100000_q200000_T7_W8_M16-5-7-11.csv \
  | tee logs/2026-07-08_P5C_E100000_q200000_T7_W8.log
```

#### Palier 5D

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 100000 \
  --qmax 200000 \
  --workers 8 \
  --chunk-size 3000 \
  --min-total 8 \
  --moduli 16,5,7,11,13 \
  --strict-24 \
  --top 50 \
  --out results/raw/2026-07-08_P5D_E100000_q200000_T8_W8_M16-5-7-11-13_s24.csv \
  | tee logs/2026-07-08_P5D_E100000_q200000_T8_W8_s24.log
```

---

### Phase 6 — Re-runs ciblés sur triplets prometteurs

Dès qu'une campagne produit des motifs intéressants :

- mêmes \((A,E,J)\) revenant souvent ;
- 6/9 très proches d'un motif Bremner-like ;
- 7/9 primitifs rares ;
- structures où les non-carrés sont “petits” en distance d'un carré ;

il faut construire un fichier `triples_file` dédié contenant seulement ces triplets, puis relancer avec `qmax` doublé ou triplé.

Exemple de relance ciblée :

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --triples-file results/promising/triples_prometteurs_phase2.csv \
  --qmax 300000 \
  --workers 8 \
  --chunk-size 1000 \
  --min-total 8 \
  --moduli 16,5,7,11,13 \
  --top 100 \
  --out results/promising/2026-07-08_P6_targeted_q300000_T8_W8.csv \
  | tee logs/2026-07-08_P6_targeted_q300000_T8_W8.log
```

C'est probablement l'étape la plus prometteuse pour transformer des 6/9 ou 7/9 inhabituels en quasi-records.

---

## 6. Règles d'arrêt / décisions après chaque phase

Après chaque CSV, prendre une décision binaire :

### Cas A — Aucun 7/9 nouveau, peu de 6/9 atypiques

Monter **d'abord `qmax`**, pas seulement `limit`.

### Cas B — Beaucoup de 6/9 structurés, mais aucun 7/9

Passer en re-run ciblé sur triplets prometteurs.

### Cas C — Un 7/9 nouveau ou très atypique

- rerun immédiat avec `qmax` doublé ;
- rerun voie sûre + voie agressive ;
- vérification avec le script original si besoin ;
- note dédiée dans `notes/bremner_like_candidates.md`.

### Cas D — Un 8/9 potentiel

- arrêt du batch courant ;
- rerun du même triplet seul avec plusieurs `qmax` et modules ;
- vérification exacte indépendante ;
- archivage complet du log, du CSV et de la factorisation des 9 valeurs.

---

## 7. Ce qu'il faut consigner pour chaque candidat sérieux

Pour chaque candidat 7/9 ou mieux, archiver :

- \(A,E,J,q\) ;
- les 9 valeurs du carré ;
- la liste des cases carrées exactes ;
- la forme canonique après déduplication ;
- les factorisations des deux ou trois non-carrés ;
- la distance au carré parfait le plus proche pour chaque non-carré ;
- le motif binaire des 6 cases dérivées (`square_mask`).

Cela permettra de repérer des familles cachées plutôt que des coups isolés.

---

## 8. Priorités de recherche mathématique parallèles

En parallèle des runs massifs, il faut continuer à alimenter deux pistes plus théoriques :

1. **analyse des motifs 6/9 récurrents** pour voir si certains masques de carrés reviennent beaucoup plus que les autres ;
2. **analyse des triplets prometteurs** pour comprendre si certaines familles pythagoriciennes \((m,n,e)\) favorisent les quasi-solutions.

C'est probablement là qu'un “Bremner-like inédit” finira par émerger : pas d'une exploration uniforme de tout l'espace, mais d'une famille qui sur-produit des cas proches du record.  
Sources : [MystiMath](https://mystimath.org/fr/articles/recherche-experimentale-carres-magiques-de-carres/), [Bremner 2001](http://www.multimagie.com/Bremner2.pdf)

---

## 9. Références

- Andrew Bremner, _On squares of squares_ (1999): http://www.multimagie.com/Bremner1.pdf
- Andrew Bremner, _On squares of squares II_ (2001): http://www.multimagie.com/Bremner2.pdf
- MystiMath — problème ouvert : https://mystimath.org/fr/articles/carre-magique-3x3-carres-parfaits-probleme-ouvert/
- MystiMath — recherche expérimentale : https://mystimath.org/fr/articles/recherche-experimentale-carres-magiques-de-carres/
- MystiMath — centre zéro : https://mystimath.org/fr/articles/carres-semi-magiques-centre-zero/
- Magic square of squares (synthèse) : https://en.wikipedia.org/wiki/Magic_square_of_squares

