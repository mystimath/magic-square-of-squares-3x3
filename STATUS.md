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
4. **D3 — fermeture structurée.** Étudier directement la condition quadratique liant deux points de `2E_n(Q)` avant reconstruction.
5. **D4 — pont elliptique → B4.** La calibration `E_138600` extrait trois
   progressions arithmétiques de Bremner et B4 retrouve ensuite exactement sa
   classe à `R=601`. Généraliser cette interface aux sorties normalisées D1–D3,
   afin de classer les fermetures par masque plutôt que de balayer une boîte.
6. **B4–B6.** Ils restent les validateurs exhaustifs dans une boîte de racines,
   pas la voie de découverte à prolonger uniformément.

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
