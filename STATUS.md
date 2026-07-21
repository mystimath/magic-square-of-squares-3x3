# État du projet — Magic Square of Squares 3×3

_Mis à jour le 21 juillet 2026._

## État actuel

Le pipeline actif est la comparaison de formulations dans
`experiments/formulations_comparison/`. Les scanners B3–B6 disposent de tests,
de validations croisées et de rapports de couverture.

| Scanner | Couverture documentée | Résultat retenu |
| --- | --- | --- |
| B3 | Famille Bremner-like, boîte complète jusqu'à `R=1 000 000` | Bremner seul dans cette famille. |
| B4 | Tous les masques exactement 7/9, jusqu'à `R=1 000 000` | Bremner seul, à symétrie et primitivité près. |
| B5 | Tous les masques exactement 8/9, jusqu'à `R=1 000 000` | Aucun candidat. |
| B6 | Cas exactement 9/9, jusqu'à `R=1 000 000` | Aucun candidat. |

Ces bornes sont des résultats computationnels dans le domaine précisé, pas une
preuve d'impossibilité générale. Les références méthodologiques sont liées dans
le `README.md` et `ARCHITECTURE.md`.

## Priorité suivante

Ne pas lancer une augmentation uniforme de borne par défaut. Avant une nouvelle
campagne, formuler une hypothèse ou un changement de couverture mesurable,
valider à petite borne contre les oracles existants, puis documenter la décision
et son coût.

## Traçabilité

L'ancien journal détaillé est conservé dans
[`docs/history/status-2026-07-08.md`](docs/history/status-2026-07-08.md). Les
nouveaux rapports détaillés vont dans `docs/` ou `results/`, pas dans ce tableau
de bord.
