# J1 — Inventaire vérifié du dépôt et des briques réutilisables

_Jalon exécuté le 16 juillet 2026. Référence de périmètre :
`docs/13-j0-scope-and-vocabulary.md`._

## 1. Portée de la vérification

Cet inventaire couvre le dépôt principal
`conjectura/magic-square-of-squares-3x3` et la bibliothèque méthodologique
`conjectura/semi-magic-powers-3x3`. Il indexe les scripts, formats, résultats
et journaux utiles à la comparaison des formulations A–D.

Une borne reçoit ici l'un des statuts suivants :

- **artefacts recoupés** : paramètres et résultat concordent entre journal,
  CSV ou résumé JSON local ;
- **documenté, non revalidé de bout en bout** : déclaration retrouvée, mais
  absence de manifeste complet ou de seconde validation indépendante ;
- **partiel par construction** : seule une couche, fenêtre, shortlist ou
  branche a été parcourue ;
- **hors périmètre principal** : résultat semi-magique, centre zéro ou autre
  variante dégénérée utile seulement comme contrôle.

Aucun moteur n'a été exécuté et aucune borne n'a été étendue pendant J1.

## 2. Dépôt principal

Le dépôt contient 3 scripts archivés, 20 scripts Python actifs ou utilitaires, 14
documents après J0, plus de 60 journaux ou résumés et 55 CSV sous `results/`.
Python local : 3.11.15. Les scripts utilisent surtout la bibliothèque standard ;
les pipelines B2 utilisent également NumPy. Aucun `requirements.txt`,
`pyproject.toml`, manifeste d'environnement ou dossier de tests n'a été trouvé.

### 2.1 Moteurs de recherche

| Famille | Script principal | Domaine naturel | Briques réutilisables | Statut J1 |
| --- | --- | --- | --- | --- |
| Centre carré historique | `src/search_magic_square_of_squares_v4.py` | centre `e=x²`, offsets de progressions | test exact par `isqrt`, construction de grille magique, score carré, facteur carré commun, canonicalisation `D4`, CSV | Réutilisable comme oracle A/contrôle positif après extraction dans un module sans CLI |
| Centre non carré historique | `src/search_magic_square_of_squares_v5_non_square_center.py` | paires de carrés opposées autour d'un centre entier | génération `offsets_by_center`, validation magique, `D4`, statistiques de rejet | Utile pour comprendre l'index centré ; architecture mémoire historique à ne pas reprendre telle quelle |
| B2 multipasse initial | `src/search_non_square_center_v2_1.py` | exact 8/9, centre non carré | comptage, sélection de centres, régénération sélective | Achevé à R50000 mais remplacé par la variante SAFE |
| B2 SAFE | `src/search_non_square_center_v2_2_safe.py` | `exact8`, `relaxed7`, centre carré/non carré | dataclass `Candidate`, `is_square`, racines, PGCD, `D4`, cribles modulaires, shards CSV, nettoyage, résumé JSON | Moteur local le plus complet pour l'index centré ; fonctions encore fortement couplées au pipeline |
| B2 minimum 6 | `src/search_non_square_center_v2_2_min6.py` | cartographie relâchée | variante de recombinaison et profils de couches | Secondaire ; sert à analyser la fertilité, pas l'exhaustivité 9/9 |
| B2 structurel | `src/search_non_square_center_v2_3_structural.py` | couches `relaxed7` non carrées | filtre structurel avant recombinaison | Campagnes par couches ; ne constitue pas une couverture uniforme complète |
| Triplets pythagoriciens | `src/magic_square_parallel_optimized.py` | une progression de carrés et paramètre `q` | génération streaming, cribles modulaires, sorties incrémentales, déduplication des dilatations | Réutilisable comme générateur spécialisé et contrôle ; domaine plus étroit que la formulation A générale |
| Variante dense antérieure | `src/magic_square_parallel.py` | même famille | paramétrisation et canonicalisation de facteur d'échelle | À conserver pour lecture croisée ; remplacée en pratique par la version optimisée |
| Branche coins carrés | `src/branch-c-corner-square-family.py` | centre et coins carrés | génération d'une sous-famille et cartographie de cases carrées | Sous-famille expérimentale, pas formulation C « triangles » |
| Recherche relâchée | `src/magic_square_relaxed_search.py` | quasi-solutions | contrôles 6/9–7/9 | Exploratoire |
| Centre zéro | `src/search_semimagic_e0_squares.py` | semi-magique dégénéré | construction, score de carrés positifs, validateur semi-magique | Hors périmètre principal selon J0 |

Les scripts `archive/search_magic_square_of_squares*.py` sont des versions
historiques. Ils ne doivent pas fournir le noyau commun, mais peuvent servir à
retracer l'évolution des hypothèses et détecter des régressions.

### 2.2 Utilitaires B2

Les scripts `filter_selected_centers*.py`,
`split_selected_centers_by_counts.py` et `profile_selected_counts.py` filtrent
ou découpent les CSV de centres sélectionnés. Ils sont utiles pour reproduire
les campagnes par couches, mais ne sont pas des moteurs indépendants. Leur
usage rend un run partiel si toutes les couches complémentaires ne sont pas
agrégées et certifiées.

`src/show_magic_squares_from_csv.py` est un outil d'affichage, non un
validateur indépendant.

## 3. Fonctions à extraire ou adapter

### Réutilisation directe sous réserve de tests

- test entier de carré positif fondé sur `math.isqrt` ;
- rotations, réflexions et clé canonique `D4` des moteurs v4/v5/B2 ;
- reconstruction de la grille magique centrée depuis le centre et deux
  offsets ;
- calcul des neuf entrées et du score carré exact ;
- sérialisation CSV et résumé JSON du pipeline SAFE ;
- compteurs de rejet, découpage en shards et fusion dédupliquée ;
- filtres modulaires nécessaires du pipeline B2, après preuve ou annotation de
  leur domaine exact.

### Adaptation obligatoire

- unifier la primitivité avec J0 : absence de facteur carré global commun ;
  certains scripts B2 utilisent actuellement le PGCD des seules racines des
  cases carrées, convention non équivalente pour 7/9 ou 8/9 ;
- séparer les fonctions pures des entrées-sorties et de `argparse` ;
- remplacer les champs CSV ambigus ou sensibles à la casse (`E` et `e`) par
  des noms explicites ; PowerShell `Import-Csv` refuse par exemple le fichier
  `results_corner_squares_E60000.csv` à cause des colonnes `E` et `e` ;
- ajouter le contrat commun défini à J0 : huit sommes, masque carré, facteur
  carré commun, clé `D4`, provenance, borne et statut complet/partiel ;
- distinguer explicitement filtre nécessaire sans faux négatif et heuristique.

### Briques manquantes dans le dépôt principal

- validateur indépendant commun testé ;
- tests unitaires et tests de non-régression ;
- modèle de manifeste garantissant la complétude d'un run ;
- empreinte du code et description de la machine dans les anciens résultats ;
- formulation B2 par index de différence commune ;
- normalisation des triangles rationnels de formulation C ;
- arithmétique elliptique et test d'appartenance à `2E_n(Q)` pour D ;
- définition démontrée d'une borne finale commune aux formulations.

## 4. Formats locaux

| Format | Emplacement | Contenu | Limite |
| --- | --- | --- | --- |
| CSV de candidats historiques | `results/*.csv` | grille, score carré, paramètres, racines | pas de manifeste ni empreinte du code ; en-têtes variables |
| CSV de campagnes paramétrées | `results/raw/*.csv` | paramètres `(A,E,J,q)`, masque et valeurs | plusieurs lignes peuvent être des dilatations de la même classe |
| CSV B2 SAFE | `results/raw/b2_*.csv` | mode, centre, offsets, score, masque, clé `D4`, neuf valeurs | fichiers vides représentés par le seul en-tête ; convention primitive à revoir |
| Journaux texte | `logs/*.log`, `logs/*.txt` | progression, paramètres, compteurs, durée | structure non stable ; environnement incomplet |
| Résumés JSON B2 | `logs/*summary.json` | configuration, compteurs, durée, disque, sortie | bonne base de manifeste, mais sans hash Git, versions ni statut de couverture globale |
| CSV temporaires | `tmp/` ou sous-dossiers de pipeline | centres, offsets, shards | artefacts de travail, parfois supprimés à chaud ; ne prouvent pas seuls la complétude |
| Markdown | `STATUS.md`, `docs/`, `notes/` | interprétation et historique | plusieurs déclarations n'ont pas encore de validation indépendante |

## 5. Résultats recoupés

### 5.1 Artefacts recoupés directement

| Branche et borne | Artefacts locaux recoupés | Résultat observé | Qualification J1 |
| --- | --- | --- | --- |
| v4, `center_root <= 3 000 000`, seuil `>=7/9`, primitif | `logs/log_7_3000000_primitive.txt` atteint 3 000 000 ; `results/results_7_3000000_primitive.csv` contient une ligne | une grille 7/9, Bremner, centre 425 | Artefacts concordants ; complétude déclarée par journal, sans manifeste ni validateur indépendant |
| v4, `center_root <= 10 000 000`, seuil `>=8/9`, primitif | `logs/log_8_10000000_primitive.txt` atteint 10 000 000 ; CSV correspondant sans ligne de données | aucun résultat | Artefacts concordants ; même réserve de certification |
| v5, racines extérieures `<=20 000`, seuil `>=8/9` | journal atteint 7 198 712 centres et indique `results_count=0` ; CSV vide | aucun résultat | Artefacts concordants ; coût mémoire historique et absence de manifeste |
| B2 v2.1 exact8, centre non carré, `R<=50 000` | journal complet : 624 918 054 paires, 1 594 960 centres recombinés, 0 résultat, 845,7 s | aucun 8/9 | Recoupé par journal et CSV d'en-tête ; remplacé par SAFE |
| B2 v2.2 SAFE exact8, centre non carré, `R<=50 000` | JSON + journal : 624 918 054 paires, 306 383 416 centres vus, 317 736 sélectionnés, 4 907 684 offsets, 0 résultat, 1 725,2 s | aucun 8/9 | Meilleur artefact B2 exact local ; résumé structuré, mais pas de validation indépendante |
| B2 v2.2 `relaxed7`, centre carré, `R<=100 000` | JSON + journal + CSV : 73 990 centres vus, 18 199 sélectionnés, 85 048 offsets, une ligne | Bremner seul à 7/9 | Contrôle positif local bien recoupé |
| triplets, `E<=500 000`, `q<=1 000 000`, seuil `>=7/9` | log P9 et CSV brut de 4 lignes | une classe distincte : Bremner ; les autres lignes sont des dilatations | Recoupé ; domaine spécialisé, pas recherche A générale |
| même borne, seuil `>=8/9`, `strict-24` | log P9b, CSV absent ou vide selon sortie | aucun résultat | Recoupé dans la branche ; `strict-24` est documenté comme potentiellement heuristique et ne certifie pas l'exhaustivité générale |
| cartographie 6/9, `E<=250 000`, `q<=500 000` | CSV MAP de 249 lignes, journal correspondant | 249 résultats bruts ; documentation annonce 66 classes après retrait des dilatations | Données brutes recoupées ; déduplication finale non rejouée pendant J1 |

### 5.2 Campagnes par couches : résultats partiels

Les résumés JSON B2 non carrés attestent zéro résultat `>=7/9` pour les
sous-domaines suivants :

- `R<=50 000`, couches de richesse traitées jusqu'à `count>=9` ;
- `R<=75 000`, couches `count>=12` avec découpage en deux fenêtres ;
- `R<=75 000`, B2 v2.3 : `count=7`, les sept fenêtres de `count=8` et la
  couche `count=9..11`.

Ces fichiers ne justifient pas la phrase « aucun 7/9 non carré jusqu'à R » sans
préciser les couches couvertes. Le résumé `count48_min6` contient trois
résultats au seuil 6, ce qui est cohérent avec une cartographie relâchée et non
avec une découverte 7/9.

### 5.3 Déclarations documentaires non revalidées pendant J1

- toutes les bornes intermédiaires et campagnes ciblées énumérées dans le long
  `STATUS.md` qui ne figurent pas dans le tableau ci-dessus ;
- la shortlist de 21 triplets poussée jusqu'à `q=10 000 000` ; les journaux
  existent, mais J1 n'a pas reconstitué la chaîne de sélection ni validé son
  exhaustivité ciblée ;
- l'assertion de 66 configurations distinctes dans la cartographie 6/9 ;
- les résultats de la branche coins carrés à `E<=60 000` au-delà de la présence
  du CSV brut ;
- toute conclusion d'antériorité ou de nouveauté.

## 6. Bibliothèque méthodologique semi-magique

Le dépôt `conjectura/semi-magic-powers-3x3` n'est pas un moteur substituable
aux formulations A–D, mais fournit les composants d'ingénierie les mieux
testés du workspace.

### Composants recommandés

- `src/semimagic_core.py` : sommes de lignes et colonnes, permutations,
  formatting et canonicalisation semi-magique ; les fonctions de sommes sont
  adaptables, la canonicalisation à 72 opérations ne l'est pas pour J0 ;
- `src/semimagic_disk_backend.py` : `RunConfig`, écriture JSON atomique,
  compatibilité de manifeste, rollback, sharding binaire, reprise, agrégation
  et validation du layout ;
- `src/search_semimagic_shards_parallel.py` : reprise parallèle avec un JSON
  atomique par shard ;
- `src/catalog_square_solutions.py` : PGCD des racines et des valeurs,
  enrichissement des catalogues ;
- `tests/` : 22 tests documentés dans l'état courant, couvrant notamment
  canonicalisation, reprise, corruption, écriture atomique et cas connus.

La logique de manifeste et de reprise doit être adaptée au domaine fini de
chaque formulation, sans importer la relation d'équivalence semi-magique.

## 7. Incohérences et risques à traiter avant J4

1. La primitivité varie entre facteur carré commun aux neuf valeurs et PGCD
   des seules racines carrées.
2. Les scripts historiques emploient des schémas CSV incompatibles.
3. Les anciens logs prouvent une fin de boucle, mais pas l'intégrité de toutes
   les unités de travail comme un manifeste par shards.
4. `strict-24` est explicitement susceptible de faux négatifs dans certains
   domaines et ne doit pas soutenir une conclusion exhaustive.
5. Les campagnes par couches B2 ne couvrent pas automatiquement les couches
   inférieures.
6. Aucun test automatique n'existe dans le dépôt principal.
7. Les résultats anciens ne consignent pas systématiquement machine, version
   Python, mémoire, disque, hash Git et statut complet/partiel.
8. Le nom « branche C » historique pour les coins carrés ne doit pas être
   confondu avec la formulation C par triangles rectangles rationnels.

## 8. Décision de réutilisation pour les jalons suivants

- J2 peut s'appuyer sur les formules centrées des moteurs v4/v5/B2, mais devra
  les redémontrer et tester les signes indépendamment.
- J3 doit créer un noyau commun neuf et testé, inspiré des fonctions pures v4
  et de l'ingénierie du dépôt semi-magique.
- J4 pourra conserver v4 comme oracle de contrôle et adapter l'index B2 SAFE,
  après unification de la primitivité et des formats.
- Les branches par triplets pythagoriciens et coins carrés resteront des
  générateurs spécialisés, pas des références d'exhaustivité générale.
- C et D restent absentes du code local et commenceront par une étude de
  faisabilité après J2.

## 9. Fin de J1

L'inventaire identifie des briques solides pour A, l'index centré de B et la
traçabilité sur disque. Il ne trouve aucun moteur triangles C ni elliptique D,
aucun validateur commun et aucune convention uniforme de résultat.

J2 n'est pas commencé par ce document. Aucun prototype, benchmark, campagne,
commit ou push n'a été effectué pendant J1.
