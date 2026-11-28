# Animations des campagnes — décisions de l'atelier

Une ligne par planche. Ce qui est choisi est figé dans les planches suivantes.

| Planche | Question | Choix d'Antoine | Conséquence |
|---|---|---|---|
| 1 | Mise en scène de la fenêtre Aventure | **C · Théâtre** (27 nov. 2026) | La scène prend toute la largeur (décor fin 192 × 80 affiché ×5 = 960 × 400) ; le texte vient par répliques dans une boîte de dialogue sous la scène, avec le portrait de qui parle ; les choix se posent sur la scène ; l'historique passe dans un carnet. Pilou vit dans le lieu (mini-Pilou), plus de boîte à gauche. |

| 2 | Taille du mini-Pilou en scène | **M · Pilou** (27 nov. 2026) | Corps 20 × 15 pixels fins (100 px à l'écran ×5), yeux ronds 4 × 4 à reflet, bouche qui s'ouvre, étincelle à cinq branches ; toile 34 × 36, pieds sur la ligne 33. |
| 2 bis | Personnages en pied dans la scène | **Oui, tous les 29** (27 nov. 2026) | Chacun en pied (environ 44 px de haut pour un adulte) : repos qui respire, clignement, parole, et un geste à lui ; le portrait reste dans la boîte de dialogue. Dessinés campagne par campagne. |

| 3 | Liens avec le Pilou du bureau | **Les quatre** (27 nov. 2026) | Échos de la scène (fenêtre ouverte : il se tourne vers elle, frissonne, saute au choix) ; bout de décor sous ses pieds pendant l'attente et, rarement, un acteur du lieu qui passe ; départ et retour joués (baluchon, arrivée par le bord avec une enveloppe) ; objets du sac portés pendant l'attente. Tout reste muet et rare. |

## Constats de départ (audit du 27 novembre 2026)

- La bande de décor faisait 118 px de haut en `UniformToFill` : on ne voyait que le tiers haut du dessin (à « La mare »,
  ni la mare ni les nénuphars).
- Pilou vivait dans une boîte séparée (ciel étoilé fixe), sans lien avec le lieu.
- Les décors bouclent sur 6 à 8 images à 4–5 images par seconde : de la vibration d'ambiance, rien ne traverse la scène.
- Aucune interaction dans la scène (`IsHitTestVisible = false`).
