# B13 — Tampons d'écriture applicatifs bornés

_Implémentation et pilote exécutés le 19 juillet 2026._

## Résultat

B13 ajoute un budget global de tampons binaires avec
`--max-buffered-write-bytes`. Les incidences sont accumulées par shard dans
un LRU de `bytearray`; lorsqu'il est plein, le tampon le moins récent est
vidé dans son fichier puis le handle est fermé. La mémoire applicative et le
nombre de handles simultanés restent ainsi bornés.

Le mode par défaut reste inchangé : tous les handles sont conservés ouverts.
Le mode borné est exact, mais son surcoût ne justifie pas une promotion globale.

## Protocole

Le benchmark
`experiments/formulations_comparison/benchmark_incidence_buffered_writes.py`
exécute B6 à `R=100000`, avec 512 shards, dans des processus Windows isolés.
Il compare le témoin non borné à des budgets de 256 KiB, 512 KiB, 1 MiB et
2 MiB, avec trois répétitions alternées par configuration.

Toutes les variantes vérifient l'égalité des classes, des compteurs de
recherche et des compteurs de couverture. Le domaine contient 122640
progressions, 367920 incidences et 86154 valeurs indexées ; aucune classe 9/9
n'est trouvée.

## Mesures

| Budget | Temps médian | Pic RSS médian | Ouvertures/flushes | Pic tampon |
| ---: | ---: | ---: | ---: | ---: |
| non borné | 4,681758 s | 28246016 octets | 512 | 0 |
| 256 KiB | 8,971450 s | 25739264 octets | 24777 | 262125 octets |
| 512 KiB | 7,809610 s | 25960448 octets | 16602 | 524275 octets |
| 1 MiB | 6,886796 s | 27389952 octets | 11634 | 1048575 octets |
| 2 MiB | 6,194599 s | 28680192 octets | 7734 | 2097150 octets |

Le budget de 256 KiB économise environ 2,4 MiB de RSS et limite le pic à un
handle ouvert, mais augmente le temps de 91,6 %. Le budget de 2 MiB réduit le
surcoût à 32,1 %, au prix d'un RSS presque équivalent au témoin et de 7734
flushes. Aucun point ne bat le témoin sur le compromis temps/mémoire dans la
configuration recommandée.

### Contrôle à 256 shards

Le même pilote à 256 shards donne un témoin à 3,579925 s et 26005504 octets
de RSS médian. Les budgets 256 KiB, 1 MiB et 2 MiB donnent respectivement
6,428116 s, 4,972648 s et 4,491149 s, sans réduction RSS par rapport au
témoin. Le budget de 2 MiB reste 25,5 % plus lent et consomme 28340224 octets.
Cette configuration recommandée ne fournit donc aucun cas d'usage pour le
tampon applicatif.

## Compteurs E/S

Le mode borné expose :

- `write_buffer_capacity_bytes` ;
- `write_buffer_flushes` ;
- `write_buffer_evictions` ;
- `max_buffered_write_bytes`.

`write_handle_opens` est égal au nombre de flushes et
`max_open_write_handles` vaut un lorsque le flux contient des incidences.
Les fichiers sont ouverts en écriture (`wb`) au premier flush d'un shard puis
en ajout (`ab`) aux flushes suivants.

## Décision

B13 est conservé comme soupape expérimentale lorsqu'une contrainte externe
impose un plafond de handles ou de mémoire. Il ne modifie ni le défaut des CLI
ni les commandes de campagne au million. Une confirmation à
`R=1000000` n'est pas engagée, car le pilote ne montre aucun compromis
suffisamment prometteur.

## Artefacts et tests

Artefacts :

- `results/formulations_comparison/benchmarks/lo_shu_b6_buffered_writes_shards512_r100000.json` ;
- `results/formulations_comparison/benchmarks/lo_shu_b6_buffered_writes_shards256_r100000.json` ;
- le CSV portant le même nom.

Les tests B13 couvrent la validation des budgets, l'exclusivité avec le cache
LRU, la préservation des classes et compteurs, le plafond mémoire, les flushes
et la réouverture en ajout.
