# Filtre précoce de primitivité du moteur like-Bremner

_Optimisation validée le 18 juillet 2026._

## 1. Idée

Chaque candidat joint deux progressions de carrés de même premier terme `A` :

```text
(A, A+r, A+2r)   et   (A, B, C).
```

Avant l'optimisation, le moteur testait d'abord si `B+r` et `C+r` étaient des
carrés, construisait la grille, puis calculait le PGCD de ses sept racines. À
`R=100000`, 175 des 176 extensions trouvées étaient seulement des dilatations
non primitives.

Le moteur calcule désormais le PGCD des cinq racines déjà connues dans les deux
progressions. Si ce PGCD est supérieur à un et si la recherche demande seulement
les classes primitives, le couple est rejeté avant les deux tests d'appartenance
à l'ensemble des carrés.

## 2. Preuve de sûreté

Soit `g>1` un diviseur commun des cinq racines connues. Les cinq valeurs carrées
sont donc divisibles par `g²`. Leurs différences montrent en particulier que
`g²` divise `r`, puis `B+r` et `C+r`.

Si ces deux dernières valeurs sont des carrés, disons `u²` et `v²`, les relations
`g² | u²` et `g² | v²` impliquent `g | u` et `g | v`. Les sept racines ont alors
le facteur commun `g` : aucune extension de ce couple ne peut être primitive.

Le rejet précoce ne change donc pas l'ensemble des classes primitives. Le calcul
final du PGCD est conservé comme contrôle défensif.

## 3. Régression dédiée

Le test utilise la dilatation par deux des deux progressions de Bremner :

```text
(46², 410², 578²)    différence 4r
(46², 746², 1054²)   différence 4q
```

En mode primitif, les deux orientations sont rejetées avant tout test de carré.
Avec `primitive_only=False`, la grille dilatée est au contraire conservée et son
PGCD de racines vaut exactement deux.

## 4. Mesures à R=100000

### Benchmark apparié principal

Le benchmark principal réutilise un catalogue paramétrique unique de 122640
progressions, alterne l'ordre des variantes à chaque tour et effectue sept
répétitions sans `tracemalloc`.

| Variante | Minimum | Médiane | Moyenne | Maximum | Écart-type |
| --- | ---: | ---: | ---: | ---: | ---: |
| Filtre précoce | 0,443344 s | 0,450491 s | 0,448813 s | 0,454075 s | 0,004401 s |
| Contrôle sans filtre | 0,461172 s | 0,471918 s | 0,470838 s | 0,476174 s | 0,005070 s |

Le rapport des médianes vaut `1,0476×`, soit une réduction de temps de `4,54 %`.
La médiane des sept accélérations appariées vaut `1,0538×`, avec un écart-type
de `0,0180`. Les sept paires favorisent le filtre ; leur accélération varie de
`1,0156×` à `1,0682×`.

| Compteur déterministe | Sans filtre | Avec filtre | Évolution |
| --- | ---: | ---: | ---: |
| Couples ordonnés | 635968 | 635968 | inchangé |
| Rejets PGCD précoces | 0 | 478344 | nouveau |
| Tests d'appartenance carré | 1271936 | 315248 | `−75,2 %` |
| Extensions atteintes | 176 | 1 | `−99,4 %` |
| Rejets non primitifs tardifs | 175 | 0 | supprimés |
| Classes primitives | 1 | 1 | identique |

### Mesure instrumentée secondaire

La mesure antérieure avec `tracemalloc`, limitée à une répétition, donnait
`3,453566 s` sans filtre et `3,149867 s` avec filtre (`−8,8 %`). Son pic mémoire
Python incrémental passait de 18883052 à 18800708 octets. Elle confirme la
direction du gain, mais le résultat apparié à sept répétitions ci-dessus est la
mesure de temps de référence.

Les variantes conservent exactement l'unique classe primitive historique de
Bremner.

Artefacts :

- benchmark apparié principal : `results/formulations_comparison/benchmarks/like_bremner_primitive_filter_paired_r100000.json` ;
- mesure instrumentée : `results/formulations_comparison/benchmarks/like_bremner_primitive_seed_r100000.json` ;
- contrôle antérieur : `results/formulations_comparison/benchmarks/like_bremner_v2_2_r100000.json`.

## 5. Conclusion

Le filtre est sûr, peu complexe et rentable. La prochaine réduction potentielle
porterait sur les 157624 tests de couples qui subsistent : préindexer les
extensions carrées ou grouper le catalogue par premier terme primitif permettrait
d'éviter une partie de ces consultations sans réintroduire les dilatations.
