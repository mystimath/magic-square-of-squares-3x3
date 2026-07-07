# Limites et précautions

Ce dossier contient des recherches expérimentales autour du problème des carrés magiques 3×3 de carrés.

Les résultats doivent être lus comme des résultats de calcul bornés, et non comme des preuves mathématiques générales.

## 1. Aucune preuve d’impossibilité

L’absence de résultat dans une branche donnée signifie seulement :

```text
aucun candidat trouvé dans la famille explorée,
avec les bornes et contraintes indiquées.
````

Cela ne prouve pas qu’un candidat n’existe pas en dehors de cette famille ou au-delà de la borne testée.

## 2. Différence entre carré magique et semi-magique

Un carré magique 3×3 doit satisfaire :

* les 3 lignes ;
* les 3 colonnes ;
* les 2 diagonales.

Un carré semi-magique ne contraint que :

* les 3 lignes ;
* les 3 colonnes.

La branche E avec centre zéro produit des carrés semi-magiques, mais ne constitue pas une solution au problème classique des carrés magiques de carrés.

## 3. Le centre zéro est dégénéré

Dans la branche E, le centre est fixé à :

```text
e = 0
```

Même si `0 = 0²`, il est préférable de compter uniquement les huit cases positives autour du centre.

Cela évite de présenter artificiellement un semi-magique comme un carré de neuf carrés positifs distincts.

## 4. Dilatations triviales

Si un carré est multiplié par un facteur carré commun :

```text
k²
```

alors toutes les cases carrées restent carrées.

Ces dilatations ne doivent pas être considérées comme de nouveaux exemples fondamentaux.

Exemple :

```text
Bremner × 4
```

est seulement une copie agrandie du carré de Bremner.

Les scripts utilisent donc, quand c’est pertinent, un filtre `primitive-only` ou un contrôle du facteur carré commun.

## 5. Bornes différentes selon les branches

Les branches ne mesurent pas toutes la même chose.

Dans la branche A, la borne porte sur :

```text
center_root = z
e = z²
```

Dans la branche B, la borne porte sur les racines des cases extérieures carrées :

```text
max_outer_root
```

Dans la branche C, la borne porte sur la racine du centre carré :

```text
E
```

Dans la branche D, deux bornes interviennent :

```text
limit
qmax
```

Dans la branche E, la borne porte sur les racines utilisées dans les coins :

```text
A, C, H, J ≤ max_root
```

Les résultats ne doivent donc pas être comparés uniquement à partir des nombres bruts de bornes.

## 6. La branche D est heuristique

La branche D relâche les contraintes en fixant seulement une progression de carrés autour du centre, puis en balayant le paramètre `q`.

Elle peut retrouver le carré de Bremner, mais elle ne garantit pas une exploration exhaustive de toutes les familles possibles avec centre carré.

Elle sert principalement de contrôle expérimental et de recherche exploratoire.

## 7. Coût mémoire de la branche B

La branche B devient rapidement coûteuse en mémoire, car elle génère un grand nombre de centres et d’offsets.

Le test jusqu’à :

```text
max_outer_root = 20 000
```

a déjà généré :

```text
99 990 000 paires de carrés
51 153 080 centres rencontrés
7 198 712 centres candidats
161 942 106 couples d’offsets testés
```

Une montée brute au-delà de cette borne nécessiterait une version plus optimisée ou une stratégie différente.

## 8. Les fichiers JSON ne sont pas publiés dans ce repo

Les structures JSON destinées au site Mystimath ne sont pas incluses dans ce dépôt.

Elles seront intégrées dans la base du site Mystimath afin de permettre :

* l’affichage interactif ;
* la validation interne ;
* la réutilisation pédagogique ;
* la séparation entre code expérimental et données éditoriales du site.

## 9. Positionnement scientifique

Ce repo ne revendique pas la découverte d’un nouveau record.

Il documente :

* des scripts reproductibles ;
* des familles de recherche ;
* des résultats négatifs bornés ;
* des exemples semi-magiques utiles pédagogiquement ;
* une base de travail pour des articles de recherche vulgarisée.

La formulation recommandée est :

```text
Aucun candidat n’a été trouvé dans cette famille et dans cette borne.
```

et non :

```text
Aucun candidat n’existe.
```

## 10. Prochaines améliorations possibles

Les pistes futures incluent :

* optimisation mémoire de la branche B ;
* parallélisation des recherches ;
* filtres modulaires ;
* analyse des motifs de 7 cases carrées parmi 9 ;
* comparaison systématique avec les formes de Lucas ;
* génération de visualisations pour Mystimath ;
* publication des structures validées dans la base du site.