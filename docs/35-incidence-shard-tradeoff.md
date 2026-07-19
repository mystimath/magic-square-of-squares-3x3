# B11 — Compromis temps/mémoire du nombre de shards

_Benchmarks, mesure RSS et campagnes exécutés le 19 juillet 2026._

## 1. Résultat

Le nombre de shards du flux d'incidences n'est pas un simple réglage mémoire.
Réduire leur nombre charge de plus grandes listes et accélère les E/S ; le
faire croître réduit d'abord la liste maximale, puis augmente le coût et la
mémoire des handles d'écriture conservés simultanément.

La politique retenue est :

- conserver 128 shards comme défaut général des CLI et du flux ;
- recommander 256 shards vers `R=1000000` ;
- utiliser 64 seulement si le temps prime sur un pic RSS d'environ 80 Mo ;
- conserver 512 comme option de mémoire minimale au million.

À 256 shards, les campagnes B4–B6 au million terminent en 31,87 s à 32,07 s.
Cela ajoute 7,7 % à 9,0 % de gain à B10 et porte le gain cumulé depuis B8 à
40,6 % environ.

## 2. Méthode

B6 sert de moteur représentatif : le catalogue streaming, les groupes
d'incidences et tous les compteurs précédant la décision 7/9, 8/9 ou 9/9 sont
communs à B4–B6.

Le benchmark `benchmark_incidence_shard_tradeoff.py` :

- alterne l'ordre des configurations ;
- exécute trois répétitions temporelles à `R=100000` ;
- mesure un pic `tracemalloc` par configuration ;
- exige l'identité des classes et de tous les compteurs de recherche ;
- enregistre les shards utilisés, la tranche maximale et le nombre estimé
  d'ouvertures de fichiers.

Au million, deux répétitions temporelles alternées sont complétées par
`benchmark_incidence_shard_rss.py`. Cette sonde lance chaque configuration
dans un processus neuf et lit `GetProcessMemoryInfo` via `ctypes`, sans
dépendance externe. Elle mesure le pic réel du working set Windows sans le fort
ralentissement de `tracemalloc`.

## 3. Pilote à R=100000

Le domaine contient 122640 progressions et 367920 incidences. Les trois
répétitions produisent :

| Shards | Médiane | Pic Python | Incidences max./shard | Ouvertures estimées |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 2,404984 s | 13,35 Mo | 43504 | 32 |
| 32 | 2,499191 s | 7,23 Mo | 23339 | 64 |
| 64 | 2,662934 s | 3,95 Mo | 12182 | 128 |
| 128 | 2,995286 s | 2,20 Mo | 6203 | 256 |
| 256 | 3,672669 s | 2,39 Mo | 3185 | 512 |
| 512 | 5,022363 s | 4,78 Mo | 1629 | 1024 |

La frontière de Pareto s'arrête à 128 shards. Au-delà, la liste maximale
continue de diminuer, mais les handles ouverts font remonter le pic Python et
le temps augmente fortement. Le défaut 128 minimise donc le pic sur cette borne.

## 4. Confirmation temporelle à R=1000000

Le domaine contient 1517296 progressions et 4551888 incidences.

| Shards | Médiane de deux runs | Incidences max./shard | Ouvertures estimées |
| ---: | ---: | ---: | ---: |
| 64 | 31,880284 s | 157546 | 128 |
| 128 | 32,939807 s | 81659 | 256 |
| 256 | 32,341760 s | 42417 | 512 |
| 512 | 33,902007 s | 21273 | 1024 |

Les écarts 64–256 sont faibles devant le coût mémoire des grandes tranches.
512 est 4,6 % plus lent que 256 dans ce balayage.

## 5. Pic RSS isolé au million

La seconde passe, non instrumentée et isolée par processus, donne :

| Shards | Temps de la sonde | Pic RSS | Baseline approximative |
| ---: | ---: | ---: | ---: |
| 64 | 32,556008 s | 80,42 Mo | 22,63 Mo |
| 128 | 31,693154 s | 54,61 Mo | 22,62 Mo |
| 256 | 32,438070 s | 40,12 Mo | 22,60 Mo |
| 512 | 33,553456 s | 33,17 Mo | 22,56 Mo |

Les temps d'une seule passe ne servent pas à classer 64 et 128 ; les médianes
de la section précédente font foi. Le RSS établit en revanche clairement le
compromis :

- 256 réduit le pic de 26,5 % par rapport à 128 ;
- 512 économise encore 6,95 Mo, mais coûte 4,6 % de temps médian ;
- 64 ajoute environ 40 Mo de pic par rapport à 256 pour un gain temporel faible.

256 constitue ainsi le coude le plus équilibré au million.

## 6. Confirmation B4–B6 à 256 shards

Les trois campagnes reprennent le domaine, l'oracle `isqrt` et le chemin de
groupes internes B10.

| Moteur | Résultat | B10, 512 shards | B11, 256 shards | Gain B11 | Gain cumulé B8→B11 |
| --- | --- | ---: | ---: | ---: | ---: |
| B4 | Bremner seul | 34,677437 s | 32,018325 s | 7,668 % | 40,571 % |
| B5 | aucune classe 8/9 | 34,833554 s | 31,866563 s | 8,518 % | 40,645 % |
| B6 | aucune classe 9/9 | 35,253956 s | 32,072967 s | 9,023 % | 40,911 % |

Les manifestes conservent 1517296 progressions, 4551888 incidences, 49800462
paires ordonnées, 10029290 triplets compatibles et 25807672 tests de carré.
Seuls le découpage du flux et le temps changent.

## 7. Artefacts

Balayages transversaux :

- `lo_shu_b6_shard_tradeoff_r100000.json` et `.csv` ;
- `lo_shu_b6_shard_tradeoff_r1000000.json` et `.csv` ;
- `lo_shu_b6_shard_rss_r1000000.json` et `.csv`.

Confirmations à 256 shards :

- `lo_shu_b4_all_masks_shards256_r1000000.json` et `.csv` ;
- `lo_shu_b5_all_masks_shards256_r1000000.json` et `.csv` ;
- `lo_shu_b6_exact9_shards256_r1000000.json` et `.csv`.

Tous se trouvent dans
`results/formulations_comparison/benchmarks/`.

## 8. Décision opérationnelle

Aucune sélection automatique dépendant de `R` n'est ajoutée : le bon compromis
dépend aussi de la mémoire disponible et du système de fichiers. Le défaut 128
reste prévisible ; les commandes documentées au million utilisent désormais
explicitement 256.

Le pic qui remonte à 256–512 shards au pilote vient du dictionnaire de handles
gardés ouverts pendant l'écriture. Une éventuelle B12 devra comparer un cache
LRU borné de handles à l'implémentation actuelle, sans multiplier les
ouvertures au point d'annuler le gain mémoire.
