# Architecture de recherche — Magic Square of Squares 3×3

## Chemin actif

Les scanners actifs se trouvent dans `experiments/formulations_comparison/`.
Ils utilisent les modèles et oracles de `prototypes/` et le contrat de
validation de `common/validation.py`.

```text
paramétrisation canonique
        ↓
catalogue / flux d'incidences
        ↓
préfiltre algébrique et test de carré
        ↓
reconstruction et canonicalisation D4
        ↓
CSV/JSON dans results/  →  documentation de campagne dans docs/
```

Les familles B3 à B6 sont les voies documentées dans le `README.md` : B3 est
spécialisée Bremner-like, B4 couvre exactement 7/9, B5 exactement 8/9 et B6
exactement 9/9. Les tests assurent les équivalences à petite borne ; les
artefacts de benchmark établissent les mesures de performance.

## Frontières

- `src/` conserve les recherches antérieures et n'est pas une dépendance du
  pipeline B3–B6.
- `archive/` est en lecture historique.
- `logs/` contient des traces de campagne, pas une documentation de référence.
- `release/` est un artefact de distribution autonome.

## Documents de référence

- Le `README.md` publie les résultats actuellement retenus.
- Le `STATUS.md` est le tableau de bord court.
- Les documents numérotés `docs/27` à `docs/39` sont les preuves de couverture,
  validations et décisions d'optimisation du pipeline actif.
- [Le journal historique du 8 juillet 2026](docs/history/status-2026-07-08.md)
  est conservé pour la traçabilité ; il n'est plus l'état courant.
