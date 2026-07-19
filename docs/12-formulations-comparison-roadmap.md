# Architecture et feuille de route — comparaison des formulations

_Version de cadrage : 2026-07-15 — état mis à jour à la clôture du 19 juillet 2026._

## 1. Portée

Cette feuille de route transforme le cahier
`CODEX_TASK_COMPARAISON_FORMULATIONS_CARRE_MAGIQUE_CARRES.md` en programme de
recherche planifié. Elle n'autorise par elle-même aucun prototype, benchmark,
run à grande borne, installation ou publication.

L'objectif est de déterminer, avec des domaines de comparaison explicites,
quelle formulation sert le mieux la recherche exhaustive bornée, la génération
de familles, la validation indépendante et l'analyse théorique.

## 2. Point de départ local vérifié

### Dépôt principal

`conjectura/magic-square-of-squares-3x3` doit accueillir l'étude. Il contient :

- la paramétrisation générale centrée et les branches à centre carré ou non ;
- les moteurs historiques et optimisés, notamment les variantes B2 ;
- des mécanismes de canonicalisation par symétries ;
- des campagnes documentées retrouvant Bremner à 7/9 ;
- des recherches négatives bornées à 8/9 et des cartographies 6/9 ;
- une roadmap antérieure orientée vers la chasse aux candidats.

### Bibliothèque méthodologique réutilisable

`conjectura/semi-magic-powers-3x3` apporte des modèles robustes pour :

- les tests entiers exacts et la validation indépendante ;
- la canonicalisation sous permutations de lignes, colonnes et transposition ;
- la distinction entre classes primitives et dilatations ;
- le sharding, les checkpoints, la reprise et l'agrégation certifiée ;
- les résumés JSON, catalogues CSV et rapports de runs.

Son moteur par triples de somme commune n'est pas un substitut direct aux
quatre formulations du carré magique complet.

### Briques absentes ou non établies

Aucun moteur local clairement identifié ne traite encore :

- la normalisation exhaustive des triangles rectangles rationnels par aire ;
- le calcul de groupes elliptiques ou l'appartenance à `2E_n(Q)` ;
- une convention de borne commune démontrée équitable entre A, B, C et D ;
- un protocole de benchmark transversal déjà validé.

C et D commencent donc comme études de faisabilité. D ne sera pas qualifiée
d'exhaustive sans contrôle des hauteurs et outil de calcul formel approprié.

## 3. Architecture cible

Les travaux futurs resteront isolés dans le dépôt principal :

```text
docs/formulations/
  mathematical_mapping.md
  comparison_protocol.md
  bounds_and_equivalence.md
experiments/formulations_comparison/
  common/
  formulation_a/
  formulation_b/
  formulation_c/
  formulation_d/
  tests/
results/formulations_comparison/
  manifests/
  benchmarks/
  cross_validation/
reports/formulations/
paper/formulations_comparison/
```

Cette arborescence est une cible ; chaque dossier ne sera créé qu'à
l'activation explicite du jalon correspondant.

### Couche 1 — contrat mathématique commun

Un candidat commun décrira : domaine et borne, neuf valeurs, neuf racines si
elles existent, somme magique, positivité, distinction, PGCD, facteur d'échelle,
forme canonique et provenance algorithmique.

Le contrat distinguera objet intermédiaire, candidat, grille validée et classe
canonique primitive.

### Couche 2 — adaptateurs de formulation

- **A** : variables `(x,y,z)` et six expressions forcées ; oracle direct.
- **B1** : index centré `D_x` et motif `{b,c,b+c,|b-c|}` ; candidat prioritaire
  pour l'exhaustivité.
- **B2** : index par différence commune puis progression des centres ; moteur
  secondaire et validation croisée de B1.
- **C** : progressions traduites en triangles rationnels normalisés et groupés
  par aire ; son surcoût doit être mesuré avant toute montée de borne.
- **D** : moteur principal de découverte théorique et constructive sur `E_n`,
  avec une piste de mesure elliptique propre ; il reste séparé du benchmark
  exhaustif A–B tant que les bornes de hauteur et le test `P in 2E_n(Q)` ne
  sont pas maîtrisés.

### Couche 3 — validation indépendante

La validation ne dépendra d'aucun générateur. Elle recalculera les carrés, les
huit sommes, la distinction, la primitivité et les symétries. Bremner sera le
contrôle positif commun ; cas dégénérés et non-solutions serviront de contrôles
négatifs.

### Couche 4 — protocole expérimental

Chaque exécution écrira un manifeste : version du code, machine, Python et
dépendances, définition exacte de la borne, paramètres, statut complet ou
partiel, compteurs, temps, mémoire et disque. Aucun CSV seul ne prouvera la
complétude.

### Couche 5 — rédaction et traçabilité

Les résultats seront promus dans cet ordre : journal brut, résultat validé,
rapport technique, note primaire éventuelle, puis papier comparatif. Une note
ne reprendra que des résultats archivés avec manifeste et validation.

## 4. Principes de comparabilité

La racine maximale `R` n'est pas automatiquement une borne équivalente pour les
triangles ou les points elliptiques. Trois vues resteront séparées :

- même domaine de grilles finales ;
- même borne naturelle propre à chaque formulation ;
- même budget de calcul, uniquement comme mesure de rendement.

Le classement principal reposera sur le premier domaine lorsque l'exhaustivité
est démontrable. Les autres ne serviront pas à déclarer abusivement une méthode
supérieure.

## 5. Feuille de route avec jalons

Les durées indiquent une charge de travail, pas des dates. Chaque jalon exige une
décision explicite avant démarrage.

### J0 — gel du périmètre (une demi-journée)

Livrable : définition de 9/9, contrôles 7/9 et 8/9, positivité, distinction,
primitivité, groupe de symétries et vocabulaire.

Sortie : aucune ambiguïté entre nombre de cases carrées et nombre de lignes
magiques ; distinction nette avec le projet semi-magique.

### J1 — inventaire vérifié (un à deux jours)

Livrable : fonctions, formats, résultats complets et partiels réutilisables. Le
volumineux `STATUS.md` historique sera indexé et non recopié.

Sortie : chaque borne citée pointe vers un artefact ou porte la mention
« déclaration documentaire non encore revalidée ».

**Note possible N1** — Retour d'expérience sur l'architecture de recherches
bornées autour du carré magique de carrés, seulement si l'inventaire révèle des
enseignements autonomes sur reprise, sharding et validation.

### J2 — équivalences mathématiques (deux à quatre jours)

Livrables : écriture centrée vérifiée, preuve des passages A–B, dégénérescences,
puis portée exacte des correspondances B–C et C–D.

Sortie : transformations testables dans les deux sens et tableau « équivalent /
injection / correspondance partielle ».

**Note possible N2** — Une écriture additive centrée du problème et ses quatre
offsets, seulement en présence d'une clarification ou d'un lemme original ;
sinon cette matière restera dans le papier final.

### J3 — noyau de validation (deux à trois jours)

Livrable : spécification et tests du validateur et de la forme canonique, sans
nouveau moteur de recherche.

Sortie : Bremner accepté, cas artificiels rejetés, invariance sur les 72
opérations et détection des dilatations.

### J4 — prototypes A et B à très petite borne (trois à six jours)

Ordre : oracle A simple, B1 centrée, puis B2 par différence commune. Les bornes
seront choisies après profilage ; `R=500` n'est pas un point de départ imposé.

Sortie : A, B1 et B2 donnent les mêmes classes sur un domaine final commun, ou
toute divergence est mathématiquement expliquée.

**Note possible N3** — Deux indexations exhaustives des progressions de trois
carrés, si B1/B2 montrent une différence reproductible et conceptuellement utile.

### J5 — faisabilité géométrique C (deux à quatre jours)

Livrable : bijection locale progression–triangle, normalisation des fractions et
étude des doublons. Aucune campagne large.

Décision : C devient moteur seulement si le groupement par aire réduit un coût
mesuré ou offre une validation réellement indépendante ; sinon elle demeure
une interprétation géométrique.

**Note possible N4** — Progressions de carrés et triangles rectangles rationnels
de même aire : coût d'une reformulation computationnelle. Un résultat négatif
peut convenir si le protocole apporte une conclusion méthodologique solide.

### J6 — faisabilité elliptique D (trois à sept jours hors installation)

Livrable : audit des outils, exemples rationnels exacts, définition de hauteur,
limites d'énumération et protocole de divisibilité par 2.

Décision : aucune comparaison de vitesse avec A/B avant de définir un domaine
fini comparable. Sans SageMath ou PARI/GP, D reste une sonde théorique Python.

**Note possible N5** — Pourquoi la formulation elliptique ne fournit pas
immédiatement un moteur exhaustif borné, éventuellement comme section
méthodologique plutôt que publication séparée.

### J7 — benchmark pilote (un à deux jours, machine incluse)

Précondition : J0 à J4 validés. C et D n'entrent que pour leurs domaines
comparables. Commencer par trois petites bornes et augmenter seulement après
estimation du coût.

Sortie : répétabilité, mêmes solutions finales, compteurs de rejet, temps,
mémoire, disque et statut de complétude. Toute exécution peut être ajournée si
les conditions thermiques sont défavorables.

### J8 — benchmark confirmatoire et validation croisée (deux à cinq jours)

Une seule borne moyenne sera retenue à partir du pilote. Un second chemin de
validation et, si possible, une répétition sur un autre environnement seront
requis avant conclusion.

**Note possible N6** — Comparaison expérimentale des formulations directes et
par progressions, première note primaire naturellement publiable si le résultat
est net.

### J9 — papier de synthèse (cinq à dix jours)

Le papier à quatre formulations ne commence qu'après J2, J4, J5, J6 et le
benchmark pilote. Il pourra classer les formulations par usage, sans forcer un
classement global.

Titre visé : **Quatre formulations du problème du carré magique de carrés :
comparaison de leur intérêt algorithmique**.

Le papier séparera explicitement trois niveaux : formulation mathématique,
algorithme dérivé et implémentation concrète. Les temps observés ne seront pas
présentés comme des propriétés intrinsèques des formulations : ils dépendent du
langage, des bibliothèques, des structures de données et de l'ingénierie. Les
conclusions principales privilégieront donc la dimension de l'espace, les
objets générés, les relations testées, l'exhaustivité et la reproductibilité ;
les chronométrages seront qualifiés de mesures de prototypes dans
l'environnement documenté.

## 6. Chemin critique et dépendances

```text
J0 -> J1 -> J2 -> J3 -> J4 -> J7 -> J8 -> J9
                  |      |             ^
                  +-> J5 +-------------+
                  +-> J6 +-------------+
```

J5 et J6 peuvent suivre J2 sans bloquer A/B. Ils bloquent cependant une
publication prétendant comparer honnêtement les quatre formulations.

## 7. Priorités recommandées

1. Établir proprement A ↔ B et leur domaine commun.
2. Extraire un validateur indépendant avant tout nouveau générateur.
3. Comparer B1 et B2 à petite borne.
4. Traiter C puis D comme études de faisabilité.
5. Préparer N3 ou N6 avant le papier global si les résultats le justifient.

## 8. Portes de décision

- **G1 après J2** : les relations justifient-elles un papier unique ?
- **G2 après J4** : B centrée domine-t-elle A sur un domaine commun ?
- **G3 après J5** : C est-elle un moteur ou seulement une traduction ?
- **G4 après J6** : D est-elle bornable de façon comparable ?
- **G5 après J7** : les mesures justifient-elles une note primaire ?
- **G6 après J8** : les résultats sont-ils assez robustes pour le papier final ?

Chaque porte peut mener à poursuivre, réviser, fusionner une note avec le papier
final ou geler une branche. Un résultat négatif n'est publiable que s'il établit
une conclusion méthodologique.

## 9. Risques principaux

- confondre équivalence mathématique et équivalence des bornes ;
- réutiliser des résultats historiques sans revalider leur complétude ;
- comparer Python pur et calcul formel sans séparer bibliothèque et algorithme ;
- sous-estimer symétries et facteurs d'échelle ;
- lancer trop tôt des benchmarks moyens ;
- multiplier des notes sans résultat autonome.

## 10. État de réalisation à la clôture du 19 juillet 2026

Les jalons J0 à J10 sont réalisés et documentés dans les notes 13 à 24.
Les optimisations spécialisées B3 à B15 sont documentées dans les notes 25 à
39. Les campagnes exhaustives en boîte complète jusqu'à `R=1000000` donnent :

- B3 et B4 : l'unique classe primitive de Bremner ;
- B5 : aucune classe exactement 8/9 ;
- B6 : aucune classe 9/9.

B9 diffère la reconstruction, B10 supprime les revalidations internes et B11
règle le découpage streaming. Avec 256 shards au million, B4–B6 terminent en
31,87 s à 32,07 s, soit 40,6 % environ de gain cumulé depuis B8, sans modifier
les compteurs de couverture ni les classes. B12 établit à `R=100000` qu'un
cache LRU borné des handles économise trop peu de RSS au regard des dizaines de
milliers de réouvertures ; il reste donc expérimental et aucune confirmation au
million n'est justifiée. B13 regroupe les écritures sous un budget mémoire
borné et réduit le pic RSS, mais son surcoût temporel reste trop élevé pour une
promotion ; aucune confirmation au million n'est donc engagée.
B14 mesure le buffering natif des handles : le réglage mémoire est utile sous
contrainte, mais l'écart de vitesse ne justifie pas de changer le défaut
plateforme.
B15 regroupe les écritures par shard et supprime les dispersions, mais demande
environ 9,2 Mo de matérialisation à `R=100000` ; il reste une option de secours
pour les limites de handles.

## 11. TODO actualisée

- [x] Formaliser le périmètre et inventorier le dépôt (J0–J1).
- [x] Adapter et valider les quatre formulations (J2–J6).
- [x] Exécuter les benchmarks pilote et confirmatoire (J7–J8).
- [x] Produire le rapport, l'audit final et les moteurs B3–B6 (J9–B6).
- [x] Supprimer la table de `R` carrés et vectoriser les tests `isqrt`
  (B7–B8).
- [x] Préfiltrer la grille et différer sa reconstruction (B9).
- [x] Éviter les revalidations et comparaisons redondantes des groupes internes
  tout en conservant le chemin défensif public (B10).
- [x] Mesurer le compromis temps/mémoire des shards, conserver 128 par défaut et
  recommander 256 à `R=1000000` (B11).
- [x] Évaluer un cache LRU borné des handles d'écriture à 256 et 512 shards
  (B12) ; conserver le témoin non borné par défaut, car le gain RSS pilote ne
  compense pas le surcoût massif des réouvertures.
- [x] Évaluer des tampons d'écriture applicatifs bornés (B13) ; conserver
  l'option expérimentale sans changer le témoin non borné par défaut.
- [x] Mesurer le buffering natif des handles persistants (B14) ; conserver le
  défaut plateforme et documenter `1024` comme profil mémoire optionnel.
- [x] Évaluer le regroupement des écritures par shard (B15) ; conserver
  l'option de secours sans changer le défaut.
