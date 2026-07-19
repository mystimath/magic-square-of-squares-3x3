# B5 — Toutes les orbites Lo Shu exactement 8/9

_Implémentation, validation et campagne exécutées le 18 juillet 2026._

## 1. Résultat

B5 cherche les carrés magiques 3×3 pleinement magiques, entiers, strictement
positifs, à neuf valeurs distinctes, dont exactement huit cases sont des carrés
parfaits. Il quotient les solutions par D4 et ne conserve par défaut que les
classes primitives.

Dans la boîte complète

```text
0 < chaque case <= R²,    R = 1000000,
```

B5 ne trouve aucune classe exactement 8/9.

Ce résultat est distinct d'une recherche `>=8/9` : une éventuelle grille 9/9
est volontairement rejetée par le test de masque exact.

## 2. Les trois orbites

Une seule case est non carrée. Sous les symétries D4, sa position possède trois
types possibles :

| Orbite | Case non carrée représentative | Masque représentatif | Taille D4 | Croisements complets |
| --- | --- | --- | ---: | ---: |
| `center` | `e` | `abcdfghi` | 1 | 4 |
| `corner` | `a` | `bcdefghi` | 4 | 4 |
| `edge` | `b` | `acdefghi` | 4 | 4 |

Les tailles totalisent les neuf positions possibles.

## 3. Couverture par la grille paramétrique

Comme dans B4, une symétrie D4 permet d'écrire toute grille distincte avec
`q>0`, `r>0` et

```text
T(x,k) = A + xq + kr,    x,k dans {0,1,2}.
```

Les coordonnées paramétriques correspondent aux positions

```text
          k=0  k=1  k=2
x=0        h    c    d
x=1        a    e    i
x=2        f    g    b.
```

Retirer une seule case laisse deux lignes complètes et deux colonnes complètes,
donc quatre croisements possibles. Chaque solution 8/9 contient ainsi au moins
une progression de trois carrés dans chaque direction, avec une valeur carrée
commune.

B5 joint ces progressions sur leur incidence commune, reconstruit `A,q,r`, puis
teste les quatre cases hors du croisement. Cinq cases carrées sont déjà connues ;
exactement trois des quatre restantes doivent être carrées. Si les quatre le
sont, la grille est 9/9 et n'appartient pas au domaine exact de B5.

Le catalogue canonique est complet pour toutes les progressions dont les
racines sont au plus `R`. La validation finale impose la boîte sur les neuf
valeurs. Le même argument de couverture que pour B4 établit donc l'exhaustivité
de B5 dans la boîte complète annoncée.

## 4. PGCD et streaming partagés avec B4

Les cinq racines des deux progressions graines sont indexées par leur PGCD. Un
couple de graines dont les PGCD ne sont pas premiers entre eux ne peut produire
une classe primitive et est rejeté combinatoirement.

Le flux binaire est exactement celui de B4 : chaque progression canonique écrit
trois incidences, distribuées par racine partagée. Une seule tranche est chargée
à la fois. Le benchmark B4 du même index à `R=100000` a mesuré un pic Python de
9,6 Mo en streaming contre 94,0 Mo pour l'index matériel (`−89,78 %`). B5 ne
modifie que le nombre de carrés exigé parmi les quatre extensions.

Les profils non instrumentés archivés à `R=100000` donnent 4,591652 s en mode matériel et
5,132885 s en streaming, avec les mêmes 686206 couples compatibles et 1749088
tests de carré. Ces deux temps sont des passages diagnostiques, pas un benchmark
apparié multi-répétition. Artefacts :
`lo_shu_b5_material_r100000.json` et `lo_shu_b5_streaming_r100000.json`
dans `results/formulations_comparison/benchmarks/`.

## 5. Validation indépendante contre v2.2 SAFE

L'oracle de petite borne génère toutes les paires opposées de carrés autour de
chaque centre entier, carré ou non carré, sans filtre de richesse. Il exécute à
la fois les recombinaisons `exact8` et `relaxed7` de v2.2, puis applique le
validateur indépendant et le quotient D4.

| Borne complète | Classes B5 | Classes v2.2 | Concordance |
| ---: | ---: | ---: | --- |
| 127 | 0 | 0 | exacte |
| 601 | 0 | 0 | exacte |
| 1202 | 0 | 0 | exacte |

Une seconde régression vérifie les neuf masques : chacun possède exactement
quatre croisements complets. Les modes matériel et streaming concordent en
classes et en compteurs aux bornes 127, 601 et 2000.

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
| Rejets faute d'exactement huit carrés | 6451918 |
| Candidats exacts 8/9 | 0 |
| Classes primitives D4 | 0 |

Le temps bout-en-bout est `63,756097 s`. Aucun des trois types de position non
carrée — centre, coin ou bord — ne produit de classe dans la boîte.

Artefact :
`results/formulations_comparison/benchmarks/lo_shu_b5_all_masks_r1000000.json`.

## 7. Utilisation

```powershell
python experiments\formulations_comparison\search_lo_shu_eight.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512
```

Le mode matériel reste le défaut aux petites bornes. `--all-scalings` désactive
le rejet précoce des dilatations non primitives.

## 8. Limites et suite

Le résultat est exhaustif pour exactement 8/9 dans la boîte finale définie. Il
ne prouve aucune impossibilité au-delà de `R=1000000` et ne couvre pas 9/9.

La même jointure permet un scanner B6 exact 9/9 en exigeant que les quatre cases
restantes soient carrées. Cette extension recouperait alors directement les
moteurs généraux A/B du problème principal, avec B5 et B4 comme contrôles de
non-régression aux seuils voisins.

## Mise à jour B8

B5 ne trouve toujours aucune classe exactement 8/9 à `R=1000000`. Le comptage `isqrt` par lot réduit le temps streaming de `63,756097 s` à `53,688051 s` (`−15,792 %`). Artefact : `results/formulations_comparison/benchmarks/lo_shu_b5_all_masks_batched_isqrt_r1000000.json`.

Profil et méthode : [32-batched-square-membership.md](32-batched-square-membership.md).

## Mise à jour B11

La campagne historique ci-dessus utilise 512 shards. Le balayage B11 recommande
désormais 256 shards vers `R=1000000`. B5 conserve le même résultat et
les mêmes compteurs en `31,866563 s`.

Artefact : `results/formulations_comparison/benchmarks/lo_shu_b5_all_masks_shards256_r1000000.json`.

Méthode : [35-incidence-shard-tradeoff.md](35-incidence-shard-tradeoff.md).
