# B8 — Tests de carrés par lot dans B3–B6

_Profilage, implémentation et campagnes exécutés le 18 juillet 2026._

## 1. Résultat

Les moteurs B3 à B6 conservent l'oracle `isqrt` à mémoire indépendante de `R`,
mais ne l'appellent plus séparément pour chaque extension d'un même candidat.

- B3 teste ses deux extensions dans un seul appel avec court-circuit ;
- B4, B5 et B6 pré-calculent les quatre indices complémentaires et comptent
  leurs carrés dans un seul appel ;
- les quatre valeurs restent toutes testées dans B4–B6, afin de préserver les
  compteurs et la classification exacte 7/9, 8/9 ou 9/9.

À `R=100000`, B5 et B6 deviennent légèrement plus rapides que le set
matérialisé, avec la réduction mémoire de B7. Au million, les quatre campagnes
sont accélérées de `4,94 %` à `16,54 %` par rapport aux artefacts historiques.

## 2. Hypothèse du cache borné

Le profil de réutilisation B6 à `R=100000` observe :

| Mesure | Valeur |
| --- | ---: |
| requêtes | 1749088 |
| valeurs distinctes | 837653 |
| requêtes répétées | 911435 |
| taux de répétition global | 52,11 % |
| succès d'un LRU de 4096 entrées | 886398 |
| taux de succès LRU | 50,68 % |

Un mode expérimental `cached_isqrt`, fondé sur le LRU C de `functools` et
borné à 4096 entrées, a donc été testé. Malgré 886398 appels à `isqrt` évités,
il ralentit le moteur :

| Version avant vectorisation | Médiane B6 |
| --- | ---: |
| `isqrt` direct | 4,750201 s |
| `cached_isqrt` | 5,316843 s |

Le cache coûte `11,9 %` de temps supplémentaire. Après vectorisation, l'écart
se creuse : `3,674959 s` pour le direct contre `4,735349 s` pour le cache. Le
cache reste donc expérimental, n'est pas exposé dans les CLI et n'est pas le
défaut.

## 3. Profil CPU

Une passe B6 instrumentée à `R=100000` totalise 34,6 millions d'appels de
fonctions. Les postes pertinents sont :

| Poste | Appels | Temps cumulé profilé |
| --- | ---: | ---: |
| `IsqrtSquareMembership.__contains__` | 1749088 | 1,915 s |
| `math.isqrt` | 1749089 | 0,188 s |
| générateur des positions restantes | 2186360 | 0,769 s direct |
| générateur des tests d'appartenance | 2186360 | 0,651 s direct |

L'extraction de racine carrée sur un entier d'au plus 40 bits est donc très
bon marché. Le coût provenait surtout des appels Python, des vérifications de
type répétées et des générateurs temporaires. Cela explique à la fois l'échec
du cache et le gain du traitement par lot.

## 4. Transformation algorithmique

Pour chaque croisement `(x0,k0)`, les cinq cases des deux progressions graines
sont déjà carrées. Les quatre autres indices de grille sont désormais calculés
une seule fois au chargement :

```text
REMAINING_GRID_INDICES[x0][k0] = (i0, i1, i2, i3).
```

Le cœur forme directement

```text
(grid[i0], grid[i1], grid[i2], grid[i3])
```

et `count_bounded_squares` exécute les quatre `isqrt` dans la même boucle.
B4 exige un compte égal à 2, B5 un compte égal à 3 et B6 un compte égal à 4.

B3 conserve sa logique différente : son lot de deux valeurs s'arrête au
premier non-carré. Le batch B3 vérifie lui-même `1 <= valeur <= R²`, car une
extension peut sortir de la borne avant le filtre de boîte. Le test de
régression `R=564/565` garantit que le terme `565²` n'est pas accepté à la
borne 564.

## 5. Benchmark transversal à R=100000

Les cinq répétitions utilisent un unique catalogue canonique de 122640
progressions. L'ordre `isqrt`/set alterne à chaque répétition.

| Moteur | Classes | `isqrt` batch | Set | Écart `isqrt` |
| --- | ---: | ---: | ---: | ---: |
| B3 | 1 | 0,383352 s | 0,366215 s | +4,7 % |
| B4 | 1 | 3,065540 s | 3,046507 s | +0,6 % |
| B5 | 0 | 3,649219 s | 3,675558 s | −0,7 % |
| B6 | 0 | 3,679767 s | 3,722376 s | −1,1 % |

L'écart B4 est du niveau du bruit de mesure. B5 et B6 obtiennent désormais à
la fois un léger gain CPU et la suppression de la table en `O(R)`.

Artefact :
`results/formulations_comparison/benchmarks/lo_shu_b3_b6_batched_isqrt_r100000.json`.

## 6. Campagnes appariées à R=1000000

Les nouveaux runs réutilisent les mêmes domaines canoniques et nombres de
tranches que leurs témoins historiques.

| Moteur | Résultat | Historique | `isqrt` batch | Gain |
| --- | --- | ---: | ---: | ---: |
| B3 | Bremner seul | 8,871859 s | 8,433562 s | 4,940 % |
| B4 | Bremner seul | 64,286310 s | 53,876882 s | 16,192 % |
| B5 | aucune classe 8/9 | 63,756097 s | 53,688051 s | 15,792 % |
| B6 | aucune classe 9/9 | 65,036925 s | 54,279316 s | 16,541 % |

Les compteurs structurels B4–B6 restent identiques : 1517296 progressions,
4551888 incidences, 10029290 grilles reconstruites et 25807672 tests de carré.
B4 valide les mêmes quatre représentants de l'unique classe de Bremner ; B5
et B6 ne valident toujours aucun candidat.

Artefacts nouveaux :

- `like_bremner_b3_batched_isqrt_r1000000.json` ;
- `lo_shu_b4_all_masks_batched_isqrt_r1000000.json` ;
- `lo_shu_b5_all_masks_batched_isqrt_r1000000.json` ;
- `lo_shu_b6_exact9_batched_isqrt_r1000000.json`.

Ils se trouvent tous dans
`results/formulations_comparison/benchmarks/`, avec leurs CSV associés.

## 7. Validation

La suite couvre les quatre oracles, l'égalité exhaustive avec le set, les
bornes, Bremner, les modes matériel/streaming et les formulations B1/B2/v2.2.
Après vectorisation, `70 tests` passent. `git diff --check` ne signale aucune
erreur d'espacement.

## 8. Décision opérationnelle

Le mode par défaut reste `isqrt`. L'expérience démontre qu'à cette taille
d'entiers la réduction du nombre d'appels Python est plus importante que la
réduction du nombre d'appels à `math.isqrt`. La prochaine optimisation doit
donc viser la reconstruction et les filtres structurels du cœur commun, pas un
cache de tests de carré.
