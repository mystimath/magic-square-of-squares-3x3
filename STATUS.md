# Status

_Mise à jour : 2026-07-08_

Ce document récapitule l’état actuel des différentes branches de recherche autour du problème du carré magique 3×3 de carrés, avec un accent particulier sur les campagnes computationnelles effectivement exécutées.

---

## Branche A — centre carré

Script principal historique :

```text
src/search_magic_square_of_squares_v4.py
```

Résultat actuel :

| Recherche    |                    Borne |               Résultat |
| ------------ | -----------------------: | ---------------------: |
| 7/9 primitif |  center_root ≤ 3 000 000 |           Bremner seul |
| 8/9 primitif | center_root ≤ 10 000 000 |                  aucun |
| 9/9 primitif |  inclus dans le test 8/9 | aucun dans cette borne |

Conclusion provisoire : dans cette branche classique à centre carré, le meilleur résultat primitif reste le carré de Bremner à 7/9.

---

## Branche B — centre non nécessairement carré

Script historique :

```text
src/search_magic_square_of_squares_v5_non_square_center.py
```

Résultat actuel :

|                        Borne |  Résultat |
| ---------------------------: | --------: |
| racines extérieures ≤ 10 000 | aucun 8/9 |
| racines extérieures ≤ 20 000 | aucun 8/9 |

La branche est figée provisoirement à 20 000, car la version actuelle devient fortement limitée par la mémoire.

Conclusion provisoire : aucun 8/9 détecté dans la branche à centre non nécessairement carré jusqu’aux bornes testées.

---

## Branche C — centre carré et quatre coins carrés

Cette branche impose que le centre et les quatre coins soient carrés parfaits :

```text
a, c, e, h, j carrés
```

Les quatre autres cases `b, d, f, i` sont ensuite déduites et testées.

Résultats synthétiques :

|      Borne | Configurations | Meilleur résultat |
| ---------: | -------------: | ----------------: |
| E ≤ 20 000 |            179 |              6/9 |
| E ≤ 60 000 |            614 |              6/9 |

Aucun 7/9 ni 8/9 trouvé dans cette famille.

Résumé détaillé du test principal :

```text
Borne : E ≤ 60 000
Paires (A,J) trouvées : 91 967
Centres E concernés : 40 891
Configurations valides : 614
Meilleur résultat : 6 carrés sur 9
Aucun 7/9
Aucun 8/9
Durée : 11 697 s ≈ 3 h 15 min
```

Répartition des carrés bonus parmi `b, d, f, i` :

```text
i carré : 354 cas
f carré : 165 cas
d carré : 78 cas
b carré : 17 cas
```

Donc la case `i = a + c - e` est de loin celle qui devient le plus souvent carrée dans cette famille.

### Multiples triviaux

Sur les 614 résultats, seulement 75 ont un facteur carré commun égal à 1. Les 539 autres sont très probablement des dilatations de configurations plus petites.

### Conclusion de la branche C

> Dans la famille des carrés magiques 3×3 où le centre et les quatre coins sont imposés carrés, la recherche jusqu’à `E ≤ 60 000` donne 614 configurations valides, toutes avec exactement 6 carrés sur 9. Aucun 7/9 ni 8/9 n’a été trouvé.

Cette branche constitue donc une bonne branche négative documentée.

---

## Branche D — une seule progression de carrés autour du centre

### D.1. Idée

On fixe une progression arithmétique de carrés autour du centre :

```text
A², E², J²
```

avec

```text
A² + J² = 2E²
```

puis on balaie un paramètre libre `q` pour tester les six autres cases :

```text
E²+q
E²-q
J²+q
J²-q
A²+q
A²-q
```

Cette famille contient le carré de Bremner.

### D.2. Seuil minimal pour retrouver Bremner

Le carré de Bremner est retrouvé dès que :

```text
A = 205
E = 425
J = 565
q = 41496
```

Donc les seuils minimaux sont :

```text
limit >= 425
qmax  >= 41496
min-total = 7
```

### D.3. Ancienne version relâchée

Script historique :

```text
magic_square_relaxed_search.py
```

Conclusion historique : ce script retrouve Bremner et ses multiples triviaux, mais n’a pas produit de nouveau 8/9.

---

## Branche D' — script optimisé parallèle et criblé

Nouveau script :

```text
src/magic_square_parallel_optimized.py
```

### D'.1. Optimisations intégrées

Le script optimisé combine :

1. génération streaming des triplets `(A,E,J)` via triplets pythagoriciens ;
2. borne de rejet immédiate dépendant de `qmax` ;
3. crible modulaire par triplet ;
4. génération sparse des seuls `q` compatibles avec une proximité à un carré ;
5. filtrage modulaire des `q` ;
6. déduplication finale des multiples triviaux.

Cette version est beaucoup plus rapide que la version dense de balayage complet sur `q`.

### D'.2. Résultats 7/9 — campagnes larges

| Campagne | Paramètres principaux | Triplets traités | Résultat distinct |
| --- | --- | ---: | --- |
| P2 | `limit=50 000`, `qmax=100 000`, `min-total=7` | 75 196 | Bremner seul |
| P5A | `limit=75 000`, `qmax=150 000`, `min-total=7` | 117 620 | Bremner seul |
| P7 | `limit=250 000`, `qmax=500 000`, `min-total=7` | 440 007 | Bremner seul |
| P9 | `limit=500 000`, `qmax=1 000 000`, `min-total=7` | 935 188 | Bremner seul |

Détails marquants :

- `P7` : 3 résultats bruts à 7/9, tous équivalents après déduplication ;
- `P9` : 4 résultats bruts à 7/9, correspondant à Bremner et à ses multiples triviaux `k=2,3,4`.

Conclusion 7/9 :

> Dans cette famille, jusqu’à `E ≤ 500 000` et `q ≤ 1 000 000`, aucun nouveau 7/9 primitif n’a été trouvé. Le seul 7/9 distinct rencontré est le carré de Bremner.

### D'.3. Résultats 8/9 — campagnes larges

| Campagne | Paramètres principaux | Triplets traités | Résultat |
| --- | --- | ---: | --- |
| P3 | `limit=50 000`, `qmax=100 000`, `min-total=8` | 75 196 | aucun 8/9 |
| P5B | `limit=75 000`, `qmax=150 000`, `min-total=8` | 117 620 | aucun 8/9 |
| P8 | `limit=250 000`, `qmax=500 000`, `min-total=8` | 440 007 | aucun 8/9 |
| P8b | `limit=250 000`, `qmax=500 000`, `min-total=8`, `strict-24` | 440 007 | aucun 8/9 |
| P9b | `limit=500 000`, `qmax=1 000 000`, `min-total=8`, `strict-24` | 935 188 | aucun 8/9 |

Conclusion 8/9 :

> Aucun 8/9 n’a été trouvé dans cette branche, y compris avec le crible plus agressif `strict-24`, jusqu’à `E ≤ 500 000` et `q ≤ 1 000 000`.

### D'.4. Cartographie 6/9

Campagne de cartographie :

```text
limit = 250 000
qmax = 500 000
min-total = 6
moduli = 16,5,7,11
```

Résultat :

```text
Triplets traités : 440 007
Résultats bruts retenus : 249
Multiples triviaux retirés : 183
Configurations distinctes : 66
Répartition : 65 cas à 6/9, 1 cas à 7/9
```

Cette cartographie est importante, car elle révèle plusieurs corridors fertiles à 6/9 sans produire de nouveau 7/9.

Observations qualitatives :

- le corridor autour de `E = 425` est particulièrement remarquable ;
- plusieurs triplets admettent plusieurs valeurs de `q` donnant 6/9 ;
- certains motifs de masque (`square_mask`) semblent plus structurés que d’autres.

Exemple de corridor notable :

```text
A=205 E=425 J=565  q=41496  -> 7/9  (Bremner)
A=289 E=425 J=527  q=41496  -> 6/9
A=355 E=425 J=485  q=42504  -> 6/9
A=205 E=445 J=595  q=31416  -> 6/9
A=267 E=447 J=573  q=48488  -> 6/9
```

### D'.5. Reruns ciblés sur une shortlist de triplets prometteurs

Fichier ciblé :

```text
results/promising/triples_prometteurs_phase2.csv
```

Contenu : 21 triplets sélectionnés à partir de la cartographie 6/9.

Campagnes exécutées :

| Campagne | Paramètres principaux | Résultat |
| --- | --- | --- |
| TARGET-T7 | `qmax=5 000 000`, `min-total=7` | Bremner seul |
| TARGET-T8 | `qmax=5 000 000`, `min-total=8` | aucun 8/9 |
| TARGET-T8-s24 | `qmax=5 000 000`, `min-total=8`, `strict-24` | aucun 8/9 |
| TARGET-T8-s24-bis | `qmax=10 000 000`, `min-total=8`, `strict-24` | aucun 8/9 |

Conclusion ciblée :

> Même en poussant `qmax` à 5 millions puis 10 millions sur une shortlist de 21 triplets prometteurs, aucun nouveau 7/9 ni aucun 8/9 n’a été trouvé. Le seul 7/9 détecté reste Bremner.

### D'.6. Conclusion générale de la branche D'

> La branche “une seule progression de carrés autour du centre”, dans sa version optimisée, a été poussée jusqu’à près d’un million de triplets utiles et `q ≤ 1 000 000` en balayage large, puis jusqu’à `q ≤ 10 000 000` sur une shortlist ciblée de 21 triplets prometteurs. Aucun nouveau 7/9 primitif ni aucun 8/9 n’a été trouvé. Le seul 7/9 distinct observé est le carré de Bremner.

Cette branche est désormais très bien documentée expérimentalement. Elle reste utile, mais les gains futurs viendront probablement davantage d’un ciblage structurel plus fin que d’une simple augmentation uniforme des bornes.

---

## Branche E — semi-magique centre zéro

Avec `e = 0`, on peut utiliser une paramétrisation plus simple.

Si les quatre coins sont :

```text
A²      C²
H²      J²
```

alors le carré semi-magique associé est :

```text
A²        H² + J²      C²
C² + J²   0            A² + H²
H²        A² + C²      J²
```

La somme commune vaut :

```text
S = A² + C² + H² + J²
```

Le but est de choisir `A, C, H, J` de sorte que les quatre sommes :

```text
H² + J²
C² + J²
A² + H²
A² + C²
```

soient elles aussi des carrés.

Commande de test historique :

```bash
python search_semimagic_e0_squares.py --max-root 100 --min-squares 7 --primitive-only --limit 10 --csv results_semimagic_e0.csv
```

Exemple obtenu rapidement :

```text
15² | 60² | 20²
52² | 0   | 39²
36² | 25² | 48²
```

En valeurs :

```text
225  | 3600 | 400
2704 | 0    | 1521
1296 | 625  | 2304
```

Les lignes et colonnes valent toutes :

```text
4225 = 65²
```

Donc on obtient :

```text
8 carrés positifs sur les 8 cases non nulles
```

ou, si l’on compte aussi `0 = 0²`, un semi-magique dégénéré à `9/9`.

### Statut conceptuel

Cette famille est intéressante pour l’exploration et la pédagogie, mais elle n’est pas le cœur du problème historique des carrés magiques 3×3 de carrés parfaits distincts, puisque :

1. le centre nul rend la famille dégénérée du point de vue du problème classique ;
2. les diagonales ne sont pas, en général, égales à la somme magique.

Elle reste néanmoins une branche constructive utile.

---

## Conclusion générale au 2026-07-08

À ce stade, les différentes branches donnent le tableau suivant :

- **branche A** : Bremner seul à 7/9 ; aucun 8/9 ni 9/9 dans les bornes historiques ;
- **branche B** : aucun 8/9 jusqu’à racines extérieures `≤ 20 000` ;
- **branche C** : beaucoup de 6/9, aucun 7/9 ni 8/9 ;
- **branche D'** (script optimisé) : vaste exploration de la famille à une progression de carrés autour du centre, avec cartographie 6/9 riche mais aucun nouveau 7/9 ni 8/9 ;
- **branche E** : semi-magique centre zéro très fertile, mais hors du cœur du problème magique complet.

La meilleure piste pour la suite n’est probablement plus une simple montée uniforme des bornes. La prochaine étape naturelle est une recherche computationnelle plus vaste mais aussi plus structurée :

1. exploitation systématique des familles fertiles à 6/9 ;
2. ciblage automatique des triplets prometteurs ;
3. cribles plus fins par motifs de cases carrées ;
4. exploration plus large des branches non centrées sur la progression unique autour du centre.

---

## Références rapides

- Bremner, *On squares of squares* (1999) : http://www.multimagie.com/Bremner1.pdf
- Bremner, *On squares of squares II* (2001) : http://www.multimagie.com/Bremner2.pdf
- MystiMath — problème ouvert : https://mystimath.org/fr/articles/carre-magique-3x3-carres-parfaits-probleme-ouvert/
- MystiMath — recherche expérimentale : https://mystimath.org/fr/articles/recherche-experimentale-carres-magiques-de-carres/
- MystiMath — centre zéro : https://mystimath.org/fr/articles/carres-semi-magiques-centre-zero/
- Magic square of squares (synthèse) : https://en.wikipedia.org/wiki/Magic_square_of_squares
