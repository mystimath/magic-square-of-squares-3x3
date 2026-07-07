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

### Conclusion de la branche C


> Dans la famille des carrés magiques 3×3 où le centre et les quatre coins sont imposés carrés, la recherche jusqu’à E≤60000 donne 614 configurations valides, toutes avec exactement 6 carrés sur 9. Aucun carré à 7/9 ou 8/9 n’a été trouvé dans cette famille.

C’est une bonne branche négative supplémentaire.

## Branche D

Avec ce script relâché, **Bremner a été retrouvé très tôt**. La limite minimale est :

```bash
python magic_square_relaxed_search.py --limit 425 --qmax 41496 --min-total 7 --top 10
```

Je l’ai testé avec mon script : il retrouve bien une configuration `7/9` en moins d’une seconde, avec :

```text
A = 205
E = 425
J = 565
q = 41496
```

Ce script fixe une progression arithmétique de carrés autour du centre :

```text
A², E², J² = 205², 425², 565²
```

puis balaie `q` pour tester les 6 autres cases. C’est exactement la stratégie décrite dans ton script relâché. 

La configuration obtenue dans l’orientation du script est :

```text
565² | 23²     | 222121
289² | 425²    | 527²
373² | 360721  | 205²
```

Elle est bien équivalente au carré de Bremner, par rotation/symétrie :

```text
373² | 360721 | 205²
289² | 425²   | 527²
565² | 23²    | 222121
```

Donc les seuils critiques sont :

```text
--limit >= 425
--qmax  >= 41496
--min-total 7
```

Commande recommandée avec un peu de marge :

```bash
python magic_square_relaxed_search.py --limit 500 --qmax 50000 --min-total 7 --top 20 --out bremner_relaxed.csv
```

À retenir : avec `--limit 424`, Bremner est impossible à retrouver, car le centre est `425²`. Avec `--qmax 41495`, il est également impossible, car le bon paramètre est exactement `q = 41496`.

Ce nouveau script ne fait pas exactement le même balayage que la v4, mais pour l’objectif 7/9 ou 8/9 avec centre carré, il risque surtout de retrouver les mêmes familles, notamment Bremner et ses multiples.

Il fixe seulement une progression de carrés autour du centre :
```text
A², E², J²
```
puis il balaie librement q et teste les six autres valeurs :

```text
r+q
r-q
r+p+q
r+p-q
r-p+q
r-p-q
```
C’est donc plus large que la v4 au niveau du balayage brut, car q n’est plus obligé d’être lui-même un offset donnant directement une deuxième progression de carrés.

Mais il y a une nuance importante.

Dans un carré magique 3×3 à centre carré avec 7/9, il y a le centre carré + 6 cases extérieures carrées. Or les 8 cases extérieures sont organisées en 4 paires opposées autour du centre. Si seulement deux cases extérieures ne sont pas carrées, alors il reste forcément au moins deux paires opposées entièrement carrées.

Donc tout vrai candidat 7/9 avec centre carré devrait déjà appartenir à la famille couverte par la v4, qui imposait deux progressions de carrés autour du centre.

Pour 8/9, c’est encore plus fort : avec une seule case non carrée parmi les 8 extérieures, il reste au moins trois paires opposées entièrement carrées. Donc la v4 couvre naturellement cette zone aussi.

### Ce que ce script peut chercher hors v4

Il peut explorer des near-misses intéressants, par exemple des 5/9 ou 6/9, où une seule progression opposée est garantie et où les autres carrés apparaissent accidentellement.

Mais pour battre Bremner avec un 8/9 à centre carré, il n’apporte probablement pas une nouvelle zone conceptuelle par rapport à v4. Il est surtout une autre manière, plus brute, de retomber sur les mêmes structures.

Il ne couvre pas non plus :
```text
centre non carré
```
ni (semi-magique):
```text
centre = 0
```
ni des familles semi-magiques qu'on va tester dans la foulée dans le cadre ce projet.

#### Commandes utiles

Pour retrouver seulement Bremner :
```bash
python magic_square_relaxed_search.py --limit 425 --qmax 41496 --min-total 7
```
Avec une petite marge :
```bash
python magic_square_relaxed_search.py --limit 500 --qmax 50000 --min-total 7 --out bremner_relaxed.csv
```
Pour retrouver Bremner et ses multiples jusqu’à k = 5 :
```bash
python magic_square_relaxed_search.py --limit 2125 --qmax 1037400 --min-total 7 --out bremner_multiples_k5.csv
```

car :
```text
425 × 5 = 2125
41496 × 5² = 1 037 400
```

### Conclusion Branche D — contrainte relâchée à une seule progression de carrés
> Résultat test : limit=10000, qmax=300000

> Candidats 7/9 trouvés : Bremner et son multiple ×4

> Aucun 8/9


## Branche Semi-Magique

Avec (e=0), on peut exploiter une paramétrisation beaucoup plus simple que le script précédent basé sur (r,p,q). 

Si les quatre coins sont :

```text
A²      C²
H²      J²
```

alors le carré semi-magique complet est automatiquement :

```text
A²        H² + J²      C²
C² + J²   0            A² + H²
H²        A² + C²      J²
```

La somme magique vaut :

```text
S = A² + C² + H² + J²
```

Le script ci-dessous cherche donc des quadruplets `A, C, H, J` tels que les quatre sommes :

```text
H² + J²
C² + J²
A² + H²
A² + C²
```

soient elles aussi des carrés.
Dans ce cas, on obtient **8 carrés positifs sur 8**, avec centre `0`.

---



#### Commande de test :

```bash
python search_semimagic_e0_squares.py --max-root 100 --min-squares 7 --primitive-only --limit 10 --csv results_semimagic_e0.csv
```

On peut obtenir très vite un carré comme celui-ci :

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

Donc on a :

```text
8 carrés positifs sur 8 cases non nulles
```

ou, si on compte aussi `0 = 0²`, un semi-magique dégénéré à `9/9`.


### Les carrés semi-magique dans la littérature des carrés magiques

**Le genre général est bien présent dans la littérature**, mais notre variante précise avec **centre (e=0)** est plutôt une **sous-famille dégénérée / constructive**, pas le cœur du problème classique.

Il faut distinguer trois niveaux.

#### 1. Les carrés semi-magiques sont parfaitement documentés

Un carré semi-magique est classiquement un carré dont **les lignes et les colonnes** ont la même somme, mais pas nécessairement les diagonales. MathWorld donne exactement cette définition : un semi-magic square échoue à être magique seulement parce qu’une ou deux diagonales ne valent pas la constante magique. ([MathWorld][1])

Donc nos carrés avec (e=0) entrent bien dans la catégorie :

```text
semi-magiques 3×3
```

car les lignes et colonnes sont équilibrées.

#### 2. Les semi-magiques “de carrés” existent aussi dans la littérature

Plus intéressant : les **semi-magic squares of squares** sont eux aussi connus. Il existe même une famille attribuée à **Euler** : une page universitaire intitulée *Euler’s family of semi-magic squares of squares of order three* indique qu’Euler a publié en 1770 une famille de carrés semi-magiques d’ordre 3 composés de carrés rationnels, puis transformables en carrés d’entiers après multiplication. ([math.ru.nl][2])

Cette même source précise que Lucas a ensuite étudié le problème des carrés de carrés d’ordre 3 et que la famille d’Euler ne contient pas de vrai carré magique de carrés, c’est-à-dire pas de cas où les deux diagonales prennent aussi la somme magique. ([math.ru.nl][2])

Donc  : **semi-magique + entrées carrées** est un objet mathématique connu.

#### 3. Notre variante avec centre (0) est probablement une sous-famille particulière

Nos carrés ont une forme spéciale :

```text
A²        H² + J²      C²
C² + J²   0            A² + H²
H²        A² + C²      J²
```

La somme commune vaut :

```text
S = A² + C² + H² + J²
```

Et pour obtenir 8 carrés positifs autour de zéro, il faut que les quatre sommes :

```text
H² + J²
C² + J²
A² + H²
A² + C²
```

soient elles-mêmes des carrés. Autrement dit, on relie le problème à un réseau de relations pythagoriciennes. Le script qu’on a préparé cherche précisément ce type de structure : un carré semi-magique 3×3 avec centre nul, quatre coins carrés et quatre cases latérales qui deviennent carrées par sommes de deux carrés. 

C’est une approche naturelle, mais elle est **moins centrale dans la littérature classique**, pour deux raisons :

1. Le centre (0) rend le carré “dégénéré” si l’on cherche des carrés positifs distincts.
2. Le vrai problème célèbre demande un **carré magique complet**, donc avec les deux diagonales aussi égales à la somme magique. Le problème 3×3 complet reste ouvert, et l’exemple de Bremner à 7 carrés reste cité comme l’unique exemple connu dans certains défis publics. ([plus.maths.org][3])


Donc notre famille particulière avec centre (0), construite par sommes pythagoriciennes autour de quatre coins carrés, semble plutôt être une sous-famille constructive simple, utile pour l’exploration et la pédagogie, mais pas le cœur du problème historique des “magic squares of squares”.



[1]: https://mathworld.wolfram.com/SemimagicSquare.html "Semimagic Square -- from Wolfram MathWorld"
[2]: https://www.math.ru.nl/lo_shu_tot_sudoku/chapters/Euler%27s_family.pdf "Euler's family.dvi"
[3]: https://plus.maths.org/os/latestnews/may-aug10/magic/index "Win money with magic squares | plus.maths.org"


