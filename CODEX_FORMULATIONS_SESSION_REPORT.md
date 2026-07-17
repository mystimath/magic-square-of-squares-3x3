# Rapport de session — comparaison des formulations

_Mise à jour : 17 juillet 2026._

## État atteint

Les jalons J0 à J10 disposent désormais de livrables locaux. J8 a confirmé le
benchmark à `R=100000`, J9 a produit le manuscrit français et J10 a consigné
l'audit final de diffusion. Aucun résultat ne prétend résoudre le problème
ouvert.

## Briques créées ou adaptées

- noyau exact de validation et canonicalisation `D4` ;
- prototypes A, B1, B2, C et D-probe ;
- sonde SageMath et contrôle PARI/GP sur `E_24` ;
- catalogue partagé et générateur paramétrique primitif ;
- benchmarks pilotes et confirmatoires avec JSON/CSV ;
- tests de correspondance et validation croisée ;
- documents mathématiques, rapports J0–J9 et manuscrit.

## Tests et résultats

- `31` tests réussis ;
- égalité des catalogues à `R=100000` sur 122 640 objets ;
- accélération du catalogue : facteur `1441,53` ;
- égalité des classes B1/B2/C/D-probe à la borne confirmatoire ;
- zéro classe 9/9 dans cette borne complète.

## Limites

- temps propres à CPython et à la machine documentée ;
- mémoire totale non mesurée de manière robuste ;
- D-probe entier non indépendant de B ;
- recherche elliptique autonome par hauteur non réalisée ;
- le cas 3×3 demeure ouvert dans la littérature évaluée par les pairs ;
- la prépublication de Hill est signalée, mais son passage final ne suffit pas
  à établir la non-existence ;
- une relecture scientifique externe et une répétition sur une seconde machine
  restent recommandées.

## Relecture finale et diffusion du 17 juillet

La relecture des §4–§6 a été intégrée : preuve de A ≡ B1 ≡ B2, borne
explicite sur les neuf racines, démonstration de la borne paramétrique et
documentation de la déduplication réellement effectuée par le code.

Les sources Lucas 1876 et 1894, Bremner 1999 et 2001, Sigler et Koblitz ont été
auditées. Le §15 distingue désormais les familles elliptiques de Bremner 1999
du cadre K3 systématique de Bremner 2001. Bremner 1980, LaBar 1984 et Silverman
2009 ont été ajoutés à la bibliographie.

La relecture stylistique, les métadonnées d'auteur et la documentation de
diffusion ont été finalisées. Les résultats 2025–2026 sur l'état du problème
ont été ajoutés avec une distinction explicite entre le résultat évalué par les
pairs de Rome–Yamagishi et la revendication non validée de Hill. Une relecture
scientifique externe des preuves reste recommandée avant une soumission en
revue.
Commandes de contrôle :

```powershell
python -m unittest discover -s experiments\formulations_comparison\tests -v
git diff --check
git status --short
```

Le présent rapport documente les contrôles locaux ; il ne déclenche aucun
envoi distant.

## Release autonome 1.0.0

Une release autonome a été construite par liste blanche sous :

```text
dist/formulations-comparison-v1.0.0/
dist/formulations-comparison-v1.0.0.zip
```

Elle contient 46 fichiers au total, dont 44 fichiers sources autorisés suivis
dans `MANIFEST.json`, plus le manifeste et `SHA256SUMS`. Les autres moteurs,
journaux, résultats historiques, caches et fichiers temporaires sont exclus.

- licence : MIT ;
- tests depuis le paquet : 31 réussis ;
- vérification du manifeste : 44/44 ;
- fichiers `__pycache__` ou `.pyc` : 0 ;
- ZIP reproductible sur deux constructions ;
- SHA-256 du ZIP :
  `0b1ca489072e4cdd5cb9fe034656c2d804a3b858a9b6024382b75ba0e76bb365`.

Le constructeur reproductible est `scripts/build_formulations_release.py` et
les modèles de métadonnées sont sous
`release/formulations-comparison-v1.0.0/`.
