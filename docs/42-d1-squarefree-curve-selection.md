# D1 — Sélection de courbes elliptiques sans facteur carré

_Étape ouverte le 21 juillet 2026._

## But

D0 fonctionne à courbe fixée. D1 sélectionne un ensemble fini et explicite de
courbes candidates sans partir d’une borne sur les racines : pour chaque entier
positif sans facteur carré `n` dans une petite plage, Sage certifie le rang de

```text
E_n : y² = x³ - n²x.
```

Seules les courbes de rang au moins deux sont transmises à D0, avec une petite
boîte de coefficients. Le résultat est une campagne de découverte par courbes,
non une recherche exhaustive dans une boîte de grilles.

## Pilote initial

- représentants sans facteur carré : `1 <= n <= 200` ;
- rang Sage demandé avec `proof=True` ;
- seuil : rang au moins 2 ;
- D0 : coefficients `[-1,1]^r` ;
- contrôle interne : `n=154` doit être retenu et produire Bremner après
  normalisation entière.

## Limites

Un rang élevé ne garantit ni un candidat 7/9 ni une borne de couverture sur les
carrés magiques. Ce pilote sert à mesurer la densité de courbes exploitables, le
coût du calcul de rang et le rendement réel de D0 avant toute extension de la
plage de `n`.
## Résultat du pilote `n <= 200`

La campagne a considéré 122 représentants positifs sans facteur carré. Sage a
certifié neuf courbes de rang 2 :

```text
34, 41, 65, 137, 138, 145, 154, 161, 194.
```

Quatre calculs de rang n’ont pas abouti à un certificat de rang certain ; ils
sont enregistrés dans le manifeste comme `rank_error` et ne sont pas classés.
Pour chacune des neuf courbes retenues, D0 a énuméré la boîte minimale
`[-1,1]^2`. Toutes ont fourni quatre centres certifiés ; seule `n=154` ferme une
configuration 7/9, dont la normalisation entière est Bremner.

Artefact reproductible :
`results/formulations_comparison/sage/d1_squarefree_n200_rank2_bound1.json`.

## Décision D1

Le filtre « rang certifié au moins deux » réduit fortement la famille de
courbes, mais ne suffit pas à prédire une fermeture 7/9 : huit des neuf courbes
retenues sont négatives à cette hauteur. La suite ne doit donc pas être une
extension uniforme de `n`. Avant `n>200`, comparer sur ces neuf courbes des
boîtes de coefficients progressivement élargies et relever les invariants des
paires de centres qui échouent de peu à la fermeture horizontale.
