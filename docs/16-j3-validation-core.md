# J3 — Noyau commun de validation

_Jalon exécuté le 16 juillet 2026. Références : J0 pour le contrat de domaine,
J1 pour l'inventaire et J2 pour les identités mathématiques._

## 1. Livrables

Le noyau indépendant se trouve dans :

```text
experiments/formulations_comparison/common/
  __init__.py
  validation.py
```

Sa suite de tests se trouve dans :

```text
experiments/formulations_comparison/tests/
  __init__.py
  test_validation.py
```

Le module ne contient aucun générateur A, B, C ou D. Il reçoit une grille déjà
construite et recalcule toutes les propriétés sans faire confiance à sa
provenance.

## 2. Contrat implémenté

`validate_grid` produit un rapport immuable comprenant :

- les neuf valeurs entières ;
- les trois sommes de lignes, trois sommes de colonnes et deux diagonales ;
- la somme magique lorsqu'elle existe ;
- les indicateurs semi-magique et magique ;
- positivité stricte et distinction ;
- score carré exact, masque et racines exactes ;
- PGCD des valeurs, facteur carré commun et primitivité ;
- représentant canonique sous `D4` ;
- décision d'acceptation et motifs de rejet explicites.

Le paramètre `min_square_count` exprime un seuil `>=k/9`. Le rapport conserve
toujours le score exact afin qu'un contrôle `>=7/9` ne soit jamais présenté
comme `exactement 7/9` sans vérification.

## 3. Carrés, positivité et types

Le test de carré utilise exclusivement `math.isqrt` et exige un entier
strictement positif. Zéro et les entiers négatifs ne sont pas des carrés
admissibles dans le contrat J0. Les booléens sont rejetés malgré leur relation
de sous-type avec `int` en Python.

Une grille doit contenir exactement neuf entiers. Les erreurs de type ou de
dimension lèvent une exception ; les échecs mathématiques apparaissent dans le
rapport.

## 4. Primitivité harmonisée

La fonction `common_square_factor` calcule le plus grand carré parfait `k²`
divisant le PGCD des neuf valeurs. Une grille est primitive si ce facteur vaut
1. Cette définition suit J0 et remplace, dans le noyau commun, les conventions
historiques fondées seulement sur les racines des cases déjà carrées.

Une multiplication globale par 4 est reconnue comme dilatation non primitive.
Une multiplication globale par 2 ne suffit pas, à elle seule, à rendre la
grille non primitive.

## 5. Symétries

`d4_orbit` génère les quatre rotations et quatre réflexions géométriques.
`canonical_d4` choisit leur minimum lexicographique. Pour une grille à neuf
valeurs distinctes, l'orbite contient huit éléments.

`semimagic_orbit_72` génère séparément les permutations indépendantes des
lignes et colonnes, avec transposition. Le test sur Bremner confirme :

- les 72 grilles conservent les six sommes semi-magiques ;
- certaines ne conservent pas les diagonales ;
- cette orbite ne doit donc pas canonicaliser le problème magique principal.

Ce contrôle résout la tension entre les anciens outils semi-magiques et le
contrat `D4` de J0.

## 6. Contrôles positifs et négatifs

Le témoin positif est la grille de Bremner :

```text
139129  360721   42025
 83521  180625  277729
319225     529  222121
```

Les huit sommes valent 541875. La grille est positive, distincte, primitive
et exactement 7/9 ; les cases `b` et `i` ne sont pas carrées. Elle est acceptée
au seuil 7 et rejetée aux seuils 8 et 9.

Les contrôles négatifs couvrent :

- altération d'une case, donc perte de la propriété magique ;
- zéro et duplication ;
- longueur de grille invalide ;
- seuil hors de l'intervalle 0–9 ;
- dilatation carrée globale ;
- booléen fourni au test de carré.

## 7. Exécution des tests

Commande exécutée depuis le dépôt principal :

```powershell
python -m unittest discover -s experiments\formulations_comparison\tests -v
```

Résultat observé le 16 juillet 2026 avec Python 3.11.15 :

```text
Ran 12 tests in 0.001s
OK
```

## 8. Limites conscientes

- aucun sérialiseur JSON commun n'est encore ajouté ; il appartient au jalon
  des prototypes ou au protocole expérimental ;
- aucune conversion A–B–C–D n'est implémentée dans ce noyau ;
- aucune arithmétique elliptique n'est incluse ;
- les 72 opérations servent seulement au diagnostic semi-magique ;
- aucune solution 9/9 positive connue ne peut servir de fixture positive ;
- Bremner valide le chemin 7/9, pas l'existence d'une solution 9/9.

## 9. Fin de J3

Le noyau commun peut désormais servir d'oracle indépendant aux futurs
prototypes. J4 n'est pas commencé. Aucun générateur, benchmark, campagne,
commit ou push n'a été réalisé pendant J3.
