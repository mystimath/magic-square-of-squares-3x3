# Roadmap v2 — recherche computationnelle du carré magique 3×3 de carrés

_Mise à jour : 2026-07-08_

Ce document définit une stratégie de recherche computationnelle **v2**, priorisée et réaliste, à partir des résultats déjà obtenus dans les branches historiques et dans la branche optimisée récente.

---

## 1. Point de départ

Les résultats consolidés à ce jour sont les suivants :

- la branche classique à centre carré retrouve **Bremner seul** à 7/9 ;
- la branche “une progression de carrés autour du centre” a été poussée très loin avec le script optimisé, jusqu’à `E ≤ 500 000` et `q ≤ 1 000 000` en balayage large, puis jusqu’à `q ≤ 10 000 000` sur une shortlist de triplets prometteurs ;
- aucun nouveau **7/9 primitif** ni aucun **8/9** n’a été trouvé dans cette famille ;
- en revanche, la cartographie à 6/9 révèle des **corridors fertiles**, en particulier autour de certains centres et de certains motifs de `square_mask` ;
- la branche à centre non nécessairement carré reste encore sous-explorée à cause d’un mur mémoire historique.

Conséquence : la v2 doit abandonner la logique “on pousse uniformément les bornes partout” au profit d’une recherche **multi-branches**, **instrumentée**, avec des **critères d’arrêt explicites**.

---

## 2. Objectifs de la v2

La v2 vise, par ordre d’ambition :

1. trouver un **8/9** ;
2. trouver un **nouveau 7/9 primitif** ;
3. dépasser proprement les anciennes bornes dans les branches encore mal couvertes ;
4. documenter de manière solide les zones mortes et les familles fertiles.

Un succès de la v2 n’implique pas forcément une découverte record : une **percée méthodologique** sur la branche à centre non carré ou une **classification expérimentale forte** des familles fertiles est aussi un résultat significatif.

---

## 3. Architecture générale de la v2

La v2 s’organise en cinq branches :

- **O — observabilité / analyse** : couche transverse d’extraction et de scoring ;
- **B2 — centre non nécessairement carré** : priorité maximale ;
- **D2 — progression unique, mais exploration guidée par motifs et corridors** ;
- **C2 — centre carré + quatre coins carrés**, montée d’échelle modérée ;
- **E2 — semi-magique centre zéro**, branche de soutien structurel ;
- **A2 — centre carré historique revisité**, en ciblé seulement.

Ordre de priorité global :

```text
B2 > D2 > C2 > A2 > E2
```

avec la couche **O** comme prérequis transversal.

---

## 4. Branche O — observabilité / analyse

### Rôle

Transformer les CSV bruts en objets exploitables mathématiquement.

### Livrables attendus

- `summaries/by_triplet.csv`
- `summaries/by_mask.csv`
- `summaries/by_center_band.csv`
- `results/promising/triples_prometteurs_v2.csv`
- `notes/corridors.md`

### Mesures à produire automatiquement

Pour chaque campagne, calculer :

- nombre de résultats distincts après déduplication ;
- fréquence par triplet `(A,E,J)` ;
- fréquence par `square_mask` ;
- regroupement par bandes de centres `E` ;
- distance moyenne des non-carrés au carré parfait le plus proche ;
- nombre de `q` distincts par triplet ;
- facteur d’échelle des multiples triviaux supprimés.

### Critère d’arrêt

La branche O ne s’arrête pas ; elle devient un outil permanent. En revanche, la **version minimale** de O est considérée comme prête dès qu’elle permet de produire automatiquement une shortlist `triples_prometteurs_v2.csv` à partir d’un CSV brut de campagne.

---

## 5. Branche B2 — centre non nécessairement carré

### Priorité

**Priorité n°1**.

### Motivation

C’est la branche la moins explorée en profondeur réelle. La borne historique `≤ 20 000` est une borne dictée par la mémoire, pas par l’épuisement mathématique de la famille.

### Objectif scientifique

Chercher des carrés magiques 3×3 avec huit cases extérieures carrées et un centre pas forcément carré.

### Stratégie computationnelle

Réécrire la branche avec :

- génération en flux ;
- traitement par blocs ;
- cribles modulaires précoces ;
- index partiel sur les paires opposées ;
- fusion retardée des candidats ;
- aucune structure globale géante en mémoire.

### Paliers

#### B2-1

```text
racines extérieures ≤ 50 000
```

But : dépasser proprement l’ancienne borne `20 000`.

#### B2-2

```text
racines extérieures ≤ 100 000
```

But : tester si la famille produit enfin des quasi-candidats 8/9 ou des motifs riches.

#### B2-3

```text
racines extérieures ≤ 250 000
```

But : établir une nouvelle borne sérieuse sur cette branche.

### Critères d’arrêt

- **Stop temporaire** si la version n’arrive pas à dépasser `20 000` sans mur mémoire après une réécriture raisonnable.
- **Poursuite forte** si des motifs prometteurs ou des quasi-candidats 8/9 apparaissent.
- **Gel de branche** si `≤ 100 000` est atteint proprement sans aucune structure nouvelle notable.

---

## 6. Branche D2 — progression unique guidée par motifs et corridors

### Priorité

**Priorité n°2**.

### Motivation

La branche large D' a maintenant bien ratissé l’espace global, mais la cartographie 6/9 révèle des structures locales prometteuses. La v2 doit exploiter cette structure au lieu de pousser encore des balayages uniformes.

### Sous-branches

#### D2-a — corridors

Identifier les centres `E` et les bandes de centres où les 6/9 sont anormalement fréquents.

#### D2-b — motifs de `square_mask`

Privilégier :

- les masques rares ;
- les triplets avec plusieurs `q` ;
- les cas où les non-carrés sont proches d’un carré ;
- les familles voisines du corridor Bremner.

#### D2-c — voisinage pythagoricien

Explorer des voisins proches dans la paramétrisation des triplets au lieu de balayer uniformément tout l’espace.

### Paliers

#### D2-1

Construire une shortlist enrichie :

```text
100 à 300 triplets prometteurs
```

#### D2-2

Reruns ciblés :

```text
qmax = 10 000 000
```

#### D2-3

Reruns ciblés sur top 20 / top 50 :

```text
qmax = 100 000 000
```

### Critères d’arrêt

- **Stop des balayages globaux uniformes** si aucune nouveauté n’apparaît au-delà des bornes déjà atteintes.
- **Poursuite ciblée** si un corridor donne plusieurs 6/9 ou un 7/9 atypique.
- **Gel partiel** si le top 200 à `qmax = 10^7` reste totalement stérile.

---

## 7. Branche C2 — centre carré et quatre coins carrés

### Priorité

**Priorité n°3**.

### Motivation

Branche négative mais propre, bien définie, et probablement extensible à coût modéré avec les outils modernes de crible.

### Objectif scientifique

Tester si le constat “6/9 seulement” reste vrai à bien plus grande échelle.

### Paliers

#### C2-1

```text
E ≤ 250 000
```

#### C2-2

```text
E ≤ 1 000 000
```

#### C2-3

Seulement si le débit reste bon et si le taux de configurations primitives reste intéressant.

### Mesures à suivre

- nombre total de configurations ;
- nombre de configurations primitives ;
- répartition par case bonus (`b,d,f,i`) ;
- éventuelle apparition d’un premier 7/9.

### Critères d’arrêt

- **Gel de branche** si aucun 7/9 n’apparaît jusqu’à `E ≤ 1 000 000` et si la structure qualitative ne change pas.
- **Poursuite** si un déséquilibre nouveau apparaît ou si des motifs inattendus émergent.

---

## 8. Branche A2 — centre carré historique revisité

### Priorité

**Priorité n°4**.

### Motivation

La branche A historique est déjà profonde. La v2 n’a pas vocation à refaire le même bruteforce. Elle doit seulement revisiter certaines sous-familles à la lumière des motifs révélés par D2 et C2.

### Stratégie

- reprise ciblée, pas massive ;
- sélection de sous-familles à partir des corridors fertiles ;
- usage préférentiel des cribles les plus fins.

### Critères d’arrêt

- branche secondaire uniquement ;
- aucun investissement massif tant que B2 et D2 n’ont pas livré leurs enseignements.

---

## 9. Branche E2 — semi-magique centre zéro

### Priorité

**Priorité n°5**.

### Rôle

Branche d’appui structurel, pas branche centrale de quête du 8/9 magique complet.

### Utilité

- générer des quadruplets pythagoriciens fertiles ;
- étudier des réseaux de sommes de deux carrés ;
- nourrir d’autres branches en motifs structurels.

### Critères d’arrêt

- poursuite légère et opportuniste ;
- pas de gros budget machine tant qu’une connexion claire avec les branches principales n’est pas établie.

---

## 10. Tableau de campagnes v2

## 10.1. Branche O — analyse

| ID | Script / outil | Entrée | Sortie | Critère d’arrêt |
| --- | --- | --- | --- | --- |
| O1 | `extract_promising_triples.py` | CSV brut 6/9–7/9 | `triples_prometteurs_v2.csv` | prêt dès qu’une shortlist 100–300 triplets est produite |
| O2 | `analyze_masks.py` | CSV brut | `by_mask.csv`, `corridors.md` | prêt dès que les masques rares et les corridors sont classés |
| O3 | `score_triplets.py` | CSV brut | `by_triplet.csv` | prêt dès que chaque triplet reçoit un score de fertilité |

## 10.2. Branche B2 — centre non carré

| ID | Script visé | Borne | Objectif | Critère d’arrêt |
| --- | --- | --- | --- | --- |
| B2-1 | `search_non_square_center_v2.py` | racines extérieures `≤ 50 000` | dépasser la borne 20 000 | stop si mur mémoire persistant après réécriture raisonnable |
| B2-2 | `search_non_square_center_v2.py` | racines extérieures `≤ 100 000` | chercher quasi-candidats 8/9 | stop si rien de nouveau qualitativement |
| B2-3 | `search_non_square_center_v2.py` | racines extérieures `≤ 250 000` | nouvelle borne robuste | gel si toujours aucun motif nouveau |

## 10.3. Branche D2 — progression unique guidée

| ID | Script | Borne | Objectif | Critère d’arrêt |
| --- | --- | --- | --- | --- |
| D2-1 | `magic_square_parallel_optimized.py` + shortlist v2 | top 100–300 triplets | shortlist fertile | stop quand la shortlist est stable |
| D2-2 | `magic_square_parallel_optimized.py` | `qmax = 10^7` | retester les corridors fertiles | stop si top 200 totalement stérile |
| D2-3 | `magic_square_parallel_optimized.py` | `qmax = 10^8` sur top 20–50 | attaque lourde ciblée | stop si aucun 7/9 atypique ni 8/9 |

## 10.4. Branche C2 — centre carré + coins carrés

| ID | Script visé | Borne | Objectif | Critère d’arrêt |
| --- | --- | --- | --- | --- |
| C2-1 | `search_center_corners_square_v2.py` | `E ≤ 250 000` | dépasser `E ≤ 60 000` | stop si résultats identiques à l’échelle précédente |
| C2-2 | `search_center_corners_square_v2.py` | `E ≤ 1 000 000` | tester stabilité du “6/9 seulement” | gel si aucun 7/9 et structure inchangée |

## 10.5. Branche A2 — centre carré ciblé

| ID | Script visé | Borne | Objectif | Critère d’arrêt |
| --- | --- | --- | --- | --- |
| A2-1 | à définir selon sous-famille | bornes ciblées | cross-check théorique-computationnel | stop si aucune sous-famille ne se détache |

## 10.6. Branche E2 — semi-magique centre zéro

| ID | Script visé | Borne | Objectif | Critère d’arrêt |
| --- | --- | --- | --- | --- |
| E2-1 | `search_semimagic_e0_squares.py` ou v2 | bornes modestes à moyennes | réservoir de motifs pythagoriciens | stop si pas d’apport structurel vers les autres branches |

---

## 11. Règles de décision globales

### Continuer une branche si

- elle produit un nouveau 7/9, un 8/9, ou un quasi-candidat très proche ;
- elle dépasse une borne historique importante ;
- elle révèle une nouvelle famille fertile ou un nouveau motif rare.

### Geler une branche si

- elle reproduit exactement les mêmes phénomènes à plus grande échelle ;
- son coût computationnel augmente sans enrichissement structurel ;
- une autre branche devient clairement plus prometteuse.

### Requalifier une branche en “branche de fond” si

- elle reste mathématiquement intéressante ;
- mais son rendement marginal devient trop faible.

---

## 12. Plan d’exécution recommandé

### Phase v2.1 — immédiate

1. Mettre en place la couche **O**.
2. Construire `triples_prometteurs_v2.csv`.
3. Concevoir la réécriture **B2**.

### Phase v2.2 — court terme

1. Lancer **B2-1**.
2. Lancer **D2-2** sur shortlist enrichie.
3. Préparer **C2-1**.

### Phase v2.3 — moyen terme

1. Monter **B2** à `100 000` si stable.
2. Lancer **C2-1** puis **C2-2** selon rendement.
3. Déclencher **D2-3** seulement sur top 20–50 réellement fertiles.

---

## 13. Critère de réussite de la v2

La v2 sera considérée comme une réussite si elle produit au moins l’un des quatre résultats suivants :

1. un **8/9** ;
2. un **nouveau 7/9 primitif** ;
3. une montée robuste de la branche B à des bornes nettement supérieures à l’historique ;
4. une cartographie expérimentale suffisamment forte pour reclasser clairement les branches fertiles et les branches mortes.

---

## 14. Références rapides

- Bremner, *On squares of squares* (1999) : http://www.multimagie.com/Bremner1.pdf
- Bremner, *On squares of squares II* (2001) : http://www.multimagie.com/Bremner2.pdf
- MystiMath — problème ouvert : https://mystimath.org/fr/articles/carre-magique-3x3-carres-parfaits-probleme-ouvert/
- MystiMath — recherche expérimentale : https://mystimath.org/fr/articles/recherche-experimentale-carres-magiques-de-carres/
- MystiMath — centre zéro : https://mystimath.org/fr/articles/carres-semi-magiques-centre-zero/
- Status consolidé : `STATUS_updated.md`
