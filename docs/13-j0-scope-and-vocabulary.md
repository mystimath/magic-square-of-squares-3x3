# J0 — Périmètre mathématique et vocabulaire figés

_Jalon exécuté le 16 juillet 2026._

## 1. Objet principal

L'étude compare quatre formulations du problème suivant : trouver une grille
3×3 d'entiers positifs, deux à deux distincts, qui est magique et dont les neuf
entrées sont des carrés parfaits. Une grille est magique lorsque ses trois
lignes, ses trois colonnes et ses deux diagonales ont une même somme `S`.

Le problème principal exclut zéro, les valeurs négatives, les répétitions et
les grilles seulement semi-magiques. Les variantes relâchées restent des
contrôles expérimentaux et doivent être étiquetées comme telles.

## 2. Convention k/9

Pour une grille déjà magique, `q(G)` désigne le nombre de ses neuf entrées qui
sont des carrés parfaits d'entiers positifs.

- `exactement 7/9` signifie `q(G) = 7` ;
- `au moins 7/9` signifie `q(G) >= 7` ;
- `exactement 8/9` signifie `q(G) = 8` ;
- `au moins 8/9` signifie `q(G) >= 8` ;
- `9/9` signifie `q(G) = 9` et constitue le problème principal.

Une commande historique comme `--min-squares 7` porte donc sur `au moins
7/9`, et non sur `exactement 7/9`. Tout rapport doit publier la valeur exacte
de `q(G)` même si le filtre est un seuil.

Cette notation ne compte jamais les lignes de même somme. En particulier, une
grille semi-magique de neuf carrés ayant trois lignes, trois colonnes et une
transversale de même somme est une grille `9/9` quant à ses cases, mais elle
n'est pas une solution magique si la seconde diagonale échoue.

## 3. Contrôles 7/9 et 8/9

Les cas `>= 7/9` et `>= 8/9` servent à valider les générateurs, mesurer les
filtres et comparer les formulations. Ils ne sont pas des solutions du
problème `9/9`.

- Bremner est le contrôle positif commun attendu à `7/9`.
- Une grille magique ayant moins de sept cases carrées est un contrôle négatif
  pour les seuils 7/9 et 8/9.
- Une grille semi-magique, même composée de neuf carrés, est rejetée par le
  validateur du problème principal.
- Un candidat `8/9` doit identifier explicitement l'unique case non carrée ;
  un candidat `7/9`, les deux cases non carrées.

## 4. Domaine arithmétique

Une entrée carrée admissible est `r²` avec `r` entier strictement positif. Le
test doit être entier et exact, par exemple avec `math.isqrt`. Pour le problème
principal :

1. les neuf valeurs sont strictement positives ;
2. les neuf valeurs sont deux à deux distinctes ;
3. chaque valeur est un carré parfait ;
4. les huit lignes standard ont une même somme positive.

Les recherches relâchées 7/9 et 8/9 conservent la positivité et la distinction
des neuf valeurs, sauf protocole séparé explicitement nommé. Le centre zéro et
les racines répétées relèvent de variantes dégénérées, hors comparaison
principale.

## 5. Primitivité et dilatation

Deux grilles sont dans la même classe de dilatation si `H = k² G` pour un
entier `k > 0`, multiplication appliquée aux neuf valeurs. Cette opération
préserve la propriété magique et le masque des cases carrées.

Une grille entière est dite primitive pour cette étude lorsque le PGCD de ses
neuf valeurs ne possède aucun diviseur carré supérieur à 1. Autrement dit,
elle ne peut pas être divisée globalement par `k²`, `k > 1`, tout en restant
entière. Cette convention est celle du filtre historique `primitive-only`.
Lorsque les neuf cases sont carrées, elle équivaut à demander que le PGCD des
neuf racines positives soit 1.

Le PGCD brut des neuf valeurs et leur plus grand facteur carré commun doivent
rester deux champs distincts dans les futurs résultats.

## 6. Symétries et équivalences

Pour une grille magique complète, le groupe d'équivalence principal est le
groupe diédral `D4` d'ordre 8 : quatre rotations et quatre réflexions. Il
préserve les lignes, colonnes, diagonales, la somme magique, le masque carré,
la positivité, la distinction et la primitivité. La forme canonique est le
minimum lexicographique des huit aplatissements.

Les permutations indépendantes des trois lignes et des trois colonnes,
complétées par la transposition, donnent 72 opérations utilisées dans le
projet semi-magique. Elles préservent les six sommes de lignes et colonnes,
mais pas nécessairement les deux diagonales. Elles ne constituent donc pas le
groupe de canonicalisation du problème magique 7/9–9/9.

Les classes géométriques sous `D4` et les classes de dilatation sont deux
quotients distincts. Un résultat doit conserver sa grille primitive canonique,
son facteur de dilatation éventuel et sa provenance.

## 7. Vocabulaire obligatoire

- **objet intermédiaire** : progression, offset, triangle ou point elliptique
  avant reconstruction d'une grille ;
- **candidat** : grille reconstruite mais pas encore validée indépendamment ;
- **grille magique validée** : grille satisfaisant exactement les huit sommes ;
- **score carré** : valeur exacte `q(G)` entre 0 et 9 ;
- **solution 9/9** : grille magique validée du domaine principal ;
- **quasi-solution k/9** : grille magique validée avec `q(G)=k<9` ;
- **semi-magique** : trois lignes et trois colonnes de même somme, sans exigence
  sur les diagonales ;
- **classe géométrique** : orbite sous `D4` ;
- **classe de dilatation** : grilles liées par un facteur carré global ;
- **complet dans une borne** : toutes les unités du domaine fini annoncé ont
  été parcourues et agrégées ;
- **partiel** : interruption, sous-domaine ou heuristique ne certifiant pas la
  couverture complète.

Les mots « exhaustif », « nouveau » et « solution » ne doivent jamais être
employés sans préciser respectivement le domaine borné, la portée de la
recherche d'antériorité et le niveau 9/9 ou relâché.

## 8. Frontière avec le projet semi-magique

Le projet `semi-magic-powers-3x3` fournit des méthodes réutilisables de
validation, reprise, sharding et traçabilité. Son objet scientifique reste
différent : il exige six sommes égales sur les lignes et colonnes. Une
transversale supplémentaire donne sept sommes égales sur huit, ce qui ne doit
jamais être abrégé en `7/9`.

Dans la présente étude, `k/9` compte toujours des cases carrées au sein d'une
grille magique ; dans le projet semi-magique, les expressions `6/8`, `7/8` ou
`8/8` peuvent compter les lignes standard égales si ce comptage est utile.

## 9. Contrat de sortie minimal pour les jalons suivants

Tout candidat promu au format commun devra contenir : les neuf valeurs, la
somme magique, les huit sommes recalculées, le score carré exact, les racines
des cases carrées, le masque carré, les indicateurs de positivité et de
distinction, le PGCD, le facteur carré commun, la forme canonique `D4`, le
facteur de dilatation, la formulation d'origine, la définition de la borne et
le statut complet ou partiel du run.

## 10. Décision de fin de J0

Le périmètre principal est figé sur les grilles magiques positives, distinctes
et `9/9`. Les niveaux 7/9 et 8/9 sont des contrôles relâchés comptant les cases
carrées. La primitivité exclut un facteur carré global, et la canonicalisation
principale utilise `D4`, non les 72 opérations semi-magiques.

J1 n'est pas commencé par ce document. Aucun prototype, benchmark ou run n'a
été créé ou lancé.
