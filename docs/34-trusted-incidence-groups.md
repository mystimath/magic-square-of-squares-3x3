# B10 — Groupes d'incidences internes de confiance

_Profilage, implémentation et campagnes exécutés le 19 juillet 2026._

## 1. Résultat

B4, B5 et B6 distinguent désormais deux origines de groupes d'incidences :

- un flux externe, validé et trié défensivement par défaut ;
- les catalogues matériel et streaming construits par le projet, dont les
  invariants ont déjà été vérifiés à leur création.

Le chemin interne évite un second tri, la reconstruction des trois valeurs de
chaque progression, la création d'un set d'incidences et leurs hashes. La
validation publique reste activée par défaut.

À `R=1000000`, B10 réduit encore les temps B9 de 14,4 % à 15,6 %. Depuis B8,
le gain cumulé atteint 35,1 % à 35,6 %, sans modifier les résultats ni les
compteurs de couverture.

## 2. Profil de référence B9

### Chemin matériel B6 à R=100000

Le catalogue canonique de 122640 progressions est construit hors profil, puis
le groupement et la recherche sont profilés ensemble.

| Mesure | B9 | B10 | Gain |
| --- | ---: | ---: | ---: |
| appels | 14145564 | 10345976 | 26,9 % |
| temps `cProfile` | 6,451 s | 5,087 s | 21,1 % |
| cœur groupé | 5,035 s | 3,391 s | 32,7 % |
| `_compatible_ordered_incidences` | 1,485 s | 1,060 s | 28,6 % |

### Chemin streaming B6 à R=100000

Le profil inclut la génération, l'écriture, la lecture et le tri de 367920
enregistrements répartis sur 128 shards.

| Mesure | B9 | B10 | Gain |
| --- | ---: | ---: | ---: |
| appels | 16890479 | 12968251 | 23,2 % |
| temps `cProfile` | 7,967 s | 6,206 s | 22,1 % |
| `_compatible_ordered_incidences` | 1,528 s | 0,974 s | 36,3 % |

Sous B9, 367920 contrôles de correspondance recréaient un tuple de valeurs,
les sets de déduplication appelaient le hash des incidences, et 720406
comparaisons structurelles de progressions servaient uniquement à exclure
l'auto-paire.

## 3. Contrat des groupes internes

`search_lo_shu_seven_incidence_groups`,
`search_lo_shu_eight_incidence_groups` et
`search_lo_shu_nine_incidence_groups` exposent le paramètre :

```python
validate_incidence_groups: bool = True
```

La valeur par défaut conserve les contrôles historiques :

- valeurs partagées strictement croissantes ;
- groupe non vide ;
- absence d'incidence dupliquée ;
- correspondance entre `term_index` et la valeur partagée ;
- tri déterministe par PGCD, différence et indice du terme.

Les seuls appelants utilisant `False` sont :

- `group_progression_incidences`, après déduplication du catalogue canonique ;
- `CanonicalProgressionIncidenceStream`, qui trie les signatures par valeur
  partagée, contrôle les doublons et construit lui-même chaque incidence ;
- les CLI et benchmarks lorsqu'ils consomment explicitement ces deux sources.

Le compteur `incidence_group_validation` vaut 1 pour le chemin défensif et 0
pour le chemin interne. Les manifestes rendent ainsi le choix observable.

## 4. Exclusion de l'auto-paire

Dans un groupe valide, une progression stricte ne peut rencontrer une valeur
partagée qu'à un seul de ses trois termes. Le catalogue est sans doublon ; la
seule paire associant une progression à elle-même est donc le même objet
`ProgressionIncidence`.

B10 remplace la comparaison structurelle

```python
r_seed.progression != q_seed.progression
```

par une comparaison d'identité dans un même bucket PGCD. Entre deux buckets
distincts, aucune vérification n'est nécessaire. Les nombres de paires
ordonnées, rejetées comme non primitives et compatibles sont inchangés.

Le tri des buckets PGCD est conservé : son coût profilé est faible et il
maintient un ordre déterministe des provenances.

## 5. Validation

Les tests B10 vérifient que :

- les modes validé et interne donnent les mêmes classes, orbites et compteurs
  structurels ;
- le compteur de mode est le seul compteur différent ;
- le mode public par défaut rejette toujours les groupes non croissants et les
  incidences dupliquées ;
- les chemins matériel et streaming internes restent exactement identiques.

Les validations antérieures contre B1, B2 et les oracles exhaustifs v2.2 restent
actives. Après B10, les 74 tests passent et `git diff --check` est propre.

## 6. Benchmark apparié à R=100000

Cinq répétitions alternent `isqrt` et le set matérialisé sur le même catalogue
canonique de 122640 progressions.

| Moteur | Classes | B9 `isqrt` | B10 `isqrt` | Gain B10 | Gain cumulé B8→B10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B3 | 1 | 0,389756 s | 0,391840 s | −0,5 % | témoin inchangé |
| B4 | 1 | 2,131395 s | 1,905395 s | 10,6 % | 37,8 % |
| B5 | 0 | 2,761757 s | 2,198038 s | 20,4 % | 39,8 % |
| B6 | 0 | 2,780880 s | 2,211273 s | 20,5 % | 39,9 % |

B4 utilisait déjà un index matériel direct sans revalidation complète ; son
gain provient surtout de l'exclusion d'auto-paire. B5 et B6 bénéficient en plus
du chemin de groupes internes.

Artefacts :

- `lo_shu_b3_b6_trusted_incidence_groups_r100000.json` ;
- `lo_shu_b3_b6_trusted_incidence_groups_r100000.csv`.

## 7. Campagnes confirmatoires à R=1000000

Les trois runs reprennent le protocole B8–B9 : flux canonique, 512 shards,
`isqrt`, temps du catalogue inclus.

| Moteur | Résultat | B8 | B9 | B10 | Gain B9→B10 | Gain B8→B10 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| B4 | Bremner seul | 53,876882 s | 41,063923 s | 34,677437 s | 15,553 % | 35,636 % |
| B5 | aucune classe 8/9 | 53,688051 s | 40,813064 s | 34,833554 s | 14,651 % | 35,119 % |
| B6 | aucune classe 9/9 | 54,279316 s | 41,167942 s | 35,253956 s | 14,366 % | 35,051 % |

Les trois manifestes conservent 1517296 progressions, 4551888 incidences,
49800462 paires ordonnées, 10029290 triplets compatibles et 25807672 tests de
carré. B4 retrouve les quatre représentants de la seule classe de Bremner ;
B5 et B6 ne valident toujours aucune grille.

Artefacts :

- `lo_shu_b4_all_masks_trusted_incidence_groups_r1000000.json` et `.csv` ;
- `lo_shu_b5_all_masks_trusted_incidence_groups_r1000000.json` et `.csv` ;
- `lo_shu_b6_exact9_trusted_incidence_groups_r1000000.json` et `.csv`.

## 8. Décision opérationnelle

B10 est validé. Le prochain profil streaming est dominé par la lecture des
shards, les ouvertures de fichiers, le tri des enregistrements, le lot de tests
de carré et l'énumération des paires compatibles. Une éventuelle B11 devra
mesurer le compromis entre nombre de shards, mémoire de pointe et coût d'E/S
avant toute modification du format ou du protocole de couverture.
