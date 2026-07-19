# B9 — Préfiltrage algébrique avant reconstruction des grilles

_Profilage, implémentation et campagnes exécutés le 19 juillet 2026._

## 1. Résultat

B4, B5 et B6 ne construisent plus systématiquement un tuple de neuf cases
pour chaque paire de progressions compatible. La positivité, la borne et la
distinction sont décidées directement sur les paramètres `(A,q,r)`, puis les
quatre cases complémentaires sont testées sans matérialiser la grille.

Dans les campagnes confirmatoires à `R=1000000` :

- B4 construit 4 grilles au lieu de 10029290 ;
- B5 et B6 n'en construisent aucune au lieu de 10029290 chacun ;
- les 10029290 triplets candidats, les 25807672 tests de carré et toutes les
  classes finales restent inchangés ;
- le temps diminue de 23,8 % à 24,2 % par rapport à B8.

## 2. Profil de référence

Le profil B6 à `R=100000`, avec le catalogue canonique partagé hors mesure,
montrait 26022686 appels en 9,758 s sous `cProfile`. La reconstruction
dominait les tests de carré :

| Poste | Appels | Temps cumulé profilé |
| --- | ---: | ---: |
| `build_like_bremner_grid` | 686206 | 2,264 s |
| validations de type du constructeur | 3431030 | 1,271 s direct |
| lot de quatre tests de carré | 437272 | 1,111 s |
| `math.isqrt` | 1749088 | 0,162 s |

Le constructeur public vérifie légitimement ses quatre types et la progression
`A,B,C`. Ces garanties étaient toutefois répétées sur chaque candidat interne,
alors que les progressions graines les impliquent déjà.

Après B9 final et inlining, le même profil compte 14145564 appels en 6,451 s :
45,6 % d'appels et 33,9 % de temps profilé en moins. Le cœur groupé B6 passe de
8,289 s à 5,035 s, soit un gain profilé de 39,3 %.

## 3. Filtres algébriques exacts

Les neuf cases de la grille sont les valeurs

```text
A + x*q + k*r, avec x,k dans {0,1,2}.
```

Les différences `q` et `r` des progressions de carrés sont strictement
positives. Il s'ensuit immédiatement que :

```text
min(grille) = A
max(grille) = A + 2*q + 2*r.
```

Une collision entre deux cases distinctes impose

```text
(x-x')*q = (k'-k)*r.
```

Les valeurs absolues non nulles des deux coefficients appartiennent à
`{1,2}`. Les seuls rapports possibles sont donc `q/r = 1`, `2` ou
`1/2`. Le cas `q=r` était déjà rejeté comme égalité des deux pas ; B9
remplace `len(set(grid)) != 9` par les deux tests restants
`q == 2*r` et `r == 2*q`.

Ces critères sont des équivalences, et non des heuristiques. Ils ne changent
donc ni le domaine exhaustif ni l'ordre des catégories de rejet.

## 4. Reconstruction différée

Pour un croisement de graines `(x0,k0)`, cinq cases sont déjà connues carrées.
Les quatre coordonnées restantes sont pré-calculées au chargement dans
`REMAINING_PARAMETER_COORDINATES`. Le cœur évalue directement leurs quatre
valeurs, puis applique le lot `isqrt` de B8.

La grille complète n'est construite qu'après le seuil propre au moteur :

- deux carrés complémentaires pour B4, donc exactement 7/9 ;
- trois pour B5, donc exactement 8/9 ;
- quatre pour B6, donc exactement 9/9.

Le nouveau compteur `candidate_parameter_triples` conserve le nombre de
triplets soumis aux filtres de boîte. `reconstructed_grids` mesure
désormais les allocations effectives, après le test des quatre cases.

## 5. Benchmark apparié à R=100000

Cinq répétitions alternent `isqrt` et le set matérialisé sur un catalogue
canonique unique de 122640 progressions.

| Moteur | Classes | B8 `isqrt` | B9 `isqrt` | Gain B9 | Set B9 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B3 | 1 | 0,383352 s | 0,389756 s | −1,7 % | 0,367362 s |
| B4 | 1 | 3,065540 s | 2,131395 s | 30,5 % | 2,182884 s |
| B5 | 0 | 3,649219 s | 2,761757 s | 24,3 % | 2,758459 s |
| B6 | 0 | 3,679767 s | 2,780880 s | 24,4 % | 2,822581 s |

B3 n'utilise pas le cœur modifié ; son écart est un témoin de bruit de mesure.
Pour B4–B6, le gain est nettement supérieur à ce bruit dans les cinq passes.
La proximité finale entre set et `isqrt` confirme que la matérialisation de la
grille, et non l'extraction de racine, était le poste supprimé.

Artefacts :

- `lo_shu_b3_b6_algebraic_prefilter_r100000.json` ;
- `lo_shu_b3_b6_algebraic_prefilter_r100000.csv`.

## 6. Campagnes confirmatoires à R=1000000

Les trois campagnes reprennent exactement le protocole B8 : catalogue canonique
streaming, 512 shards, oracle `isqrt`, temps du catalogue inclus.

| Moteur | Résultat | B8 | B9 | Gain | Grilles B8 → B9 |
| --- | --- | ---: | ---: | ---: | ---: |
| B4 | Bremner seul | 53,876882 s | 41,063923 s | 23,782 % | 10029290 → 4 |
| B5 | aucune classe 8/9 | 53,688051 s | 40,813064 s | 23,981 % | 10029290 → 0 |
| B6 | aucune classe 9/9 | 54,279316 s | 41,167942 s | 24,155 % | 10029290 → 0 |

Les compteurs structurels sont identiques à B8 : 1517296 progressions,
4551888 incidences, 49800462 paires ordonnées, 10029290 triplets compatibles
et 25807672 tests de carré. B4 valide les mêmes quatre représentants de
Bremner, réduits à la même classe D4. B5 et B6 ne valident toujours rien.

Artefacts :

- `lo_shu_b4_all_masks_algebraic_prefilter_r1000000.json` et `.csv` ;
- `lo_shu_b5_all_masks_algebraic_prefilter_r1000000.json` et `.csv` ;
- `lo_shu_b6_exact9_algebraic_prefilter_r1000000.json` et `.csv`.

## 7. Validation

Deux tests nouveaux vérifient :

- pour tous `1 <= q,r <= 9`, l'équivalence entre le critère de ratios et
  `len(set(grid)) == 9`, ainsi que les formules du minimum et du maximum ;
- pour les neuf croisements `(x0,k0)`, l'identité entre les quatre valeurs
  directes et les quatre cases extraites d'une grille matérialisée.

Les tests existants couvrent l'égalité avec les oracles exhaustifs v2.2,
Bremner, B1/B2, tous les modes d'appartenance et l'identité des chemins matériel
et streaming. Après B9, les 72 tests passent et `git diff --check` est propre.

## 8. Décision opérationnelle

B9 est validé. La reconstruction n'est plus un poste chaud dans B4–B6. Les
profils désignent désormais le groupement des incidences, leurs tris et
`_compatible_ordered_incidences` comme prochains postes possibles. Une
éventuelle B10 devra les mesurer séparément et préserver le protocole streaming,
la canonicalisation et les compteurs de couverture.
