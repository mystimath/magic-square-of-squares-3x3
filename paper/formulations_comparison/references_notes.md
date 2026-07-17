# Notes bibliographiques — comparaison des formulations

_État au 17 juillet 2026. Ce fichier consigne les notices vérifiées et les
décisions bibliographiques retenues pour la diffusion 1.0._

## Source Lucas collationnée le 17 juillet 2026

Les pages 224–225 du tome IV des *Récréations mathématiques*, volume Google
Books `Ea8AAAAAMAAJ`, ont été collationnées directement :
<https://play.google.com/books/reader?id=Ea8AAAAAMAAJ&pg=GBS.PA224&hl=en>.

Lucas centre d'abord le carré, réduit sa forme à deux paramètres, puis donne
p. 225 le tableau

```text
-p      p+q     -q
p-q      0      q-p
 q      -p-q     p
```

Après réintroduction du centre `x²` et substitution
`p=x²-y², q=x²-z²`, les neuf cases coïncident terme à terme avec le §3 du
manuscrit. Les p. 224–225, citées par Nordgren, sont donc la source pertinente.
La p. 226 ouvre le problème distinct des « carrés à deux degrés » ; son tableau
ne doit pas être présenté comme la source de la forme centrée employée ici.

Les captures servent de justificatifs bibliographiques mais ne sont pas
incluses dans l'archive MIT : cette licence ne peut pas être étendue
automatiquement aux images d'un ouvrage numérisé. La lecture de l'article de
1876, p. 97–101, confirme séparément que Lucas y pose explicitement le défi du
carré magique de neuf carrés.

## État récent du problème (2025–2026)

### Rome–Yamagishi 2025

Nick Rome et Shuntaro Yamagishi, « On the existence of magic squares of
powers », *Research in Number Theory* 11, article 91, 2025. DOI
`10.1007/s40993-025-00671-5`.

Article évalué par les pairs :
<https://doi.org/10.1007/s40993-025-00671-5>.

L'article démontre l'existence de carrés magiques de carrés pour tout ordre
`k≥4` et traite encore le cas `k=3` comme non résolu. Il constitue la référence
récente retenue pour l'état établi du problème.

### Hill 2026

Oscar Hill, « On Arithmetic Progressions and a Proof of the Nonexistence of
Magic Squares of Squares », arXiv:2510.08286 [math.GM], version 3 du
7 avril 2026. DOI `10.48550/arXiv.2510.08286`.

Prépublication : <https://arxiv.org/abs/2510.08286>.

Cette prépublication revendique la non-existence d'un carré magique 3×3 de
carrés. La version 3 a été lue intégralement. À l'étape finale, l'égalité (29)
porte sur des valeurs arithmétiques fixées du paramètre ; le paragraphe suivant
compare pourtant les coefficients des expressions correspondantes comme si une
identité polynomiale dans ce paramètre avait été établie. Aucune justification
de cette promotion en identité n'est fournie. La contradiction annoncée dépend
de ce passage.

Le manuscrit cite donc cette revendication récente, mais ne l'adopte pas comme
théorème. En l'absence d'une correction de ce point ou d'une validation
indépendante, le statut retenu reste celui de la littérature évaluée par les
pairs : problème ouvert pour l'ordre 3.

## Références vérifiées

### Bremner 1999

Andrew Bremner, « On squares of squares », *Acta Arithmetica*, volume 88,
numéro 3, pages 289–297, 1999. DOI `10.4064/aa-88-3-289-297`.

Notice primaire et PDF :
<https://www.impan.pl/en/publishing-house/journals-and-series/acta-arithmetica/all/88/3/110732/on-squares-of-squares>.

Le PDF intégral a été audité. Le §1 reprend de Robertson l'équivalence entre une
grille magique de carrés et trois points de `2E(Q)` dont les abscisses sont en
progression. Le témoin 7/9 figure p. 290. L'objet principal de l'article est
cependant l'autre problème partiel : neuf entrées carrées et sept sommes égales
sur huit. Aux p. 292–294, un point d'ordre infini sur une courbe sur `Q(λ)`, ses
multiples, une fibration elliptique et la formule de Shioda produisent des
familles paramétrées. Bremner 1999 ne doit donc pas être réduit à une recherche
de points isolés et n'introduit pas le cadre K3 développé en 2001.

### Bremner 2001

Andrew Bremner, « On squares of squares II », *Acta Arithmetica*, volume 99,
numéro 3, pages 289–308, 2001. DOI `10.4064/aa99-3-6`.

Notice primaire et PDF :
<https://www.impan.pl/en/publishing-house/journals-and-series/acta-arithmetica/all/99/3>.

Le PDF intégral a été audité. L'article porte sur les seize configurations de
six cases carrées dans une grille pleinement magique. Le §2 (p. 291–297)
construit des familles par des courbes elliptiques ; le §3 (p. 298–305) étudie
en détail une intersection non singulière de trois quadriques dans `P^5`, donc
une surface K3, ses fibrations, ses rangs et ses points d'ordre infini ; le §4
(p. 306–307) poursuit sur `Q(√3)`. Il systématise et approfondit ainsi la
géométrie globale, mais n'est pas le premier des deux articles à utiliser
fibrations, rangs ou familles.

### Bremner 1980

Andrew Bremner, « Pythagorean triangles and a quartic surface », *Journal für
die reine und angewandte Mathematik* 318, pages 120–125, 1980. DOI
`10.1515/crll.1980.318.120`.

La notice et le DOI sont vérifiés. Ce travail est la référence directement
topique pour les paramétrisations de triangles pythagoriciens de même aire
réutilisées par Bremner en 1999 et citées au §4.3 du manuscrit.

### Fibonacci–Sigler 1987

Leonardo Pisano Fibonacci, *The Book of Squares (Liber Quadratorum)*,
traduction annotée par L. E. Sigler, Academic Press, 1987,
ISBN `0-12-643130-2`.

La Proposition 14, p. 53–74, traite le problème du *congruum* : déterminer un
nombre qui, ajouté à un carré ou soustrait de celui-ci, donne encore un carré.
Ce passage fournit le contexte historique cité au §6 ; la preuve moderne de la
paramétrisation reste référencée séparément par Conrad.

### Koblitz 1984

Neal Koblitz, *Introduction to Elliptic Curves and Modular Forms*, Graduate
Texts in Mathematics 97, Springer-Verlag, 1984. DOI
`10.1007/978-1-4684-0255-1`, ISBN `0-387-96029-5`.

Le chapitre I passe des nombres congruents (p. 3) à une équation cubique (p. 6),
puis aux courbes elliptiques (p. 9). La p. 36 ouvre la section sur les points
d'ordre fini ; elle n'est donc pas citée comme source du critère de 2-descente
propre au manuscrit, mieux attesté par Robertson et Bremner 1999.

### Silverman 2009

Joseph H. Silverman, *The Arithmetic of Elliptic Curves*, Graduate Texts in
Mathematics 106, Springer, 2ᵉ édition, 2009. DOI
`10.1007/978-0-387-09494-6`.

Le chapitre VIII, §9, donne la définition et les propriétés de la hauteur
canonique ; le chapitre X traite le calcul du groupe de Mordell–Weil. Cette
référence [16] soutient désormais la distinction entre borne entière sur les
racines et borne de hauteur elliptique aux §4.4, §15 et §18.

## Statut des références Lucas et LaBar

La forme centrée est attribuée à la source primaire [12], p. 224–225, après
collation terme à terme. La p. 226 relève d'un sujet voisin et n'est pas
utilisée comme preuve. La lecture de [11, p. 97–101] confirme directement que
Lucas pose en 1876 le défi du carré magique de neuf carrés. L'ouvrage de 1873
reste une référence générale sur l'analyse indéterminée, non la source de la
forme centrée.

La notice de LaBar est : M. LaBar, « Problem 270 », *College Mathematics
Journal* 15 (1984), p. 69. Elle est corroborée par les bibliographies de
Bremner et figure dans le manuscrit comme référence [9].

## Décisions éditoriales et travaux ultérieurs

Les références indispensables mobilisées par le manuscrit ont été identifiées
et leurs attributions principales contrôlées. Les décisions suivantes sont
retenues pour la diffusion 1.0 :

1. Gardner reste couvert par le panorama historique de Boyer, car aucun
   résultat technique de Gardner n'est utilisé ;
2. Sallows n'est pas ajouté, faute d'affirmation du manuscrit qui dépende
   directement de ses travaux ;
3. une référence algorithmique plus spécialisée sera ajoutée si une véritable
   énumération elliptique sous hauteur est implémentée ultérieurement ;
4. une relecture scientifique externe demeure recommandée, sans constituer un
   défaut bibliographique de l'archive reproductible.

## Règle éditoriale

Tout futur marqueur `[Référence à vérifier]` ou `[Source primaire nécessaire]`
ne devra être supprimé qu'après consultation effective de la source
correspondante.
Les documents Web secondaires ne doivent pas servir de seule autorité pour une
affirmation mathématique importante.
