# Idées pour plus tard

Réserve d'idées validées par Antoine mais pas encore construites. Avant d'en lancer une, relire les
principes de Pilou : il reste d'abord passif, chaque soin ou action tient en un ou deux clics, il n'y a
pas de mode de difficulté, tout le contenu est original (aucun nom, personnage ou asset de jeu
existant), et aucune couleur ne s'oppose en rouge contre vert : chaque état a aussi un signe de forme.

## Petits jeux de bureau

| Idée | Principe | Remarque |
|---|---|---|
| Tape-taupe des icônes | Des bugs sortent de derrière les icônes du bureau ; un clic les renvoie. | Ne lire que la position des icônes, jamais leur nom. |
| Ping-pong de la barre des tâches | Pilou renvoie une balle qui rebondit le long de la barre des tâches. | Partie courte, uniquement à la demande. |
| Rythme musical | Quand de la musique joue (Spotify ou Core Audio), des notes tombent et il faut cliquer en mesure. | Repose sur la détection audio existante. |
| Course d'escargots | Pari de quelques po sur une course tirée au sort ; Pilou commente l'arrivée. | Gains plafonnés par jour. |
| Memory de la boutique | Retourner des paires de cartes illustrées par les objets de la boutique. | Fait aussi découvrir le catalogue. |

## Notifications et téléphone

- **Lire les notifications Windows** : il faut donner à Pilou une identité de paquet signé (sparse
  package et certificat). L'affichage et les réglages existent déjà ; voir
  [NOTIFICATIONS.md](NOTIFICATIONS.md).
- **Notifications Android** : passer par `NotificationListenerService`, sur activation explicite,
  avec la même règle de confidentialité que sur PC.

## Vidéo

- Refaire la promo avec de vraies images de l'écran de gauche, tournées par
  `outils/tourner-ecran-gauche.ps1`, dès que ce script est fusionné.
