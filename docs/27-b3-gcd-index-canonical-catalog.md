# Branche B3 : index PGCD et catalogue canonique

_Implémentation, régressions et mesures exécutées le 18 juillet 2026._

## 1. Portée

B3 accélère la recherche Lo Shu spécialisée du masque exact de Bremner
`acdefgh`. Elle cherche des carrés pleinement magiques, positifs, à neuf
valeurs distinctes, avec exactement sept cases carrées, puis quotient par les
symétries D4 et ne conserve par défaut que les classes primitives.

Cette branche est opérationnelle indépendamment de la formulation elliptique D.
Elle exploite directement les progressions arithmétiques de trois carrés. D
reste utile pour expliquer les courbes, construire des familles et guider de
nouvelles paramétrisations ; l'index PGCD de B3 n'est donc pas, en l'état, une
optimisation du moteur D.

## 2. Jointure indexée par PGCD

Deux progressions partageant le premier carré `A` sont jointes :

```text
(A, A+r, A+2r)    et    (A, B, C).
```

À chaque progression `P`, B3 associe le PGCD `g(P)` de ses trois racines. Le
PGCD des cinq racines connues d'un couple est exactement le PGCD des deux
indices. Si `g(P1)` et `g(P2)` ne sont pas premiers entre eux, toute extension
carrée possède ce facteur commun et ne peut pas être primitive.

Le moteur groupe donc les progressions de même `A` en seaux de PGCD et ne
matérialise que les produits de seaux compatibles. À `R=100000` :

| Variante | Médiane | Couples matérialisés | Tests de carré | Classes |
| --- | ---: | ---: | ---: | ---: |
| Index PGCD B3 | 0,360110 s | 157624 | 315248 | 1 |
| Filtre PGCD couple par couple | 0,451117 s | 635968 | 315248 | 1 |
| Filtre désactivé | 0,471228 s | 635968 | 1271936 | 1 |

L'index réduit le temps de `20,17 %` face au filtre couple par couple et de
`23,58 %` face au contrôle sans filtre. Il rejette combinatoirement 478344 des
635968 couples ordonnés théoriques, sans changer la classe obtenue.

Artefact :
`results/formulations_comparison/benchmarks/like_bremner_gcd_index_r100000.json`.

## 3. Domaine paramétrique canonique

Le générateur historique parcourt les couples positifs copremiers `(m,n)` dans
la paramétrisation

```text
x = |m² + 2mn - n²|
y =  m² + n²
z = |-m² + 2mn + n²|,
```

puis réduit le PGCD de `(x,y,z)`. Il rencontre quatre représentants positifs de
chaque progression primitive.

L'échange `m <-> n` conserve le triplet non ordonné. Après cet échange, on peut
supposer `t=n/m>1`. La transformation

```text
(m,n) -> (|n-m|, n+m),    t -> (t+1)/(t-1)
```

conserve aussi le triplet après réduction. Elle est involutive et son unique
point fixe positif supérieur à un est irrationnel, `1+sqrt(2)`. Pour un rapport
rationnel `t>1`, exactement un des deux représentants est donc dans

```text
1 < n/m < 1 + sqrt(2),
```

condition testée sans flottants par

```text
m < n    et    (n-m)² < 2m².
```

Ce domaine fondamental émet directement une fois chaque signature, dilatations
comprises. Les régressions comparent exactement son catalogue au générateur
historique aux bornes `127`, `601`, `2000` et `100000`.

À `R=100000`, les quatre variantes produisent les mêmes 122640 progressions,
les mêmes compteurs de recherche et l'unique classe de Bremner :

| Catalogue bout-en-bout | Domaine historique | Domaine canonique | Réduction |
| --- | ---: | ---: | ---: |
| Matérialisé | 0,833980 s | 0,663140 s | 20,48 % |
| Streaming, 64 tranches | 1,284488 s | 0,959346 s | 25,31 % |

Le domaine historique écrit 490560 signatures, contre 122640 pour le domaine
canonique. Le pic mémoire Python reste proche de 46,5 Mo en mode matérialisé et
11,1 Mo en streaming, car le catalogue unique final, l'ensemble des carrés et
la plus grande tranche ne changent pas. Le streaming canonique économise ainsi
environ `76,2 %` de mémoire face au mode matérialisé canonique, au prix d'un
temps plus élevé.

Artefact :
`results/formulations_comparison/benchmarks/like_bremner_canonical_catalog_r100000.json`.

## 4. Recherche progressive en boîte complète

La borne `R` est une borne sur les neuf cases : `0 < case <= R²`. Elle inclut
donc les deux cases non carrées, ce qui explique la première apparition de
Bremner à `R=601`, et non à la racine carrée maximale 565 de ses sept carrés.

| Borne complète | Progressions | Couples compatibles | Classes primitives nouvelles |
| ---: | ---: | ---: | ---: |
| 250000 | 335559 | 468140 | 0 |
| 500000 | 714896 | 1055252 | 0 |
| 1000000 | 1517296 | 2366180 | 0 |

À chaque borne, l'unique classe totale est la classe historique de Bremner. Le
passage final à `R=1000000`, en streaming canonique avec 256 tranches, effectue
4732360 tests d'appartenance à l'ensemble des carrés. Deux passages ont demandé
8,871859 s et 9,293436 s, contre 14,286857 s pour le flux historique précédent ;
ces comparaisons ponctuelles donnent une réduction comprise entre `35 %` et
`38 %`. L'artefact archivé est
`results/formulations_comparison/benchmarks/like_bremner_b3_canonical_scan_r1000000.json`.

Ce résultat est exhaustif pour la branche B3 et le masque canonique `acdefgh`
dans cette boîte. Il ne couvre ni les autres orbites de masques à sept carrés,
ni toutes les familles possibles d'un moteur général, et ne constitue pas une
preuve d'unicité globale.

## 5. Utilisation

Le domaine canonique matérialisé est le défaut :

```powershell
python experiments\formulations_comparison\search_like_bremner_b3.py `
  --complete-box-root 601
```

Pour monter en borne avec moins de mémoire :

```powershell
python experiments\formulations_comparison\search_like_bremner_b3.py `
  --complete-box-root 1000000 --catalog-mode streaming --shard-count 256
```

Le contrôle historique reste disponible avec `--parameter-domain historical`.
Les options `--all-scalings`, `--csv-out` et `--json-out` conservent leur sens.

## 6. Suite recommandée

L'étape suivante la plus informative est d'énumérer les orbites D4 des autres
masques exactement 7/9, puis de dériver pour chacune une jointure couverte par
preuve et contrôlée contre v2.2 SAFE à petite borne. La formulation D pourra
ensuite servir à interpréter les contraintes résiduelles ou à proposer des
familles, tandis que B3 restera le scanner entier rapide du motif Bremner.

## Mise à jour B8

B3 retrouve toujours uniquement Bremner à `R=1000000`. Le test `isqrt` groupé et court-circuité réduit le temps streaming de `8,871859 s` à `8,433562 s` (`−4,940 %`). Artefact : `results/formulations_comparison/benchmarks/like_bremner_b3_batched_isqrt_r1000000.json`.

Profil et méthode : [32-batched-square-membership.md](32-batched-square-membership.md).
