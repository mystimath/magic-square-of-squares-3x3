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
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512
```

Preuve de couverture, validation v2.2 et résultats :
[docs/28-lo-shu-all-seven-mask-orbits.md](docs/28-lo-shu-all-seven-mask-orbits.md).

## Scanner exhaustif B5 pour exactement 8/9

B5 couvre les neuf positions possibles de l'unique case non carrée, regroupées
en trois orbites D4. Dans la boîte complète jusqu'à `R=1000000`, il ne trouve
aucune classe exactement 8/9.

```powershell
python experiments\formulations_comparison\search_lo_shu_eight.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512
```

Preuve de couverture, validation v2.2 et résultats :
[docs/29-lo-shu-all-eight-mask-orbits.md](docs/29-lo-shu-all-eight-mask-orbits.md).

## Scanner exhaustif B6 pour 9/9

B6 applique le même index au problème principal. Dans la boîte complète jusqu'à
`R=1000000` — soit neuf valeurs au plus égales à `10^12` — il ne trouve
aucune classe de carré magique composée de neuf carrés distincts.

```powershell
python experiments\formulations_comparison\search_lo_shu_nine.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 512
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

