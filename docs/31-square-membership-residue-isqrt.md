# B7 — Appartenance exacte aux carrés sans table de taille R

_Implémentation, validation et campagne exécutées le 18 juillet 2026._

## 1. Résultat

Les moteurs Lo Shu B3, B4, B5 et B6 ne matérialisent plus par défaut
l'ensemble Python

```text
{1², 2², ..., R²}.
```

Ils utilisent par défaut `math.isqrt` directement. Une chaîne de résidus
quadratiques suivie de `isqrt` reste disponible pour l'étude des grands
entiers, et l'ancienne table demeure l'oracle témoin. Les trois modes sont
`isqrt`, `residue_isqrt` et `materialized_set`.

Cette modification rend la mémoire du test d'appartenance indépendante de
`R`. Elle ne rend pas tout le moteur constant en mémoire : le flux conserve
encore la tranche d'incidences courante et les classes acceptées.

## 2. Exactitude mathématique

Le mode `isqrt` applique directement la décision exacte ci-dessous à chaque
requête. Le mode résiduel la précède de conditions nécessaires. Pour un module
`m`, soit

```text
Q_m = {x² mod m : 0 <= x < m}.
```

Si `n` est un carré parfait, alors `n mod m` appartient nécessairement à
`Q_m`. Rejeter `n` lorsque ce résidu est absent est donc toujours sûr. Passer
tous les filtres n'est en revanche qu'une condition nécessaire ; la décision
finale est

```python
root = math.isqrt(n)
is_square = root * root == n
```

après vérification de `1 <= n <= R²`. Il n'existe ainsi ni faux négatif ni
faux positif. Les modules influencent uniquement le temps, jamais le résultat.

La chaîne retenue est :

```text
1001, 41, 37, 29, 31.
```

`1001 = 7 × 11 × 13` fournit un premier filtre dense en information ; les
quatre nombres premiers suivants réduisent successivement les survivants.

## 3. Étude des filtres adaptés au flux Lo Shu

Un premier essai avec les modules usuels `64` et `63` s'est révélé mal adapté
aux extensions produites par B6 : le filtre modulo 64 ne rejetait aucune des
requêtes observées à `R=601`. Les modules définitifs ont donc été choisis sur
les valeurs d'extension réellement rencontrées, tout en conservant la preuve
d'exactitude ci-dessus.

Sur le profil B6 à `R=100000`, la chaîne donne :

| Étape | Rejets nouveaux |
| --- | ---: |
| modulo 1001 | 1062612 |
| modulo 41 | 317508 |
| modulo 37 | 163130 |
| modulo 29 | 91576 |
| modulo 31 | 50558 |
| total résiduel | 1685384 |
| appels finaux à `isqrt` | 63704 |
| carrés exacts | 1582 |

Sur `1749088` requêtes, `96,36 %` sont donc décidées avant `isqrt`. Malgré
ce taux, les opérations modulo et la boucle Python coûtent davantage que les
appels directs à la primitive C pour nos entiers d'au plus 40 bits.

## 4. Validation

La suite vérifie :

- l'égalité exhaustive avec la table pour tous les entiers de `-5` à
  `127² + 5` ;
- les carrés, voisins et bornes à `R=1000000` ;
- la partition cohérente des compteurs de rejet ;
- l'égalité des classes produites par les quatre oracles dans B3, B4, B5 et B6
  à `R=601`.

Les tests fonctionnels ciblés B3–B6 passent également, puis la suite complète
du dépôt confirme le raccordement : `70 tests` réussis. Le contrôle dédié exerce
explicitement les quatre modes, dont le cache borné expérimental.

## 5. Benchmark apparié à R=100000

Ce benchmark mesure les oracles scalaires avant la vectorisation B8.

Les cinq répétitions de temps utilisent le même catalogue canonique matériel,
généré une seule fois. L'ordre des trois modes alterne à chaque répétition. La
mesure mémoire est séparée et utilise le vrai flux de 128 tranches, afin que le
catalogue global ne masque pas le coût du set.

| Oracle | Temps médian | Pic Python streaming | Classes |
| --- | ---: | ---: | ---: |
| `isqrt` direct | 4,733436 s | 2215677 octets | 0 |
| résidus + `isqrt` | 5,244076 s | 2206799 octets | 0 |
| set matérialisé | 4,304581 s | 9600263 octets | 0 |

`isqrt` direct réduit le pic mesuré d'un facteur `4,33`, soit `76,9 %`.
Dans cette première version scalaire, il avait un surcoût médian de `10,0 %`
face au set. B8 supprime ensuite ce surcoût : B6 vectorisé mesure `3,679767 s`
contre `3,722376 s` pour le set sur le même catalogue.

Artefacts :
`results/formulations_comparison/benchmarks/lo_shu_b6_square_membership_r100000.json`
et le CSV de même nom.

## 6. Campagne B6 appariée à R=1000000

Les runs finaux reprennent les 512 tranches de la campagne B6 historique. Ils
diffèrent uniquement par l'oracle d'appartenance :

| Oracle | Temps bout-en-bout | Tests | Classes 9/9 |
| --- | ---: | ---: | ---: |
| set matérialisé historique | 65,036925 s | 25807672 | 0 |
| `isqrt` direct scalaire | 69,631168 s | 25807672 | 0 |
| résidus + `isqrt` | 76,537590 s | 25807672 | 0 |
| `isqrt` vectorisé B8 | 54,279316 s | 25807672 | 0 |

La version vectorisée est `16,5 %` plus rapide que le run historique avec set
et `22,1 %` plus rapide que l'oracle direct scalaire. Elle exécute toujours
`25807672` appels à `isqrt` et reconnaît les mêmes `4676` occurrences carrées.
Aucun couple compatible n'atteint le validateur avec neuf cases carrées, et
aucune classe primitive D4 n'est trouvée dans la boîte `0 < case <= 10^12`.

Artefacts : les deux fichiers précédents, plus
`results/formulations_comparison/benchmarks/lo_shu_b6_exact9_batched_isqrt_r1000000.json`.
La vectorisation complète B3–B6 est documentée dans
[32-batched-square-membership.md](32-batched-square-membership.md).

## 7. Utilisation

Le mode `isqrt` direct, à mémoire indépendante de `R`, est le défaut :

```powershell
python experiments\formulations_comparison\search_lo_shu_nine.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512
```

Pour reproduire l'ancien comportement :

```powershell
python experiments\formulations_comparison\search_lo_shu_nine.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512 `
  --square-membership materialized_set
```

Le même sélecteur est exposé par les CLI B3, B4 et B5.

## 8. Décision opérationnelle

Le set matérialisé reste un témoin utile et conserve un léger avantage dans B3
à `R=100000`. Dans B5 et B6, `isqrt` vectorisé est déjà légèrement plus rapide
tout en supprimant la mémoire linéaire en `R`; il reste donc le défaut général.
Le mode résiduel sert aux domaines d'entiers beaucoup plus grands, et le cache
borné est conservé uniquement comme expérience reproductible.
