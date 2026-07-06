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

