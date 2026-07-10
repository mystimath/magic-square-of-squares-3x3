# Status

_Mise à jour : 2026-07-08_

Ce document récapitule l’état actuel des différentes branches de recherche autour du problème du carré magique 3×3 de carrés, avec un accent particulier sur les campagnes computationnelles effectivement exécutées.

---

## Branche A — centre carré

Script principal historique :

```text
src/search_magic_square_of_squares_v4.py
```

Résultat actuel :

| Recherche    |                    Borne |               Résultat |
| ------------ | -----------------------: | ---------------------: |
| 7/9 primitif |  center_root ≤ 3 000 000 |           Bremner seul |
| 8/9 primitif | center_root ≤ 10 000 000 |                  aucun |
| 9/9 primitif |  inclus dans le test 8/9 | aucun dans cette borne |

Conclusion provisoire : dans cette branche classique à centre carré, le meilleur résultat primitif reste le carré de Bremner à 7/9.

---

## Branche B — centre non nécessairement carré

Script historique :

```text
src/search_magic_square_of_squares_v5_non_square_center.py
```

Résultat actuel :

|                        Borne |  Résultat |
| ---------------------------: | --------: |
| racines extérieures ≤ 10 000 | aucun 8/9 |
| racines extérieures ≤ 20 000 | aucun 8/9 |

La branche est figée provisoirement à 20 000, car la version actuelle devient fortement limitée par la mémoire.

Conclusion provisoire : aucun 8/9 détecté dans la branche à centre non nécessairement carré jusqu’aux bornes testées.

### B2-1

J’ai rédigé un **script optimisé pour la branche la plus prometteuse, B2** : le cas **centre non nécessairement carré**, avec **parallelisation** et **gestion mémoire par sharding disque**.

src/search_non_square_center_v2_optimized.py

#### Ce que fait ce script

Il met en œuvre une architecture plus sérieuse que le squelette :

- **génération parallèle** des paires opposées de carrés autour d’un centre ;
- **sharding sur disque** par plages de centres, pour éviter de tout garder en RAM ;
- **traitement indépendant des shards** ;
- reconstruction exacte des candidats via la structure en offsets
  \[
  u,\ v,\ u+v,\ |u-v|
  \]
  autour du centre \(e\) ;
- **déduplication par symétries** du carré ;
- filtres optionnels :
  - `--primitive-only`
  - `--distinct-roots`
  - `--non-square-center-only`
- sortie **CSV incrémentale**.

#### Pourquoi cette branche

C’est celle que je considère toujours comme la **plus prometteuse** à ce stade, parce que :
- les branches “centre carré / Bremner-like” ont déjà été très largement ratissées ;
- la branche B historique était surtout bloquée par la **mémoire**, pas par une vraie exploration complète ;
- ce script est justement conçu pour casser ce verrou mémoire.


#### Commande  recommandée

Pour une première vraie campagne **B2-1** :

```bash
python search_non_square_center_v2_optimized.py ^
  --profile B2-1 ^
  --max-root 50000 ^
  --workers 8 ^
  --shard-workers 8 ^
  --shard-size 10000000 ^
  --flush-lines 200000 ^
  --primitive-only ^
  --distinct-roots ^
  --non-square-center-only ^
  --clean-tmp ^
  --tmp-dir tmp\\b2_non_square_center ^
  --out results\\raw\\b2_non_square_center_v2_B2-1.csv
```

#### Remarques importantes

C’est un **script optimisé et structuré**, mais pas encore la version mathématiquement ultime de B2. Il constitue une base solide pour lancer les premières vraies campagnes mémoire-safe.

#### Resultats

Après lancement de run, l’architecture de coût que montre mon run : **624 918 054 paires** générées, **11,7 Go temporaires** écrits sur disque, **306 065 680 centres** vus, puis **zéro candidat au final**. On n’a pas une branche “difficile mais prometteuse”, on a ici une branche dont la première implémentation a surtout déplacé le mur de la **RAM** vers le **disque**.

Autrement dit, le critère d’arrêt prévu dans la roadmap est déjà atteint en pratique : _“stop si mur mémoire persistant après réécriture raisonnable”_. Même si le mur est ici I/O + espace temporaire plus que RAM pure, c’est bien la même catégorie d’échec technique. 

Le chiffre le plus parlant est celui-ci :  
\[
624\,918\,054 / 306\,065\,680 \approx 2.04
\]
Tu génères donc en moyenne seulement **un peu plus de 2 paires par centre**. Or un candidat B2 exige au minimum **4 offsets distincts** autour d’un même centre, structurés comme
\[
\{u,\ v,\ u+v,\ |u-v|\}.
\]
Cela explique pourquoi **257 705 567 centres** meurent immédiatement en `centers_too_few_offsets`. Le script écrit donc massivement des données pour des centres qui sont, en grande majorité, **mathématiquement incapables** de produire un candidat.

Plus subtil encore : même parmi les centres qui survivent au seuil “au moins 4 offsets”, il reste **48 360 113 centres** sans candidat. Donc un simple filtrage par multiplicité ne suffira pas. Il est nécessaire, mais pas suffisant. C’est la vraie leçon algorithmique de ce run.

**Ce que ce run prouve**:

Il prouve trois choses.

* La première : la branche B2 reste intéressante, mais **pas avec une génération brute des paires**.

* La deuxième : le modèle “écrire toutes les paires puis filtrer ensuite” est trop coûteux dès `max-root = 50000`.

* La troisième : pour rendre B2 viable, il faut une **v2.1** plus intelligente, en plusieurs passes, avec des filtres exacts **avant** l’écriture massive des offsets.

**Ce qu’on peut faire maintenant**

La bonne suite n’est pas de relancer avec d’autres paramètres. Il faut **réécrire l’algorithme**. À mon avis, la bonne architecture B2-v2.1 est la suivante.

* Pass 1 — comptage seulement, pas d’offsets
On ne doit plus écrire `(center, offset)` pour chaque paire. On doit d’abord faire une passe ultra-légère qui ne stocke que des **comptes par centre**, idéalement agrégés localement par worker puis fusionnés par shard.

    * But : ne conserver que les centres avec multiplicité suffisante.  
C’est une réduction de volume énorme par rapport aux lignes CSV de paires.

* Pass 2 — filtrage structurel sur centres survivants
Les centres avec au moins 4 offsets restent beaucoup trop nombreux. Il faut leur appliquer un second filtre nécessaire, beaucoup plus sélectif, avant de régénérer les offsets complets.
Le filtre à viser doit tester quelque chose comme :  
“le multiensemble d’offsets observés autour de ce centre a-t-il au moins une chance de contenir une structure additive de type \(\{u,v,u+v,|u-v|\}\) ?”
Même un test partiel, exact mais bon marché, ferait déjà gagner énormément.

* Pass 3 — régénération des offsets uniquement pour les centres retenus
Une fois qu’on a une vraie shortlist de centres, on peut refaire la génération et ne stocker les offsets **que pour ces centres-là**.

Et là, il faut abandonner le CSV texte temporaire : il faut écrire en **binaire compact**. Le texte m’a coûté 11,7 Go ; en binaire 32 bits, le coût va tomber immédiatement beaucoup plus bas.

* Pass 4 — recherche exacte des motifs \((u,v)\)
C’est seulement à ce stade qu’on fait la vraie recherche :
\[
u,\ v,\ u+v,\ |u-v| \in S_e.
\]
Cette étape devient alors réaliste.

** Ma conclusion opérationnelle**

Cette campagne B2-1 est :

- **mathématiquement informative** ;
- **algorithmiquement non viable en l’état** ;
- et **suffisante pour justifier une v2.1** avant toute montée vers 100 000.

En clair : **ne pas lancer B2-2 avec ce script actuel**.



Je résumerais la situation comme suit :

> La première implémentation optimisée de B2 a permis de dépasser la borne historique sur le plan architectural, mais pas encore sur le plan pratique. À `max-root = 50 000`, elle génère ~625 millions de paires, écrit ~11,7 Go de données temporaires et ne produit aucun candidat. Le goulot d’étranglement principal n’est plus la RAM mais l’explosion combinatoire des paires et des centres. La branche B2 reste prometteuse, mais nécessite une réécriture v2.1 en plusieurs passes, avec comptage des centres, filtrage structurel précoce et stockage binaire compact.

**La bonne suite immédiate**

La suite correcte est maintenant une **réécriture B2-v2.1** avec :

- pass de comptage par centre ;
- shortlist de centres survivants ;
- régénération sélective des offsets ;
- stockage binaire compact ;
- traitement exact final.

La priorité la plus utile est un nouveau script du type :

```text
search_non_square_center_v2_1.py
```

avec cette architecture en **deux passes + offsets sélectifs**.

---

### B2-v2.1 — campagne exacte `R ≤ 50 000`

Script utilisé :

```text
src/search_non_square_center_v2_1.py
````

Nom du log :

```text
B2_v2_1_exact8_non_square_R50000_2026-07-09.log
```

Objectif : chercher un carré magique 3×3 avec centre non carré et huit cases extérieures carrées, en utilisant une architecture en deux passes : préfiltrage des centres par masques modulaires, puis régénération sélective des offsets.

Résumé du run :

```text
Racines extérieures : ≤ 50 000
Paires vues : 624 918 054
Centres vus : 307 660 640
Lignes temporaires Pass 1 : 620 675 115
Centres sélectionnés après filtres : 1 594 960
Offsets régénérés en Pass 2 : 9 427 690
Centres recombinés sans candidat : 1 594 960
Résultats distincts : 0
Durée totale : 845.7 s
Volume temporaire observé : environ 19 Go
```

Résultat :

> Aucun candidat 8/9 n’a été trouvé dans cette campagne B2-v2.1 jusqu’à `R ≤ 50 000`, avec centre non carré.

Interprétation :

La Pass 2 est restée maîtrisée : environ 9,4 millions d’offsets seulement ont été régénérés. Le vrai coût reste la Pass 1, qui écrit encore presque autant de lignes temporaires que de paires rencontrées. Le run confirme donc que la stratégie v2.1 est correcte et termine, mais qu’elle reste trop verbeuse côté disque pour monter brutalement vers `R = 100 000`.

Conclusion opérationnelle :

> La branche B2-v2.1 donne un résultat négatif propre à `R ≤ 50 000`. Avant toute montée de borne, il faut nettoyer automatiquement `pass1_partials`, renforcer les filtres modulaires et ajouter un mode de recherche plus souple visant aussi les candidats `≥ 7/9`, pas seulement les candidats exacts à huit cases extérieures carrées.


### B2-v2.2 — campagne exacte `R ≤ 50 000` (SAFE)

Script utilisé :

```text
src/search_non_square_center_v2_2_safe.py

```

Nom du log :

```text
B2_v2_2_exact8_non_square_R50000.log

```

Objectif : chercher un carré magique 3×3 avec centre non carré et huit cases extérieures carrées, en utilisant une architecture hybride en deux passes intégrant un crible modulaire renforcé (modules 127, 131, 137), un sharding par vagues et un nettoyage à chaud des fichiers temporaires pour sécuriser l'espace disque.

Résumé du run :

```text
Racines extérieures : ≤ 50 000
Paires vues : 624 918 054
Centres vus : 306 383 416
Lignes temporaires Pass 1 : 608 982 791
Centres sélectionnés après filtres : 317 736
Offsets régénérés en Pass 2 : 4 907 684
Centres recombinés sans candidat : 317 736
Résultats distincts : 0
Durée totale : 1725.2 s (28.7 min)
Volume temporaire cumulé détruit : 46.2 Go
Taille résiduelle finale : 0.13 Go

```

Résultat :

> Aucun candidat 8/9 n’a été trouvé dans cette campagne B2-v2.2 jusqu’à `R ≤ 50 000`, avec centre non carré.

Interprétation :

La mise en place du crible à trois modules (127, 131, 137) a fait chuter le nombre de centres sélectionnés à seulement 317 736 (contre 1,59 million en v2.1), divisant par deux le volume d'offsets à régénérer en Pass 2 (4,9 millions). Bien que la génération brute du Pass 1A écrive un volume cumulé massif de 46,2 Go de données intermédiaires, l'intégration du nettoyage à chaud (`--cleanup-partials`) a permis de purger le disque au fur et à mesure du traitement des shards, ramenant l'empreinte résiduelle finale à un niveau insignifiant (0,13 Go) et éliminant tout risque de saturation.

Conclusion opérationnelle :

> La branche B2-v2.2 valide avec succès l'architecture "SAFE". L'espace disque est désormais totalement maîtrisé grâce à la purge dynamique des shards et au filtrage modulaire drastique. Le pipeline étant robuste, la montée de borne vers `R = 100 000` ou l'exploration des structures à centre carré de type Bremner (`≥ 7/9` via le mode `relaxed7`) peuvent être lancées en toute sécurité.

### B2-v2.2 — relaxed7, centre carré, `R ≤ 100 000`

Script utilisé :

```text
src/search_non_square_center_v2_2_safe.py
```
Log :
```text
B2_v2_2_relaxed7_square_R100000_2026-07-09.log
```
Commande : recherche relâchée de carrés magiques 3×3 avec au moins 7 cases carrées, centre carré, racines extérieures ≤ 100 000.

Résumé :
```text
Paires utiles vues : 122 640
Centres vus : 73 990
Centres sélectionnés : 18 199
Offsets régénérés : 85 048
Résultats distincts : 1
Durée : 865.8 s
Taille temporaire finale : 0.004 Go
```
Résultat :
> Un seul candidat distinct à 7/9 ou plus a été trouvé dans ce run. Il s'agit du carré de Bremner.aucun nouveau 7/9 primitif + aucun 8/9

Conclusion :

> Le run relaxed7, centre carré, R ≤ 100 000, retrouve uniquement le carré de Bremner. Aucun nouveau candidat primitif à 7/9 ou plus n’a été trouvé.
> C’est un bon résultat négatif : le script retrouve bien le témoin attendu, puis ne trouve rien d’autre dans la borne testée.

### B2-v2.2 — relaxed7, centre non carré, couches `count >= 10`, `R ≤ 50 000`

Après profilage des centres sélectionnés du run `relaxed7 / non-square / R ≤ 50 000`, plusieurs couches de richesse ont été testées en Pass 2.

Résultats cumulés :

```text
count >= 32 : 6 656 centres, 221 614 offsets, 0 résultat
count >= 24 : 53 226 centres, 1 346 542 offsets, 0 résultat
count >= 16 : 457 060 centres, 7 952 316 offsets, 0 résultat
count >= 12 : 1 363 694 centres, 18 894 170 offsets, 0 résultat
count >= 10 : 1 546 979 centres, 20 752 424 offsets, 0 résultat
count >=  9 :   1 699 797 centres → 0 résultat
```

#### Résultat :

> Aucun candidat ≥ 7/9 n’a été trouvé parmi les centres non carrés de richesse count >= 9 jusqu’à R ≤ 50 000.

Interprétation :

La richesse brute en offsets autour d’un centre ne suffit pas à produire une configuration magique 7/9. Les couches hautes et intermédiaires sont désormais éliminées expérimentalement. Descendre à count >= 8 devient nettement plus coûteux, car cette couche contient environ 7,24 millions de centres. La suite recommandée est soit de traiter count8 par tranches, soit de passer à une v2.3 avec filtrage structurel plus fort.


### B2-v2.2 — relaxed7, centre non carré, couches riches `R ≤ 75 000`

Après le run brut `relaxed7 / non-square / R ≤ 75 000`, les centres sélectionnés ont été profilés par richesse (`count`). Le profil contient 133 515 666 centres sélectionnés, avec un maximum `count = 64`.

Couches testées en Pass 2 :

```text
count >= 64 :      13 centres,        832 offsets, 0 résultat
count >= 48 :     957 centres,     46 291 offsets, 0 résultat
count >= 40 :   1 804 centres,     80 347 offsets, 0 résultat
count >= 36 :   5 792 centres,    223 997 offsets, 0 résultat
count >= 32 :  24 475 centres,    822 043 offsets, 0 résultat
count >= 24 : 160 678 centres,  4 112 871 offsets, 0 résultat
count >= 20 :   205 559 centres → 0 résultat
count >= 16 : 1 246 528 centres → 0 résultat
```

**Conclusion provisoire** :

> Aucun candidat ≥ 7/9 n’a été trouvé parmi les centres non carrés de richesse count >= 16 jusqu’à R ≤ 75 000.

**Suite prévue** :

La couche count >= 12 contient 3 454 727 centres et devra être traitée avec prudence ou par échantillonnage plafonné.


---

## Branche C — centre carré et quatre coins carrés

Cette branche impose que le centre et les quatre coins soient carrés parfaits :

```text
a, c, e, h, j carrés
```

Les quatre autres cases `b, d, f, i` sont ensuite déduites et testées.

Résultats synthétiques :

|      Borne | Configurations | Meilleur résultat |
| ---------: | -------------: | ----------------: |
| E ≤ 20 000 |            179 |              6/9 |
| E ≤ 60 000 |            614 |              6/9 |

Aucun 7/9 ni 8/9 trouvé dans cette famille.

Résumé détaillé du test principal :

```text
Borne : E ≤ 60 000
Paires (A,J) trouvées : 91 967
Centres E concernés : 40 891
Configurations valides : 614
Meilleur résultat : 6 carrés sur 9
Aucun 7/9
Aucun 8/9
Durée : 11 697 s ≈ 3 h 15 min
```

Répartition des carrés bonus parmi `b, d, f, i` :

```text
i carré : 354 cas
f carré : 165 cas
d carré : 78 cas
b carré : 17 cas
```

Donc la case `i = a + c - e` est de loin celle qui devient le plus souvent carrée dans cette famille.

### Multiples triviaux

Sur les 614 résultats, seulement 75 ont un facteur carré commun égal à 1. Les 539 autres sont très probablement des dilatations de configurations plus petites.

### Conclusion de la branche C

> Dans la famille des carrés magiques 3×3 où le centre et les quatre coins sont imposés carrés, la recherche jusqu’à `E ≤ 60 000` donne 614 configurations valides, toutes avec exactement 6 carrés sur 9. Aucun 7/9 ni 8/9 n’a été trouvé.

Cette branche constitue donc une bonne branche négative documentée.

---

## Branche D — une seule progression de carrés autour du centre

### D.1. Idée

On fixe une progression arithmétique de carrés autour du centre :

```text
A², E², J²
```

avec

```text
A² + J² = 2E²
```

puis on balaie un paramètre libre `q` pour tester les six autres cases :

```text
E²+q
E²-q
J²+q
J²-q
A²+q
A²-q
```

Cette famille contient le carré de Bremner.

### D.2. Seuil minimal pour retrouver Bremner

Le carré de Bremner est retrouvé dès que :

```text
A = 205
E = 425
J = 565
q = 41496
```

Donc les seuils minimaux sont :

```text
limit >= 425
qmax  >= 41496
min-total = 7
```

### D.3. Ancienne version relâchée

Script historique :

```text
magic_square_relaxed_search.py
```

Conclusion historique : ce script retrouve Bremner et ses multiples triviaux, mais n’a pas produit de nouveau 8/9.

---

## Branche D' — script optimisé parallèle et criblé

Nouveau script :

```text
src/magic_square_parallel_optimized.py
```

### D'.1. Optimisations intégrées

Le script optimisé combine :

1. génération streaming des triplets `(A,E,J)` via triplets pythagoriciens ;
2. borne de rejet immédiate dépendant de `qmax` ;
3. crible modulaire par triplet ;
4. génération sparse des seuls `q` compatibles avec une proximité à un carré ;
5. filtrage modulaire des `q` ;
6. déduplication finale des multiples triviaux.

Cette version est beaucoup plus rapide que la version dense de balayage complet sur `q`.

### D'.2. Résultats 7/9 — campagnes larges

| Campagne | Paramètres principaux | Triplets traités | Résultat distinct |
| --- | --- | ---: | --- |
| P2 | `limit=50 000`, `qmax=100 000`, `min-total=7` | 75 196 | Bremner seul |
| P5A | `limit=75 000`, `qmax=150 000`, `min-total=7` | 117 620 | Bremner seul |
| P7 | `limit=250 000`, `qmax=500 000`, `min-total=7` | 440 007 | Bremner seul |
| P9 | `limit=500 000`, `qmax=1 000 000`, `min-total=7` | 935 188 | Bremner seul |

Détails marquants :

- `P7` : 3 résultats bruts à 7/9, tous équivalents après déduplication ;
- `P9` : 4 résultats bruts à 7/9, correspondant à Bremner et à ses multiples triviaux `k=2,3,4`.

Conclusion 7/9 :

> Dans cette famille, jusqu’à `E ≤ 500 000` et `q ≤ 1 000 000`, aucun nouveau 7/9 primitif n’a été trouvé. Le seul 7/9 distinct rencontré est le carré de Bremner.

### D'.3. Résultats 8/9 — campagnes larges

| Campagne | Paramètres principaux | Triplets traités | Résultat |
| --- | --- | ---: | --- |
| P3 | `limit=50 000`, `qmax=100 000`, `min-total=8` | 75 196 | aucun 8/9 |
| P5B | `limit=75 000`, `qmax=150 000`, `min-total=8` | 117 620 | aucun 8/9 |
| P8 | `limit=250 000`, `qmax=500 000`, `min-total=8` | 440 007 | aucun 8/9 |
| P8b | `limit=250 000`, `qmax=500 000`, `min-total=8`, `strict-24` | 440 007 | aucun 8/9 |
| P9b | `limit=500 000`, `qmax=1 000 000`, `min-total=8`, `strict-24` | 935 188 | aucun 8/9 |

Conclusion 8/9 :

> Aucun 8/9 n’a été trouvé dans cette branche, y compris avec le crible plus agressif `strict-24`, jusqu’à `E ≤ 500 000` et `q ≤ 1 000 000`.

### D'.4. Cartographie 6/9

Campagne de cartographie :

```text
limit = 250 000
qmax = 500 000
min-total = 6
moduli = 16,5,7,11
```

Résultat :

```text
Triplets traités : 440 007
Résultats bruts retenus : 249
Multiples triviaux retirés : 183
Configurations distinctes : 66
Répartition : 65 cas à 6/9, 1 cas à 7/9
```

Cette cartographie est importante, car elle révèle plusieurs corridors fertiles à 6/9 sans produire de nouveau 7/9.

Observations qualitatives :

- le corridor autour de `E = 425` est particulièrement remarquable ;
- plusieurs triplets admettent plusieurs valeurs de `q` donnant 6/9 ;
- certains motifs de masque (`square_mask`) semblent plus structurés que d’autres.

Exemple de corridor notable :

```text
A=205 E=425 J=565  q=41496  -> 7/9  (Bremner)
A=289 E=425 J=527  q=41496  -> 6/9
A=355 E=425 J=485  q=42504  -> 6/9
A=205 E=445 J=595  q=31416  -> 6/9
A=267 E=447 J=573  q=48488  -> 6/9
```

### D'.5. Reruns ciblés sur une shortlist de triplets prometteurs

Fichier ciblé :

```text
results/promising/triples_prometteurs_phase2.csv
```

Contenu : 21 triplets sélectionnés à partir de la cartographie 6/9.

Campagnes exécutées :

| Campagne | Paramètres principaux | Résultat |
| --- | --- | --- |
| TARGET-T7 | `qmax=5 000 000`, `min-total=7` | Bremner seul |
| TARGET-T8 | `qmax=5 000 000`, `min-total=8` | aucun 8/9 |
| TARGET-T8-s24 | `qmax=5 000 000`, `min-total=8`, `strict-24` | aucun 8/9 |
| TARGET-T8-s24-bis | `qmax=10 000 000`, `min-total=8`, `strict-24` | aucun 8/9 |

Conclusion ciblée :

> Même en poussant `qmax` à 5 millions puis 10 millions sur une shortlist de 21 triplets prometteurs, aucun nouveau 7/9 ni aucun 8/9 n’a été trouvé. Le seul 7/9 détecté reste Bremner.

### D'.6. Conclusion générale de la branche D'

> La branche “une seule progression de carrés autour du centre”, dans sa version optimisée, a été poussée jusqu’à près d’un million de triplets utiles et `q ≤ 1 000 000` en balayage large, puis jusqu’à `q ≤ 10 000 000` sur une shortlist ciblée de 21 triplets prometteurs. Aucun nouveau 7/9 primitif ni aucun 8/9 n’a été trouvé. Le seul 7/9 distinct observé est le carré de Bremner.

Cette branche est désormais très bien documentée expérimentalement. Elle reste utile, mais les gains futurs viendront probablement davantage d’un ciblage structurel plus fin que d’une simple augmentation uniforme des bornes.

---

## Branche E — semi-magique centre zéro

Avec `e = 0`, on peut utiliser une paramétrisation plus simple.

Si les quatre coins sont :

```text
A²      C²
H²      J²
```

alors le carré semi-magique associé est :

```text
A²        H² + J²      C²
C² + J²   0            A² + H²
H²        A² + C²      J²
```

La somme commune vaut :

```text
S = A² + C² + H² + J²
```

Le but est de choisir `A, C, H, J` de sorte que les quatre sommes :

```text
H² + J²
C² + J²
A² + H²
A² + C²
```

soient elles aussi des carrés.

Commande de test historique :

```bash
python search_semimagic_e0_squares.py --max-root 100 --min-squares 7 --primitive-only --limit 10 --csv results_semimagic_e0.csv
```

Exemple obtenu rapidement :

```text
15² | 60² | 20²
52² | 0   | 39²
36² | 25² | 48²
```

En valeurs :

```text
225  | 3600 | 400
2704 | 0    | 1521
1296 | 625  | 2304
```

Les lignes et colonnes valent toutes :

```text
4225 = 65²
```

Donc on obtient :

```text
8 carrés positifs sur les 8 cases non nulles
```

ou, si l’on compte aussi `0 = 0²`, un semi-magique dégénéré à `9/9`.

### Statut conceptuel

Cette famille est intéressante pour l’exploration et la pédagogie, mais elle n’est pas le cœur du problème historique des carrés magiques 3×3 de carrés parfaits distincts, puisque :

1. le centre nul rend la famille dégénérée du point de vue du problème classique ;
2. les diagonales ne sont pas, en général, égales à la somme magique.

Elle reste néanmoins une branche constructive utile.

---

## Conclusion générale au 2026-07-08

À ce stade, les différentes branches donnent le tableau suivant :

- **branche A** : Bremner seul à 7/9 ; aucun 8/9 ni 9/9 dans les bornes historiques ;
- **branche B** : aucun 8/9 jusqu’à racines extérieures `≤ 20 000` ;
- **branche C** : beaucoup de 6/9, aucun 7/9 ni 8/9 ;
- **branche D'** (script optimisé) : vaste exploration de la famille à une progression de carrés autour du centre, avec cartographie 6/9 riche mais aucun nouveau 7/9 ni 8/9 ;
- **branche E** : semi-magique centre zéro très fertile, mais hors du cœur du problème magique complet.

La meilleure piste pour la suite n’est probablement plus une simple montée uniforme des bornes. La prochaine étape naturelle est une recherche computationnelle plus vaste mais aussi plus structurée :

1. exploitation systématique des familles fertiles à 6/9 ;
2. ciblage automatique des triplets prometteurs ;
3. cribles plus fins par motifs de cases carrées ;
4. exploration plus large des branches non centrées sur la progression unique autour du centre.

---

## Références rapides

- Bremner, *On squares of squares* (1999) : http://www.multimagie.com/Bremner1.pdf
- Bremner, *On squares of squares II* (2001) : http://www.multimagie.com/Bremner2.pdf
- MystiMath — problème ouvert : https://mystimath.org/fr/articles/carre-magique-3x3-carres-parfaits-probleme-ouvert/
- MystiMath — recherche expérimentale : https://mystimath.org/fr/articles/recherche-experimentale-carres-magiques-de-carres/
- MystiMath — centre zéro : https://mystimath.org/fr/articles/carres-semi-magiques-centre-zero/
- Magic square of squares (synthèse) : https://en.wikipedia.org/wiki/Magic_square_of_squares
