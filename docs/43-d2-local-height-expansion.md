# D2 — Élargissement local sur les courbes de rang 2

_Étape ouverte le 21 juillet 2026._

D2 ne sélectionne aucune nouvelle courbe. Il reprend les neuf courbes de rang
certifié 2 issues de D1 et compare les boîtes de coefficients `[-2,2]^2` et
`[-3,3]^2`. Les mesures sont le nombre de centres certifiés, de paires de
centres examinées, de fermetures horizontales carrées et de candidats 7/9.

Le pilote doit confirmer que la croissance de la boîte n’introduit pas de faux
positifs et indiquer si une courbe autre que `E_154` mérite une étude ciblée.
## Résultat

Les neuf courbes ont été exécutées avec `proof=True` aux bornes 2 et 3.
Chaque courbe fournit respectivement 12 puis 24 centres certifiés, donc 66 puis
276 paires de centres. Les huit courbes `34, 41, 65, 137, 138, 145, 161, 194`
ne produisent aucune fermeture horizontale carrée. `E_154` produit exactement
une fermeture et une seule, Bremner, aux deux bornes.

| Boîte | Paires par courbe | Fermetures hors `E_154` | Fermetures sur `E_154` |
| --- | ---: | ---: | ---: |
| `[-2,2]^2` | 66 | 0 | 1 |
| `[-3,3]^2` | 276 | 0 | 1 |

Artefact reproductible :
`results/formulations_comparison/sage/d2_rank2_curves_bounds2_3.json`.

## Décision

D2 est négatif mais informatif : le rang 2 et une petite hauteur ne suffisent
pas à isoler une nouvelle configuration. Ne pas augmenter uniformément la
boîte de coefficients. D3 devra traiter directement la condition de fermeture

```text
2*x_haut - x_bas - n = carré rationnel,
```

sur deux points certifiés de `2E_n(Q)`, afin de sélectionner des paires avant
la reconstruction de la grille.
