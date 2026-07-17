# J4 — Prototypes A, B1 et B2 à très petite borne

_Jalon exécuté le 16 juillet 2026. Le noyau J3 est l'oracle commun._

## 1. Domaine final commun

Pour un entier `R`, les trois prototypes recherchent les classes `D4` de
grilles magiques 3×3 telles que :

- les neuf valeurs sont des carrés parfaits strictement positifs ;
- les neuf valeurs sont deux à deux distinctes ;
- chaque racine positive est au plus `R` ;
- les huit sommes sont égales ;
- la primitivité est mesurée, mais n'est pas imposée par défaut.

Les exécutions J4 sont complètes seulement pour `R=10`, `20`, `30` et `50`.
Ces bornes servent à contrôler l'accord logique, pas à produire un résultat
scientifique nouveau.

## 2. Livrables

```text
experiments/formulations_comparison/prototypes/
  __init__.py
  model.py
  formulation_a.py
  formulation_b1.py
  formulation_b2.py

experiments/formulations_comparison/tests/
  test_prototypes.py
```

Les prototypes utilisent directement
`common.validation.validate_grid`. Aucun d'eux ne possède son propre
validateur final.

## 3. Oracle A

`formulation_a.py` énumère les triplets ordonnés de racines `(x,y,z)` entre 1
et `R`, pose

```text
p=x²-y², q=x²-z²,
```

puis construit les six valeurs forcées de la forme centrée. Il rejette
successivement :

1. les collisions entre les trois carrés de base ;
2. les valeurs forcées non positives ;
3. les valeurs forcées absentes de la table des carrés bornés ;
4. les grilles rejetées par le noyau J3 ;
5. les classes `D4` déjà rencontrées.

Il est volontairement simple et de coût cubique. Il sert d'oracle à petite
borne, pas de moteur recommandé pour une campagne.

## 4. Prototype B1 : index centré

`formulation_b1.py` commence par générer exactement les progressions

```text
u², v², w²,   u²+w²=2v²,
```

avec racines distinctes au plus `R`. Il construit ensuite

```text
offsets_by_center[v²] = {v²-u²}.
```

Pour chaque paire `q<p` du même centre, il teste l'appartenance de `p-q` et
`p+q`. Un hit reconstruit la grille centrée, qui est ensuite soumise à J3.

## 5. Prototype B2 : index par différence

`formulation_b2.py` groupe le même catalogue de progressions par différence :

```text
centers_by_difference[n] = {v²}.
```

Dans chaque groupe, il cherche trois centres `low,center,high` en progression.
La différence commune des progressions devient un offset de la grille ; la
différence entre centres devient l'autre. La grille finale passe par le même
oracle J3 et la même canonicalisation `D4`.

B1 et B2 partagent volontairement le générateur de progressions. J4 compare
les deux stratégies d'indexation ; une validation indépendante de ce catalogue
sera ajoutée au protocole de validation croisée avant toute conclusion forte.

## 6. Compteurs instrumentés

### A

- triplets de base ;
- collisions de base ;
- valeurs forcées calculées ;
- rejets de positivité ;
- tests d'appartenance à la table des carrés ;
- rejets non carrés ;
- candidats complets, classes acceptées et doublons.

### B1

- progressions générées et centres indexés ;
- paires d'offsets ;
- tests d'appartenance additive et hits ;
- candidats complets, classes acceptées et doublons.

### B2

- progressions et groupes de différence ;
- paires de centres et tests du troisième centre ;
- progressions de centres trouvées ;
- candidats complets, classes acceptées et doublons.

Ces compteurs préparent J7, mais J4 ne mesure ni temps, ni mémoire, ni disque.

## 7. Tests

La suite ajoute six tests :

- présence de la progression `1,25,49`, de différence 24 ;
- exactitude et unicité du catalogue à `R=30` ;
- propriété magique de la forme centrée pour des paramètres entiers arbitraires ;
- accord A–B1–B2 à `R=10`, `20` et `30` ;
- même nombre de progressions indexées par B1 et B2 ;
- rejet des bornes invalides.

Avec les douze tests J3, la commande

```powershell
python -m unittest discover -s experiments\formulations_comparison\tests -v
```

donne :

```text
Ran 18 tests in 0.047s
OK
```

## 8. Validation croisée à R=50

Les trois recherches complètes donnent zéro classe 9/9, ce qui est cohérent à
cette petite borne. L'accord porte sur les ensembles canoniques finaux, pas
seulement sur leurs cardinalités.

| Compteur | A | B1 | B2 |
| --- | ---: | ---: | ---: |
| triplets de base | 125 000 | — | — |
| collisions de base | 7 400 | — | — |
| valeurs forcées calculées | 705 600 | — | — |
| rejets non positifs | 100 324 | — | — |
| tests de carré après positivité | 103 656 | — | — |
| rejets forcés non carrés | 17 276 | — | — |
| progressions de trois carrés | — | 15 | 15 |
| centres ou différences indexés | — | 14 | 14 |
| paires d'offsets ou de centres | — | 1 | 1 |
| tests additifs ou du troisième centre | — | 2 | 1 |
| hits structurels | 0 | 0 | 0 |
| classes finales | 0 | 0 | 0 |

Ces chiffres montrent une différence d'espace intermédiaire, mais ils ne sont
pas un benchmark de performance. Aucun classement algorithmique n'en est
déduit à J4.

## 9. Divergences et limites

Aucune divergence de classes n'est observée aux quatre bornes. L'absence de
solution 9/9 connue empêche cependant un test positif final. La confiance
repose donc actuellement sur :

- les preuves de J2 ;
- la progression témoin `1,25,49` ;
- l'identité de la forme centrée ;
- l'accord exhaustif des trois ensembles vides aux petites bornes ;
- le validateur indépendant J3.

Avant J7, une validation croisée plus forte devra comparer aussi les objets
intermédiaires sur un domaine artificiel ou rationnel où un hit complet est
connu, sans le présenter comme solution entière du problème.

## 10. Fin de J4 et porte G2

J4 établit que les trois chemins produisent le même résultat sur le domaine
entier minuscule testé. Il confirme la faisabilité des deux indexations B, mais
ne permet pas encore d'affirmer que B1 domine A : cette décision exige les
mesures de J7.

J5, J6 et J7 ne sont pas commencés. Aucun run moyen ou lourd, commit ou push
n'a été effectué pendant J4.
