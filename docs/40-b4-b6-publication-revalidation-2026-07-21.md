# B4–B6 — revalidation de publication au million

_Date : 21 juillet 2026._

## Objet

Cette campagne revalide les scanners publiés B4, B5 et B6 après les décisions
B12–B15. Elle utilise le chemin de référence : flux `streaming`, oracle
`isqrt`, 256 shards, et aucune des options expérimentales B12–B15
(`--max-open-shard-handles`, `--max-buffered-write-bytes`,
`--write-handle-buffering`, `--group-writes-by-shard`).

Les fichiers temporaires ont été placés sous `tmp/revalidation-2026-07-21/`.
Les sous-répertoires transmis à `--temp-dir` ont été créés avant l’exécution,
condition actuellement requise par le moteur.

## Résultats

| Scanner | Résultat | Temps de revalidation | Référence B11 |
| --- | --- | ---: | ---: |
| B4, exactement 7/9 | une classe : Bremner | 32,433 s | 32,018 s |
| B5, exactement 8/9 | aucune classe | 32,312 s | 31,867 s |
| B6, exactement 9/9 | aucune classe | 32,520 s | 32,073 s |

Les trois manifestes concordent exactement avec les références pour les
compteurs de couverture : 1 517 296 progressions, 4 551 888 incidences,
49 800 462 paires ordonnées, 10 029 290 triplets compatibles et 25 807 672
tests de carré. L’inventaire de classes et les hits B4 sont identiques.

Le contrôle positif indépendant B3 dans la boîte complète `R=601` retrouve une
classe, Bremner, sous le chemin de catalogue matérialisé. Les tests du pipeline
ont tous réussi : `79 passed in 18.15s`.

## RSS isolé B6

La sonde Windows isolée à `R=1 000 000`, 256 shards, donne :

- 32,594 s ;
- pic RSS : 39 903 232 octets ;
- référence B11 : 40 124 416 octets ;
- écart : −221 184 octets.

Aucune régression de résultat, de compteur ou de mémoire n’est observée. B16
n’est donc pas justifié par cette revalidation.

## Artefacts et SHA-256

```text
E68C102B5AB219370A6B96E6FB3233C90A50E32FF2B2A685C2A8C8B7718BD3AA  like_bremner_b3_revalidation_r601_20260721.csv
393ACB580A66B9516D6AFBDF867D7F3A5C840ED592436745D69FB4E1F33CD566  like_bremner_b3_revalidation_r601_20260721.json
B9D0715B87813BAF42F9A75F053882E79EC23E8715A77A2B2D4DEF4BD8130420  lo_shu_b4_revalidation_r1000000_20260721.csv
F0F289D4C9ABEA0D293BF9CB9E49B3A8C524A4EB84BC92DAB6DEC794A1ADEE91  lo_shu_b4_revalidation_r1000000_20260721.json
2C7ADC4F373F7BD1403BF88FB439CE0C9AB6C737E59D8753884DCFDB205BB475  lo_shu_b5_revalidation_r1000000_20260721.csv
9A38D210E55C5B7CD7AE36E0F1C82455A9F40282E77567DA453F6AE7649AADCD  lo_shu_b5_revalidation_r1000000_20260721.json
56D664B4AD572EB68C39BBC113374A5CDE11CFA02A5C8A9ED34BC4CE4073E6E7  lo_shu_b6_revalidation_r1000000_20260721.csv
B34C028F044E6A63E157EE2C5E2FF9CAEC8385EC808C0AD55C0A490DE33CC32F  lo_shu_b6_revalidation_r1000000_20260721.json
0EDF7E2B8774525122CC8BEE526FC4670F0FCD9BF5441C165A38D326F06E0259  lo_shu_b6_rss_revalidation_shards256_r1000000_20260721.csv
80FB4400D98FA1BF508555B6C8E3323616271D80FE752CA84A494C575E2DA84A  lo_shu_b6_rss_revalidation_shards256_r1000000_20260721.json
```

Tous les artefacts sont dans `results/formulations_comparison/benchmarks/`.