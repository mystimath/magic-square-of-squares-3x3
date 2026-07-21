# État du projet — Magic Square of Squares 3×3

_Mis à jour le 21 juillet 2026._

## État actuel

Le pipeline actif est la comparaison de formulations dans
`experiments/formulations_comparison/`. Les scanners B3–B6 disposent de tests,
de validations croisées et de rapports de couverture.

La revalidation de publication du 21 juillet 2026 confirme les résultats B4–B6 à R=1 000 000, les compteurs de couverture et le RSS B6 à 256 shards ; voir [docs/40-b4-b6-publication-revalidation-2026-07-21.md](docs/40-b4-b6-publication-revalidation-2026-07-21.md).

| Scanner | Couverture documentée | Résultat retenu |
| --- | --- | --- |
| B3 | Famille Bremner-like, boîte complète jusqu'à `R=1 000 000` | Bremner seul dans cette famille. |
| B4 | Tous les masques exactement 7/9, jusqu'à `R=1 000 000` | Bremner seul, à symétrie et primitivité près. |
| B5 | Tous les masques exactement 8/9, jusqu'à `R=1 000 000` | Aucun candidat. |
| B6 | Cas exactement 9/9, jusqu'à `R=1 000 000` | Aucun candidat. |

Ces bornes sont des résultats computationnels dans le domaine précisé, pas une
preuve d'impossibilité générale. Les références méthodologiques sont liées dans
le `README.md` et `ARCHITECTURE.md`.

## Pistes de recherche actives

1. **D0 — prototype elliptique autonome.** À courbe fixée, énumérer des
   combinaisons de générateurs de Mordell–Weil sous faible hauteur, certifier
   les points de `2E_n(Q)`, puis reconstruire des configurations 7/9. Le test
   de calibration est de retrouver Bremner pour sa courbe associée sans lire le
   catalogue B. Cette étape ne prétend pas encore borner tous les `n`.
2. **D1 — sélection de courbes.** Pilote sur les représentants
 sans facteur carré, rang Sage certifié au moins 2, puis D0 à très faible hauteur.
3. **D2 — terminé.** Les neuf courbes D1 restent négatives sauf `E_154`; ne pas augmenter uniformément la hauteur.
4. **D3 — tamis de fermeture terminé jusqu'à la borne 20.** Sur les 71
   courbes de rang positif certifié jusqu'à `n=200`, soit 3 183 200 paires,
   Bremner sur `E_154` reste l'unique fermeture. Le moteur par défaut pré-calcule
   les résidus pour 16 premiers ; voir `docs/45-d3-local-closure-sieve.md`.
5. **D4 — pont elliptique → B4.** Terminé pour D0–D3 : après normalisation
   et déduplication, `E_154`/Bremner est l'unique fermeture, dans l'orbite
   `corner_edge_nonincident`.
6. **B4–B6.** Ils restent les validateurs exhaustifs dans une boîte de racines,
   pas la voie de découverte à prolonger uniformément.

## Priorité suivante

Ne pas augmenter uniformément la borne de coefficients au-delà de 20 sur les 71
courbes déjà traitées. La prochaine campagne doit changer l'axe de couverture :
sélectionner de nouvelles courbes ou familles elliptiques justifiées, avec rang
positif et générateurs de faible hauteur, puis appliquer D3 à petite borne et
valider toute fermeture par D4/B4.

## Traçabilité

L'ancien journal détaillé est conservé dans
[`docs/history/status-2026-07-08.md`](docs/history/status-2026-07-08.md). Les
nouveaux rapports détaillés vont dans `docs/` ou `results/`, pas dans ce tableau
de bord.
