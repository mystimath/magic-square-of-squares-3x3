# Moteur Lo Shu spécialisé pour un « like-Bremner »

_Prototype, régression et mesures exécutés le 18 juillet 2026._

## 1. But et statut scientifique

La paramétrisation de Lo Shu n'est pas présentée comme une nouveauté
mathématique. Elle sert ici à réduire le coût logiciel d'une recherche ciblée :
un carré pleinement magique, positif, à neuf valeurs distinctes, dont exactement
sept cases sont des carrés, avec le masque canonique de l'exemple de Bremner
`acdefgh`.

Le prototype est une branche spécialisée. Il ne remplace ni le moteur général
v2.2 SAFE, conservé comme oracle, ni les pistes elliptiques destinées à construire
des familles.

## 2. Forme utilisée

La grille est écrite

```text
 B       C+2r    A+r
 A+2r    B+r     C
 C+r     A       B+2r
```

Elle est pleinement magique si et seulement si

```text
A + C = 2B.
```

Le masque `acdefgh` impose alors :

- une progression de trois carrés `(A, A+r, A+2r)` ;
- une progression de trois carrés `(A, B, C)` ;
- les carrés supplémentaires `B+r` et `C+r` ;
- les non-carrés exacts `C+2r` et `B+2r`.

Le moteur joint donc seulement deux progressions de trois carrés ayant le même
premier terme `A`, puis effectue deux tests d'appartenance à l'ensemble des
carrés. Il valide ensuite le masque exact, la positivité, la distinction des neuf
valeurs, la primitivité des sept racines et la classe diédrique D4.

## 3. Paramètres de Bremner et borne correcte

Pour l'exemple connu :

```text
A = 529       = 23²
B = 139129    = 373²
C = 277729    = 527²
r = 41496
q = B-A       = 138600
```

on reconstruit exactement

```text
139129  360721   42025
 83521  180625  277729
319225     529  222121
```

La somme magique est `541875`. La plus grande racine parmi les sept cases
carrées vaut `565`, mais cette convention ne borne pas les deux non-carrés. La
borne de boîte complète est bien `R=601`, car

```text
600² = 360000 < 360721 < 361201 = 601².
```

La régression vérifie donc zéro classe à `R=600` et exactement la classe de
Bremner à `R=601`.

## 4. Comparaison expérimentale

Les deux adaptateurs reçoivent le même catalogue paramétrique de progressions de
trois carrés. Les temps ci-dessous sont des médianes, sauf la ligne `R=100000`
qui n'a qu'une répétition à cause du coût de la mesure mémoire de v2.2.

| Borne | Catalogue | Lo Shu ciblé | v2.2 SAFE, catalogue partagé | Accélération |
| ---: | ---: | ---: | ---: | ---: |
| `601` | 351 | 0,003759 s | 0,020501 s | `5,45×` |
| `100000` | 122640 | 3,453566 s | 22,477677 s | `6,51×` |

À `R=100000`, les deux moteurs retrouvent exactement l'unique classe historique
de Bremner. Le nouveau moteur teste 635968 couples ordonnés de progressions et
1271936 appartenances à l'ensemble des carrés. Il obtient 176 extensions : 175
sont des dilatations non primitives et une seule classe primitive subsiste.

Le pipeline historique v2.2 complet avait demandé `865,826 s`. Le catalogue
paramétrique actuel (`4,922 s`) suivi du moteur ciblé (`3,454 s`) demande environ
`8,375 s`, soit un gain opérationnel proche de `103×`. Cette dernière comparaison
inclut toutefois une différence d'architecture (fichiers, multiprocessus et
passes intermédiaires dans l'ancien pipeline) ; le facteur comparable entre les
deux adaptateurs reste `6,51×`.

Résultats reproductibles :

- `results/formulations_comparison/benchmarks/like_bremner_v2_2_r601.json` ;
- `results/formulations_comparison/benchmarks/like_bremner_v2_2_r100000.json`.

## 5. Limite observée de v2.3

Le filtre v2.3 « structural » exige qu'au moins une paire bonus soit une paire
opposée complète autour du centre. Cette réduction est motivée par le cas à
centre non carré. Bremner possède au contraire un centre carré et complète ses
sept carrés avec un seul élément dans chacune de deux paires bonus. Le filtre
v2.3 renvoie donc zéro candidat, y compris sur le centre exact `180625` et à
`R=100000`.

En conséquence, v2.3 ne doit pas servir d'oracle pour ce motif à centre carré.
Le test de non-régression consigne explicitement que v2.2 trouve la classe à
`R=601` tandis que v2.3 ne la couvre pas.

## 6. Utilisation

Depuis la racine du dépôt :

```powershell
python experiments\formulations_comparison\search_like_bremner.py --complete-box-root 601
```

La commande impose `0 < case <= R²` aux neuf valeurs et écrit un CSV de résultats
ainsi qu'un résumé JSON dans `results/raw/`. L'option `--all-scalings` conserve
également les dilatations non primitives.

Benchmark comparatif :

```powershell
python experiments\formulations_comparison\benchmark_like_bremner_v2_2.py `
  --max-square-root 601 --repeats 5
```

## 7. Recommandation pour la suite

La branche Lo Shu ciblée est suffisamment rapide et validée pour devenir le
scanner principal du motif `acdefgh`. v2.2 reste le contrôle général. Le filtre
précoce de primitivité est mesuré dans le document 26 ; le groupement par `A`,
l'index PGCD, le streaming et le domaine paramétrique canonique sont désormais
réalisés et mesurés dans le document 27. Toute extension à d'autres masques 7/9
devra recevoir sa propre preuve de couverture et une comparaison indépendante
avec v2.2.