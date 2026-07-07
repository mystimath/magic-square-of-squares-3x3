# Status

## Branche A — centre carré

Script principal :

```text
src/search_magic_square_of_squares_v4.py
````

Résultat actuel :

| Recherche    |                    Borne |               Résultat |
| ------------ | -----------------------: | ---------------------: |
| 7/9 primitif |  center_root ≤ 3 000 000 |           Bremner seul |
| 8/9 primitif | center_root ≤ 10 000 000 |                  aucun |
| 9/9 primitif |  inclus dans le test 8/9 | aucun dans cette borne |




## Branche B — centre non nécessairement carré

Script :

```text
src/search_magic_square_of_squares_v5_non_square_center.py
````

Résultat actuel :

|                        Borne |  Résultat |
| ---------------------------: | --------: |
| racines extérieures ≤ 10 000 | aucun 8/9 |
| racines extérieures ≤ 20 000 | aucun 8/9 |

La branche est figée provisoirement à 20 000, car la version actuelle devient fortement limitée par la mémoire.

## Branche C — centre carré et quatre coins carrés

Cette branche impose que les quatre coins et le centre soient des carrés parfaits :

```text
a, c, e, h, j carrés
```

Les quatre autres cases b, d, f, i sont ensuite testées.

Résultat actuel :
|      Borne |                Résultat |
| ---------: | ----------------------: |
| E ≤ 20 000 | meilleur résultat : 6/9 |
| E ≤ 20 000 |               aucun 7/9 |
| E ≤ 20 000 |               aucun 8/9 |


**Résultats -test 2 :**

| Borne | Configurations | Meilleur résultat |
|---:|---:|---:|
| E ≤ 20 000 | 179 | 6/9 |
| E ≤ 60 000 | 614 | 6/9 |

Aucun 7/9 ou 8/9 trouvé dans cette famille.

**Résumé test 2:**

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

La répartition des carrés bonus parmi b, d, f, i est intéressante :
```text
i carré : 354 cas
f carré : 165 cas
d carré : 78 cas
b carré : 17 cas
```

Donc la case i = a + c - e est de loin celle qui devient le plus souvent carrée dans cette famille.

### Point important : beaucoup de multiples triviaux

Sur les 614 résultats, seulement 75 ont un facteur carré commun égal à 1.

Les 539 autres ont un facteur carré commun supérieur à 1, donc ce sont probablement des dilatations de configurations plus petites.

## Conclusion de la branche C


> Dans la famille des carrés magiques 3×3 où le centre et les quatre coins sont imposés carrés, la recherche jusqu’à E≤60000 donne 614 configurations valides, toutes avec exactement 6 carrés sur 9. Aucun carré à 7/9 ou 8/9 n’a été trouvé dans cette famille.

C’est une bonne branche négative supplémentaire.