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

## Politique de promotion des moteurs

Un moteur devient **privilégié** pour son domaine dès qu'il satisfait les quatre
critères suivants :

1. concordance avec un oracle indépendant à petite borne ;
2. conservation des classes et des compteurs attendus ;
3. benchmark reproductible montrant le gain annoncé ;
4. documentation de ses limites et de sa commande par défaut.

Le moteur promu est alors utilisé par les explorations suivantes. Les versions
antérieures restent archivées comme témoins et contrôles de non-régression ;
elles ne sont pas supprimées ni présentées comme moteur actif.

| Domaine | Moteur privilégié actuel | Preuve de promotion |
| --- | --- | --- |
| Like-Bremner elliptique | D3, tamis local à 16 premiers et résidus pré-calculés | concordance D2, 71 courbes, B4 indépendant ; [docs/45](docs/45-d3-local-closure-sieve.md) |
| Validation elliptique 7/9 | Pont D4 → B4 | Bremner retrouvé et masque classifié ; [docs/44](docs/44-elliptic-b4-bridge.md) |
| 7/9 exhaustif entier | B4 streaming, 256 shards au million | couverture des 36 masques et benchmark B11 |
| 8/9 et 9/9 exhaustif entier | B5/B6 streaming, 256 shards au million | validations croisées et revalidation R=1 000 000 |

Toute nouvelle optimisation doit d'abord passer ces quatre portes et mettre à
jour cette table, `STATUS.md` et la note de campagne correspondante.
