# Résultats expérimentaux

## Recherche 7/9 primitive

Commande :

```bash
python src/search_magic_square_of_squares_v4.py --max-center-root 3000000 --min-squares 7 --primitive-only --progress 100000 --csv results/results_7_3000000_primitive.csv
````

Résultat :

```text
1 résultat : le carré de Bremner
```

## Recherche 8/9 primitive

Commande :

```bash
python src/search_magic_square_of_squares_v4.py --max-center-root 10000000 --min-squares 8 --primitive-only --progress 250000 --csv results/results_8_10000000_primitive.csv
```

Résultat :

```text
0 résultat
```

## Conclusion expérimentale

Aucun carré magique 3×3 primitif avec au moins 8 entrées carrées n’a été trouvé dans cette famille jusqu’à :

```text
e ≤ 10¹⁴
```
