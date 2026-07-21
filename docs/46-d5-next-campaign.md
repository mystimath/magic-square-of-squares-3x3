# D5 — Sélection ciblée de nouvelles courbes elliptiques

## Tâches de la prochaine session

Objectif : chercher un nouveau like-Bremner sans augmenter uniformément la borne
sur les courbes déjà traitées.

1. Construire une liste de nouvelles valeurs `n` sans facteur carré, en priorité
   au-delà de `n=200`.
2. Retenir d'abord les courbes `E_n` de rang Sage certifié au moins 2 avec des
   générateurs de faible hauteur.
3. Appliquer le moteur D3 privilégié avec une boîte de coefficients `[-10,10]`.
4. Mesurer pour chaque courbe les centres certifiés, paires, survivants locaux,
   tests exacts, fermetures et candidats 7/9.
5. Réserver `[-20,20]` aux courbes présentant un signal favorable ; valider
   chaque fermeture par D4 → B4.
6. Arrêter la tranche après environ 100 courbes sans fermeture ni amélioration
   du rendement, puis étudier une famille paramétrée issue de la fibration
   elliptique de Bremner.

La campagne ne doit pas relancer uniformément les 71 courbes déjà couvertes,
ni augmenter `R` au-delà des validations B4–B6 existantes.