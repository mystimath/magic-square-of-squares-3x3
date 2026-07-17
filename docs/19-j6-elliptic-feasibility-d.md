# J6 — Faisabilité elliptique de la formulation D

_Jalon exécuté le 16 juillet 2026. Aucune installation et aucune recherche
elliptique à grande hauteur n'ont été effectuées._

## 1. Objet

La formulation D fixe un nombre congruent rationnel positif `n` et considère

```text
E_n : y²=x³-n²x.
```

Elle cherche trois points admissibles de `2E_n(Q)` dont les abscisses sont en
progression arithmétique. J6 vérifie la traduction exacte et détermine si cette
formulation fournit déjà un domaine fini comparable aux prototypes A–C.

## 2. Audit des outils locaux

| Outil | État local |
| --- | --- |
| SageMath / `sage` | absent |
| PARI/GP | absent ; `gp` est l'alias PowerShell de `Get-ItemProperty` |
| `cypari2` | absent |
| Magma | absent |
| SymPy | présent dans l'environnement Anaconda |
| Python | 3.11.15 |

Rien n'a été installé. SymPy n'a pas été utilisé comme substitut à un calcul
de rang, de générateurs, de hauteur canonique ou de groupe de Selmer. La sonde
J6 repose uniquement sur `fractions.Fraction` et l'arithmétique exacte de la
bibliothèque standard.

## 3. Livrables

```text
experiments/formulations_comparison/prototypes/formulation_d.py
experiments/formulations_comparison/tests/test_formulation_d.py
```

Le module fournit :

- `EllipticPoint` rationnel et le point à l'infini ;
- vérification exacte de l'équation de `E_n` ;
- négation, addition et duplication ;
- racine carrée rationnelle exacte ;
- conversion progression–point et retour ;
- certificat des trois carrés de 2-descente ;
- hauteur naïve multiplicative de l'abscisse ;
- petite sonde obtenue depuis le catalogue entier borné des progressions.

Il ne calcule ni rang, ni base de Mordell–Weil, ni Selmer, ni hauteur canonique.

## 4. Trois niveaux de vérification à ne pas confondre

### Point sur la courbe

`is_on_curve` vérifie seulement

```text
y²=x(x-n)(x+n).
```

Cette condition ne prouve pas que `P` appartient à `2E_n(Q)`.

### Certificat de 2-descente

Pour un point non torsion avec `x>n`, la sonde exige que

```text
x-n=u², x=v², x+n=w²
```

dans `Q`, et vérifie `|y|=uvw`. Ce certificat est le critère de 2-descente
formalisé à J2. Les points `x=0,±n`, de 2-torsion, sont rejetés comme
progressions admissibles.

### Moitié rationnelle explicite

Lorsqu'un point `Q` est fourni, la loi de groupe peut vérifier directement
`2Q=P`. J6 ne cherche pas une moitié rationnelle générale ; il vérifie le
certificat explicite de l'exemple de contrôle.

## 5. Contrôles exacts

La progression

```text
1,25,49, différence n=24
```

donne

```text
P=(25,35) sur E_24.
```

Le certificat de carrés vaut `(1,5,7)`. La moitié explicite

```text
Q=(72,576)
```

est sur `E_24` et la duplication exacte redonne `P`.

Le point `(12,36)` est sur `E_6`, mais `x-n=6` n'est pas un carré rationnel :
il est donc rejeté par le certificat employé ici. Cet exemple empêche de
confondre appartenance à la courbe et appartenance certifiée au sous-groupe des
doubles.

## 6. Petite sonde finie

La sonde part du catalogue entier de progressions de racines au plus `R`, puis
traduit chacune en point elliptique. Elle groupe les points par `n` et cherche
trois abscisses en progression. Sa finitude provient de la borne B2 initiale,
pas d'une énumération elliptique autonome.

| R | Progressions | Points sur la courbe | Certificats 2-descente | Groupes n | Tests de progression des x | Classes 9/9 | Hauteur naïve x maximale |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 15 | 15 | 15 | 14 | 1 | 0 | 1 681 |
| 100 | 37 | 37 | 37 | 35 | 2 | 0 | 7 225 |
| 200 | 88 | 88 | 88 | 82 | 7 | 0 | 32 761 |

Aux bornes complètes `R=10`, `20`, `30` et `50`, la sonde et B2 donnent les
mêmes ensembles canoniques finaux. Cet accord valide la traduction, mais ne
rend pas D indépendante puisque le catalogue initial est partagé.

## 7. Tests

J6 ajoute six tests :

- racines carrées rationnelles exactes ;
- appartenance de `P` et `Q` à `E_24` et duplication `2Q=P` ;
- aller-retour progression–point et certificat `(1,5,7)` ;
- rejet d'un point de courbe sans certificat de trois carrés ;
- rejet de la 2-torsion comme progression positive ;
- accord de la sonde avec B2 aux petites bornes.

Résultat global :

```text
Ran 29 tests in 0.056s
OK
```

## 8. Bornes et hauteurs

Pour `x=a/b` en fraction irréductible, la sonde définit la hauteur naïve
multiplicative

```text
H_x(P)=max(|a|,b).
```

À `n` fixé et `H_x<=H`, il n'existe qu'un nombre fini d'abscisses rationnelles
à examiner. Cela ne suffit cependant pas à produire une recherche comparable :

1. il faut aussi borner ou normaliser `n` ;
2. il faut énumérer exhaustivement les points rationnels correspondants ;
3. il faut certifier `P∈2E_n(Q)` ;
4. il faut contrôler les dénominateurs communs lors du retour aux carrés
   entiers ;
5. il faut éliminer les dilatations `n→k²n`, `x→k²x`, `y→k³y` ;
6. une borne de hauteur elliptique ne se traduit pas directement en
   `max_root<=R`.

La hauteur canonique serait plus naturelle pour le groupe, mais son calcul
fiable et l'énumération par rang/générateurs nécessitent précisément les outils
de calcul formel absents de l'environnement.

## 9. Ce qu'exigerait un moteur D réellement indépendant

- fixer des représentants sans facteur carré pour `n` ;
- calculer ou certifier rang, torsion et générateurs de `E_n(Q)` ;
- énumérer les combinaisons de générateurs sous une hauteur prouvée ;
- tester la divisibilité par 2 ou produire une moitié ;
- rechercher les triplets d'abscisses en progression ;
- ramener les trois progressions rationnelles à une échelle entière commune ;
- prouver que la hauteur choisie couvre exactement le domaine final comparé.

Sans ces éléments, une liste de petits points trouvés n'est qu'une sonde et ne
peut soutenir une affirmation exhaustive.

## 10. Porte G4 : D est-elle bornable de façon comparable ?

### Décision

**Pas encore.** D est mathématiquement équivalente à B2 au niveau rationnel
admissible, mais elle ne dispose pas localement d'une borne elliptique traduite
en domaine entier commun.

### Rôle retenu à J6, révisé par J6bis

- moteur principal de découverte théorique et constructive ;
- langage naturel pour étudier rang, divisibilité et familles rationnelles ;
- recherche ciblée par courbe et recherche exhaustive par tranche de hauteur
  lorsque le groupe de Mordell--Weil est certifié ;
- validation ponctuelle avec certificats exacts.

D ne participera pas au classement exhaustif de vitesse A–B tant que le
protocole de hauteur n'est pas résolu. Cela ne lui confère aucun statut
scientifique secondaire : son rendement de découverte sera mesuré dans une
piste elliptique distincte. Voir `docs/20-j6bis-elliptic-strategy-bremner.md`.

## 11. Fin de J6

La faisabilité rationnelle de D est établie et ses limites algorithmiques sont
formalisées. La porte G4 reste fermée pour une comparaison exhaustive directe.
J7 n'est pas commencé. Aucun outil n'a été installé, aucun run moyen ou lourd,
commit ou push n'a été effectué.
