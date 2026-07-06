# Stratégie de recherche v4

La recherche génère les progressions arithmétiques de carrés :

```text
x², z², y²
````

avec :

```text
x² + y² = 2z²
```

Ces progressions sont générées via les triplets pythagoriciens.

Ensuite, deux progressions autour du même centre sont combinées pour construire un carré magique 3×3 candidat.

Le script compte ensuite combien d’entrées sont des carrés parfaits.