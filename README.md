# 3x3 Magic Square of Squares

Recherche expérimentale autour du problème ouvert des carrés magiques 3×3 composés de carrés parfaits.

Ce dossier documente une branche de recherche basée sur les carrés magiques 3×3 à centre carré, construits à partir de progressions arithmétiques de carrés autour du centre.

## Résultat principal de cette branche

- Borne testée : center_root ≤ 10 000 000
- Centre maximal : e ≤ 10¹⁴
- Filtre : solutions primitives uniquement, sans dilatation triviale par facteur carré commun
- Résultat 8/9 : aucun candidat trouvé
- Résultat 7/9 : le carré connu de Bremner est retrouvé

## Carré de Bremner retrouvé

```text
373² | 360721 | 205²
289² | 425²   | 527²
565² | 23²    | 222121
````

Somme magique : 541875

## Avertissement

Ces résultats ne constituent pas une preuve d’impossibilité générale.
Ils documentent une recherche exhaustive dans une famille structurée précise.

