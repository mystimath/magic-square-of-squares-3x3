# J6bis — Stratégie elliptique et réévaluation à partir de Bremner

_Jalon exécuté le 16 juillet 2026._

## 1. Motif de la révision

J6 a correctement conclu que D ne possédait pas encore de domaine fini directement comparable à la borne entière des formulations A–B. Cette limite expérimentale ne doit pas être interprétée comme un rôle scientifique secondaire.

J6bis sépare désormais deux axes :

- l'exhaustivité dans une boîte entière, où A–B disposent d'une borne naturelle ;
- la découverte arithmétique et la construction de familles, où D est une voie principale.

## 2. Source primaire vérifiée

Andrew Bremner, *On squares of squares*, Acta Arithmetica 88 (1999), 289–297, DOI `10.4064/aa-88-3-289-297`.

Texte intégral : <https://matwbn.icm.edu.pl/ksiazki/aa/aa88/aa8837.pdf>

La section 1 écrit tout carré magique rationnel sous la forme centrée `(a,b,c)`, associe la courbe

```text
E : y² = x(x²-c²),
```

et établit le critère suivant : `{X,X-c,X+c}` est un triplet de carrés rationnels exactement lorsque le point d'abscisse `X` appartient à `2E(Q)`. Le problème 9/9 devient donc la recherche de trois points de `2E(Q)` dont les abscisses sont en progression arithmétique.

La section 2 ne se contente pas d'une validation ponctuelle. Bremner travaille sur une courbe elliptique au-dessus de `Q(λ)`, utilise un point d'ordre infini et ses multiples, étudie une fibration elliptique et des spécialisations de rang au moins deux, puis en déduit des familles paramétrées. C'est un mécanisme de construction et de découverte.

L'article distingue aussi deux problèmes voisins : maximiser les cases carrées d'un carré réellement magique, et maximiser les sommes égales dans une grille composée de carrés. Les familles paramétrées de 1999 concernent principalement le second ; l'article donne séparément un exemple magique à sept cases carrées. Cette distinction doit rester visible dans nos comparaisons.

Référence complémentaire à intégrer lors de son audit détaillé : Andrew Bremner, *On squares of squares II*, Acta Arithmetica 99 (2001), 289–308, DOI `10.4064/aa99-3-6`.

## 3. Nouveau statut de D

D est promue au statut de **moteur principal de découverte théorique et constructive**. Elle n'est pas rétrogradée parce qu'elle ne partage pas encore la même borne que A–B.

Quatre usages sont retenus :

1. **certification elliptique** : vérifier exactement les images issues de B2/C et la divisibilité par 2 ;
2. **découverte ciblée** : choisir des `n`, courbes, rangs ou générateurs prometteurs et explorer leurs combinaisons ;
3. **construction de familles** : imposer les relations de progression aux abscisses sur des familles ou fibrations elliptiques ;
4. **exhaustivité par tranche** : à courbe fixée et groupe de Mordell–Weil certifié, énumérer sous une borne de hauteur prouvée.

Le troisième usage est central dans l'approche de Bremner. Le mot « ciblé » décrit un régime algorithmique, non une limitation du rôle scientifique.

## 4. Deux pistes expérimentales séparées

### Piste entière A–B

Mesures : borne maximale des racines, complétude du domaine final, temps, mémoire, disque, classes primitives.

### Piste elliptique D

Mesures : familles ou courbes traitées, rang certifié, générateurs connus, hauteur canonique couverte, combinaisons énumérées, points dans `2E(Q)`, progressions d'abscisses, dénominateurs, rendement de conversion en configurations 7/9, 8/9 ou 9/9.

Un classement global unique serait trompeur. Le papier final classera les formulations par fonction : exhaustivité, rendement de découverte, pouvoir explicatif et validation indépendante.

## 5. Outillage essayé

État observé le 16 juillet 2026 :

| Élément | Résultat |
| --- | --- |
| `winget search SageMath` | aucun paquet |
| `winget search PARI` | aucun paquet pertinent |
| conda-forge Windows | interrogation expirée après 60 s ; aucune installation effectuée |
| WSL | exécutable présent, fonctionnalité non installée |
| `wsl --install` | échec immédiat : la fonctionnalité WSL doit être activée au niveau Windows |
| SageMath / PARI/GP | toujours absents |

L'autorisation d'installation est acquise, mais l'activation de WSL exige une opération Windows administrateur hors de la session courante et peut imposer un redémarrage. Après activation, la voie recommandée est Ubuntu sous WSL, puis SageMath et PARI/GP depuis les paquets de la distribution ou la procédure officielle compatible.

Aucun paquet partiel et aucun environnement conda supplémentaire n'ont été laissés sur la machine.

## 6. Protocole d'installation à reprendre

Après activation administrateur de WSL et redémarrage éventuel :

1. vérifier `wsl --status` et installer Ubuntu ;
2. mettre à jour l'index des paquets Ubuntu ;
3. vérifier les versions candidates de `sagemath` et `pari-gp` avant installation ;
4. installer les outils dans WSL ;
5. consigner versions, commandes et empreinte de l'environnement ;
6. exécuter un test de fumée sur `E_24`, `Q=(72,576)` et `2Q=(25,35)` ;
7. seulement ensuite développer rang, générateurs, hauteur canonique et divisibilité.

## 7. Porte G4 révisée

- **Comparabilité exhaustive directe avec A–B : fermée pour l'instant.**
- **Faisabilité comme moteur principal de découverte : ouverte.**
- **Benchmark elliptique autonome : ouvert dès que SageMath/PARI est opérationnel.**

Cette décision remplace toute lecture de J6 qui réduirait D à une simple sonde de second plan.

## 8. Sortie de J6bis

Le rôle de D est corrigé dans J6 et dans la feuille de route. L'audit bibliographique primaire justifie la promotion. L'installation a été tentée sans succès destructif ; le seul blocage restant est l'activation administrateur de WSL au niveau Windows. J7 n'est pas commencé.

## 9. Reprise avec SageMath et PARI/GP

L'environnement WSL2 est opérationnel sous Ubuntu 24.04 : SageMath 10.9
(Python 3.12.13) est installé dans l'environnement conda `sage`, et PARI/GP
2.15.4 provient du paquet Ubuntu. Les deux tests de fumée exacts sur
`E_24 : y²=x³-576x` donnent `2(72,576)=(25,35)`.

La sonde `experiments/formulations_comparison/sage_elliptic_probe.py` isole les
calculs formels de la sonde Python rationnelle. Sur le contrôle `n=24`,
`P=(25,35)`, Sage certifie avec l'option `proof=True` :

- rang `1` ;
- torsion de type `[2,2]` ;
- générateur retourné `(-12,72)` ;
- quatre moitiés rationnelles de `P`, dont `(72,576)` ;
- vérification directe de `2Q=P` pour chacune des quatre moitiés.

Commande reproductible depuis la racine du dépôt :

```bash
~/miniforge3/bin/conda run -n sage python \
  experiments/formulations_comparison/sage_elliptic_probe.py
```

Ces calculs portent sur une courbe et un point explicitement fournis. Ils ne
constituent ni une énumération des `n`, ni une recherche exhaustive par hauteur.
La porte G4 reste donc fermée pour la comparabilité exhaustive avec A--B, mais
l'outillage requis pour une piste elliptique autonome limitée est validé.
