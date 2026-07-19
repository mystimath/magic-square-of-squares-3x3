# B6 — Scanner Lo Shu exact 9/9

_Implémentation, validation et campagne exécutées le 18 juillet 2026._

## 1. Résultat

B6 applique l'index de progressions partagé de B4/B5 au problème principal :
chercher un carré magique 3×3 dont les neuf cases sont des carrés parfaits.

Dans la boîte complète

```text
0 < chaque case <= R²,    R = 1000000,
```

B6 ne trouve aucune classe primitive à neuf valeurs distinctes.

Ce résultat est une recherche bornée exhaustive dans la boîte annoncée. Il ne
constitue pas une preuve d'impossibilité générale.

## 2. Couverture par neuf croisements

Après une symétrie D4, toute grille magique 3×3 distincte s'écrit avec `q>0`,
`r>0` et

```text
T(x,k) = A + xq + kr,    x,k dans {0,1,2}.
```

Les coordonnées paramétriques sont

```text
          k=0  k=1  k=2
x=0        h    c    d
x=1        a    e    i
x=2        f    g    b.
```

Dans une grille 9/9, les trois lignes et les trois colonnes paramétriques sont
des progressions de trois carrés. Leurs neuf intersections sont disponibles.
B6 joint deux progressions sur une valeur carrée commune, retrouve les indices
`(x,k)` de l'intersection et calcule

```text
A = valeur_commune - xq - kr.
```

Les cinq cases du croisement sont déjà carrées. Les quatre cases restantes
doivent toutes appartenir à l'ensemble des carrés bornés. Le validateur
indépendant recalcule ensuite les huit sommes, la positivité, la distinction,
les neuf racines, leur PGCD et la classe D4.

Le catalogue paramétrique canonique contient toutes les progressions dont les
racines sont au plus `R`. Puisque les neuf cases finales sont bornées par `R²`,
aucune progression nécessaire ne se trouve hors du catalogue. B6 est donc
exhaustif dans la boîte finale définie.

## 3. PGCD et flux d'incidences

Comme B4 et B5, B6 rejette par seaux de PGCD tout couple de graines qui ne peut
pas produire une classe primitive. Chaque progression canonique écrit trois
incidences binaires, distribuées selon leur racine carrée partagée. Le mode
streaming ne charge qu'une des tranches à la fois.

Le benchmark de l'index partagé B4 à `R=100000` a mesuré une réduction de pic
mémoire Python de `89,78 %` grâce à ce flux. B6 ne change ni le catalogue ni la
structure des incidences ; il remplace uniquement le seuil d'extension par
quatre carrés sur quatre.

## 4. Validation croisée

### B1 et B2

B6 est comparé aux deux formulations entières historiques sur le même catalogue
canonique :

| Borne | B1 | B2 | B6 | Concordance |
| ---: | ---: | ---: | ---: | --- |
| 30 | 0 | 0 | 0 | exacte |
| 127 | 0 | 0 | 0 | exacte |
| 601 | 0 | 0 | 0 | exacte |

### v2.2 SAFE

L'oracle v2.2 de petite borne indexe toutes les paires opposées de carrés autour
de chaque centre, sans filtre heuristique, puis exécute ses chemins `exact8` et
`relaxed7` avant d'exiger neuf carrés :

| Borne complète | Classes B6 | Classes v2.2 | Concordance |
| ---: | ---: | ---: | --- |
| 127 | 0 | 0 | exacte |
| 601 | 0 | 0 | exacte |
| 1202 | 0 | 0 | exacte |

Les modes matériel et streaming B6 concordent en classes et en compteurs aux
bornes 127, 601 et 2000. La suite vérifie également que le témoin de Bremner est
rejeté, puisqu'il ne possède que sept cases carrées.

## 5. Profils à R=100000

Deux passages non instrumentés archivés donnent :

| Mode | Temps bout-en-bout | Couples compatibles | Tests de carré | Classes |
| --- | ---: | ---: | ---: | ---: |
| Matériel | 4,807218 s | 686206 | 1749088 | 0 |
| Streaming, 128 tranches | 5,143709 s | 686206 | 1749088 | 0 |

Il s'agit de profils diagnostiques individuels, et non d'un benchmark apparié
multi-répétition.

Artefacts :
`results/formulations_comparison/benchmarks/lo_shu_b6_material_r100000.json` et
`lo_shu_b6_streaming_r100000.json` dans le même dossier.

## 6. Campagne complète à R=1000000

Le run final utilise 512 tranches :

| Compteur | Valeur |
| --- | ---: |
| Progressions canoniques | 1517296 |
| Incidences | 4551888 |
| Valeurs carrées indexées | 880631 |
| Valeurs partagées | 660293 |
| Couples théoriques | 49800462 |
| Rejets PGCD combinatoires | 39771172 |
| Couples compatibles reconstruits | 10029290 |
| Tests de carré sur les extensions | 25807672 |
| Rejets faute de quatre extensions carrées | 6451918 |
| Candidats 9/9 validés | 0 |
| Classes primitives D4 | 0 |

Le temps bout-en-bout est `65,036925 s`. Aucun couple compatible n'atteint le
validateur final avec neuf cases carrées.

Artefact :
`results/formulations_comparison/benchmarks/lo_shu_b6_exact9_r1000000.json`.

## 7. Utilisation

```powershell
python experiments\formulations_comparison\search_lo_shu_nine.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512
```

Le mode matériel reste le défaut aux petites bornes. `--all-scalings` désactive
le rejet précoce par PGCD, principalement pour les contrôles de dilatation.

## 8. Limites et optimisation réalisée

La borne `R=1000000` signifie que chaque case est au plus `10^12`. Elle est
commune aux neuf valeurs finales et ne doit pas être confondue avec une borne de
centre ou une hauteur elliptique.

La table Python des `R` carrés a depuis été remplacée par défaut par un test
`isqrt` direct à mémoire indépendante de `R`. Une variante à résidus a aussi été
évaluée. La preuve d'exactitude, le compromis temps/mémoire et le nouveau run
au million sont documentés dans
[31-square-membership-residue-isqrt.md](31-square-membership-residue-isqrt.md).

## Mise à jour B8

B6 ne trouve toujours aucune classe 9/9 à `R=1000000`. Le test `isqrt` vectorisé réduit le temps streaming de `65,036925 s` à `54,279316 s` (`−16,541 %`). Artefact : `results/formulations_comparison/benchmarks/lo_shu_b6_exact9_batched_isqrt_r1000000.json`.

Profil et méthode : [32-batched-square-membership.md](32-batched-square-membership.md).

## Mise à jour B11

La campagne historique ci-dessus utilise 512 shards. Le balayage B11 recommande
désormais 256 shards vers `R=1000000`. B6 conserve le même résultat et
les mêmes compteurs en `32,072967 s`.

Artefact : `results/formulations_comparison/benchmarks/lo_shu_b6_exact9_shards256_r1000000.json`.

Méthode : [35-incidence-shard-tradeoff.md](35-incidence-shard-tradeoff.md).
