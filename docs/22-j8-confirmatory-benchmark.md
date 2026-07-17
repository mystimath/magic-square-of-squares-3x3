# J8 — Benchmark confirmatoire et validation croisée

_Exécution du 16 juillet 2026. Borne unique `R=100000`._

## 1. Domaine et protocole

Le domaine final commun est celui des grilles magiques 3×3 positives à neuf
carrés distincts, toutes les racines étant au plus `R`, quotientées par `D4`.
Le catalogue de progressions est généré une fois par la paramétrisation
primitive, puis injecté dans B1, B2, C et D-probe.

Chaque adaptateur est exécuté cinq fois. L'ordre est tournant et inversé entre
les répétitions. Les classes finales sont comparées objet par objet. Le
catalogue paramétrique est en outre validé indépendamment, à la même borne, par
l'oracle quadratique exhaustif.

Commande principale :

```powershell
python experiments\formulations_comparison\benchmark_shared_catalog.py `
  --bound 100000 --repetitions 5 --catalog-engine parametric `
  --output results\formulations_comparison\benchmarks\shared_catalog_parametric_r100000.json
```

## 2. Validation du catalogue

Les deux générateurs produisent exactement les mêmes 122 640 progressions :

| Générateur | Temps (s) | Statut |
| --- | ---: | --- |
| quadratique | 607,693954 | complet |
| paramétrique primitif | 0,421561 | complet |

Le facteur mesuré est `1441,53`. Cette égalité objet par objet fournit une
seconde voie indépendante pour la brique commune du benchmark.

## 3. Résultats confirmatoires

Le catalogue paramétrique du benchmark principal prend `0,395904` seconde.

| Adaptateur | Minimum (s) | Médiane (s) | Maximum (s) |
| --- | ---: | ---: | ---: |
| B1 | 0,103635 | 0,105599 | 0,132432 |
| B2 | 0,090774 | 0,117933 | 0,141048 |
| C | 4,678045 | 4,717564 | 4,772368 |
| D-probe | 7,555667 | 7,676005 | 7,749274 |

Les quatre ensembles canoniques sont exactement égaux et vides. Cette absence
est un résultat exhaustif borné à `R=100000` dans le domaine défini ; elle ne
constitue pas une preuve globale d'absence de carré magique de neuf carrés.

## 4. Compteurs structurels

| Formulation | Objets traduits | Groupes | Relations testées | Hits structurels |
| --- | ---: | ---: | ---: | ---: |
| B1 | 122 640 progressions | 55 791 centres | 238 294 paires | 0 |
| B2 | 122 640 progressions | 114 267 différences | 9 920 paires | 0 |
| C | 122 640 triangles | 114 267 aires | 9 920 paires | 0 |
| D-probe | 122 640 points certifiés | 114 267 valeurs de `n` | 9 920 paires | 0 |

B2 réduit d'un facteur `24,02` le nombre de paires par rapport à B1. Malgré
cela, B1 est légèrement plus rapide en médiane dans cette implémentation. Les
opérations de B1 sont simples, les durées restent voisines d'un dixième de
seconde et leurs distributions se recouvrent : aucun classement temporel
intrinsèque B1/B2 n'est établi.

C et D-probe ont un coût propre nettement supérieur, dû aux objets rationnels,
aux normalisations et aux certificats exacts. D-probe reste une traduction du
catalogue entier partagé ; ce résultat ne mesure ni recherche Sage autonome,
ni rang, ni générateurs, ni hauteur elliptique.

## 5. Conclusions et limites

1. L'oracle A cubique n'est pas compétitif pour une borne de cette taille ; il
   reste un validateur à petite borne.
2. La formulation B fournit le cadre entier exhaustif le plus efficace dans
   nos prototypes et dans les bornes testées.
3. B2 possède le meilleur compteur structurel, mais pas un avantage temporel
   stable sur B1 dans CPython.
4. C ajoute surtout un coût de représentation dans ce moteur partagé ; sa
   valeur est géométrique et comme validation de transformation.
5. D conserve son rôle principal de découverte elliptique et de construction
   théorique, non mesuré par ce classement entier dépendant de B2.
6. Les temps qualifient ces algorithmes et cette implémentation CPython ; ils ne
   sont pas des propriétés absolues des formulations mathématiques.

Le pic mémoire du processus et une répétition sur une seconde machine ne sont
pas encore disponibles. Les répétitions ne sont pas isolées dans des processus
distincts, mais l'ordre alterné limite les biais de position.

## 6. Porte G6

Le benchmark confirmatoire sur la machine principale est achevé et cohérent
avec J7. Les résultats sont suffisamment structurés pour commencer la rédaction
du papier, à condition de conserver les limites ci-dessus. Une répétition sur
un autre environnement renforcerait la portée expérimentale mais n'est pas
nécessaire pour établir les identités, compteurs et exhaustivités bornées déjà
certifiés.

Artefacts :

- `results/formulations_comparison/benchmarks/catalog_validation_r100000.json` ;
- `results/formulations_comparison/benchmarks/shared_catalog_parametric_r100000.json`.

J9 n'est pas commencé. Aucun commit ni push n'a été effectué.
