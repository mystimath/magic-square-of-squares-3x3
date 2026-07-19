# B15 — Regroupement des écritures par shard

_Pilote exécuté le 19 juillet 2026._

## Objectif

B12 et B13 ont montré que l'ordre de génération disperse les écritures entre
les shards. B15 ajoute l'option `--group-writes-by-shard` : toutes les
incidences sont d'abord matérialisées dans un tampon par shard, puis chaque
fichier est écrit en une seule séquence.

Le mode ouvre au plus un handle d'écriture à la fois et supprime les
réouvertures et flushes intermédiaires. En contrepartie, les incidences sont
conservées en mémoire jusqu'à la phase d'écriture.

## Pilote

À `R=100000` et 256 shards, trois répétitions ont comparé le témoin courant
au mode regroupé. Les deux variantes conservent les mêmes classes et compteurs :
122640 progressions, 367920 incidences, 86154 valeurs indexées et 3185
incidences maximales par shard.

| Mode | Temps des répétitions | Ouvertures | Handles simultanés | Octets matérialisés |
| --- | --- | ---: | ---: | ---: |
| témoin | 3,743 / 3,677 / 3,723 s | 256 | 256 | 0 |
| regroupé | 3,714 / 3,737 / 3,649 s | 256 | 1 | 9198000 |

La médiane est comparable : environ 3,70 s dans les deux cas. Le regroupement
ne constitue donc pas une accélération, mais il supprime effectivement la
dispersion et peut contourner une limite stricte du système sur les handles.

## Décision

`group_writes_by_shard` est conservé comme option expérimentale de secours.
Il reste désactivé par défaut, car sa matérialisation d'environ 9,2 Mo à
`R=100000` annule l'intérêt mémoire de B11. Aucune campagne à
`R=1000000` n'est engagée : le pilote n'apporte ni gain temporel ni gain
mémoire.

Le test `test_grouped_writes_preserve_exhaustive_results` vérifie les classes,
les compteurs, le nombre d'ouvertures, le plafond de handles et la matérialisation
positive.
