# B4 — Toutes les orbites Lo Shu exactement 7/9

_Implémentation, validation et campagne exécutées le 18 juillet 2026._

## 1. Résultat

La branche B4 étend le scanner B3 du seul masque de Bremner aux 36 masques
possédant exactement sept cases carrées. Ces masques forment huit orbites sous
les symétries D4 du carré.

Dans la boîte complète

```text
0 < chaque case <= R²,    R = 1000000,
```

B4 ne trouve qu'une classe primitive, positive et à neuf valeurs distinctes :
la classe historique de Bremner. Elle appartient à l'orbite où une case de coin
et une case de bord non incidente sont non carrées.

Ce résultat couvre toutes les orbites exactement 7/9, contrairement à B3 qui
ne couvre que l'orbite et l'orientation ciblées de Bremner.

## 2. Les huit orbites

Les lettres désignent les positions

```text
a b c
d e f
g h i
```

| Orbite | Cases non carrées représentatives | Masque représentatif | Taille D4 | Croisements complets |
| --- | --- | --- | ---: | ---: |
| `center_corner` | `ae` | `bcdfghi` | 4 | 2 |
| `center_edge` | `be` | `acdfghi` | 4 | 1 |
| `corner_corner_adjacent` | `ac` | `bdefghi` | 4 | 1 |
| `corner_corner_opposite` | `ai` | `bcdefgh` | 2 | 2 |
| `edge_edge_adjacent` | `bd` | `acefghi` | 4 | 2 |
| `edge_edge_opposite` | `bh` | `acdefgi` | 2 | 1 |
| `corner_edge_incident` | `ab` | `cdefghi` | 8 | 1 |
| `corner_edge_nonincident` | `af` | `bcdeghi` | 8 | 2 |

Les tailles totalisent bien les `C(9,2)=36` choix. Le masque de l'orientation B3
`acdefgh`, dont les cases non carrées sont `b` et `i`, appartient à la dernière
orbite.

## 3. Forme additive générale

Après une symétrie D4, tout carré magique 3×3 à valeurs distinctes peut être
écrit avec `q>0` et `r>0` sous la forme

```text
 B       C+2r    A+r
 A+2r    B+r     C
 C+r     A       B+2r,
```

où

```text
B = A+q,    C = A+2q.
```

Les neuf valeurs sont donc les sommes

```text
T(x,k) = A + xq + kr,    x,k dans {0,1,2}.
```

Dans les coordonnées paramétriques, leurs positions sont

```text
          k=0  k=1  k=2
x=0        h    c    d
x=1        a    e    i
x=2        f    g    b
```

Chaque ligne en `k` est une progression de raison `r`, et chaque colonne en
`x` une progression de raison `q`.

## 4. Preuve de couverture de la jointure

Un masque exactement 7/9 retire deux cases de cette grille paramétrique 3×3.
Deux cases peuvent toucher au plus deux de ses trois lignes ; il reste donc une
ligne complète. Le même argument laisse au moins une colonne complète. Leur
intersection est elle-même une des sept cases carrées.

Toute solution contient ainsi :

- une progression de trois carrés de raison `r` ;
- une progression de trois carrés de raison `q` ;
- une valeur carrée commune aux deux progressions.

B4 indexe chacune des trois valeurs de chaque progression canonique, joint deux
progressions sur une valeur commune, retrouve les indices `(x,k)` de leur
intersection puis calcule

```text
A = valeur_commune - xq - kr.
```

Les quatre cases extérieures au croisement sont ensuite testées. Exactement deux
d'entre elles doivent être carrées. Le validateur indépendant recalcule les huit
sommes magiques, le masque exact, la positivité, la distinction, la primitivité
des sept racines et la classe D4.

Le catalogue paramétrique canonique énumère toutes les progressions de trois
carrés dont les racines sont bornées par `R`. Comme les neuf cases finales sont
bornées par `R²`, aucune progression carrée nécessaire ne se trouve hors du
catalogue. La jointure est donc exhaustive dans la boîte complète annoncée.

## 5. Index PGCD

Les deux progressions graines fournissent cinq cases carrées distinctes. Si le
PGCD de leurs cinq racines vaut `g>1`, leurs valeurs et les différences `q,r`
sont divisibles par `g²`. Les neuf valeurs reconstruites le sont alors aussi ;
toute case carrée supplémentaire a une racine divisible par `g`.

B4 reprend donc l'index de compatibilité PGCD de B3 et ne matérialise que les
couples de seaux dont les PGCD sont premiers entre eux.

## 6. Validation contre v2.2 SAFE

L'oracle de contrôle génère, sans sélection heuristique, toutes les paires de
carrés opposées autour de chaque centre entier, carré ou non carré. Il applique
ensuite la recombinaison `relaxed7` de v2.2 SAFE et le même validateur final.

| Borne complète | Classes B4 | Classes v2.2 | Concordance |
| ---: | ---: | ---: | --- |
| 127 | 0 | 0 | exacte |
| 601 | 1 | 1 | exacte |
| 1202 | 1 | 1 | exacte |

À `R=1202`, v2.2 rencontre également la dilatation par deux de Bremner, puis la
rejette comme non primitive. Les deux moteurs conservent la même classe.

La régression combinatoire vérifie en plus, pour chacun des 36 masques, la
présence d'au moins un croisement ligne-colonne entièrement carré.

## 7. Coût de la couverture générale à R=100000

Sur le même catalogue canonique de 122640 progressions, cinq répétitions
alternées donnent :

| Moteur | Portée | Médiane du cœur | Pic Python incrémental | Classes |
| --- | --- | ---: | ---: | ---: |
| B3 | masque Bremner ciblé | 0,353836 s | 17,1 Mo | 1 |
| B4 matériel | 36 masques, 8 orbites | 3,638062 s | 64,6 Mo | 1 |

Le facteur temporel `10,28×` mesure le prix de la couverture générale ; il ne
compare pas deux moteurs de même portée.

Artefact :
`results/formulations_comparison/benchmarks/lo_shu_b4_vs_b3_r100000.json`.

## 8. Flux d'incidences

Le mode matériel conserve simultanément le catalogue et les trois incidences de
chaque progression. Le mode streaming écrit ces incidences dans des tranches
binaires classées par racine partagée, puis ne charge qu'une tranche à la fois.

Le benchmark bout-en-bout à `R=100000`, avec 128 tranches et quatre répétitions,
donne :

| Variante B4 | Médiane | Pic Python | Évolution mémoire |
| --- | ---: | ---: | ---: |
| Matérielle | 3,896174 s | 94,0 Mo | référence |
| Streaming | 4,983201 s | 9,6 Mo | `−89,78 %` |

Le coût temporel du streaming est `+27,9 %`. Les deux variantes ont exactement
les mêmes classes et tous leurs compteurs déterministes sont identiques.

Artefact :
`results/formulations_comparison/benchmarks/lo_shu_b4_streaming_r100000.json`.

## 9. Campagne complète à R=1000000

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
| Candidats exacts 7/9 avant quotient D4 | 4 |
| Classes primitives D4 | 1 |

Le temps bout-en-bout est `64,286310 s`. Les quatre candidats exacts sont quatre
reconstructions de la même classe de Bremner. Les sept autres orbites ne
contiennent aucune classe primitive dans la boîte.

Artefact :
`results/formulations_comparison/benchmarks/lo_shu_b4_all_masks_r1000000.json`.

## 10. Utilisation

À petite ou moyenne borne, le mode matériel est le défaut :

```powershell
python experiments\formulations_comparison\search_lo_shu_seven.py `
  --complete-box-root 100000
```

Pour les grandes bornes :

```powershell
python experiments\formulations_comparison\search_lo_shu_seven.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512
```

L'option `--all-scalings` désactive le rejet des dilatations non primitives.

## 11. Limites et suite

Le résultat est exhaustif pour les carrés magiques 3×3 pleinement magiques,
entiers, positifs, distincts et exactement 7/9 dans la boîte finale annoncée.
Il ne résout pas le problème 9/9 et ne constitue pas une preuve d'unicité de
Bremner au-delà de la borne.

La prochaine optimisation possible est de remplacer l'ensemble Python des
`R` carrés bornés par un test entier ou un filtre résiduel lorsque `R` devient
beaucoup plus grand. Sur le plan scientifique, la prochaine extension naturelle
est le seuil exactement 8/9, où une seule case non carrée laisse encore deux
directions paramétriques complètes mais impose trois carrés supplémentaires au
lieu de deux.

## Mise à jour B8

B4 retrouve toujours uniquement la classe de Bremner à `R=1000000`. Le comptage `isqrt` par lot réduit le temps streaming de `64,286310 s` à `53,876882 s` (`−16,192 %`). Artefact : `results/formulations_comparison/benchmarks/lo_shu_b4_all_masks_batched_isqrt_r1000000.json`.

Profil et méthode : [32-batched-square-membership.md](32-batched-square-membership.md).
