# Branch C corner-square-family 

On  ouvre ici en fait une troisième branche, différente de la v4 et de la v5.

Ce n’est pas exactement la branche “centre non carré”. Ici, on impose :

```text
a, c, e, h, j carrés
````
Donc on explore la famille :

```text
coin carré | ?      | coin carré
?          | carré  | ?
coin carré | ?      | coin carré
````
Autrement dit : centre carré + quatre coins carrés. Les quatre cases restantes b, d, f, i sont ensuite testées.

Le résultat obtenu est :

```text
E ≤ 20 000
27 175 progressions arithmétiques de carrés trouvées
13 211 centres E concernés
179 configurations valides
meilleur résultat : 6 carrés sur 9
aucun 7/9
aucun 8/9
````

Donc cette branche ne retrouve pas Bremner, et c’est normal : dans le carré de Bremner, les quatre coins ne sont pas tous des carrés. Dans notre orientation précédente, la case j = 222121 n’est pas carrée.

## Interprétation du meilleur résultat

Le premier résultat affiché est :

```text
455²   | 1426681 | 713²
1015369| 845²    | 412681
959²   | 37²     | 1105²
````
Il contient bien 6 carrés :
```text
455², 713², 845², 959², 37², 1105²
````

Les trois cases non carrées sont :
```text
1426681
1015369
412681
````

Donc c’est un 6/9, pas un concurrent de Bremner.

## Point important

Cette branche est plus restrictive que v4 sur certains aspects, car elle exige que les **deux diagonales** soient composées de carrés 

Alors que Bremner n’a qu’une diagonale entièrement carrée dans l’orientation que nous utilisons.

## conclusion

la conclusion correcte ici est :

> Dans la famille des carrés magiques 3×3 à centre carré et quatre coins carrés, aucun candidat à 7 carrés ou plus n’a été trouvé jusqu’à (E \leq 20,000). Le meilleur résultat observé contient 6 carrés sur 9.

