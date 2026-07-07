# Résumé expérimental

Ce dossier documente plusieurs branches de recherche autour du problème des carrés magiques 3×3 composés de carrés parfaits.

Le problème classique consiste à trouver un carré magique 3×3 dont les neuf entrées sont des carrés parfaits distincts. Aucun exemple complet à 9 carrés n’est connu à ce jour.

Le meilleur exemple connu dans cette recherche est le carré de Bremner, contenant 7 carrés sur 9.

## Carré de Bremner retrouvé

Dans l’orientation utilisée dans plusieurs scripts, le carré de Bremner est :

```text
373² | 360721 | 205²
289² | 425²   | 527²
565² | 23²    | 222121
````

Sa somme magique est :

```text
541875
```

Il contient 7 carrés parfaits sur 9.

## Branche A — Centre carré et progressions de carrés

Script principal :

```text
src/search_magic_square_of_squares_v4.py
```

Cette branche impose un centre carré :

```text
e = z²
```

et construit les candidats à partir de progressions arithmétiques de carrés autour du centre.

Résultats principaux :

| Recherche |                   Borne | Filtre   |               Résultat |
| --------- | ----------------------: | -------- | ---------------------: |
| 7/9       |         `z ≤ 3 000 000` | primitif |           Bremner seul |
| 8/9       |        `z ≤ 10 000 000` | primitif |                  aucun |
| 9/9       | inclus dans le test 8/9 | primitif | aucun dans cette borne |

La borne maximale atteinte pour le test 8/9 correspond à :

```text
e = z² ≤ 10¹⁴
```

## Branche B — Centre non nécessairement carré

Script principal :

```text
src/search_magic_square_of_squares_v5_non_square_center.py
```

Cette branche cherche des carrés magiques 3×3 avec huit cases extérieures carrées et un centre entier non nécessairement carré.

Résultats principaux :

|                        Borne | Paires générées | Centres rencontrés | Centres candidats | Couples testés |  Résultat |
| ---------------------------: | --------------: | -----------------: | ----------------: | -------------: | --------: |
| racines extérieures ≤ 10 000 |      24 995 000 |         13 256 086 |         1 676 050 |     35 224 376 | aucun 8/9 |
| racines extérieures ≤ 20 000 |      99 990 000 |         51 153 080 |         7 198 712 |    161 942 106 | aucun 8/9 |

La branche est figée provisoirement à `max_outer_root = 20 000`, car la version actuelle devient fortement limitée par la mémoire.

## Branche C — Centre carré et quatre coins carrés

Script principal :

```text
src/search_magic_square_corner_squares.py
```

Cette branche impose que les cases suivantes soient des carrés parfaits :

```text
a, c, e, h, j
```

Autrement dit, le centre et les quatre coins sont carrés.

Résultats principaux :

|        Borne | Paires `(A,J)` | Centres concernés | Configurations valides | Meilleur résultat |
| -----------: | -------------: | ----------------: | ---------------------: | ----------------: |
| `E ≤ 20 000` |         27 175 |            13 211 |                    179 |               6/9 |
| `E ≤ 60 000` |         91 967 |            40 891 |                    614 |               6/9 |

Aucun candidat 7/9 ou 8/9 n’a été trouvé dans cette famille jusqu’à `E ≤ 60 000`.

## Branche D — Recherche relâchée à une seule progression de carrés

Script principal :

```text
src/magic_square_relaxed_search.py
```

Cette branche fixe seulement une progression de carrés autour du centre :

```text
A², E², J²
```

puis balaie librement le paramètre `q`.

Test effectué :

```bash
python src/magic_square_relaxed_search.py --limit 10000 --qmax 300000 --min-total 7 --out results/best.csv
```

Résultat :

| Paramètres                       |        Résultat |
| -------------------------------- | --------------: |
| `limit = 10000`, `qmax = 300000` | 2 candidats 7/9 |

Les deux candidats sont :

```text
k = 1 : carré de Bremner
k = 2 : dilatation de Bremner par 2²
```

Aucun candidat 8/9 n’a été trouvé dans ce test.

Cette branche sert surtout de contrôle : elle retrouve bien le carré de Bremner et son multiple attendu.

## Branche E — Semi-magique avec centre zéro

Script principal :

```text
src/search_semimagic_e0_squares.py
```

Cette branche sort du cadre du carré magique complet et explore les carrés semi-magiques 3×3 avec centre :

```text
e = 0
```

Forme utilisée :

```text
A²        H² + J²      C²
C² + J²   0            A² + H²
H²        A² + C²      J²
```

Exemple obtenu :

```text
15² | 60² | 20²
52² | 0   | 39²
36² | 25² | 48²
```

Somme commune :

```text
4225 = 65²
```

Cette branche produit facilement des semi-magiques avec huit carrés positifs autour du centre zéro, mais elle ne résout pas le problème classique des carrés magiques complets.

## Synthèse générale

Les recherches menées dans ce dossier n’ont produit aucun nouveau carré magique 3×3 améliorant le record connu de 7 carrés sur 9.

Elles ont cependant permis de documenter plusieurs familles :

| Branche | Famille explorée                                             |             Meilleur résultat |
| ------- | ------------------------------------------------------------ | ----------------------------: |
| A       | centre carré, progressions de carrés                         |                   Bremner 7/9 |
| B       | centre non nécessairement carré, 8 cases extérieures carrées |                     aucun 8/9 |
| C       | centre carré et quatre coins carrés                          |                           6/9 |
| D       | recherche relâchée à une progression                         |        Bremner 7/9 + multiple |
| E       | semi-magique centre zéro                                     | 8 carrés positifs autour de 0 |

Ces résultats sont expérimentaux, bornés et reproductibles à partir des scripts fournis.


