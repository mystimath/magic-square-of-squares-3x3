# B14 — Buffering natif des handles persistants

_Pilote exécuté le 19 juillet 2026._

## Objectif

B13 a montré que des tampons applicatifs bornés réduisent la mémoire au prix de
flushes fréquents. B14 mesure une variante plus locale : le paramètre Python
`buffering` de chaque handle persistant, sans changer le nombre de handles ni
la partition des shards.

La CLI expose cette sonde avec `--write-handle-buffering`. La valeur absente
conserve le buffering implicite de la plateforme.

## Protocole

`benchmark_incidence_handle_buffering.py` exécute B6 à `R=100000`, avec
512 shards, dans des processus Windows isolés. Les valeurs testées sont le
défaut, 256, 1024, 4096 et 16384 octets, avec trois répétitions alternées.

Chaque variante doit conserver les mêmes classes, compteurs de recherche et
compteurs de couverture. Le domaine contient 122640 progressions, 367920
incidences, 86154 valeurs indexées et 1629 incidences maximales par shard.

## Résultats

| Buffering | Temps médian | Pic RSS médian | Ouvertures |
| ---: | ---: | ---: | ---: |
| défaut | 4,729369 s | 28200960 octets | 512 |
| 256 | 4,926640 s | 25325568 octets | 512 |
| 1024 | 4,748491 s | 25333760 octets | 512 |
| 4096 | 4,738692 s | 26042368 octets | 512 |
| 16384 | 4,700360 s | 31567872 octets | 512 |

`1024` réduit le RSS médian de 2,7 Mio environ pour un surcoût de 0,4 %.
`16384` est 0,6 % plus rapide que le défaut, mais consomme environ 3,4 Mio
de RSS supplémentaire. L'écart temporel reste comparable au bruit des
processus isolés.

## Décision

Le défaut plateforme est conservé : il reste le choix le plus prévisible et
aucun gain de vitesse robuste ne justifie une modification globale. Sous
contrainte mémoire, `1024` est documenté comme profil optionnel. B14 ne
justifie pas de campagne à `R=1000000`.

## Artefacts

- `results/formulations_comparison/benchmarks/lo_shu_b6_handle_buffering_shards512_r100000.json` ;
- le CSV portant le même nom.

L'artefact contient les classes, les compteurs exhaustifs et les statistiques de
flux de chaque variante.
