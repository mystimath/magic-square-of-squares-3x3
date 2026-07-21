# D3 — Tamis local de la fermeture elliptique like-Bremner

_Expérience exécutée le 21 juillet 2026._

## Résultat

D3 traite directement la condition de fermeture entre deux centres certifiés
sur une même courbe congruente `E_n` :

```text
z² = 2*x_haut - x_bas - n.
```

Sur toutes les 71 courbes sans facteur carré de rang positif certifié dans D1
jusqu'à `n=200`, et dans la boîte de coefficients `[-20,20]^rang`, l'unique
fermeture exacte est Bremner sur `E_154`. Les 62 courbes de rang 1, auparavant
écartées par le seuil heuristique de rang 2, ne produisent aucun candidat.

| Domaine | Centres | Paires | Tests exacts après tamis | Fermetures | Classes 7/9 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 62 courbes de rang 1 | 1 240 | 11 780 | 524 | 0 | 0 |
| 9 courbes de rang ≥ 2 | 7 560 | 3 171 420 | 33 282 | 1 | 1 |
| Total | 8 800 | 3 183 200 | 33 806 | 1 | 1 |

La validation D4/B4 normalise cette fermeture et retrouve uniquement la classe
canonique de Bremner, dans l'orbite `corner_edge_nonincident`.

## Sûreté du tamis

Pour chaque petit premier `p`, D3 pré-calcule la réduction de chaque centre
rationnel modulo `p`. Si le dénominateur est divisible par `p`, ce premier est
considéré comme indécis et ne rejette rien. Sinon, une paire est rejetée lorsque

```text
2*x_haut - x_bas - n (mod p)
```

n'appartient pas à l'ensemble des résidus quadratiques modulo `p`. Tout carré
rationnel passe nécessairement chacun de ces tests : le tamis ne peut donc pas
supprimer une fermeture exacte. L'absence d'obstruction locale n'est pas une
preuve ; les survivants sont toujours contrôlés par racine rationnelle exacte,
reconstruction magique, masque 7/9, positivité et distinction.

Le contrôle à borne 3 sur les neuf courbes de rang 2 concorde exactement avec
D2 : seule `E_154` ferme et produit Bremner.

## Optimisation retenue

La première version réduisait chaque grand rationnel à chaque paire. La version
retenue pré-calcule une fois les résidus des centres et ne construit le grand
rationnel qu'après le tamis. Seize premiers sont désormais le défaut :

```text
13, 29, 19, 17, 23, 31, 7, 11, 37, 41, 43, 47, 53, 59, 61, 67
```

| Borne | Variante | Tests exacts | Temps paires | Temps total |
| ---: | --- | ---: | ---: | ---: |
| 10 | 8 premiers, réduction par paire | 55 509 | 13,848 s | 18,719 s |
| 10 | 8 premiers pré-calculés | 55 932 | 1,240 s | 6,352 s |
| 10 | 16 premiers pré-calculés | 2 201 | 0,260 s | 5,225 s |
| 20 | 8 premiers pré-calculés | 813 527 | 76,524 s | 100,124 s |
| 20 | 16 premiers pré-calculés | 33 282 | 9,305 s | 33,413 s |

À borne 20, le moteur retenu divise donc le temps des paires par `8,22` et le
temps total par `3,00` face au pré-calcul à huit premiers. Les variations du
nombre de survivants entre réduction directe et pré-calcul proviennent des
premiers divisant un dénominateur individuel : le pré-calcul passe alors de
façon conservatrice, sans risque de faux négatif.

## Reproduction

Depuis WSL/SageMath :

```bash
~/miniforge3/bin/conda run -n sage python \
  experiments/formulations_comparison/sage_search_bremner_d3.py \
  --n-values <liste D1 de rang positif> --coefficient-bound 20 \
  --output results/formulations_comparison/sage/d3_squarefree_n200_positive_rank_bound20.json
```

Artefact principal :
`results/formulations_comparison/sage/d3_squarefree_n200_positive_rank_bound20.json`.
Validation B4 :
`results/formulations_comparison/sage/d4_b4_bridge_d3_positive_rank_bound20.json`.

## Décision

Une nouvelle hausse uniforme de la boîte de coefficients sur ces 71 courbes est
peu prometteuse : le passage de 3 à 20 n'ajoute aucune fermeture. La prochaine
étape doit changer l'axe de couverture : sélectionner de nouvelles courbes ou
familles elliptiques justifiées (notamment rang positif et générateurs de faible
hauteur), puis leur appliquer D3 à petite borne. Les familles elliptiques de
Bremner restent prioritaires sur un balayage brut des racines.
