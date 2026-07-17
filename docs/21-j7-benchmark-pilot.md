# J7 — Benchmark pilote A, B1 et B2

_Jalon exécuté le 16 juillet 2026. Aucune borne moyenne ni campagne J8._

## 1. Domaine et protocole

Les trois formulations parcourent le même domaine final : grilles magiques
3×3 positives, neuf carrés distincts, racines au plus `R`, classes sous `D4`.
Chaque exécution indiquée est complète pour sa borne propre. Le pilote utilise
`R=50,75,100` après une estimation complète à `R=50` ; l'extrapolation cubique
de A a conduit à écarter `R=200` de ce jalon.

Le script reproductible est :

```powershell
python experiments\formulations_comparison\benchmark_pilot.py --bounds 50 75 100
```

Il mesure le temps mural (`perf_counter`), le temps CPU du processus et le pic
d'allocations Python observé par `tracemalloc`. Il compare ensuite les tuples de
classes canoniques, et interrompt l'exécution en cas de divergence.

## 2. Environnement

- Windows `10.0.26200`, AMD64 ;
- processeur déclaré : Intel64 Family 6 Model 167 Stepping 1 ;
- 16 processeurs logiques ;
- CPython 3.11.15, distribution Anaconda, MSC 64 bits ;
- exécution séquentielle, un seul run mesuré par moteur et par borne.

Le manifeste conserve aussi l'empreinte `HEAD` et le fait que l'arbre de travail
était sale, les livrables J0--J7 n'étant pas encore commités.

## 3. Résultats

| R | A (s) | B1 (s) | B2 (s) | triplets A | progressions B | classes A/B1/B2 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 2,054881 | 0,002254 | 0,002489 | 125 000 | 15 | 0 / 0 / 0 |
| 75 | 7,062513 | 0,004497 | 0,005224 | 421 875 | 24 | 0 / 0 / 0 |
| 100 | 17,196251 | 0,008329 | 0,010375 | 1 000 000 | 37 | 0 / 0 / 0 |

Les ensembles canoniques sont exactement égaux aux trois bornes. L'absence de
classe 9/9 est donc un résultat expérimental borné commun, et non une preuve
globale d'absence.

Dans ce prototype et sur cette machine, l'écart A/B est déjà de trois ordres de
grandeur. La croissance de A suit son million de triplets à `R=100`, tandis que
B1 et B2 ne manipulent que 37 progressions. Ces mesures soutiennent nettement
l'emploi d'une formulation B pour l'exhaustivité bornée plutôt que l'oracle A.

## 4. Mémoire et limites

Les pics `tracemalloc` restent inférieurs à 182 ko, mais ils ne mesurent que les
allocations Python suivies pendant l'appel. Ils excluent l'interpréteur, les
bibliothèques et une partie de la mémoire native. Le pic de A à `R=50` est en
outre influencé par le premier appel et les caches. Ces valeurs ne permettent
donc aucun classement mémoire robuste.

Les temps B1/B2 sont inférieurs à 10 ms et proviennent d'un seul run : bruit du
système, résolution et caches interdisent de départager honnêtement B1 et B2.
J8 devra utiliser répétitions, ordre alterné ou processus isolés et une borne où
leur travail devient mesurable. Le catalogue de progressions reste partagé ;
la validation croisée n'est donc pas entièrement indépendante à ce niveau.

## 5. Porte G5

Le pilote établit un avantage reproductible de l'espace structuré B sur l'oracle
cubique A dans les bornes testées. Il ne justifie pas encore une note primaire :
le résultat final est vide, B1/B2 ne sont pas départagées, et une mesure
confirmatoire isolée reste nécessaire.

Décision recommandée : ouvrir J8 uniquement après choix explicite d'une borne
moyenne et amélioration du protocole de répétition. C et D restent hors du
classement de vitesse A–B, leurs domaines naturels n'étant pas comparables.

## 6. Artefacts

- `experiments/formulations_comparison/benchmark_pilot.py` ;
- `results/formulations_comparison/benchmarks/pilot_benchmarks.json` ;
- `results/formulations_comparison/benchmarks/pilot_benchmarks.csv` ;
- `results/formulations_comparison/benchmarks/artifact_sizes.json` ;
- `results/formulations_comparison/benchmarks/estimate_r50/` (estimation préalable).

J8 n'est pas commencé. Aucun commit ni push n'a été effectué.

## 7. Prétests postérieurs au jalon

Après clôture de J7, un prétest unique à `R=5000` a été autorisé pour préparer
le choix de borne de J8. Il inclut B1, B2, C et D-probe sur le domaine entier
commun. Les quatre ensembles finaux sont identiques et vides ; les temps muraux
sont respectivement `1,155192`, `1,136829`, `1,281494` et `1,404408` seconde.

Ce prétest complet pour sa borne n'est pas un benchmark confirmatoire : il ne
comporte qu'un passage, ni ordre alterné, ni processus isolés. Son artefact est
`results/formulations_comparison/benchmarks/preflight_r5000.json`. A n'a pas été
exécutée : son oracle cubique aurait parcouru 125 milliards de triplets.

Un second prétest autorisé à `R=10000` donne, dans l'ordre d'exécution B1, B2,
C, D-probe : `4,703677`, `4,612865`, `5,014628` et `5,191646` secondes. Les
quatre ensembles canoniques sont encore identiques et vides. B2 précède B1 de
1,93 % dans ce passage unique, écart encore insuffisant pour un classement
confirmatoire. L'artefact est `preflight_r10000.json`. A aurait exigé 1 000
milliards de triplets avec l'oracle cubique et n'a pas été exécutée.

Le prétest suivant à `R=25000` est également complet. B1, B2, C et D-probe ont
pris respectivement `28,097871`, `27,710989`, `28,615022` et `29,370048`
secondes, pour 26 285 progressions de carrés. Les ensembles finaux sont égaux
et vides. B2 précède B1 de 1,38 % dans ce passage unique. B1 teste 39 262
paires structurelles contre 2 337 pour B2, mais la génération quadratique du
catalogue commun domine le temps total. Artefact : `preflight_r25000.json`.

## 8. Limite formulation–algorithme–implémentation

Les temps de ce rapport comparent des prototypes CPython précis, et non des
formulations mathématiques indépendamment de toute réalisation. Le classement
observé peut varier avec le langage (C, Rust, Python), les bibliothèques, les
structures de données, les caches, la parallélisation et la qualité de
l'ingénierie.

Le papier final devra donc distinguer :

1. la formulation mathématique ;
2. l'algorithme choisi pour l'exploiter ;
3. son implémentation concrète.

Les affirmations robustes porteront d'abord sur les grandeurs structurelles :
variables libres, croissance de l'espace, objets intermédiaires, relations
testées, redondances et facilité de certifier l'exhaustivité. Les temps seront
présentés comme des observations « dans notre prototype, notre environnement et
les bornes testées ». En particulier, la génération commune des progressions
sera mesurée séparément du coût propre aux adaptateurs B1, B2, C et D-probe.

## 9. Séparation expérimentale du coût commun

Le protocole partagé a ensuite été implémenté sans changer les résultats des
moteurs : les 30 tests passent, dont un test comparant pour chaque adaptateur le
mode autonome et le mode à catalogue injecté.

À `R=10000`, la génération unique des 9 354 progressions prend `4,518798`
secondes. Cinq répétitions des seuls adaptateurs, avec ordre alterné, donnent :

| Adaptateur | Minimum (s) | Médiane (s) | Maximum (s) |
| --- | ---: | ---: | ---: |
| B1 | 0,005332 | 0,005462 | 0,006219 |
| B2 | 0,005109 | 0,005235 | 0,005768 |
| C | 0,326195 | 0,333849 | 0,339290 |
| D-probe | 0,564595 | 0,565856 | 0,583333 |

B2 précède B1 de 4,17 % sur leurs médianes propres. Cette mesure isole mieux
leur différence d'indexation, mais les durées de cinq millisecondes restent
sensibles au bruit. C mesure ici le coût de la traduction exacte en triangles ;
D-probe celui de la traduction rationnelle et des certificats de carrés, pas
des calculs Sage de rang ou de hauteur.

Le résultat principal est que le catalogue commun domine très largement le
temps total. Une optimisation de sa génération pourrait donc modifier beaucoup
plus la performance globale que le choix B1/B2. Artefact :
`results/formulations_comparison/benchmarks/shared_catalog_r10000.json`.

## 10. Passage partagé à R=50000

Le même protocole, avec cinq répétitions et ordre alterné, a été exécuté à
`R=50000`. La génération unique des 56 946 progressions prend `138,010594`
secondes. Les médianes propres aux adaptateurs sont :

| Adaptateur | Minimum (s) | Médiane (s) | Maximum (s) |
| --- | ---: | ---: | ---: |
| B1 | 0,042309 | 0,046438 | 0,061424 |
| B2 | 0,038488 | 0,050314 | 0,051327 |
| C | 2,113125 | 2,126668 | 2,156181 |
| D-probe | 3,462664 | 3,500063 | 3,552802 |

Les quatre ensembles canoniques sont égaux et vides. B1 devient 7,70 % plus
rapide que B2 sur les médianes, alors même que B1 examine 97 419 paires
d'offsets et B2 seulement 4 833 paires de centres. Le minimum isolé de B2 est
inférieur à celui de B1, et les deux coûts restent de l'ordre de 50 ms : ce
renversement interdit de conclure à une supériorité temporelle stable de B1 ou
B2 dans cette implémentation.

En revanche, l'avantage structurel de B2 sur le nombre de relations testées est
net. Le catalogue représente plus de 99,96 % d'un temps total catalogue+B1 ou
catalogue+B2. L'optimisation prioritaire est donc sa génération, et non le choix
entre ces deux adaptateurs. C et D-probe mesurent des transformations plus
riches mais restent très minoritaires devant le catalogue partagé.

Artefact :
`results/formulations_comparison/benchmarks/shared_catalog_r50000.json`. Ce
passage satisfait répétitions, ordre alterné et domaine commun, mais reste un
candidat J8 plutôt qu'une clôture de J8 faute de répétition en processus isolés
et de seconde voie indépendante pour le catalogue.

## 11. Générateur paramétrique du catalogue

Le catalogue quadratique a été conservé comme oracle et complété par une
paramétrisation primitive des solutions de `u²+w²=2v²`. Les catalogues triés
sont exactement égaux aux bornes `10,50,100,250,500,1000,5000,10000,25000`.
À `R=25000`, les deux chemins produisent les mêmes 26 285 progressions :

- oracle quadratique : `28,402864` secondes ;
- générateur paramétrique primitif : `0,076922` seconde ;
- accélération observée : facteur `369,24`.

À `R=50000`, le générateur paramétrique final construit les 56 946 progressions
en `0,165242` seconde, contre `138,010594` secondes pour le catalogue
quadratique du passage précédent. Avec cinq répétitions alternées, les médianes
des adaptateurs sont `0,045192` s (B1), `0,050895` s (B2), `2,142960` s (C) et
`3,491336` s (D-probe). Les quatre sorties restent égales et vides.

Cette optimisation change l'analyse des coûts : B1/B2 deviennent presque
négligeables, tandis que les conversions exactes C et D-probe dominent désormais
leurs parcours respectifs. Elle illustre aussi la distinction essentielle entre
formulation, algorithme et ingénierie. Artefact :
`results/formulations_comparison/benchmarks/shared_catalog_parametric_r50000.json`.

### Validation directe à R=100000

Une comparaison exhaustive supplémentaire a été exécutée à `R=100000`, sans
extrapolation. Les deux catalogues triés contiennent exactement les mêmes
122 640 progressions :

| Générateur | Temps mural |
| --- | ---: |
| Quadratique | 607,693954 s |
| Paramétrique primitif | 0,421561 s |

Le facteur d'accélération directement mesuré est `1441,53`. Le statut est
complet pour la borne et l'égalité porte sur chaque objet du catalogue, pas
seulement sur leur cardinalité. Environnement : Windows `10.0.26200`, CPython
3.11.15 64 bits, 16 processeurs logiques. Artefact :
`results/formulations_comparison/benchmarks/catalog_validation_r100000.json`.

Cette mesure consolide fortement le gain d'ingénierie algorithmique, mais elle
ne doit pas être attribuée à B1 ou B2 séparément : les deux formulations peuvent
consommer le même catalogue paramétrique.
