# État du travail

À mettre à jour à la fin de chaque session : ce qui est fait, ce qui est en cours, ce qui attend.
Dernière mise à jour : 27 novembre 2026.

## En ligne (v0.9.62)

- Overlay Windows, app Android, mod Claude Code, extensions VS Code et Visual Studio.
- Boutique garnie, métiers et succès partagés entre appareils, expéditions, Défense du bureau,
  visites entre amis, connecteurs, météo.
- Dessin fin 2× (visage, cosmétiques, tenues de voyage, boutique, pêche, cuisine, variantes, bonus, particules : tous les sprites hors décors de campagne).
- Moteur des campagnes (PC et Android, validateur, synchronisation) et quatre histoires : prologue,
  La Grande Panne, Le phare éteint, Petit Nuage. **Aucune interface ne permet encore de les jouer.**

## En cours (branches `claude/…`, une PR chacune)

| Branche | Travail |
|---|---|
| `android-aventure` | Refonte de l'app Android : onglet Aventure (conversation, épreuves, attente), notification de retour, bulle flottante, accueil repensé |
| `windows-aventure` | Campagnes sur Windows : Pilou occupé, annonce de retour, fenêtre Aventure, épreuves, récompenses, scènes d'essai |
| `relecture-petit-nuage` | Relecture de tous les parcours, orthographe, dosage des fins |
| `relecture-grande-panne` | Idem, plus le prologue |
| `relecture-phare-eteint` | Idem, plus la loyauté de l'enquête |
| `animations-campagnes` | Décors animés en boucle, portraits animés de 29 personnages (champ `personnage` des nœuds), écriture lettre à lettre, volet entre décors, fond selon le ton et l'heure, réglage des animations (PC et Android) |
| `illustrations-campagnes` | Décors `decor-<campagne>-<id>`, objets exclusifs des fins, vignettes de souvenirs, 80 sprites de plus en fin |
| `presence` | Présence au quotidien (docs/PRESENCE.md) : 573 petits mots, cadence (3 par jour sur PC, 1 le soir sur téléphone), complicité, dates, journal identique des deux côtés, prénom, « Pilou et moi » |

## Ensuite

1. **Présence au quotidien, la suite** : relire les mots et le journal sur une vraie semaine (PC et téléphone),
   ajuster les seuils de complicité si les paliers arrivent trop vite ou trop lentement.
2. **Test de jeu complet** : parcours entiers rejoués par le moteur des deux côtés, synchronisation
   entre appareils, revue des captures de chaque écran.
3. **Vidéo de promo** avec les campagnes. Il faut tourner sur le PC d'Antoine
   (`outils/tourner-ecran-gauche.ps1`) puis monter (scripts dans l'historique : cartons, caméra qui
   suit les rectangles de `chronologie.json`).

## Jamais vérifié sur un vrai appareil

- Sous Windows : le dessin fin sur le bureau (charge, netteté à 125 % et 150 %), les extensions
  d'éditeur, la fenêtre des expéditions, tout ce qui touche aux campagnes.
- Sur téléphone : les métiers, la boutique garnie, la fluidité du dessin fin.
- La présence au quotidien : la cadence d'une vraie journée, la fenêtre Journal, le mot du soir (notification,
  Doze), le widget et la bulle avec le mot, la synchronisation entre deux appareils réels.
- Entre deux PC : le cumul des métiers et des succès, une visite entre amis.

## Points connus

- Lecture des notifications Windows : attend un paquet signé (voir `NOTIFICATIONS.md`).
- Deux écrans à des échelles différentes : Windows étire encore la fenêtre de Pilou sur le second.
- L'exe pèse 128 Mo (.NET embarqué) ; la compression le ramènerait vers 60–70 Mo, non faite.
- Lancer une expédition ou une campagne depuis le téléphone : seule la campagne le permet.
