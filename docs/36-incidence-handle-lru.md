# B12 — Cache LRU borné des handles de shards

_Implémentation et benchmarks exécutés le 19 juillet 2026._

## 1. Résultat

Le cache LRU borné est correct, mesurable et disponible comme option
expérimentale, mais il ne doit pas remplacer le comportement non borné par
défaut.

À `R=100000`, les limites proches du nombre total de shards réduisent peu le
pic RSS tout en provoquant des dizaines de milliers de réouvertures :

- avec 256 shards, limiter à 224 économise 0,23 Mio de RSS médian mais ajoute
  150,1 % de temps ;
- avec 512 shards, limiter à 448 économise 1,61 Mio mais ajoute 119,4 % de
  temps ;
- les limites plus basses économisent au plus 2,26 Mio et coûtent jusqu'à
  405,3 % de temps.

Aucune configuration bornée ne constitue donc un candidat robuste à promouvoir
à `R=1000000`. Conformément à la porte de décision prévue, aucune campagne au
million n'a été lancée.

## 2. Implémentation

`CanonicalProgressionIncidenceStream` accepte désormais
`max_open_shard_handles` :

- `None` conserve tous les handles ouverts, comme avant B12 ;
- un entier positif active un `OrderedDict` utilisé comme LRU ;
- à saturation, le handle le moins récemment utilisé est fermé ;
- la première ouverture d'un shard utilise `wb`, les réouvertures utilisent
  `ab`, ce qui préserve tous les enregistrements déjà écrits ;
- tous les handles encore actifs sont fermés dans le bloc `finally`.

Les trois CLI B4–B6 exposent l'option
`--max-open-shard-handles`. Elle n'a pas de valeur par défaut et n'altère donc
pas les commandes publiées.

Le flux publie quatre compteurs E/S supplémentaires :

- `write_handle_cache_capacity` — zéro signifie non borné ;
- `write_handle_opens` ;
- `write_handle_evictions` ;
- `max_open_write_handles`.

## 3. Protocole pilote

B6 sert encore de moteur représentatif, car B4–B6 partagent le catalogue,
l'écriture des incidences et les compteurs précédant leur décision finale.

Le benchmark `benchmark_incidence_handle_lru.py` :

- fixe `R=100000` ;
- teste 256 shards avec les limites non bornée, 128, 192 et 224 ;
- teste 512 shards avec les limites non bornée, 256, 384 et 448 ;
- exécute trois répétitions dans des processus neufs et alterne réellement
  l'ordre des configurations ;
- effectue une chauffe non comptée à `R=10000` ;
- mesure le pic réel du working set Windows avec
  `GetProcessMemoryInfo` ;
- exige l'identité des classes, de tous les compteurs de recherche et des six
  compteurs de couverture du flux.

Les temps incluent la génération, l'écriture, la lecture et le scan B6. Ils
n'incluent pas le démarrage du processus parent.

## 4. Préservation exhaustive

Toutes les variantes donnent zéro classe 9/9 et les artefacts portent :

- `all_classes_equal: true` ;
- `all_search_stats_equal: true` ;
- `all_coverage_stats_equal: true`.

Les compteurs communs incluent 122640 progressions, 367920 incidences,
86154 valeurs indexées, 61904 valeurs partagées, 2861724 paires de graines
ordonnées, 686206 triplets compatibles et 1749088 tests de carré. Aucun
candidat n'est accepté.

| Shards | Incidences max./shard | Doublons | Valeurs indexées |
| ---: | ---: | ---: | ---: |
| 256 | 3185 | 0 | 86154 |
| 512 | 1629 | 0 | 86154 |

## 5. Résultats avec 256 shards

| Limite | Temps médian | Pic RSS médian | Ouvertures | Évictions |
| ---: | ---: | ---: | ---: | ---: |
| non bornée | 3,617478 s | 25952256 octets | 256 | 0 |
| 128 | 21,577249 s | 25518080 octets | 104068 | 103940 |
| 192 | 13,256218 s | 25595904 octets | 56037 | 55845 |
| 224 | 9,046448 s | 25706496 octets | 31454 | 31230 |

Même la limite 224, qui ne ferme que 32 handles par rapport au témoin, rouvre
des shards 31454 fois. Elle réduit le RSS de 0,9 % et multiplie le temps par
2,50.

## 6. Résultats avec 512 shards

| Limite | Temps médian | Pic RSS médian | Ouvertures | Évictions |
| ---: | ---: | ---: | ---: | ---: |
| non bornée | 4,993145 s | 28106752 octets | 512 | 0 |
| 256 | 25,229420 s | 25735168 octets | 115855 | 115599 |
| 384 | 15,589538 s | 26005504 octets | 60679 | 60295 |
| 448 | 10,956923 s | 26415104 octets | 33850 | 33402 |

La limite 256 obtient le plus bas RSS, soit 8,4 % de moins que le témoin, mais
multiplie le temps par 5,05. La limite 448 ne gagne plus que 6,0 % de RSS et
multiplie encore le temps par 2,19.

## 7. Interprétation et décision

Le générateur parcourt de nombreuses familles primitives puis leurs dilatations.
Les shards récemment utilisés par une famille ne suffisent pas à la suivante :
le LRU évince puis rouvre continuellement les mêmes fichiers. La faible localité
temporelle explique le nombre d'ouvertures, très supérieur au nombre de shards.

La politique B11 reste donc inchangée :

- 128 shards demeurent le défaut général ;
- 256 shards restent recommandés vers `R=1000000` ;
- les handles restent non bornés par défaut ;
- le cache LRU n'est à utiliser que sous une contrainte externe stricte sur le
  nombre de fichiers ouverts, en acceptant son fort surcoût.

## 8. Artefacts et tests

Les artefacts sont dans
`results/formulations_comparison/benchmarks/` :

- `lo_shu_b6_handle_lru_shards256_r100000.json` et `.csv` ;
- `lo_shu_b6_handle_lru_shards512_r100000.json` et `.csv`.

Le test `test_bounded_lru_preserves_classes_and_exhaustive_counters` force une
capacité de trois handles pour onze shards et compare le résultat au témoin non
borné. Les tests couvrent aussi la validation de l'option, le bornage effectif,
les évictions, les ouvertures en ajout et le nettoyage des répertoires
temporaires.
