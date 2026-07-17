# J10 — Audit final avant diffusion

_Jalon exécuté le 17 juillet 2026._

## Décisions scientifiques et éditoriales

- l'état récent du problème est désormais explicite : Rome et Yamagishi (2025)
  démontrent l'existence pour tout ordre au moins égal à 4, tandis que le cas
  3×3 reste non résolu dans la littérature évaluée par les pairs ;
- la prépublication de Hill, version 3 du 7 avril 2026, est citée sans être
  tenue pour démonstrative : son étape finale compare des coefficients sans
  avoir établi l'identité polynomiale nécessaire ;
- les notations signées `p,q` et les amplitudes positives `r,s` sont maintenant
  distinguées ;
- la terminologie française a été uniformisée autour de « nombre congruent » ;
- la bibliographie compte 16 références, toutes appelées dans le texte, avec
  les DOI et statuts éditoriaux pertinents.

## Contrôles du manuscrit

- dernière lecture intégrale du texte et confrontation des tableaux aux
  artefacts JSON confirmatoires ;
- contrôle automatique des 16 définitions bibliographiques et de leurs
  appels : aucune référence absente, dupliquée, inutilisée ou indéfinie ;
- résolution des 22 cibles de la table des matières et de la figure locale ;
- conversion du Markdown GFM en HTML avec Pandoc et `--fail-if-warnings` ;
- production d'un PDF final de 15 pages à partir du rendu HTML autonome ;
- validation YAML de `CITATION.cff` et contrôle de sa version, de sa date, de
  l'auteur et de l'ORCID ;
- recherche des marqueurs provisoires et des formulations obsolètes : aucun
  reste dans les fichiers de diffusion actifs.

## Contrôles logiciels

- 31 tests unitaires réussis sous CPython 3.11.15 ;
- syntaxe du constructeur d'archive validée ;
- aucune nouvelle campagne longue n'a été lancée : les résultats publiés sont
  ceux des artefacts conservés et déjà contrôlés objet par objet.

## Contrôles de l'archive

- reconstruction par l'allowlist de `scripts/build_formulations_release.py` ;
- génération de `MANIFEST.json` et `SHA256SUMS`, puis vérification indépendante
  de chaque taille et empreinte ;
- identité contrôlée entre les sources allowlistées, le répertoire de diffusion
  et le contenu de l'archive ZIP ;
- reproductibilité contrôlée par deux constructions successives donnant la
  même empreinte SHA-256.

## Limites maintenues

Les mesures mémoire, une répétition sur une seconde machine et une relecture
scientifique externe restent souhaitables. Elles sont présentées comme limites
ou prolongements, non comme résultats déjà acquis. Elles n'affectent ni la
cohérence interne du paquet ni la portée bornée explicitement revendiquée.

## Statut

Le manuscrit et le paquet autonome 1.0 sont prêts pour diffusion dans leur
périmètre déclaré. Aucun commit, envoi distant ou dépôt sur une plateforme de
publication n'a été effectué au cours de cet audit.

Le DOI Zenodo `10.5281/zenodo.21418008` est réservé pour la diffusion 1.0 et
est inclus dans les métadonnées du paquet final ; le record Zenodo demeure à
publier par son déposant.
