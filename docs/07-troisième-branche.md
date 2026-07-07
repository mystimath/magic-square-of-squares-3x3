# Branche E — Carrés semi-magiques 3×3 avec centre zéro

Cette branche explore une famille différente du problème classique des carrés magiques de carrés.

On ne cherche plus ici un carré magique complet, mais un carré **semi-magique** : les trois lignes et les trois colonnes ont la même somme, tandis que les diagonales ne sont pas nécessairement contraintes.

Le centre est fixé à :

```text
e = 0
````

## Forme utilisée

On choisit quatre entiers positifs distincts :

```text
A, C, H, J
```

Les quatre coins du carré sont :

```text
A²      C²
H²      J²
```

Le carré semi-magique complet est alors construit sous la forme :

```text
A²        H² + J²      C²
C² + J²   0            A² + H²
H²        A² + C²      J²
```

La somme commune des lignes et des colonnes vaut :

```text
S = A² + C² + H² + J²
```

## Vérification semi-magique

Ligne 1 :

```text
A² + (H² + J²) + C² = S
```

Ligne 2 :

```text
(C² + J²) + 0 + (A² + H²) = S
```

Ligne 3 :

```text
H² + (A² + C²) + J² = S
```

Colonne 1 :

```text
A² + (C² + J²) + H² = S
```

Colonne 2 :

```text
(H² + J²) + 0 + (A² + C²) = S
```

Colonne 3 :

```text
C² + (A² + H²) + J² = S
```

Les lignes et colonnes sont donc automatiquement équilibrées.

## Objectif de recherche

Les quatre coins sont déjà des carrés parfaits.

Pour obtenir un carré semi-magique avec huit cases positives carrées autour du centre zéro, il faut que les quatre sommes suivantes soient elles aussi des carrés parfaits :

```text
H² + J²
C² + J²
A² + H²
A² + C²
```

Autrement dit, la recherche revient à trouver des relations pythagoriciennes compatibles entre les quatre racines `A`, `C`, `H` et `J`.

## Exemple obtenu

Un exemple simple est :

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

Toutes les lignes et colonnes ont pour somme :

```text
4225 = 65²
```

Ce carré contient donc huit carrés positifs sur les huit cases non nulles.

Le centre `0` peut être vu comme `0²`, mais il est préférable de ne pas le compter dans le résultat afin d’éviter une confusion avec le problème classique des carrés magiques de carrés positifs distincts.

## Script associé

```text
src/search_semimagic_e0_squares.py
```

Commande de base :

```bash
python src/search_semimagic_e0_squares.py --max-root 100 --min-squares 7 --primitive-only --limit 20 --csv results/results_semimagic_e0.csv
```

## Positionnement

Cette branche ne résout pas le problème classique du carré magique 3×3 de carrés.

Elle sert plutôt de famille constructive intermédiaire :

* elle conserve une structure additive forte ;
* elle montre comment des relations pythagoriciennes produisent naturellement des carrés semi-magiques ;
* elle offre une porte d’entrée pédagogique vers le problème plus difficile des carrés magiques complets.

## Statut

Branche ajoutée comme exploration complémentaire.

Les structures JSON destinées au site Mystimath ne sont pas publiées dans ce repo. Elles seront intégrées dans la base de données du site.