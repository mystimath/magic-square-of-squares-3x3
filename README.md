# 3x3 Magic Square of Squares

Recherche expérimentale autour du problème ouvert des carrés magiques 3×3 composés de carrés parfaits.

Ce dossier documente une branche de recherche basée sur les carrés magiques 3×3 à centre carré, construits à partir de progressions arithmétiques de carrés autour du centre.

## Résultat principal de cette branche

- Borne testée : center_root ≤ 10 000 000
- Centre maximal : e ≤ 10¹⁴
- Filtre : solutions primitives uniquement, sans dilatation triviale par facteur carré commun
- Résultat 8/9 : aucun candidat trouvé
- Résultat 7/9 : le carré connu de Bremner est retrouvé

## Carré de Bremner retrouvé

```text
373² | 360721 | 205²
289² | 425²   | 527²
565² | 23²    | 222121
```

Somme magique : 541875

## Avertissement

Ces résultats ne constituent pas une preuve d’impossibilité générale.
Ils documentent une recherche exhaustive dans une famille structurée précise.

## Scanner spécialisé B3

La branche B3 indexe les progressions compatibles par PGCD et utilise par
défaut un domaine paramétrique sans doublons. Elle retrouve Bremner dès la borne
de boîte complète `R=601` et ne trouve aucune autre classe primitive du même
masque jusqu’à `R=1000000`.

```powershell
python experiments\formulations_comparison\search_like_bremner_b3.py `
  --complete-box-root 601
```

Méthode, preuves de couverture et mesures :
[docs/27-b3-gcd-index-canonical-catalog.md](docs/27-b3-gcd-index-canonical-catalog.md).

## Scanner exhaustif B4 pour exactement 7/9

B4 couvre les 36 masques exactement 7/9, regroupés en huit orbites D4. Dans la
boîte complète `0 < case <= R²` jusqu'à `R=1000000`, il ne trouve qu'une
classe primitive : Bremner.

```powershell
python experiments\formulations_comparison\search_lo_shu_seven.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 256
```

Preuve de couverture, validation v2.2 et résultats :
[docs/28-lo-shu-all-seven-mask-orbits.md](docs/28-lo-shu-all-seven-mask-orbits.md).

## Scanner exhaustif B5 pour exactement 8/9

B5 couvre les neuf positions possibles de l'unique case non carrée, regroupées
en trois orbites D4. Dans la boîte complète jusqu'à `R=1000000`, il ne trouve
aucune classe exactement 8/9.

```powershell
python experiments\formulations_comparison\search_lo_shu_eight.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 256
```

Preuve de couverture, validation v2.2 et résultats :
[docs/29-lo-shu-all-eight-mask-orbits.md](docs/29-lo-shu-all-eight-mask-orbits.md).

## Scanner exhaustif B6 pour 9/9

B6 applique le même index au problème principal. Dans la boîte complète jusqu'à
`R=1000000` — soit neuf valeurs au plus égales à `10^12` — il ne trouve
aucune classe de carré magique composée de neuf carrés distincts.

```powershell
python experiments\formulations_comparison\search_lo_shu_nine.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 256
```

Preuve de couverture, validations B1/B2/v2.2 et résultats :
[docs/30-lo-shu-exact-nine-scanner.md](docs/30-lo-shu-exact-nine-scanner.md).

## Oracle de carrés B7 à mémoire constante

B3 à B6 utilisent désormais `isqrt` directement, sans table de `R` carrés.
À `R=100000`, le pic Python du scan B6 streaming passe de 9,60 Mo à
2,22 Mo (−76,9 %). Les modes résiduel et matérialisé restent sélectionnables
pour les contrôles.

Preuve et benchmark des oracles :
[docs/31-square-membership-residue-isqrt.md](docs/31-square-membership-residue-isqrt.md).

## Vectorisation B8 des tests de carré

Les quatre extensions B4–B6 sont maintenant testées dans un seul appel Python ;
B3 utilise un lot court-circuité. Au million, les temps passent à 8,43 s pour
B3, 53,88 s pour B4, 53,69 s pour B5 et 54,28 s pour B6, sans modifier
les résultats. B6 est ainsi 16,5 % plus rapide que le run historique avec set,
tout en conservant l'économie mémoire.

Profil CPU, expérience de cache et campagnes appariées :
[docs/32-batched-square-membership.md](docs/32-batched-square-membership.md).

## Préfiltrage algébrique B9

B4–B6 testent maintenant la positivité, la borne et la distinction directement
sur `(A,q,r)`, puis évaluent les quatre cases complémentaires avant de
construire la grille. Au million, B4 ne reconstruit plus que les quatre
représentants de Bremner ; B5 et B6 n'allouent aucune grille complète. Les temps
streaming passent à 41,06 s, 40,81 s et 41,17 s, soit environ 24 % de gain
supplémentaire sans modifier les résultats.

Preuve algébrique, profils et campagnes confirmatoires :
[docs/33-algebraic-grid-prefilter.md](docs/33-algebraic-grid-prefilter.md).

## Groupes d'incidences internes B10

Les groupes créés par le catalogue canonique et le flux streaming ne sont plus
revalidés ni retriés par le consommateur ; les flux externes restent contrôlés
par défaut. L'auto-paire est exclue par identité sans comparaison structurelle
des progressions. Au million, B4–B6 passent à 34,68 s, 34,83 s et 35,25 s,
soit environ 35 % de gain cumulé depuis B8.

Contrat de confiance, profils et campagnes :
[docs/34-trusted-incidence-groups.md](docs/34-trusted-incidence-groups.md).

## Réglage des shards B11

Un balayage temps/mémoire conserve 128 shards comme défaut général et recommande
256 shards au million. Cette configuration limite le pic RSS à environ
40,1 Mo tout en ramenant B4, B5 et B6 à 32,02 s, 31,87 s et 32,07 s. Le gain
cumulé depuis B8 atteint ainsi environ 40,6 %, sans changement de couverture.

Mesures `tracemalloc`, RSS isolé et confirmations :
[docs/35-incidence-shard-tradeoff.md](docs/35-incidence-shard-tradeoff.md).

## Cache LRU des handles B12

Un cache LRU borné est disponible avec `--max-open-shard-handles`, mais reste
désactivé par défaut. Le pilote à `R=100000` montre que la localité des écritures
est insuffisante : même les limites proches du nombre de shards multiplient les
réouvertures et coûtent de 119 % à 150 % de temps pour seulement 0,9 % à 6,0 %
de RSS gagné. Aucun candidat n'a donc été promu au benchmark au million.

Protocole, compteurs exhaustifs et décision :
[docs/36-incidence-handle-lru.md](docs/36-incidence-handle-lru.md).

## Tampons d'écriture B13

Les tampons applicatifs bornés sont disponibles avec
`--max-buffered-write-bytes`. À `R=100000` et 512 shards, un budget de
256 KiB ramène le pic RSS d'environ 27,0 Mio à 24,5 Mio et limite les handles
simultanés à un seul, mais le temps passe de 4,68 s à 8,97 s. Le témoin non
borné reste donc le choix par défaut ; aucune confirmation au million n'est
lancée pour cette branche expérimentale.

Le contrôle à 256 shards est encore moins favorable : 256 KiB ajoute environ
80 % de temps sans gain RSS, et 2 MiB ajoute environ 25 % de temps avec un RSS
supérieur au témoin.

Le contrôle à 256 shards est encore moins favorable : 256 KiB ajoute environ
80 % de temps sans gain RSS, et 2 MiB ajoute environ 25 % de temps avec un RSS
supérieur au témoin.

Mesures et compteurs :
[docs/37-incidence-buffered-writes.md](docs/37-incidence-buffered-writes.md).

## Buffering natif des handles B14

Le paramètre `--write-handle-buffering` permet d'ajuster le tampon Python de
chaque handle persistant. À `R=100000` et 512 shards, `1024` octets réduisent
le RSS médian d'environ 2,7 Mio pour un surcoût temporel de 0,4 %. La valeur
`16384` est marginalement la plus rapide, mais augmente le RSS d'environ
3,4 Mio. Le défaut plateforme reste donc inchangé.

Résultats :
[docs/38-incidence-handle-buffering.md](docs/38-incidence-handle-buffering.md).

## Regroupement des écritures B15

Le mode `--group-writes-by-shard` écrit chaque shard en une seule séquence,
supprimant les dispersions d'écriture. À `R=100000`, 256 shards, il conserve
un temps médian comparable au témoin (~3,70 s), mais matérialise environ 9,2 Mo
d'incidences. Il reste donc une option de secours pour les systèmes imposant
une limite stricte de handles, et ne change pas le défaut.

Mesure et décision :
[docs/39-incidence-grouped-writes.md](docs/39-incidence-grouped-writes.md).
