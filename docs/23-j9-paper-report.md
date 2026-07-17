# J9 — Rapport de rédaction du papier

_Jalon exécuté le 16 juillet 2026._

> Ce rapport conserve l'état historique du jalon J9. Il est complété et
> remplacé, pour la diffusion 1.0, par l'audit final J10 du 17 juillet 2026.

## Livrables

- `paper/formulations_comparison/comparaison_algorithmique_formulations_carre_magique_carres.md` ;
- `paper/formulations_comparison/references_notes.md`.

Le manuscrit contient 20 sections, un résumé, une bibliographie provisoire et
une section de reproductibilité. Il synthétise exclusivement les résultats
validés de J0–J8 ; aucun nouveau benchmark ou run scientifique n'a été lancé
pour compléter la rédaction.

## Conclusion scientifique retenue

- B est le meilleur cadre entier exhaustif dans les prototypes et bornes
  testés ;
- A reste l'oracle direct de validation à petite borne ;
- C est principalement une traduction géométrique et un contrôle indépendant
  des transformations ;
- D est un moteur théorique et constructif majeur, mais le D-probe du benchmark
  entier dépend du catalogue B et ne mesure pas une recherche Sage autonome ;
- le classement temporel B1/B2 n'est pas stable, tandis que l'avantage
  structurel de B2 sur le nombre de relations est net ;
- formulation, algorithme et implémentation sont explicitement séparés.

## Données principales reprises

- borne confirmatoire `R=100000` ;
- 122 640 progressions ;
- égalité exacte des catalogues quadratique et paramétrique ;
- 607,693954 s contre 0,421561 s, facteur 1441,53 ;
- cinq répétitions alternées des adaptateurs ;
- sorties A/B/C/D-probe qualifiées selon leur domaine réel ;
- zéro classe 9/9 dans la borne, sans extrapolation globale.

## Vérifications effectuées

- concordance des chiffres avec les JSON J8 ;
- présence des 20 sections prévues ;
- `git diff --check` sans erreur ;
- 31 tests réussis avant la rédaction ;
- notices primaires de Bremner 1999 et 2001 vérifiées auprès de l'éditeur.

## Validations encore nécessaires avant soumission

1. relire intégralement le manuscrit sur le style et l'homogénéité éditoriale ;
2. vérifier la convention de l'auteur, de l'affiliation et de l'ORCID ;
3. décider du format de soumission, puis convertir en LaTeX si nécessaire ;
4. envisager une répétition sur une seconde machine et une mesure mémoire ;
5. obtenir une relecture scientifique externe des preuves révisées ;
6. décider si Gardner et Sallows doivent être cités comme sources primaires.

Les audits de Bremner 1999 et 2001, Lucas 1876 et 1894, Sigler et Koblitz sont
intégrés. Silverman [14] fournit désormais la référence standard sur la hauteur
canonique et le groupe de Mordell–Weil.

## Statut

J9 est rédigé sous forme de manuscrit de travail. Il est scientifiquement
cohérent avec les artefacts disponibles et ses principaux blocages
bibliographiques sont levés. Il n'est pas encore prêt à être soumis avant la
relecture stylistique et externe, la validation des métadonnées d'auteur et le
choix du format. Aucun commit, push ou publication n'a été effectué.
