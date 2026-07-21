# Consignes locales — Magic Square of Squares 3×3

## Cartographie

- `experiments/formulations_comparison/` : moteurs actifs, benchmarks et tests.
- `experiments/formulations_comparison/common/` : validation partagée.
- `results/formulations_comparison/` : artefacts de campagnes.
- `docs/` : méthode et résultats ; `docs/history/` contient les synthèses
  remplacées, notamment l'ancien journal d'état du 8 juillet 2026.
- `src/` et `archive/` : scripts historiques ; ne pas les présenter comme la
  voie active sans justification.

## Avant de modifier

Lire `README.md`, `STATUS.md` et le document Bx correspondant. Toute
optimisation doit préserver la couverture et être validée par les tests de
`experiments/formulations_comparison/tests/` ainsi que par une comparaison à
petite borne lorsqu'elle change un scanner.

## Documentation de campagne

Un nouveau run reproductible doit fournir : la commande, la borne, le mode,
la version du moteur, les métriques essentielles et l'artefact de résultat.
Mettre le détail dans `docs/` ou `results/`; réduire `STATUS.md` à l'état et à
la prochaine décision. Ne modifier ni les résultats publiés ni les journaux
historiques pour les adapter à une nouvelle narration.

## Coût

Les scans à grande borne, benchmarks complets et analyses Sage sont coûteux :
ne les exécuter que sur demande explicite. Pour les changements de code,
commencer par le test unitaire ou une borne de contrôle minimale.
