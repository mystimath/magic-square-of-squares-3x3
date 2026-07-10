## Feuille de route  concrète

L’idée directrice est simple : **ne pas monter `limit` tout seul**. Avec notre moteur de recherche, les campagnes les plus rentables sont celles où **`qmax` et `limit` montent ensemble**, parce que la borne d’écart entre carrés impose déjà des zones mortes si `qmax` est trop petit. Pour viser 7/9, il faut nécessairement \(E \le (qmax+1)/2\), et pour viser 8/9 il faut essentiellement que les trois racines restent dans la zone contributive, donc il faut rester très attentif à \(J\) et donc à la taille effective des triplets. [script optimisé]

### Palier 0 — validation
À faire une seule fois, pour vérifier la machine et le débit réel :

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

Puis estimation :

```bash
python3 scripts/magic_square_parallel_optimized.py \
  --limit 50000 \
  --qmax 100000 \
  --workers 8 \
  --chunk-size 2000 \
  --min-total 7 \
  --estimate-only
```

---

### Palier 1 — première couverture 7/9 rentable
Comme `qmax = 50000`, on borne naturellement `limit = 25000` :

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

Et en parallèle, une campagne 6/9 pour repérer les familles “chaudes” :

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

Cette phase sert surtout à détecter des motifs récurrents et des triplets non banals. [MystiMath](https://mystimath.org/fr/articles/recherche-experimentale-carres-magiques-de-carres/)

---

### Palier 2 — vraie chasse “Bremner-like”
C’est le premier run que je considère comme vraiment prioritaire :

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

Avec une machine à 16 cœurs physiques, la variante naturelle est :

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

C’est à ce palier qu'on a de bonnes chances de tomber sur un **7/9 inhabituel**, s’il y en a un accessible dans cette famille. [script optimisé]

---

### Palier 3 — première offensive 8/9, voie sûre
Là, on vise explicitement la joie de danser :

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

Ici, je conseille d’ajouter 13 au crible, car les survivants sont rarissimes et on veut serrer la vis sans activer encore le mode le plus agressif. [Wikipedia](https://en.wikipedia.org/wiki/Magic_square_of_squares)

---

### Palier 4 — offensive 8/9, voie agressive
Même domaine, mais avec `--strict-24` :

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

Cette campagne ne remplace pas la précédente ; elle la complète. La voie sûre protège contre un faux rejet trop agressif, la voie stricte attaque le cœur arithmétique des cas très structurés. [Wikipedia](https://en.wikipedia.org/wiki/Magic_square_of_squares)

---

### Palier 5 — montée coordonnée
Si rien de neuf n’apparaît, la bonne montée est :

#### 5A
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

#### 5B
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

#### 5C
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

#### 5D
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

### Palier 6 — reruns ciblés
Dès qu’une campagne donne :
- un 7/9 atypique,
- un triplet qui revient souvent,
- un 6/9 très proche d’un motif Bremner-like,

il faut faire un `triples-file` dédié et relancer plus haut en `qmax` :

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

C’est probablement **la phase la plus prometteuse** pour transformer un quasi-candidat en vraie trouvaille.

---

## Règle décisionnelle simple

Si on veut un protocole ultra-pratique :

- **aucun 7/9 intéressant** → on monte `qmax` ;
- **beaucoup de 6/9 structurés** → on extrait des triplets ciblés ;
- **un 7/9 atypique** → rerun immédiat avec `qmax` doublé ;
- **un 8/9 potentiel** → arrêt de tout le reste, vérification indépendante complète.

