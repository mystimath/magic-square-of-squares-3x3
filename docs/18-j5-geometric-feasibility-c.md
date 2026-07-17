# J5 — Faisabilité géométrique de la formulation C

_Jalon exécuté le 16 juillet 2026. Domaine expérimental limité aux petites
bornes entières `R=10` à `200`._

## 1. Question étudiée

J2 établit une bijection entre une progression de trois carrés rationnels et
un triangle rectangle rationnel dont l'aire égale la différence de la
progression. J5 vérifie si cette traduction :

- reste exacte dans une implémentation à fractions ;
- normalise correctement signes, échange des jambes et similitudes ;
- permet de retrouver le prototype B2 par groupement d'aires ;
- réduit le nombre d'objets ou le volume de représentation ;
- mérite un moteur autonome avant les benchmarks.

## 2. Livrables

```text
experiments/formulations_comparison/prototypes/formulation_c.py
experiments/formulations_comparison/tests/test_formulation_c.py
```

Le module fournit :

- `RationalTriangle` avec côtés `Fraction`, jambes ordonnées et contrôle exact
  de Pythagore ;
- `RationalSquareProgression` ;
- `progression_to_triangle` ;
- `triangle_to_progression` ;
- une clé de similitude indépendante de l'échelle ;
- `search_formulation_c`, groupé par aire exacte et validé par J3.

## 3. Correspondance implémentée

Pour

```text
u², v², w²,   v²-u²=w²-v²=n,
```

le triangle est

```text
(w-u, w+u, 2v),   aire=n.
```

L'inverse, pour les jambes ordonnées `a<=b` et l'hypoténuse `c`, est

```text
u=(b-a)/2, v=c/2, w=(a+b)/2.
```

Toutes les opérations sont effectuées avec `fractions.Fraction`. Aucune
comparaison flottante n'intervient.

## 4. Normalisation et doublons

Le constructeur impose :

- trois côtés strictement positifs ;
- ordre canonique des jambes ;
- identité pythagoricienne exacte.

La clé de similitude divise les trois côtés par la plus petite jambe. Elle
identifie donc `(3,4,5)` et `(6,8,10)`. Ces triangles ne sont cependant pas
interchangeables dans la recherche par aire : leurs aires sont 6 et 24.

Réduire globalement par similitude détruirait l'information d'échelle qui est
précisément la différence commune `n`. Dans un groupe d'aire fixé, deux
triangles semblables positifs ont déjà la même échelle ; la normalisation ne
fournit donc pas de réduction supplémentaire exploitable.

## 5. Contrôles exacts

### Entier

```text
1,25,49 ↔ (6,8,10), aire 24.
```

### Rationnel

```text
(3,4,5), aire 6 ↔ racines (1/2,5/2,7/2).
```

La conversion aller-retour restitue exactement les objets initiaux. Les
triangles non rectangles ou dégénérés sont rejetés.

## 6. Prototype de recherche par aire

Le prototype C utilise le même domaine final entier que B2 : racines des
progressions au plus `R`. Chaque progression devient un triangle, puis les
triangles sont groupés par aire. Dans chaque groupe, le programme cherche trois
carrés d'hypoténuses en progression.

Comme `hypoténuse²=4v²`, cette recherche est exactement celle des carrés
centraux de B2, avec un facteur 4 commun. Chaque candidat reconstruit passe par
le validateur J3.

Aux bornes complètes `R=10`, `20`, `30` et `50`, C et B2 produisent les mêmes
ensembles canoniques finaux : zéro classe 9/9. Ils indexent aussi le même nombre
d'objets intermédiaires.

## 7. Tests

La suite J5 ajoute cinq tests :

- progression entière vers `(6,8,10)` ;
- aller-retour rationnel exact de `(3,4,5)` ;
- échange des jambes et similitude ;
- rejet des triangles invalides ou dégénérés ;
- accord C–B2 aux quatre petites bornes.

Résultat global :

```text
Ran 23 tests in 0.054s
OK
```

## 8. Surcoût de représentation

Les tailles suivantes sont celles d'un JSON UTF-8 déterministe sans espaces.
Elles comparent :

- B2 compact : `(u,v,w,n)` ;
- C entier compact : `(a,b,c,aire)` ;
- C rationnel sûr : chaque quantité stockée comme `(numérateur,dénominateur)`.

| R | Progressions = triangles | Groupes différence = aire | Classes de similitude | B2 compact | C entier compact | C rationnel sûr |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 15 | 14 | 7 | 213 octets | 223 octets | 463 octets |
| 100 | 37 | 35 | 12 | 562 octets | 605 octets | 1 197 octets |
| 200 | 88 | 82 | 25 | 1 491 octets | 1 569 octets | 2 977 octets |

Constats dans ces bornes :

- la transformation crée exactement un triangle par progression ;
- le nombre de groupes d'aire est exactement le nombre de groupes de
  différence ;
- le format entier C coûte légèrement plus que B2 ;
- le format rationnel générique coûte environ deux fois le format B2 compact ;
- les classes de similitude sont moins nombreuses, mais ne peuvent pas être
  fusionnées sans perdre l'aire et la borne entière.

Ces mesures portent sur la représentation, pas sur une performance temporelle
générale. Elles ne constituent pas J7.

## 9. Porte G3 : moteur ou interprétation ?

### Décision

À ce stade, C doit rester une **interprétation géométrique et une voie de
validation**, pas devenir le moteur exhaustif principal.

### Motifs

1. C ne réduit ni le nombre d'objets ni le nombre de groupes par rapport à B2.
2. La gestion rationnelle ajoute numérateurs, dénominateurs et normalisation.
3. La similitude ne peut pas éliminer les changements d'échelle utiles sans
   perdre l'aire commune.
4. La borne naturelle sur côtés ou dénominateurs n'est pas équivalente à la
   borne entière sur les racines finales.
5. La traduction offre néanmoins un contrôle mathématique indépendant des
   identités et une présentation géométrique claire.

Cette décision pourrait être révisée si un futur groupement géométrique évite
une génération coûteuse ou fournit un filtre nécessaire plus fort. Les données
de J5 ne montrent pas un tel avantage.

## 10. Limite d'indépendance actuelle

Le prototype C partage encore avec B2 le générateur entier de progressions.
Son accord final vérifie la conversion et le groupement par aire, mais ne
constitue pas une seconde énumération indépendante du catalogue initial. Une
validation indépendante réelle devrait générer les triangles rationnels sous
une normalisation propre, puis démontrer que sa borne couvre le même domaine.

## 11. Fin de J5

La faisabilité mathématique et logicielle de C est établie à petite échelle.
La porte G3 classe C comme interprétation et validateur secondaire. J6 et J7 ne
sont pas commencés. Aucun run moyen ou lourd, commit ou push n'a été effectué.
