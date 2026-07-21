# D4 — Pont elliptique vers le validateur B4

_Mis à jour le 21 juillet 2026._

## But

Relier un candidat produit par la voie elliptique au scanner B4, sans relancer
une énumération uniforme des racines. La voie elliptique sert à proposer des
configurations rares ; B4 vérifie alors exactement les quatre termes restants,
la primitivité et les 36 masques 7/9.

## Calibration Bremner

La sortie D0 `results/formulations_comparison/sage/d0_e138600_bound1.json`
contient la grille entière de Bremner. Le module
`prototypes/elliptic_b4_bridge.py` en extrait les trois progressions complètes
de la paramétrisation additive :

| Racines | Pas au carré |
| --- | ---: |
| `(23, 205, 289)` | `41496` |
| `(23, 373, 527)` | `138600` |
| `(205, 425, 565)` | `138600` |

Injectées seules dans `search_lo_shu_seven_box(R=601)`, elles retournent la
classe canonique de Bremner et aucun autre résultat. Le test
`test_elliptic_b4_bridge.py` conserve cette calibration.

## Contrat de l'interface

`progressions_from_d0_artifact` accepte une grille de valeurs entières sous
`candidate.grid` ou `candidate.integer_normalization.grid`. Il ne retient que
les triplets strictement positifs, croissants et carrés parfaits des trois
lignes de paramètres de B4. `search_b4_from_d0_artifact` passe ensuite ce
catalogue parcimonieux au moteur B4 existant.

La complétude de B4 demeure celle du catalogue qui lui est fourni : elle ne
transforme pas une exploration elliptique bornée en preuve globale. C'est une
validation exacte et un classificateur de masque pour les candidats elliptiques.

## Suite contrôlée

1. Normaliser les sorties D1–D3 dans le même schéma de grille rationnelle puis
   entière.
2. Extraire les progressions et mesurer le taux de fermeture par masque B4.
3. N'élargir la hauteur elliptique ou la sélection de courbes que si cette
   mesure apporte une fermeture nouvelle ou un filtre prédictif vérifiable.

## Premier passage D0--D2

Le script `analyze_elliptic_b4_bridge.py` parcourt aussi les structures
imbriquées D1 et D2, déduplique les grilles normalisées et choisit la plus petite
borne B4 couvrante. Les trois artefacts déjà disponibles donnent le même bilan :

| Source | Grilles entières distinctes | Borne B4 | Classes | Orbite |
| --- | ---: | ---: | ---: | --- |
| D0 `E_154`, borne 1 | 1 | 601 | 1 | `corner_edge_nonincident` |
| D1 jusqu'à `n=200`, borne 1 | 1 | 601 | 1 | `corner_edge_nonincident` |
| D2, coefficients jusqu'à 3 | 1 | 601 | 1 | `corner_edge_nonincident` |

Cette unique grille est Bremner. D4 confirme donc que les fermetures D1--D2 ne
cachent ni une nouvelle classe ni un nouveau masque : elles redécouvrent le
même point de la courbe `E_154`. Le prochain gain doit venir de D3 (sélection
par condition de fermeture), non d'une nouvelle traversée uniforme de D2.

Artefacts :
`results/formulations_comparison/sage/d4_b4_bridge_d0_e154_bound1.json`,
`d4_b4_bridge_d1_n200_bound1.json` et
`d4_b4_bridge_d2_bounds2_3.json`.

## Passage D3

L'artefact D3 couvrant les 71 courbes de rang positif certifié jusqu'à `n=200`
et la borne de coefficients 20 contient une seule grille entière distincte.
Le pont extrait les trois progressions de Bremner ; B4 retourne une classe dans
l'orbite `corner_edge_nonincident`. Aucun nouveau masque n'est introduit.

Artefact :
`results/formulations_comparison/sage/d4_b4_bridge_d3_positive_rank_bound20.json`.
