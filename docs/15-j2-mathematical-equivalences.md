# J2 — Relations mathématiques entre les formulations A, B, C et D

_Jalon exécuté le 16 juillet 2026. Les conventions de domaine et de vocabulaire
sont celles de `docs/13-j0-scope-and-vocabulary.md`._

## 1. Domaine commun et niveaux de lecture

Le problème principal porte sur une grille magique 3×3 de neuf carrés
parfaits entiers, strictement positifs et deux à deux distincts. Les relations
ci-dessous doivent être lues à trois niveaux différents :

1. **niveau entier positif** : domaine de la recherche 9/9 ;
2. **niveau rationnel positif** : domaine naturel des triangles et courbes
   elliptiques ;
3. **niveau projectif ou à dilatation près** : les dénominateurs rationnels
   peuvent être éliminés par une dilatation carrée globale.

Une équivalence au niveau rationnel ne transporte pas automatiquement une
borne sur les racines entières.

## 2. Lemme de la forme centrée générale

Soit une grille magique

```text
a  b  c
d  e  f
g  h  i
```

de somme magique `S`. Alors `S=3e` et les cases opposées ont pour somme `2e` :

```text
a+i = b+h = c+g = d+f = 2e.
```

En choisissant deux paramètres signés `p` et `q`, toute grille magique 3×3
peut s'écrire :

```text
e-p       e+p+q       e-q
e+p-q     e           e-p+q
e+q       e-p-q       e+p
```

Chaque ligne, colonne et diagonale vaut exactement `3e`. Réciproquement, cette
matrice est magique pour tous `e,p,q` dans un anneau commutatif.

La grille est déterminée par `e` et deux cases indépendantes, donc cette forme
est la paramétrisation affine générale, pas une sous-famille.

## 3. Formulation A et écriture centrée

La formulation A choisit trois carrés `x²`, `y²`, `z²`, avec centre `e=x²`, et
écrit :

```text
y²                    3x²-y²-z²          z²
x²-y²+z²              x²                 x²+y²-z²
2x²-z²                -x²+y²+z²          2x²-y²
```

Posons

```text
p = x²-y²,
q = x²-z².
```

Alors les neuf cases deviennent :

```text
x²-p       x²+p+q       x²-q
x²+p-q     x²           x²-p+q
x²+q       x²-p-q       x²+p
```

Les huit offsets autour du centre sont donc exactement

```text
±p, ±q, ±(p+q), ±(p-q).
```

Les signes de `p` et `q` ne sont pas supposés positifs dans A. Passer à
`P=|p|` et `Q=|q|` ne change pas le multiensemble des quatre offsets absolus :

```text
{|p|,|q|,|p+q|,|p-q|} = {P,Q,P+Q,|P-Q|}.
```

Cette identité explique la version positive de B.

## 4. Formulation B1 : catalogue centré D_x

Pour un entier positif `x`, définissons

```text
D_x = {d entier : 0<d<x² et x²-d, x²+d sont des carrés parfaits positifs}.
```

### Théorème A–B1

À symétrie `D4` près, les solutions entières positives et distinctes de A de
centre `x²` correspondent exactement aux couples non ordonnés `P,Q` tels que

```text
P,Q,P+Q,|P-Q| appartiennent à D_x,
```

et que ces quatre offsets sont distincts.

**Sens A vers B1.** Les huit cases sont des carrés si et seulement si chaque
paire `x²±d`, pour les quatre offsets absolus ci-dessus, est formée de carrés.

**Sens B1 vers A.** À partir de `P,Q`, la matrice centrée de la section 2
reconstruit huit carrés autour de `x²`. Choisir `p=P,q=Q` donne une orientation ;
les autres choix de signes ou l'échange de `P,Q` ne changent que l'orientation
dans l'orbite géométrique pertinente.

### Positivité et distinction

L'appartenance à `D_x` impose déjà `d<x²`, donc toutes les cases sont
positives. Les neuf valeurs sont distinctes si et seulement si les quatre
offsets absolus sont strictement positifs et deux à deux distincts.

Pour `P,Q>0`, cela revient à exclure :

```text
P=Q,  P=2Q,  Q=2P.
```

En effet, `P+Q` est strictement le plus grand ; les seules collisions restantes
sont `|P-Q|=0`, `|P-Q|=P` ou `|P-Q|=Q`.

## 5. Formulation B2 : même différence et centres en progression

Une progression de trois carrés rationnels ou entiers est notée

```text
u², v², w²,     u²+w²=2v²,
```

et sa différence est `n=v²-u²=w²-v²>0`.

Supposons que trois progressions aient la même différence `n` et que leurs
centres carrés soient eux-mêmes en progression de différence `h` :

```text
m-h, m, m+h.
```

La réunion de leurs neuf termes est

```text
{m+an+bh : a,b dans {-1,0,1}},
```

soit, autour de `m`, les offsets

```text
0, ±n, ±h, ±(n+h), ±(n-h).
```

Ils se placent dans la forme magique centrée avec `p=n,q=h`. Réciproquement,
une donnée B1 de paramètres `P,Q` se partitionne en trois progressions de même
différence `P`, centrées en `x²-Q,x²,x²+Q` ; on peut aussi échanger `P` et `Q`.

Ainsi B1 et B2 sont deux indexations exactes du même objet : B1 fixe le centre
global, B2 fixe une différence commune. Elles sont équivalentes au niveau des
grilles finales, mais leurs doublons, bornes naturelles et coûts d'indexation
ne sont pas équivalents.

## 6. Formulation C : triangles rectangles rationnels de même aire

### Lemme progression–triangle

À une progression positive de carrés rationnels

```text
u², v², w²,     w>u>=0,
```

de différence `n`, associons le triangle

```text
jambe 1 = w-u,
jambe 2 = w+u,
hypoténuse = 2v.
```

Il est rectangle car

```text
(w-u)²+(w+u)² = 2(w²+u²) = 4v².
```

Son aire est

```text
((w-u)(w+u))/2 = (w²-u²)/2 = n.
```

Réciproquement, pour un triangle rationnel rectangle de jambes `a,b>0`, avec
`b>a` après échange éventuel, et d'hypoténuse `c`, posons

```text
u=(b-a)/2,  v=c/2,  w=(a+b)/2.
```

Alors `u²,v²,w²` sont en progression de différence `ab/2`, égale à l'aire.
Les deux constructions sont inverses à l'échange des jambes et aux signes des
racines près.

### Portée B2–C

Trois progressions de carrés de même différence `n` correspondent donc à trois
triangles rectangles rationnels de même aire `n`. Leurs hypoténuses sont
`2v_i`; par conséquent, les carrés des hypoténuses sont en progression si et
seulement si les carrés centraux `v_i²` le sont.

B2 et C sont donc équivalentes sur les classes rationnelles positives
normalisées. Pour revenir aux neuf carrés entiers, il faut multiplier toutes
les racines rationnelles par un dénominateur commun ; les valeurs sont alors
multipliées par son carré. Cette opération préserve la grille à dilatation
près, mais déforme les bornes sur racines, numérateurs, dénominateurs et
hypoténuses.

Une recherche de triangles bornée séparément n'est donc pas automatiquement
exhaustive pour une borne entière `R` donnée.

## 7. Formulation D : courbe du nombre congruent

Fixons `n>0` rationnel et la courbe

```text
E_n : y²=x³-n²x=x(x-n)(x+n).
```

### Critère de 2-descente utilisé

Pour un point rationnel non torsion `P=(x,y)` avec `x>n`, le critère standard
de 2-descente sur une courbe à trois points de 2-torsion rationnels donne :

```text
P appartient à 2E_n(Q)
si et seulement si
x-n, x et x+n sont des carrés dans Q.
```

Les points `x=0,±n` sont les points de 2-torsion et sont exclus de ce critère
non dégénéré. La condition `x>n` sélectionne les trois carrés positifs.

Dans le sens élémentaire, si

```text
x-n=u², x=v², x+n=w²,
```

alors `y=±uvw` satisfait l'équation de `E_n`. L'affirmation supplémentaire que
le point est un double est précisément le contenu du critère de 2-descente ;
elle devra recevoir une source primaire dans le papier final.

### Portée B2–D

Une progression rationnelle de carrés de différence `n` produit donc un point
de `2E_n(Q)` dont l'abscisse est son carré central `x=v²`. Réciproquement, un
point admissible de `2E_n(Q)` restitue la progression `x-n,x,x+n`.

Par conséquent, trois progressions de même différence `n` dont les centres
sont en progression correspondent à trois points admissibles de `2E_n(Q)`
dont les abscisses sont en progression.

Cette équivalence est exacte au niveau rationnel sous les conditions :

- même `n>0` pour les trois points ;
- points non torsion et abscisses `x_i>n` ;
- appartenance effective à `2E_n(Q)`, pas seulement à `E_n(Q)` ;
- trois abscisses distinctes en progression non constante.

Elle n'offre pas encore une énumération finie comparable : une borne de
hauteur sur les points elliptiques ne se traduit pas directement en borne sur
les racines entières après élimination des dénominateurs.

## 8. Chaîne directe C–D via les triangles

Pour le triangle associé à `u²,v²,w²`, d'aire `n`, le point elliptique de la
section 7 a

```text
x=v²,
y=±uvw.
```

Inversement, les racines de `x-n,x,x+n` donnent le triangle

```text
(w-u, w+u, 2v).
```

C et D décrivent donc le même objet rationnel non dégénéré, C par ses côtés et
D par un point double. Là encore, la correspondance mathématique n'implique
pas une équivalence algorithmique des bornes.

## 9. Dégénérescences et exclusions

| Cas | Effet | Traitement |
| --- | --- | --- |
| `p=0` ou `q=0` | une paire opposée répète le centre | exclu par distinction |
| `p=±q` | offset nul et collisions | exclu |
| `|p|=2|q|` ou `|q|=2|p|` | deux offsets absolus coïncident | exclu |
| offset absolu `>=x²` | case nulle ou négative | exclu par `D_x` et positivité |
| racine nulle | carré non positif | exclu du problème principal |
| progression constante `n=0` | triangle d'aire nulle, courbe dégénérée | exclu |
| triangle avec jambe nulle | progression répétée | exclu |
| points `x=0,±n` | 2-torsion, progression non positive ou répétée | exclus |
| trois centres elliptiques égaux | progression constante | exclue par distinction |
| dénominateurs rationnels différents | aucune borne entière immédiate | prendre un dénominateur commun et suivre la dilatation |
| changement de signes des racines ou de `y` | même objet carré ou triangle | quotienter lors de la normalisation |

## 10. Tableau de portée des relations

| Relation | Portée mathématique | Inverse | Portée algorithmique actuelle |
| --- | --- | --- | --- |
| grille magique générale ↔ forme centrée | équivalence affine | explicite | même domaine fini si la borne est posée sur la grille finale |
| A ↔ B1 | équivalence entière positive, à `D4` près | explicite | bornes comparables si le même `max_root` final est imposé |
| B1 ↔ B2 | équivalence des grilles ; double indexation centre/différence | explicite | espaces intermédiaires et doublons différents |
| B2 ↔ C | équivalence rationnelle positive normalisée | explicite | correspondance partielle pour des bornes indépendantes |
| B2 ↔ D | équivalence rationnelle via le critère `P∈2E_n(Q)` | explicite sous exclusions | aucune exhaustivité comparable sans borne de hauteur traduite |
| C ↔ D | équivalence rationnelle non dégénérée | explicite | représentations et coûts très différents |
| recherche entière bornée ↔ recherche rationnelle bornée | aucune équivalence générale de bornes | non | comparaison seulement après protocole spécifique |

## 11. Exemple exact de contrôle

La progression entière

```text
1, 25, 49
```

a pour racines `u=1,v=5,w=7` et différence `n=24`. Elle donne le triangle
rectangle `(6,8,10)`, d'aire 24. Elle donne aussi le point

```text
P=(25,35) sur E_24,
```

car

```text
35²=25(25-24)(25+24)=1225.
```

Les trois facteurs `1,25,49` sont des carrés rationnels ; le critère de
2-descente place donc `P` dans `2E_24(Q)`. L'inversion redonne le triangle et la
progression initiale. On dispose en outre du certificat explicite

```text
Q=(72,576),     2Q=(25,35)=P.
```

La formule de duplication donne une pente `13`, puis
`x(2Q)=13²-2·72=25` et `y(2Q)=13(72-25)-576=35`.

### 11 bis. Paramétrisation du catalogue entier

L'équation des racines d'une progression de trois carrés est

```text
u²+w²=2v².
```

La paramétrisation rationnelle du cercle `U²+W²=2`, depuis le point `(1,1)`,
donne après homogénéisation les trois racines non ordonnées

```text
m²+2mn-n²,   m²+n²,   -m²+2mn+n².
```

Leurs carrés vérifient identiquement la relation de progression. Réciproquement,
tout point rationnel non dégénéré du cercle est obtenu par une droite de pente
rationnelle passant par `(1,1)` ; après écriture de cette pente sous la forme
`n/m` et élimination des dénominateurs, toute progression entière apparaît à
une dilatation rationnelle près.

Le générateur choisit `gcd(m,n)=1`, prend les valeurs absolues, divise les trois
racines par leur PGCD (égal à `1` ou `2` dans le cas primitif), puis énumère les
dilatations entières compatibles avec `max_root`. Il suffit donc de parcourir
`m²+n²<=2R` avant normalisation. Les cas nuls, répétés ou mal ordonnés sont
exclus explicitement et les représentations multiples sont dédupliquées.

Cette justification établit la couverture paramétrique ; indépendamment, le
programme compare l'ensemble trié au générateur quadratique direct. L'égalité
exacte a été vérifiée à toutes les bornes de test jusqu'à `R=25000`, soit 26 285
progressions. Cette vérification bornée renforce l'implémentation mais ne se
substitue pas à l'argument de paramétrisation.

Une validation exhaustive ultérieure à `R=100000` a confirmé l'égalité objet
par objet des deux catalogues sur 122 640 progressions.

## 12. Conséquences pour les jalons suivants

1. A, B1 et B2 peuvent être comparées sur un même domaine de grilles entières.
2. C peut fournir une validation indépendante ou un moteur seulement si sa
   normalisation des dénominateurs et sa borne sont explicites.
3. D ne doit pas entrer dans un classement exhaustif avant définition d'une
   hauteur finie et preuve de sa traduction vers le domaine final.
4. Le validateur J3 devra tester les identités de la forme centrée, les quatre
   offsets, les dégénérescences et les conversions progression–triangle.
5. L'appartenance à `2E_n(Q)` exigera soit un outil formel fiable, soit un
   certificat de moitié rationnelle ; vérifier seulement l'équation de la
   courbe est insuffisant.

## 13. Fin de J2 et porte G1

Les quatre formulations appartiennent à une chaîne mathématique cohérente : A,
B1 et B2 sont équivalentes sur le problème entier ; C et D leur sont
équivalentes au niveau rationnel positif correctement normalisé. La différence
essentielle est algorithmique : les bornes naturelles ne sont pas préservées
en passant aux triangles ou aux hauteurs elliptiques.

Cette cohérence justifie de conserver un papier de synthèse unique, sous
réserve de ne comparer expérimentalement que des domaines finis explicitement
alignés. J3 n'est pas commencé par ce document. Aucun prototype, benchmark ou
run scientifique n'a été créé ou lancé pendant J2.
