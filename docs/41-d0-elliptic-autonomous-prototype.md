# D0 — Prototype elliptique autonome vers Bremner

_Étape ouverte le 21 juillet 2026._

## But

Construire un générateur de candidats 7/9 qui ne part pas du catalogue B de
progressions entières. À une courbe congruente fixée

```text
E_n : y² = x³ - n²x,
```

le prototype doit énumérer des combinaisons bornées de générateurs de
Mordell–Weil, retenir les points possédant le certificat exact de trois carrés,
et tester les relations entre leurs abscisses nécessaires à une grille 7/9.

## Calibration

La première courbe est celle de la structure Bremner avec différence verticale
`n = 138600`. Le prototype devra retrouver, par énumération elliptique, les
progressions de centres `139129 = 373²` et `180625 = 425²`, puis vérifier que
leur écart `41496` engendre la progression horizontale
`529 = 23², 42025 = 205², 83521 = 289²`.

Les valeurs connues servent seulement de test d’acceptation après l’énumération
sur `E_138600`; le code ne doit pas appeler le catalogue B pour les produire.

## Contrat D0

- SageMath est la source des générateurs, du rang et de la hauteur canonique.
- Les opérations sur points et la reconstruction finale restent vérifiées par
  l’arithmétique rationnelle exacte locale et le validateur commun.
- La borne porte sur les coefficients des générateurs ou la hauteur, jamais sur
  une prétendue boîte de racines exhaustive.
- Un échec à retrouver Bremner invalide le prototype ; une réussite ne prouve
  aucune couverture des autres courbes `E_n`.

## Sortie attendue

Un JSON reproductible doit indiquer la courbe, les générateurs certifiés, la
borne d’énumération, les points testés, les certificats de trois carrés et les
candidats reconstruits. Aucun scan large de `n` ne sera lancé avant cette
calibration.
## Première calibration réussie

SageMath 10.9, avec `proof=True`, calcule sur `E_138600` un rang 2 et les
générateurs `(-88200,31752000)` et `(315000,158760000)`. La boîte de
coefficients `[-1,1]^2`, soit huit moitiés non nulles, produit quatre centres
certifiés. Une seule paire ferme une grille 7/9 : les centres `139129` et
`180625`, de différence `41496`, avec différence verticale `138600`.

Les moitiés utilisées sont respectivement `-G2` et `-G1`; leurs doubles donnent
les progressions de racines `(23,373,527)` et `(205,425,565)`. Le validateur
commun confirme la grille Bremner, positive, distincte, primitive et magique,
avec exactement sept carrés. L’artefact est
`results/formulations_comparison/sage/d0_e138600_bound1.json`.

Cette réussite calibre le moteur sur une courbe choisie; elle ne constitue pas
encore une recherche autonome sur l’ensemble des valeurs de `n`.
## Élargissement local et normalisation

Sur `E_138600`, les boîtes de coefficients donnent :

| Boîte des coefficients | Moitiés testées | Centres certifiés | Fermetures 7/9 |
| --- | ---: | ---: | ---: |
| `[-1,1]^2` | 8 | 4 | 1 |
| `[-2,2]^2` | 24 | 12 | 1 |
| `[-3,3]^2` | 48 | 24 | 1 |

La seule fermeture reste Bremner. L’augmentation locale de hauteur ajoute donc
des points certifiés, mais aucun faux signal 7/9.

La relation `138600 = 30² × 154` permet d’indexer la même courbe rationnelle par
son noyau sans facteur carré `154`. Sur `E_154`, la même boîte `[-1,1]^2`
retrouve la configuration rationnelle correspondante. La normalisation entière
minimale calculée par D0 est `root_scale = 30`, donc `value_scale = 900`, et le
validateur commun retrouve exactement la grille primitive de Bremner.

La porte suivante D1 sera un **sélecteur de courbes** : travailler sur des
représentants `n` sans facteur carré, retenir des courbes de rang certifié au
moins deux ou issues d’une famille justifiée, puis lancer D0 sous une petite
borne de coefficients. Aucun balayage uniforme de racines ni de valeurs de `n`
n’est engagé à ce stade.
